"""
RunPass is a harness fixture: an 'AppTest' that passes, and by passing
shows the parts of the unittest contract the harness honours - its tests
run inside the live event loop, 'setUpClass' runs, a test method inherited
from a base class runs, and 'skipTest' counts as a pass. The module also
imports 'unittest.TestCase', a 'Test*' class it does not define, which
must not stop it resolving to 'RunPass'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from unittest import TestCase  # noqa: F401  # imported, not defined here

from PySide6.QtCore import QThread

from worQt.qtest import AppTest


class _InheritedTests(AppTest):
  """A base class whose test method the fixture inherits."""

  def run_inherited(self) -> None:
    """A test method defined on a base class runs on the subclass."""


class RunPass(_InheritedTests):
  """Passes, exercising the unittest contract along the way."""

  __set_up_class__ = False

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.__set_up_class__ = True

  def run_set_up_class_ran(self) -> None:
    """'setUpClass' ran before the first test."""
    self.assertTrue(self.__set_up_class__)

  def run_inside_live_loop(self) -> None:
    """The test runs inside the running 'exec' loop of the application."""
    self.assertIsNotNone(self.app)
    self.assertEqual(QThread.currentThread().loopLevel(), 1)

  def run_skipped(self) -> None:
    """A skipped test is not a failure."""
    self.skipTest('skipping is not failing')
