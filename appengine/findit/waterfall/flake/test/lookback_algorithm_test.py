# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import copy

from gae_libs.testcase import TestCase

from waterfall.flake import lookback_algorithm
from waterfall.flake.lookback_algorithm import NormalizedDataPoint
from waterfall.test.wf_testcase import DEFAULT_CONFIG_DATA


class LookbackAlgorithmTest(TestCase):

  def testGetNextFlakySingleFlakyDataPoint(self):
    data_points = [NormalizedDataPoint(100, 0.8)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'])
    self.assertEqual(99, next_run)
    self.assertIsNone(result)

  def testGetNextWithLowerBoundaryNotYetHit(self):
    data_points = [
        NormalizedDataPoint(2, 0.8),
        NormalizedDataPoint(1, 0.8)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertEqual(0, next_run)
    self.assertIsNone(result)

  def testGetNextWithLowerBoundaryAlreadyHit(self):
    data_points = [
        NormalizedDataPoint(2, 0.8),
        NormalizedDataPoint(1, 1.0)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 1)

    self.assertIsNone(next_run)
    self.assertEqual(2, result)

  def testSequentialSearchAtLowerBoundaryStable(self):
    data_points = [NormalizedDataPoint(8, 0.8),
                   NormalizedDataPoint(3, 0.8),
                   NormalizedDataPoint(0, 1.0)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)
    self.assertEqual(1, next_run)
    self.assertIsNone(result)

  def testSequentialSearchAtLowerBoundaryFlaky(self):
    data_points = [NormalizedDataPoint(8, 0.8),
                   NormalizedDataPoint(3, 0.8),
                   NormalizedDataPoint(0, 0.8)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['try_job_rerun'], 0)

    self.assertIsNone(next_run)
    self.assertEqual(0, result)

  def testGetNextRunFlakedOut(self):
    data_points = [
        NormalizedDataPoint(100, 0.6),
        NormalizedDataPoint(99, 0.7),
        NormalizedDataPoint(97, 0.5),
        NormalizedDataPoint(94, 0.6),
        NormalizedDataPoint(90, 0.7)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEqual(next_run, 85)

  def testSequentialNextRunReadyAfterStableRegionFound(self):
    data_points = [
        NormalizedDataPoint(100, 0.6),
        NormalizedDataPoint(99, 0.8),
        NormalizedDataPoint(97, 0.7),
        NormalizedDataPoint(94, 1.0)]

    algorithm_settings = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithm_settings['max_iterations_to_rerun'] = 100
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points, algorithm_settings)
    self.assertIsNone(result)
    self.assertEqual(next_run, 95)

  def testSequentialNextRunFoundFlaky(self):
    data_points = [
        NormalizedDataPoint(100, 0.6),
        NormalizedDataPoint(99, 0.8),
        NormalizedDataPoint(97, 0.7),
        NormalizedDataPoint(95, 0.8),
        NormalizedDataPoint(94, 1.0)]

    algorithm_settings = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithm_settings['max_iterations_to_rerun'] = 100
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points, algorithm_settings)

    self.assertEqual(result, 95)
    self.assertIsNone(next_run)

  def testSequentialNextRunDone(self):
    data_points = [
        NormalizedDataPoint(100, 0.6),
        NormalizedDataPoint(99, 0.8),
        NormalizedDataPoint(97, 0.7),
        NormalizedDataPoint(96, 0.8),
        NormalizedDataPoint(95, 1.0)]

    algorithm_settings = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithm_settings['max_iterations_to_rerun'] = 100
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points, algorithm_settings)

    self.assertEqual(result, 96)
    self.assertIsNone(next_run)

  def testRunPositionIntroducedFlakiness(self):
    data_points = [NormalizedDataPoint(100, 0.8),
                   NormalizedDataPoint(99, -1)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'], 0)
    self.assertIsNone(next_run)
    self.assertEqual(100, result)

  def testFlakyFromBeginning(self):
    data_points = [NormalizedDataPoint(100, 0.8),
                   NormalizedDataPoint(99, 0.8),
                   NormalizedDataPoint(97, 0.8),
                   NormalizedDataPoint(94, 0.8),
                   NormalizedDataPoint(91, 0.8),
                   NormalizedDataPoint(90, -1)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'], 0)
    self.assertIsNone(next_run)
    self.assertEqual(91, result)

  def testTestDoesNotExist(self):
    data_points = [NormalizedDataPoint(100, -1)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'], 0)
    self.assertIsNone(result)
    self.assertIsNone(next_run)

  def testNextBuildWhenTestNotExistingAfterFlakeInARow(self):
    data_points = [
        NormalizedDataPoint(100, 0.8),
        NormalizedDataPoint(80, 0.7),
        NormalizedDataPoint(70, 0.75),
        NormalizedDataPoint(60, -1)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEqual(61, next_run)

  def testNextBuildWhenDiveHappened(self):
    data_points = [
        NormalizedDataPoint(100, 0.3),
        NormalizedDataPoint(80, 0.8)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEqual(79, next_run)

  def testNextBuildWhenRiseHappened(self):
    data_points = [
        NormalizedDataPoint(100, 0.3),
        NormalizedDataPoint(99, 0.8),
        NormalizedDataPoint(98, 0.3)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEqual(95, next_run)

  def testNextBuildWhenDivedOut(self):
    data_points = [
        NormalizedDataPoint(100, 0.3),
        NormalizedDataPoint(99, 0.8),
        NormalizedDataPoint(98, 0.8),
        NormalizedDataPoint(97, 0.7),
        NormalizedDataPoint(96, 0.8),
        NormalizedDataPoint(95, 0.9)]
    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertEqual(100, result)
    self.assertIsNone(next_run)

  def testNextBuildWhenDivedOutSequence(self):
    data_points = [
        NormalizedDataPoint(100, 0.3),
        NormalizedDataPoint(99, 0.2),
        NormalizedDataPoint(97, 0.8),
        NormalizedDataPoint(96, 0.7),
        NormalizedDataPoint(95, 0.8),
        NormalizedDataPoint(94, 0.9),
        NormalizedDataPoint(93, 0.8)]

    next_run, result, _ = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEqual(98, next_run)

  def testRerunWithHigherIterationsWhenFirstBuildStable(self):
    data_points = [NormalizedDataPoint(100, 1.0)]

    algorithms = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithms['iterations_to_rerun'] = 100
    algorithms['max_iterations_to_rerun'] = 800
    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
        data_points, algorithms)
    self.assertIsNone(result)
    self.assertEqual(200, iterations)
    self.assertEqual(100, next_run)

  def testBailOutWhenIterationsGreaterThanMax(self):
    data_points = [NormalizedDataPoint(100, 1.0)]

    algorithms = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithms['iterations_to_rerun'] = 800
    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
        data_points, algorithms)
    self.assertIsNone(result)
    self.assertIsNone(next_run)
    self.assertIsNone(iterations)

  def testBuildWithExceptionNormal(self):
    data_points = [
      NormalizedDataPoint(100, 0.5),
      NormalizedDataPoint(99, -1, False)
    ]

    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEquals(98, next_run)
    self.assertIsNone(iterations)

  def testBuildWithExceptionSequential(self):
    data_points = [
      NormalizedDataPoint(100, 0.5),
      NormalizedDataPoint(98, -1, False),
      NormalizedDataPoint(97, 1.0),
    ]

    algorithms = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithms['iterations_to_rerun'] = 800
    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
      data_points, algorithms)
    self.assertIsNone(result)
    self.assertEquals(99, next_run)
    self.assertIsNone(iterations)

  def testBuildWithExceptionAnalysisFindNeighbor(self):
    data_points = [
      NormalizedDataPoint(100, 0.5),
      NormalizedDataPoint(99, -1, False),
      NormalizedDataPoint(98, -1, False),
    ]

    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEquals(97, next_run)
    self.assertIsNone(iterations)

  def testBuildWithExceptionAnalysisKeepSearchingAfterValidBuildFound(self):
    data_points = [
      NormalizedDataPoint(100, 0.5),
      NormalizedDataPoint(99, -1, False),
      NormalizedDataPoint(98, -1, False),
      NormalizedDataPoint(97, 0.5),
    ]

    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
        data_points,
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    self.assertIsNone(result)
    self.assertEquals(95, next_run)
    self.assertIsNone(iterations)

  def testBuildWithExceptionAnalysisKeepSearchingSequential(self):
    data_points = [
      NormalizedDataPoint(100, 0.5),
      NormalizedDataPoint(99, -1, False),
      NormalizedDataPoint(98, -1, False),
      NormalizedDataPoint(97, 0.5),
      NormalizedDataPoint(96, 1.0),
      NormalizedDataPoint(95, 1.0),
    ]

    algorithms = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithms['iterations_to_rerun'] = 800
    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
      data_points, algorithms)
    self.assertIsNone(next_run)
    self.assertEquals(97, result)
    self.assertIsNone(iterations)

  def testBuildWithExceptionAnalysisStop(self):
    data_points = [
      NormalizedDataPoint(100, 0.5),
      NormalizedDataPoint(99, -1, False),
      NormalizedDataPoint(98, -1, False),
      NormalizedDataPoint(97, -1, False),
      NormalizedDataPoint(96, 1.0),
    ]

    algorithms = copy.deepcopy(
        DEFAULT_CONFIG_DATA['check_flake_settings']['swarming_rerun'])
    algorithms['iterations_to_rerun'] = 800
    next_run, result, iterations = lookback_algorithm.GetNextRunPointNumber(
      data_points, algorithms)
    self.assertIsNone(next_run)
    self.assertEquals(97, result)
    self.assertIsNone(iterations)