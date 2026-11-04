"""
RunCrash is a harness fixture: an 'AppTest' that segfaults, the way a Qt
call on a dead C++ object does.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import signal

from worQt.qtest import AppTest


class RunCrash(AppTest):
  """Kills its own process with a segmentation fault."""

  def run_crash(self) -> None:
    """This test segfaults on purpose."""
    os.kill(os.getpid(), signal.SIGSEGV)
