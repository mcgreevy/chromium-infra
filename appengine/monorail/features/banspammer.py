# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Classes for banning spammer users"""

import logging
import webapp2
import json
import time

from datetime import date
from datetime import datetime
from datetime import timedelta

from framework import framework_helpers
from framework import permissions
from framework import jsonfeed 
from framework import servlet
from framework import urls
from google.appengine.api import taskqueue
from google.appengine.api import app_identity
from framework import gcs_helpers

class BanSpammer(servlet.Servlet):
  """Ban a user and mark their content as spam"""

  def AssertBasePermission(self, mr):
    """Check whether the user has any permission to ban users.

    Args:
      mr: commonly used info parsed from the request.
    """
    super(BanSpammer, self).AssertBasePermission(mr)
    if not permissions.CanBan(mr, self.services):
      raise permissions.PermissionException(
          'User is not allowed to ban users.')

  def ProcessFormData(self, mr, post_data):
    self.AssertBasePermission(mr)
    viewed_user_id = mr.viewed_user_auth.user_pb.user_id
    reporter_id = mr.auth.user_id

    # First ban the user as a spammer.
    framework_helpers.UserSettings.ProcessBanForm(
        mr.cnxn, self.services.user, post_data, mr.viewed_user_auth.user_id,
        mr.viewed_user_auth.user_pb)

    # Now enqueue a task to mark all of their content as spam.
    taskqueue.add(url=urls.BAN_SPAMMER_TASK + '.do',
        params={'spammer_id': viewed_user_id, 'reporter_id': reporter_id})

    return framework_helpers.FormatAbsoluteURL(
        mr, mr.viewed_user_auth.user_view.profile_url, include_project=False,
        saved=1, ts=int(time.time()))


class BanSpammerTask(jsonfeed.InternalTask):
  """This task will update all of the comments and issues created by the
     target user with is_spam=True, and also add a manual verdict attached
     to the user who originated the ban request. This is a potentially long
     running operation, so it is implemented as an async task.
  """

  def HandleRequest(self, mr):
    spammer_id = mr.GetPositiveIntParam('spammer_id')
    reporter_id = mr.GetPositiveIntParam('reporter_id')

    print "\n\n\n\nspammer_id: %d, reporter_id: %d" % (spammer_id, reporter_id)
    # Get all of the issues reported by the spammer.
    issue_ids = self.services.issue.GetIssueIDsReportedByUser(mr.cnxn,
        spammer_id)

    issues = self.services.issue.GetIssues(mr.cnxn, issue_ids)

    # Mark them as spam in bulk.
    self.services.spam.RecordManualIssueVerdicts(mr.cnxn, self.services.issue,
        issues, reporter_id, True)

    # Get all of the comments
    comments = self.services.issue.GetCommentsByUser(mr.cnxn, spammer_id)

    for comment in comments:
      all_comments = self.services.issue.GetCommentsForIssue(mr.cnxn,
        comment.issue_id)
      sequence_num = -1
      for c in all_comments:
        if c.id == comment.id:
          sequence_num = c.sequence
      if comment.is_spam or sequence_num == 0:
        # IssueComment 0 should already be counted as spam in the previous
        # step where we marked the whole issue as spam.
        continue

      self.services.spam.RecordManualCommentVerdict(mr.cnxn,
            self.services.issue, self.services.user, comment.id,
            sequence_num, reporter_id, True)

    self.response.body = json.dumps({
      'comments': len(comments),
      'issues': len(issues),
    })

