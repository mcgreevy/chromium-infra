# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from collections import defaultdict
import logging
import math

from analysis.crash_report import CrashReport
from analysis.linear.model import UnnormalizedLogLinearModel
from analysis.suspect import Suspect
from libs.deps.chrome_dependency_fetcher import ChromeDependencyFetcher

# The ratio of the probabilities of 2 suspects equal to
# exp(suspect1.confidence)/exp(suspect2.confidence), so
# suspect1.confidence - suspect2.confidence <= log(0.5) means the
# suspect1 is half likely than suspect2.
_THRESHOLD_RATIO = math.log(0.5)


class ChangelistClassifier(object):
  """A ``LogLinearModel``-based implementation of CL classification."""

  def __init__(self, get_repository, meta_feature, meta_weight,
               top_n_frames=7, top_n_suspects=3):
    """
    Args:
      get_repository (callable): a function from DEP urls to ``Repository``
        objects, so we can get changelogs and blame for each dep. Notably,
        to keep the code here generic, we make no assumptions about
        which subclass of ``Repository`` this function returns. Thus,
        it is up to the caller to decide what class to return and handle
        any other arguments that class may require (e.g., an http client
        for ``GitilesRepository``).
      meta_feature (MetaFeature): All features.
      meta_weight (MetaWeight): All weights. the weights for the features.
        The keys of the dictionary are the names of the feature that weight is
        for. We take this argument as a dict rather than as a list so that
        callers needn't worry about what order to provide the weights in.
      top_n_frames (int): how many frames of each callstack to look at.
      top_n_suspects (int): maximum number of suspects to return.
    """
    self._dependency_fetcher = ChromeDependencyFetcher(get_repository)
    self._get_repository = get_repository
    self._top_n_frames = top_n_frames
    self._top_n_suspects = top_n_suspects
    self._model = UnnormalizedLogLinearModel(meta_feature, meta_weight)

  def __call__(self, report):
    """Finds changelists suspected of being responsible for the crash report.

    Args:
      report (CrashReport): the report to be analyzed.

    Returns:
      List of ``Suspect``s, sorted by probability from highest to lowest.
    """
    suspects = self.GenerateSuspects(report)
    if not suspects:
      logging.warning('%s.__call__: Found no suspects for report: %s',
          self.__class__.__name__, str(report))
      return []

    return self.RankSuspects(report, suspects)

  def GenerateSuspects(self, report):
    """Generate all possible suspects for the reported crash.

    Args:
      report (CrashReport): the crash we seek to explain.

    Returns:
      A list of ``Suspect``s who may be to blame for the
      ``report``. Notably these ``Suspect`` instances do not have
      all their fields filled in. They will be filled in later by
      ``RankSuspects``.
    """
    reverted_revisions = []
    revision_to_suspects = {}
    for dep_roll in report.dependency_rolls.itervalues():
      repository = self._get_repository(dep_roll.repo_url)
      changelogs = repository.GetChangeLogs(dep_roll.old_revision,
                                            dep_roll.new_revision)

      for changelog in changelogs or []:
        # When someone reverts, we need to skip both the CL doing
        # the reverting as well as the CL that got reverted. If
        # ``reverted_revision`` is true, then this CL reverts another one,
        # so we skip it and save the CL it reverts in ``reverted_cls`` to
        # be filtered out later.
        if changelog.reverted_revision:
          reverted_revisions.append(changelog.reverted_revision)
          continue

        revision_to_suspects[changelog.revision] = Suspect(changelog,
                                                           dep_roll.path)

    for reverted_revision in reverted_revisions:
      if reverted_revision in revision_to_suspects:
        del revision_to_suspects[reverted_revision]

    return revision_to_suspects.values()

  def RankSuspects(self, report, suspects):
    """Returns a lineup of the suspects in order of likelihood.

    Suspects with a discardable score or lower ranking than top_n_suspects
    will be filtered.

    Args:
      report (CrashReport): the crash we seek to explain.
      suspects (iterable of Suspect): the CLs to consider blaming for the crash.

    Returns:
      A list of suspects in order according to their likelihood. This
      list contains elements of the ``suspects`` list, where we mutate
      some of the fields to store information about why that suspect
      is being blamed (e.g., the ``confidence``, ``reasons``, and
      ``changed_files`` fields are updated). In addition to sorting the
      suspects, we also filter out those which are exceedingly unlikely
      or don't make the ``top_n_suspects`` cut.
    """
    # Score the suspects and organize them for outputting/returning.
    features_given_report = self._model.Features(report)
    score_given_report = self._model.Score(report)

    scored_suspects = []
    for suspect in suspects:
      score = score_given_report(suspect)
      if self._model.LogZeroish(score):
        logging.debug('Discarding suspect because it has zero probability: %s'
            % str(suspect.ToDict()))
        continue

      suspect.confidence = score
      # features is ``MetaFeatureValue`` object containing all feature values.
      features = features_given_report(suspect)
      suspect.reasons = self._model.FilterReasonWithWeight(features.reason)
      suspect.changed_files = [changed_file.ToDict()
                               for changed_file in features.changed_files]
      scored_suspects.append(suspect)

    return self.SortAndFilterSuspects(scored_suspects)

  def SortAndFilterSuspects(self, suspects):
    """Sorts and Filter suspects by probability ratio."""
    if not suspects or len(suspects) == 1:
      return suspects

    suspects.sort(key=lambda suspect: -suspect.confidence)
    max_score = suspects[0].confidence
    min_score = max(suspects[-1].confidence, 0.0)
    if max_score == min_score:
      return []

    filtered_suspects = []
    for suspect in suspects:  # pragma: no cover
      # The ratio of the probabilities of 2 suspects equal to
      # exp(suspect1.confidence)/exp(suspect2.confidence), so
      # suspect1.confidence - suspect2.confidence <= log(0.5) means the
      # suspect1 is half likely than suspect2.
      if (suspect.confidence <= min_score or
          suspect.confidence - max_score <= _THRESHOLD_RATIO):
        break

      filtered_suspects.append(suspect)

    return filtered_suspects
