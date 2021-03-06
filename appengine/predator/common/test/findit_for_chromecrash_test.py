# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock

from analysis import chromecrash_parser
from analysis import detect_regression_range
from analysis.chromecrash_parser import ChromeCrashParser
from analysis.component_classifier import ComponentClassifier
from analysis.crash_report import CrashReport
from analysis.culprit import Culprit
from analysis.project_classifier import ProjectClassifier
from analysis.suspect import Suspect
from analysis.stacktrace import CallStack
from analysis.stacktrace import Stacktrace
from analysis.type_enums import CrashClient
from common import findit
from common import findit_for_chromecrash
from common.appengine_testcase import AppengineTestCase
from common.findit_for_chromecrash import FinditForChromeCrash
from common.findit_for_chromecrash import FinditForFracas
from common.model import crash_analysis
from common.model.crash_config import CrashConfig
from common.model.fracas_crash_analysis import FracasCrashAnalysis
from gae_libs.http.http_client_appengine import HttpClientAppengine
from libs import analysis_status
from libs.deps import chrome_dependency_fetcher
from libs.deps.dependency import DependencyRoll
from libs.gitiles.gitiles_repository import GitilesRepository


MOCK_GET_REPOSITORY = lambda _: None # pragma: no cover


class _FinditForChromeCrash(FinditForChromeCrash):  # pylint: disable = W
  # We allow overriding the default ``get_repository`` because one unittest
  # needs to.
  def __init__(self, get_repository=MOCK_GET_REPOSITORY, config=None):
    super(_FinditForChromeCrash, self).__init__(get_repository, config)

  @classmethod
  def _ClientID(cls): # pragma: no cover
    """Avoid throwing a NotImplementedError.

    Since this method is called from ``FinditForChromeCrash.__init__``
    in order to construct the Azalea object, we need to not throw
    exceptions since we want to be able to test the FinditForChromeCrash
    class itself.
    """
    return 'ChromeCrash'


def _FinditForFracas(config=None):
  """A helper to pass in the standard pipeline class."""
  return FinditForFracas(MOCK_GET_REPOSITORY, config or {})


class FinditForChromeCrashTest(AppengineTestCase):

  # TODO(wrengr): what was the purpose of this test? As written it's
  # just testing that mocking works. I'm guessing it was to check that
  # we fail when the analysis is for the wrong client_id; but if so,
  # then we shouldn't need to mock FindCulprit...
  def testFindCulprit(self):
    self.mock(FinditForChromeCrash, 'FindCulprit', lambda self, *_: None)

    # TODO(wrengr): would be less fragile to call
    # FinditForFracas.CreateAnalysis instead; though if I'm right about
    # the original purpose of this test, then this is one of the few
    # places where calling FracasCrashAnalysis directly would actually
    # make sense.
    analysis = FracasCrashAnalysis.Create({'signature': 'sig'})
    findit_client = _FinditForChromeCrash(
        GitilesRepository.Factory(HttpClientAppengine()), CrashConfig.Get())
    self.assertIsNone(findit_client.FindCulprit(analysis))


class FinditForFracasTest(AppengineTestCase):

  def setUp(self):
    super(FinditForFracasTest, self).setUp()
    self._client = _FinditForFracas(config=CrashConfig.Get())

  def testCheckPolicyBlacklistSignature(self):
    raw_crash_data = self.GetDummyChromeCrashData(
        client_id = CrashClient.FRACAS,
        signature='Blacklist marker signature')
    crash_data = self._client.GetCrashData(raw_crash_data)
    self.assertFalse(self._client._CheckPolicy(crash_data))

  def testCheckPolicyUnsupportedPlatform(self):
    raw_crash_data = self.GetDummyChromeCrashData(
        client_id = CrashClient.FRACAS,
        platform='unsupported_platform')
    crash_data = self._client.GetCrashData(raw_crash_data)
    self.assertFalse(self._client._CheckPolicy(crash_data))

  def testScheduleNewAnalysisSkipsUnsupportedChannel(self):
    raw_crash_data = self.GetDummyChromeCrashData(
        client_id = CrashClient.FRACAS,
        channel='unsupported_channel')
    crash_data = self._client.GetCrashData(raw_crash_data)
    self.assertFalse(self._client._CheckPolicy(crash_data))

  def testCheckPolicySuccess(self):
    crash_data = self._client.GetCrashData(self.GetDummyChromeCrashData(
        client_id = CrashClient.FRACAS))
    self.assertTrue(self._client._CheckPolicy(crash_data))

  def testCreateAnalysis(self):
    self.assertIsNotNone(self._client.CreateAnalysis(
        {'signature': 'sig'}))

  def testGetAnalysis(self):
    crash_identifiers = {'signature': 'sig'}
    # TODO(wrengr): would be less fragile to call
    # FinditForFracas.CreateAnalysis instead.
    analysis = FracasCrashAnalysis.Create(crash_identifiers)
    analysis.put()
    self.assertEqual(self._client.GetAnalysis(crash_identifiers), analysis)

  @mock.patch('google.appengine.ext.ndb.Key.urlsafe')
  @mock.patch('gae_libs.appengine_util.GetDefaultVersionHostname')
  def testProcessResultForPublishing(self, mocked_get_default_host,
                                     mocked_urlsafe):
    mocked_host = 'http://host'
    mocked_get_default_host.return_value = mocked_host
    urlsafe_key = 'abcde'
    mocked_urlsafe.return_value = urlsafe_key

    crash_identifiers = {'signature': 'sig'}
    analysis = FracasCrashAnalysis.Create(crash_identifiers)
    analysis.result = {'other': 'data'}
    expected_processed_suspect = {
        'client_id': self._client.client_id,
        'crash_identifiers': {'signature': 'sig'},
        'result': {
            'feedback_url': crash_analysis._FEEDBACK_URL_TEMPLATE % (
                mocked_host, CrashClient.FRACAS, urlsafe_key),
            'other': 'data'
        }
    }

    self.assertDictEqual(self._client.GetPublishableResult(crash_identifiers,
                                                           analysis),
                         expected_processed_suspect)
