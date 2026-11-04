"""
RunHang is a harness fixture: an 'AppTest' that never finishes, with a
one second deadline.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import time

from worQt.qtest import AppTest


class RunHang(AppTest):
  """Sleeps far past its deadline."""

  __time_out__ = 1.0

  def run_hang(self) -> None:
    """This test hangs on purpose."""
    time.sleep(60)
