"""
TestPlain is a harness fixture: a plain 'BaseTest', which runs in a child
of its own like any 'AppTest' but without an application.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QApplication
from worktoy.work_test import BaseTest


class TestPlain(BaseTest):
  """Passes without a 'QApplication'."""

  def test_no_application(self) -> None:
    """A plain test class runs without a 'QApplication'."""
    self.assertIsNone(QApplication.instance())
