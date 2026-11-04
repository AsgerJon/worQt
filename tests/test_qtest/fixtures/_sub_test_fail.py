"""
RunSubTestFail is a harness fixture: a failing 'subTest' block. worktoy's
'SubTest' records the failure and 'BaseTest.tearDown' raises it, so the
failure arrives from 'tearDown' - the path that used to escape the harness
and be reported as a pass.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.qtest import AppTest


class RunSubTestFail(AppTest):
  """Fails through a 'subTest' block; the test after it still runs."""

  def run_sub_test_fails(self) -> None:
    """A failing 'subTest' block fails the test from 'tearDown'."""
    with self.subTest('failing on purpose'):
      self.assertEqual(1, 2)

  def run_after_sub_test(self) -> None:
    """A failure raised from 'tearDown' does not stop the tests after it."""
