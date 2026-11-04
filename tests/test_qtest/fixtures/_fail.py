"""
RunFail is a harness fixture: an 'AppTest' with a failing test followed by
a passing one, which must still run.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.qtest import AppTest


class RunFail(AppTest):
  """Fails one test; the test after it still runs."""

  def run_fails(self) -> None:
    """This test fails on purpose."""
    self.assertEqual(1, 2)

  def run_after_failure(self) -> None:
    """A failure does not stop the tests after it."""
