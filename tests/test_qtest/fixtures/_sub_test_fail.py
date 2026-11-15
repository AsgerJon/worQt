"""
RunSubTestFail is a harness fixture: a failing 'subTest' block. worktoy's
'SubTest' records the failure and the report raises it among the test's
cleanups ('doCleanups', from worktoy 1.2.0; before, 'BaseTest.tearDown'
raised it) - the path that once escaped the harness and was reported as a
pass.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.qtest import AppTest


class RunSubTestFail(AppTest):
  """Fails through a 'subTest' block; the test after it still runs."""

  def run_sub_test_fails(self) -> None:
    """A failing 'subTest' block fails the test from its cleanups."""
    with self.subTest('failing on purpose'):
      self.assertEqual(1, 2)

  def run_after_sub_test(self) -> None:
    """A failure raised from the cleanups does not stop the tests after
    it."""
