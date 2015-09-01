# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

import mock

from infra_libs import temporary_directory
from infra.services.mastermon import monitor


class MasterMonitorTest(unittest.TestCase):
  def test_poll(self):
    mock_poller_class = mock.Mock()
    mock_poller = mock_poller_class.return_value

    class MasterMonitor(monitor.MasterMonitor):
      POLLER_CLASSES = [mock_poller_class]

    m = MasterMonitor('http://example.com')

    mock_poller.poll.return_value = True
    m.poll()
    self.assertTrue(m.up.get())

    mock_poller.poll.return_value = False
    m.poll()
    self.assertFalse(m.up.get())

  def test_poll_with_name(self):
    mock_poller_class = mock.Mock()
    mock_poller = mock_poller_class.return_value

    class MasterMonitor(monitor.MasterMonitor):
      POLLER_CLASSES = [mock_poller_class]

    m = MasterMonitor('http://example.com', name='foobar')

    mock_poller.poll.return_value = True
    m.poll()
    self.assertTrue(m.up.get({'master': 'foobar'}))

    mock_poller.poll.return_value = False
    m.poll()
    self.assertFalse(m.up.get({'master': 'foobar'}))

  def test_ts_mon_file_deletion(self):
    class MasterMonitor(monitor.MasterMonitor):
      POLLER_CLASSES = []

    with temporary_directory(prefix='monitor-test-') as tempdir:
      ts_mon_filename = os.path.join(tempdir, 'ts_mon.json')
      with open(ts_mon_filename, 'w') as f:
        f.write(' ')
      self.assertTrue(os.path.isfile(ts_mon_filename))
      MasterMonitor('http://example.com',
                    name='foobar',
                    results_file=ts_mon_filename)
      self.assertFalse(os.path.isfile(ts_mon_filename))

  def test_ts_mon_file_polling_file_missing(self):
    # Test that asking to poll a missing file works.
    # Mostly a smoke test.
    class MasterMonitor(monitor.MasterMonitor):
      POLLER_CLASSES = []

    with temporary_directory(prefix='monitor-test-') as tempdir:
      ts_mon_filename = os.path.join(tempdir, 'ts_mon.json')
      self.assertFalse(os.path.isfile(ts_mon_filename))
      MasterMonitor('http://example.com',
                    name='foobar',
                    results_file=ts_mon_filename)
      self.assertFalse(os.path.isfile(ts_mon_filename))


class MastermapTest(unittest.TestCase):
  def test_create_from_mastermap(self):
    specs = [
      {'port': 1234, 'dirname': 'master.foo.bar'},
      {'port': 5678, 'dirname': 'master.baz'},
    ]
    monitors = monitor._create_from_mastermap(specs)

    self.assertEquals(len(specs), len(monitors))
    for mon, spec in zip(monitors, specs):
      self.assertEquals(2, len(mon._pollers))
      self.assertTrue(mon._pollers[0]._url.startswith(
          'http://localhost:%s/' % spec['port']))
      self.assertEquals({'master': spec['dirname']},
                        mon._pollers[0].fields())
      self.assertEquals(mon._pollers[1]._url,
                        monitor.RESULTS_FILE % spec['dirname'])
