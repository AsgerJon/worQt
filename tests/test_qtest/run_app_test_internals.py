"""
RunAppTestInternals covers the 'AppTest' lifecycle that needs a running
'QApplication': the 'tearDown' widget disposal - with and without a
'setUp' snapshot, and in a test failed by a 'subTest' block - an
'AppTest' running under the standard 'TestCase.run', and worktoy's
report of failed 'subTest' blocks (among the cleanups): it fails the
test even when its 'tearDown' does not hand on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Any


class _Probe(AppTest):
  """An 'AppTest' with a passing and a raising test to run directly."""

  def test_pass(self) -> None:
    pass

  def test_raise(self) -> None:
    raise RuntimeError('boom')


class _SubFailProbe(AppTest):
  """An 'AppTest' opening a window and failing a 'subTest' block."""

  def test_sub_fail(self) -> None:
    self.opened = QWidget()
    self.opened.show()
    with self.subTest('failing on purpose'):
      self.assertEqual(1, 2)


class _NoHandOnProbe(AppTest):
  """An 'AppTest' whose 'tearDown' does not hand on, failing a 'subTest'
  block."""

  def tearDown(self) -> None:
    pass

  def test_sub_fail(self) -> None:
    with self.subTest('failing on purpose'):
      self.assertEqual(1, 2)


class RunAppTestInternals(AppTest):
  """Tests for the 'AppTest' lifecycle internals."""

  def run_teardown_without_setup(self) -> None:
    """'tearDown' with no prior 'setUp' treats the open set as empty and
    does not raise."""
    probe = _Probe('test_pass')
    probe.tearDown()

  def run_teardown_disposes_new_widget(self) -> None:
    """A top-level widget opened after 'setUp' is freed by 'tearDown'."""
    probe = _Probe('test_pass')
    probe.setUp()
    widget = QWidget()
    widget.show()
    probe.tearDown()
    self.assertFalse(isValid(widget))

  def run_teardown_keeps_preopen_widget(self) -> None:
    """A top-level widget already open at 'setUp' is left alone by
    'tearDown'."""
    widget = QWidget()
    widget.show()
    probe = _Probe('test_pass')
    probe.setUp()
    probe.tearDown()
    self.assertTrue(isValid(widget))
    self.assertTrue(widget.isVisible())
    widget.hide()
    widget.deleteLater()

  def run_sub_test_failure_disposes(self) -> None:
    """A test failed by a 'subTest' block, run by 'TestCase.run', is one
    failure, and the window it opened is freed."""
    result = unittest.TestResult()
    probe = _SubFailProbe('test_sub_fail')
    probe.run(result)
    self.assertEqual(len(result.failures), 1)
    self.assertEqual(len(result.errors), 0)
    self.assertFalse(isValid(probe.opened))

  def run_sub_test_failure_without_hand_on(self) -> None:
    """A test whose 'tearDown' does not hand on still fails by its failed
    'subTest' block: the report runs among the cleanups."""
    result = unittest.TestResult()
    _NoHandOnProbe('test_sub_fail').run(result)
    self.assertEqual(len(result.failures), 1)

  def run_test_case_run_pass(self) -> None:
    """Under 'TestCase.run' a passing 'AppTest' test is a success."""
    result = unittest.TestResult()
    _Probe('test_pass').run(result)
    self.assertTrue(result.wasSuccessful())

  def run_test_case_run_error(self) -> None:
    """Under 'TestCase.run' a raising 'AppTest' test is an error."""
    result = unittest.TestResult()
    _Probe('test_raise').run(result)
    self.assertEqual(len(result.errors), 1)
