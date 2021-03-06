# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Servlet that searches for issues that the specified user cannot view.

The GET request to a backend has query string parameters for the
shard_id, a user_id, and list of project IDs.  It returns a
JSON-formatted dict with issue_ids that that user is not allowed to
view.  As a side-effect, this servlet updates multiple entries
in memcache, including each "nonviewable:USER_ID;PROJECT_ID;SHARD_ID".
"""

import logging

from google.appengine.api import memcache

from framework import framework_constants
from framework import framework_helpers
from framework import jsonfeed
from framework import permissions
from framework import sql


RESTRICT_VIEW_PATTERN = 'restrict-view-%'

# We cache the set of IIDs that a given user cannot view, and we invalidate
# that set when the issues are changed via Monorail.  Also, we limit the live
# those cache entries so that changes in a user's (direct or indirect) roles
# in a project will take effect.
NONVIEWABLE_MEMCACHE_EXPIRATION = 15 * framework_constants.SECS_PER_MINUTE


class BackendNonviewable(jsonfeed.InternalTask):
  """JSON servlet for getting issue IDs that the specified user cannot view."""

  CHECK_SAME_APP = True

  def HandleRequest(self, mr):
    """Get all the user IDs that the specified user cannot view.

    Args:
      mr: common information parsed from the HTTP request.

    Returns:
      Results dictionary {project_id: [issue_id]} in JSON format.
    """
    if mr.shard_id is None:
      return {'message': 'Cannot proceed without a valid shard_id.'}
    user_id = mr.specified_logged_in_user_id
    user = self.services.user.GetUser(mr.cnxn, user_id)
    effective_ids = self.services.usergroup.LookupMemberships(mr.cnxn, user_id)
    if user_id:
      effective_ids.add(user_id)
    project_id = mr.specified_project_id
    project = self.services.project.GetProject(mr.cnxn, project_id)

    perms = permissions.GetPermissions(user, effective_ids, project)

    nonviewable_iids = self.GetNonviewableIIDs(
      mr.cnxn, user, effective_ids, project, perms, mr.shard_id)

    cached_ts = mr.invalidation_timestep
    if mr.specified_project_id:
      memcache.set(
        'nonviewable:%d;%d;%d' % (project_id, user_id, mr.shard_id),
        (nonviewable_iids, cached_ts),
        time=NONVIEWABLE_MEMCACHE_EXPIRATION)
    else:
      memcache.set(
        'nonviewable:all;%d;%d' % (user_id, mr.shard_id),
        (nonviewable_iids, cached_ts),
        time=NONVIEWABLE_MEMCACHE_EXPIRATION)

    logging.info('set nonviewable:%s;%d;%d to %r', project_id, user_id,
                 mr.shard_id, nonviewable_iids)

    return {
      'nonviewable': nonviewable_iids,

      # These are not used in the frontend, but useful for debugging.
      'project_id': project_id,
      'user_id': user_id,
      'shard_id': mr.shard_id,
      }

  def GetNonviewableIIDs(
    self, cnxn, user, effective_ids, project, perms, shard_id):
    """Return a list of IIDs that the user cannot view in the project shard."""
    # Project owners and site admins can see all issues.
    if not perms.consider_restrictions:
      return []

    # There are two main parts to the computation that we do in parallel:
    # getting at-risk IIDs and getting OK-iids.
    cnxn_2 = sql.MonorailConnection()
    at_risk_iids_promise = framework_helpers.Promise(
      self.GetAtRiskIIDs, cnxn_2, user, effective_ids, project, perms, shard_id)
    ok_iids = self.GetViewableIIDs(
      cnxn, effective_ids, project.project_id, shard_id)
    at_risk_iids = at_risk_iids_promise.WaitAndGetValue()

    # The set of non-viewable issues is the at-risk ones minus the ones where
    # the user is the reporter, owner, CC'd, or granted "View" permission.
    nonviewable_iids = set(at_risk_iids).difference(ok_iids)

    return list(nonviewable_iids)

  def GetAtRiskIIDs(
    self, cnxn, user, effective_ids, project, perms, shard_id):
    """Return IIDs of restricted issues that user might not be able to view."""
    at_risk_label_ids = self.GetPersonalAtRiskLabelIDs(
      cnxn, user, effective_ids, project, perms)
    at_risk_iids = self.services.issue.GetIIDsByLabelIDs(
      cnxn, at_risk_label_ids, project.project_id, shard_id)

    return at_risk_iids

  def GetPersonalAtRiskLabelIDs(
    self, cnxn, _user, effective_ids, project, perms):
    """Return list of label_ids for restriction labels that user can't view."""
    at_risk_label_ids = []
    label_def_rows = self.services.config.GetLabelDefRowsAnyProject(
      cnxn, where=[('LOWER(label) LIKE %s', [RESTRICT_VIEW_PATTERN])])
    for label_id, _pid, _rank, label, _docstring, _hidden in label_def_rows:
      label_lower = label.lower()
      needed_perm = label_lower.split('-', 2)[-1]
      if not perms.CanUsePerm(needed_perm, effective_ids, project, []):
        at_risk_label_ids.append(label_id)

    return at_risk_label_ids

  def GetViewableIIDs(self, cnxn, effective_ids, project_id, shard_id):
    """Return IIDs of issues that user can view because they participate."""
    # Anon user is never reporter, owner, CC'd or granted perms.
    if not effective_ids:
      return []

    ok_iids = self.services.issue.GetIIDsByParticipant(
      cnxn, effective_ids, [project_id], shard_id)

    return ok_iids
