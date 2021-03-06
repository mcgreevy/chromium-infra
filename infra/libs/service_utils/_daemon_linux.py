# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Locking, timeout, and other process management functions."""

from ._daemon_nix import (
    become_daemon,
    close_all_fds,
    flock,
    LockAlreadyLocked,
)


def add_timeout(cmd, timeout_secs):
  """Adds a timeout to a command using linux's (gnu) /bin/timeout."""
  return ['timeout', str(timeout_secs)] + cmd
