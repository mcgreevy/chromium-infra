# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import math
import re

from analysis import callstack_detectors
from analysis import callstack_filters
from analysis.stacktrace import CallStackBuffer
from analysis.stacktrace import StacktraceBuffer
from analysis.stacktrace import StackFrame
from analysis.stacktrace import Stacktrace
from analysis.stacktrace_parser import StacktraceParser
from analysis.type_enums import CallStackFormatType
from analysis.type_enums import LanguageType

DEFAULT_TOP_N_FRAMES = 7


class ChromeCrashParser(StacktraceParser):

  def Parse(self, stacktrace_string, deps, signature=None, top_n_frames=None):
    """Parse fracas stacktrace string into Stacktrace instance."""
    # Filters to filter callstack buffers.
    filters = [callstack_filters.FilterInlineFunction(),
               callstack_filters.KeepTopNFrames(top_n_frames or
                                                DEFAULT_TOP_N_FRAMES)]
    stacktrace_buffer = StacktraceBuffer(signature=signature, filters=filters)

    stack_detector = callstack_detectors.ChromeCrashStackDetector()
    # Initial background callstack which is not to be added into Stacktrace.
    stack_buffer = CallStackBuffer()
    for line in stacktrace_string.splitlines():
      start_of_callstack = stack_detector(line)

      if start_of_callstack:
        stacktrace_buffer.AddFilteredStack(stack_buffer)
        stack_buffer = CallStackBuffer.FromStartOfCallStack(start_of_callstack)
      else:
        frame = StackFrame.Parse(stack_buffer.language_type,
                                 stack_buffer.format_type, line, deps,
                                 len(stack_buffer.frames))
        if frame is not None:
          stack_buffer.frames.append(frame)

    # Add the last stack to stacktrace.
    stacktrace_buffer.AddFilteredStack(stack_buffer)
    return stacktrace_buffer.ToStacktrace()
