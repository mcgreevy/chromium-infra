# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from datetime import datetime

import webapp2

from testing_utils import testing

from handlers import culprit
from model import analysis_status as status
from model.wf_suspected_cl import WfSuspectedCL


class CulpritTest(testing.AppengineTestCase):
  app_module = webapp2.WSGIApplication(
      [('/culprit', culprit.Culprit), ], debug=True)

  def testGetCulpritSuccess(self):
    suspected_cl = WfSuspectedCL.Create('chromium', 'r1', 123)
    suspected_cl.builds['m/b1/1'] = {}
    suspected_cl.builds['m/b2/2'] = {}
    suspected_cl.cr_notification_status = status.COMPLETED
    suspected_cl.cr_notification_time = datetime(2016, 06, 24, 10, 03, 00)
    suspected_cl.put()

    expected_result = {
        'project_name': 'chromium',
        'revision': 'r1',
        'commit_position': 123,
        'cr_notified': True,
        'cr_notification_time': '2016-06-24 10:03:00 UTC',
        'builds': [
            {
                'master_name': 'm',
                'builder_name': 'b1',
                'build_number': '1',
            },
            {
                'master_name': 'm',
                'builder_name': 'b2',
                'build_number': '2',
            },
        ],
        'key': suspected_cl.key.urlsafe(),
    }

    response = self.test_app.get(
        '/culprit?key=%s&format=json' % suspected_cl.key.urlsafe())
    self.assertEqual(200, response.status_int)
    self.assertEqual(expected_result, response.json_body)
