"""
RunAppTestInternals covers the 'AppTest' lifecycle that needs a running
'QApplication': the 'tearDown' widget disposal - with and without a
'setUp' snapshot, and after the base 'tearDown' fails the test - and an
'AppTest' running under the standard 'TestCase.run'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import unittest
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _Probe(AppTest):
  """An 'AppTest' with a passing and a raising test to run directly."""

  def test_pass(self) -> None:
    pass

  def test_raise(self) -> None:
    raise RuntimeError('boom')


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

  def run_teardown_disposes_after_failed_base(self) -> None:
    """When the base 'tearDown' fails the test over a failed 'subTest'
    block, the widgets the test opened are still freed."""
    probe = _Probe('test_pass')
    probe.setUp()
    widget = QWidget()
    widget.show()
    with probe.subTest('failing on purpose'):
      probe.assertEqual(1, 2)
    with self.assertRaises(AssertionError):
      probe.tearDown()
    self.assertFalse(isValid(widget))

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
