# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from frontend.handlers.result_feedback import ResultFeedback


class CracasResultFeedback(ResultFeedback):  # pragma: no cover

  @property
  def client(self):
    return 'cracas'
