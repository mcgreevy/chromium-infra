# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Persistence class for user groups.

User groups are represented in the database by:
- A row in the Users table giving an email address and user ID.
  (A "group ID" is the user_id of the group in the User table.)
- A row in the UserGroupSettings table giving user group settings.

Membership of a user X in user group Y is represented as:
- A row in the UserGroup table with user_id=X and group_id=Y.
"""

import collections
import logging
import re

from framework import permissions
from framework import sql
from proto import usergroup_pb2
from services import caches


USERGROUP_TABLE_NAME = 'UserGroup'
USERGROUPSETTINGS_TABLE_NAME = 'UserGroupSettings'
USERGROUPPROJECTS_TABLE_NAME = 'Group2Project'

USERGROUP_COLS = ['user_id', 'group_id', 'role']
USERGROUPSETTINGS_COLS = ['group_id', 'who_can_view_members',
                          'external_group_type', 'last_sync_time']
USERGROUPPROJECTS_COLS = ['group_id', 'project_id']


class MembershipTwoLevelCache(caches.AbstractTwoLevelCache):
  """Class to manage RAM and memcache for each user's memberships."""

  def __init__(self, cache_manager, usergroup_service, group_dag):
    super(MembershipTwoLevelCache, self).__init__(
        cache_manager, 'user', 'memberships:', None)
    self.usergroup_service = usergroup_service
    self.group_dag = group_dag

  def _DeserializeMemberships(self, memberships_rows):
    """Reserialize the DB results into a {user_id: {group_id}}."""
    result_dict = collections.defaultdict(set)
    for user_id, group_id in memberships_rows:
      result_dict[user_id].add(group_id)

    return result_dict

  def FetchItems(self, cnxn, keys):
    """On RAM and memcache miss, hit the database to get memberships."""
    direct_memberships_rows = self.usergroup_service.usergroup_tbl.Select(
        cnxn, cols=['user_id', 'group_id'], distinct=True,
        user_id=keys)
    memberships_set = set()
    self.group_dag.MarkObsolete()
    logging.info('Rebuild group dag on RAM and memcache miss')
    for c_id, p_id in direct_memberships_rows:
      all_parents = self.group_dag.GetAllAncestors(cnxn, p_id, True)
      all_parents.append(p_id)
      memberships_set.update([(c_id, g_id) for g_id in all_parents])
    retrieved_dict = self._DeserializeMemberships(list(memberships_set))

    # Make sure that every requested user is in the result, and gets cached.
    retrieved_dict.update(
        (user_id, set()) for user_id in keys
        if user_id not in retrieved_dict)
    return retrieved_dict


class UserGroupService(object):
  """The persistence layer for user group data."""

  def __init__(self, cache_manager):
    """Initialize this service so that it is ready to use.

    Args:
      cache_manager: local cache with distributed invalidation.
    """
    self.usergroup_tbl = sql.SQLTableManager(USERGROUP_TABLE_NAME)
    self.usergroupsettings_tbl = sql.SQLTableManager(
        USERGROUPSETTINGS_TABLE_NAME)
    self.usergroupprojects_tbl = sql.SQLTableManager(
        USERGROUPPROJECTS_TABLE_NAME)

    self.group_dag = UserGroupDAG(self)

    # Like a dictionary {user_id: {group_id}}
    self.memberships_2lc = MembershipTwoLevelCache(
        cache_manager, self, self.group_dag)

  ### Group creation

  def CreateGroup(self, cnxn, services, group_name, who_can_view_members,
                  ext_group_type=None, friend_projects=None):
    """Create a new user group.

    Args:
      cnxn: connection to SQL database.
      services: connections to backend services.
      group_name: string email address of the group to create.
      who_can_view_members: 'owners', 'members', or 'anyone'.
      ext_group_type: The type of external group to import.
      friend_projects: The project ids declared as group friends to view its
        members.

    Returns:
      int group_id of the new group.
    """
    friend_projects = friend_projects or []
    assert who_can_view_members in ('owners', 'members', 'anyone')
    if ext_group_type:
      ext_group_type = str(ext_group_type).lower()
      assert ext_group_type in (
          'chrome_infra_auth', 'mdb', 'baggins'), (
           ext_group_type)
      assert who_can_view_members == 'owners'
    group_id = services.user.LookupUserID(
        cnxn, group_name.lower(), autocreate=True, allowgroups=True)
    group_settings = usergroup_pb2.MakeSettings(
        who_can_view_members, ext_group_type, 0, friend_projects)
    self.UpdateSettings(cnxn, group_id, group_settings)
    return group_id

  def DeleteGroups(self, cnxn, group_ids):
    """Delete groups' members and settings. It will NOT delete user entries.

    Args:
      cnxn: connection to SQL database.
      group_ids: list of group ids to delete.
    """
    member_ids_dict, owner_ids_dict = self.LookupMembers(cnxn, group_ids)
    citizens_id_dict = collections.defaultdict(list)
    for g_id, user_ids in member_ids_dict.iteritems():
      citizens_id_dict[g_id].extend(user_ids)
    for g_id, user_ids in owner_ids_dict.iteritems():
      citizens_id_dict[g_id].extend(user_ids)
    for g_id, citizen_ids in citizens_id_dict.iteritems():
      logging.info('Deleting group %d', g_id)
      # Remove group members, friend projects and settings
      self.RemoveMembers(cnxn, g_id, citizen_ids)
      self.usergroupprojects_tbl.Delete(cnxn, group_id=g_id)
      self.usergroupsettings_tbl.Delete(cnxn, group_id=g_id)

  def DetermineWhichUserIDsAreGroups(self, cnxn, user_ids):
    """From a list of user IDs, identify potential user groups.

    Args:
      cnxn: connection to SQL database.
      user_ids: list of user IDs to examine.

    Returns:
      A list with a subset of the given user IDs that are user groups
      rather than individual users.
    """
    # It is a group if there is any entry in the UserGroupSettings table.
    group_id_rows = self.usergroupsettings_tbl.Select(
        cnxn, cols=['group_id'], group_id=user_ids)
    group_ids = [row[0] for row in group_id_rows]
    return group_ids

  ### User memberships in groups

  def LookupAllMemberships(self, cnxn, user_ids, use_cache=True):
    """Lookup all the group memberships of a list of users.

    Args:
      cnxn: connection to SQL database.
      user_ids: list of int user IDs to get memberships for.
      use_cache: set to False to ignore cached values.

    Returns:
      A dict {user_id: {group_id}} for the given user_ids.
    """
    result_dict, missed_ids = self.memberships_2lc.GetAll(
        cnxn, user_ids, use_cache=use_cache)
    assert not missed_ids
    return result_dict

  def LookupMemberships(self, cnxn, user_id):
    """Return a set of group_ids that this user is a member of."""
    membership_dict = self.LookupAllMemberships(cnxn, [user_id])
    return membership_dict[user_id]

  ### Group member addition, removal, and retrieval

  def RemoveMembers(self, cnxn, group_id, old_member_ids):
    """Remove the given members/owners from the user group."""
    self.usergroup_tbl.Delete(
        cnxn, group_id=group_id, user_id=old_member_ids)

    all_affected = self._GetAllMembersInList(cnxn, old_member_ids)

    self.group_dag.MarkObsolete()
    self.memberships_2lc.InvalidateAllKeys(cnxn, all_affected)

  def UpdateMembers(self, cnxn, group_id, member_ids, new_role):
    """Update role for given members/owners to the user group."""
    # Circle detection
    for mid in member_ids:
      if self.group_dag.IsChild(cnxn, group_id, mid):
        raise CircularGroupException(
            '%s is already an ancestor of group %s.' % (mid, group_id))

    self.usergroup_tbl.Delete(
        cnxn, group_id=group_id, user_id=member_ids)
    rows = [(member_id, group_id, new_role) for member_id in member_ids]
    self.usergroup_tbl.InsertRows(
        cnxn, ['user_id', 'group_id', 'role'], rows)

    all_affected = self._GetAllMembersInList(cnxn, member_ids)

    self.group_dag.MarkObsolete()
    self.memberships_2lc.InvalidateAllKeys(cnxn, all_affected)

  def _GetAllMembersInList(self, cnxn, group_ids):
    """Get all direct/indirect members/owners in a list."""
    children_member_ids, children_owner_ids = self.LookupAllMembers(
        cnxn, group_ids)
    all_members_owners = set()
    all_members_owners.update(group_ids)
    for users in children_member_ids.itervalues():
      all_members_owners.update(users)
    for users in children_owner_ids.itervalues():
      all_members_owners.update(users)
    return list(all_members_owners)

  def LookupAllMembers(self, cnxn, group_ids):
    """Retrieve user IDs of members/owners of any of the given groups
    transitively."""
    direct_member_rows = self.usergroup_tbl.Select(
        cnxn, cols=['user_id', 'group_id', 'role'], distinct=True,
        group_id=group_ids)
    member_ids_dict = {}
    owner_ids_dict = {}
    for gid in group_ids:
      all_descendants = self.group_dag.GetAllDescendants(cnxn, gid, True)
      indirect_member_rows = self.usergroup_tbl.Select(
          cnxn, cols=['user_id'], distinct=True,
          group_id=all_descendants)

      # Owners must have direct membership. All indirect users are members.
      owner_ids_dict[gid] = [m[0] for m in direct_member_rows
                             if m[1] == gid and m[2] == 'owner']
      member_ids_list = [r[0] for r in indirect_member_rows]
      member_ids_list.extend([m[0] for m in direct_member_rows
                             if m[1] == gid and m[2] == 'member'])
      member_ids_dict[gid] = list(set(member_ids_list))
    return member_ids_dict, owner_ids_dict

  def LookupMembers(self, cnxn, group_ids):
    """"Retrieve user IDs of direct members/owners of any of the given groups.

    Args:
      cnxn: connection to SQL database.
      group_ids: list of int user IDs for all user groups to be examined.

    Returns:
      A dict of member IDs, and a dict of owner IDs keyed by group id.
    """
    member_rows = self.usergroup_tbl.Select(
        cnxn, cols=['user_id', 'group_id', 'role'], distinct=True,
        group_id=group_ids)
    member_ids_dict = {}
    owner_ids_dict = {}
    for gid in group_ids:
      member_ids_dict[gid] = [row[0] for row in member_rows
                               if row[1] == gid and row[2] == 'member']
      owner_ids_dict[gid] = [row[0] for row in member_rows
                              if row[1] == gid and row[2] == 'owner']
    return member_ids_dict, owner_ids_dict

  def ExpandAnyUserGroups(self, cnxn, user_ids):
    """Transitively expand any user groups and return member user IDs.

    Args:
      cnxn: connection to SQL database.
      user_ids: list of user IDs to check.

    Returns:
      A pair (individual_user_ids, transitive_ids). individual_user_ids
          is a list of user IDs that were in the given user_ids list and
          that identify individual members. transitive_ids is a list of
          user IDs of the members of any user group in the given list of
          user_ids and the individual members of any nested groups.
    """
    group_ids = self.DetermineWhichUserIDsAreGroups(cnxn, user_ids)
    direct_ids = [uid for uid in user_ids if uid not in group_ids]
    member_ids_dict, owner_ids_dict = self.LookupAllMembers(cnxn, group_ids)
    indirect_ids = set()
    for gid in group_ids:
      indirect_ids.update(member_ids_dict[gid])
      indirect_ids.update(owner_ids_dict[gid])

    # Note: we return direct and indirect member IDs separately so that
    # the email notification footer can give more a specific reason for
    # why the user got an email.  E.g., "You were Cc'd" vs. "You are a
    # member of a user group that was Cc'd".
    return direct_ids, list(indirect_ids)

  def LookupVisibleMembers(
      self, cnxn, group_id_list, perms, effective_ids, services):
    """"Retrieve the list of user group direct member/owner IDs that the user
    may see.

    Args:
      cnxn: connection to SQL database.
      group_id_list: list of int user IDs for all user groups to be examined.
      perms: optional PermissionSet for the user viewing this page.
      effective_ids: set of int user IDs for that user and all
          his/her group memberships.
      services: backend services.

    Returns:
      A list of all the member IDs from any group that the user is allowed
      to view.
    """
    settings_dict = self.GetAllGroupSettings(cnxn, group_id_list)
    group_ids = settings_dict.keys()
    (owned_project_ids, membered_project_ids,
     contrib_project_ids) = services.project.GetUserRolesInAllProjects(
         cnxn, effective_ids)
    project_ids = owned_project_ids.union(
        membered_project_ids).union(contrib_project_ids)
    # We need to fetch all members/owners to determine whether the requester
    # has permission to view.
    direct_member_ids_dict, direct_owner_ids_dict = self.LookupMembers(
        cnxn, group_ids)
    all_member_ids_dict, all_owner_ids_dict = self.LookupAllMembers(
        cnxn, group_ids)
    visible_member_ids = {}
    visible_owner_ids = {}
    for gid in group_ids:
      member_ids = all_member_ids_dict[gid]
      owner_ids = all_owner_ids_dict[gid]

      if permissions.CanViewGroup(perms, effective_ids, settings_dict[gid],
                                  member_ids, owner_ids, project_ids):
        visible_member_ids[gid] = direct_member_ids_dict[gid]
        visible_owner_ids[gid] = direct_owner_ids_dict[gid]

    return visible_member_ids, visible_owner_ids

  ### Group settings

  def GetAllUserGroupsInfo(self, cnxn):
    """Fetch (addr, member_count, usergroup_settings) for all user groups."""
    group_rows = self.usergroupsettings_tbl.Select(
        cnxn, cols=['group_id', 'email', 'who_can_view_members',
                    'external_group_type', 'last_sync_time'],
        left_joins=[('User ON UserGroupSettings.group_id = User.user_id', [])])
    count_rows = self.usergroup_tbl.Select(
        cnxn, cols=['group_id', 'COUNT(*)'],
        group_by=['group_id'])
    count_dict = dict(count_rows)
    group_ids = [g[0] for g in group_rows]
    friends_dict = self.GetAllGroupFriendProjects(cnxn, group_ids)

    user_group_info_tuples = [
        (email, count_dict.get(group_id, 0),
         usergroup_pb2.MakeSettings(visiblity, group_type, last_sync_time,
                                    friends_dict.get(group_id, [])),
         group_id)
        for (group_id, email, visiblity, group_type, last_sync_time)
        in group_rows]
    return user_group_info_tuples

  def GetAllGroupSettings(self, cnxn, group_ids):
    """Fetch {group_id: group_settings} for the specified groups."""
    # TODO(jrobbins): add settings to control who can join, etc.
    rows = self.usergroupsettings_tbl.Select(
        cnxn, cols=USERGROUPSETTINGS_COLS, group_id=group_ids)
    friends_dict = self.GetAllGroupFriendProjects(cnxn, group_ids)
    settings_dict = {
        group_id: usergroup_pb2.MakeSettings(
            vis, group_type, last_sync_time, friends_dict.get(group_id, []))
        for group_id, vis, group_type, last_sync_time in rows}
    return settings_dict

  def GetGroupSettings(self, cnxn, group_id):
    """Retrieve group settings for the specified user group.

    Args:
      cnxn: connection to SQL database.
      group_id: int user ID of the user group.

    Returns:
      A UserGroupSettings object, or None if no such group exists.
    """
    return self.GetAllGroupSettings(cnxn, [group_id]).get(group_id)

  def UpdateSettings(self, cnxn, group_id, group_settings):
    """Update the visiblity settings of the specified group."""
    who_can_view_members = str(group_settings.who_can_view_members).lower()
    ext_group_type = group_settings.ext_group_type
    assert who_can_view_members in ('owners', 'members', 'anyone')
    if ext_group_type:
      ext_group_type = str(group_settings.ext_group_type).lower()
      assert ext_group_type in (
          'chrome_infra_auth', 'mdb', 'baggins'), (
           ext_group_type)
      assert who_can_view_members == 'owners'
    self.usergroupsettings_tbl.InsertRow(
        cnxn, group_id=group_id, who_can_view_members=who_can_view_members,
        external_group_type=ext_group_type,
        last_sync_time=group_settings.last_sync_time,
        replace=True)
    self.usergroupprojects_tbl.Delete(
        cnxn, group_id=group_id)
    if group_settings.friend_projects:
      rows = [(group_id, p_id) for p_id in group_settings.friend_projects]
      self.usergroupprojects_tbl.InsertRows(
        cnxn, ['group_id', 'project_id'], rows)

  def GetAllGroupFriendProjects(self, cnxn, group_ids):
    """Get {group_id: [project_ids]} for the specified user groups."""
    rows = self.usergroupprojects_tbl.Select(
        cnxn, cols=USERGROUPPROJECTS_COLS, group_id=group_ids)
    friends_dict = {}
    for group_id, project_id in rows:
      friends_dict.setdefault(group_id, []).append(project_id)
    return friends_dict

  def GetGroupFriendProjects(self, cnxn, group_id):
    """Get a list of friend projects for the specified user group."""
    return self.GetAllGroupFriendProjects(cnxn, [group_id]).get(group_id)

  def ValidateFriendProjects(self, cnxn, services, friend_projects):
    """Validate friend projects.

    Returns:
      A list of project ids if no errors, or an error message.
    """
    project_names = filter(None, re.split('; |, | |;|,', friend_projects))
    id_dict = services.project.LookupProjectIDs(cnxn, project_names)
    missed_projects = []
    result = []
    for p_name in project_names:
      if p_name in id_dict:
        result.append(id_dict[p_name])
      else:
        missed_projects.append(p_name)
    error_msg = ''
    if missed_projects:
      error_msg = 'Project(s) %s do not exist' % ', '.join(missed_projects)
      return None, error_msg
    else:
      return result, None

  # TODO(jrobbins): re-implement FindUntrustedGroups()


class UserGroupDAG(object):
  """A directed-acyclic graph of potentially nested user groups."""

  def __init__(self, usergroup_service):
    self.usergroup_service = usergroup_service
    self.user_group_parents = collections.defaultdict(list)
    self.user_group_children = collections.defaultdict(list)
    self.initialized = False

  def Build(self, cnxn, circle_detection=False):
    if not self.initialized:
      self.user_group_parents.clear()
      self.user_group_children.clear()
      group_ids = self.usergroup_service.usergroupsettings_tbl.Select(
          cnxn, cols=['group_id'])
      usergroup_rows = self.usergroup_service.usergroup_tbl.Select(
          cnxn, cols=['user_id', 'group_id'], distinct=True,
          user_id=[r[0] for r in group_ids])
      for user_id, group_id in usergroup_rows:
        self.user_group_parents[user_id].append(group_id)
        self.user_group_children[group_id].append(user_id)
    self.initialized = True

    if circle_detection:
      for child_id, parent_ids in self.user_group_parents.iteritems():
        for parent_id in parent_ids:
          if self.IsChild(cnxn, parent_id, child_id):
            logging.error(
                'Circle exists between group %d and %d.', child_id, parent_id)

  def GetAllAncestors(self, cnxn, group_id, circle_detection=False):
    """Return a list of distinct ancestor group IDs for the given group."""
    self.Build(cnxn, circle_detection)
    result = set()
    child_ids = [group_id]
    while child_ids:
      parent_ids = set()
      for c_id in child_ids:
        group_ids = self.user_group_parents[c_id]
        parent_ids.update(g_id for g_id in group_ids if g_id not in result)
        result.update(parent_ids)
      child_ids = list(parent_ids)
    return list(result)

  def GetAllDescendants(self, cnxn, group_id, circle_detection=False):
    """Return a list of distinct descendant group IDs for the given group."""
    self.Build(cnxn, circle_detection)
    result = set()
    parent_ids = [group_id]
    while parent_ids:
      child_ids = set()
      for p_id in parent_ids:
        group_ids = self.user_group_children[p_id]
        child_ids.update(g_id for g_id in group_ids if g_id not in result)
        result.update(child_ids)
      parent_ids = list(child_ids)
    return list(result)

  def IsChild(self, cnxn, child_id, parent_id):
    """Returns True if child_id is a direct/indirect child of parent_id."""
    all_descendants = self.GetAllDescendants(cnxn, parent_id)
    return child_id in all_descendants

  def MarkObsolete(self):
    """Mark the DAG as uninitialized so it'll be re-built."""
    self.initialized = False

  def __repr__(self):
    result = {}
    result['parents'] = self.user_group_parents
    result['children'] = self.user_group_children
    return str(result)


class Error(Exception):
  """Base class for errors from this module."""
  pass


class CircularGroupException(Error):
  """Circular nested group exception."""
  pass


class GroupExistsException(Error):
  """Group already exists exception."""
  pass


class NoSuchGroupException(Error):
  """Requested group was not found exception."""
  pass
