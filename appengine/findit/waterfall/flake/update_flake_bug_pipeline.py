# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.ext import ndb

from issue_tracker import IssueTrackerAPI

from gae_libs.pipeline_wrapper import BasePipeline
from waterfall import monitoring


def _GetIssue(bug_id, issue_tracker):
  """Returns the issue of the given bug.

  Traverse if the bug was merged into another."""
  issue = issue_tracker.getIssue(bug_id)
  checked_issues = {}
  while issue and issue.merged_into:
    logging.info('%s was merged into %s' % (issue.id, issue.merged_into))
    checked_issues[issue.id] = issue
    issue = issue_tracker.getIssue(issue.merged_into)
    if issue.id in checked_issues:
      break  # Break the loop.
  return issue


_COMMENT_FOOTER= """
Automatically posted by the findit-for-me app (https://goo.gl/Ot9f7N).
Flake Analyzer is in alpha version.
Feedback is welcome using component Tools>Test>FindIt>Flakiness !""".lstrip()

_LINK = 'https://findit-for-me.appspot.com/waterfall/flake?key=%s'

_ERROR_COMMENT_TEMPLATE = ("""
Oops, due to an error, only a partial flakiness trend was generated for
the config "%s / %s":""".lstrip().replace('\n', ' ')
                           + '\n\n' + _LINK
                           + '\n\n' + _COMMENT_FOOTER)

_CULPRIT_COMMENT_TEMPLATE = ("""
Findit identified the culprit r%s with confidence %.1f%% in the config "%s / %s"
based on the flakiness trend:""".lstrip()
                           + '\n\n' + _LINK
                           + '\n\n' + _COMMENT_FOOTER)

_BUILD_HIGH_CONFIDENCE_COMMENT_TEMPLATE = ("""
Findit found the flake started in build %s of the config "%s / %s"
with confidence %.1f%% based on the flakiness trend:""".lstrip()
                           + '\n\n' + _LINK
                           + '\n\n' + _COMMENT_FOOTER)

_LOW_FLAKINESS_COMMENT_TEMPLATE = ("""
This flake is a longstanding one, with low flakiness, or not reproducible
based on the flakiness trend in the config "%s / %s":""".lstrip()
                           + '\n\n' + _LINK
                           + '\n\n' + _COMMENT_FOOTER)

_FINDIT_ANALYZED_LABEL_TEXT = 'Test-Findit-Analyzed'


def _GenerateComment(analysis):
  """Generates a comment based on the analysis result."""
  if analysis.failed:
    return _ERROR_COMMENT_TEMPLATE % (
        analysis.original_master_name,
        analysis.original_builder_name,
        analysis.key.urlsafe(),
    )
  elif analysis.culprit is not None:
    return _CULPRIT_COMMENT_TEMPLATE % (
        analysis.culprit.commit_position,
        analysis.culprit.confidence * 100,
        analysis.original_master_name,
        analysis.original_builder_name,
        analysis.key.urlsafe(),
    )
  elif (analysis.suspected_flake_build_number and
        analysis.confidence_in_suspected_build > 0.6):
    return _BUILD_HIGH_CONFIDENCE_COMMENT_TEMPLATE % (
        analysis.suspected_flake_build_number,
        analysis.original_master_name,
        analysis.original_builder_name,
        analysis.confidence_in_suspected_build * 100,
        analysis.key.urlsafe(),
    )
  else:
    return _LOW_FLAKINESS_COMMENT_TEMPLATE % (
        analysis.original_master_name,
        analysis.original_builder_name,
        analysis.key.urlsafe(),
    )


def _LogBugNotUpdated(reason):
  logging.info('Bug not updated: %s', reason)


def _ShouldUpdateBugForAnalysis(analysis):
  if analysis.error:
    _LogBugNotUpdated('error in analysis: %s' % analysis.error.get('message'))
    return False

  if not analysis.completed:
    _LogBugNotUpdated('completed=%s' % analysis.completed)
    return False

  if not analysis.bug_id:
    _LogBugNotUpdated('bug=%s' % analysis.bug_id)
    return False

  if len(analysis.data_points) < 2:
    _LogBugNotUpdated('%d data points' % len(analysis.data_points))
    return False

  if analysis.suspected_flake_build_number is None:
    _LogBugNotUpdated('no regression range identifed')
    return False

  if not analysis.algorithm_parameters.get('update_monorail_bug'):
    _LogBugNotUpdated('update_monorail_bug not set or is False')
    return False

  if (not analysis.culprit and
      analysis.confidence_in_suspected_build <
      analysis.algorithm_parameters.get(
          'minimum_confidence_score_to_run_tryjobs')):
    _LogBugNotUpdated('insufficient confidence in suspected build')
    return False

  return True


class UpdateFlakeBugPipeline(BasePipeline):

  # Arguments number differs from overridden method - pylint: disable=W0221
  def run(self, urlsafe_flake_analysis_key):
    """Updates the attached bug of the flake with the analysis result.

    Args:
      urlsafe_flake_analysis_key (str): The urlsafe-key of the
          MasterFlakeAnalysis.
    """
    analysis = ndb.Key(urlsafe=urlsafe_flake_analysis_key).get()
    assert analysis

    if not _ShouldUpdateBugForAnalysis(analysis):
      return False

    project_name = 'chromium'
    issue_tracker = IssueTrackerAPI(project_name)
    issue = _GetIssue(analysis.bug_id, issue_tracker)
    if not issue:
      logging.warn('Bug %s/%s or the merged-into one seems deleted!',
                   project_name, analysis.bug_id)
      return False

    comment = _GenerateComment(analysis)

    # Since a flake bug may be updated twice, once when the regression range
    # is identified and again when a culprit is identified, ensure the
    # 'Test-Findit-Analyzed' label is only present once.
    if _FINDIT_ANALYZED_LABEL_TEXT not in issue.labels:  # pragma: no branch
      issue.labels.append(_FINDIT_ANALYZED_LABEL_TEXT)

    monitoring.issues.increment({'operation': 'update', 'category': 'flake'})

    issue_tracker.update(issue, comment, send_email=True)
    logging.info('Bug %s/%s was updated.', project_name, analysis.bug_id)
    return True
