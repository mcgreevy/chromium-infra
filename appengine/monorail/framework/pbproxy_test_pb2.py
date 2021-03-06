# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Message classes for use by template_helpers_test."""

from protorpc import messages


class PBProxyExample(messages.Message):
  """A simple protocol buffer to test template_helpers.PBProxy."""
  foo = messages.StringField(1)
  bar = messages.BooleanField(2, default=False)


class PBProxyNested(messages.Message):
  """A simple protocol buffer to test template_helpers.PBProxy."""
  nested = messages.MessageField(PBProxyExample, 1)
  multiple_strings = messages.StringField(2, repeated=True)
  multiple_pbes = messages.MessageField(PBProxyExample, 3, repeated=True)
