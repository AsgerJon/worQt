"""
RunAppTestInternals covers the 'AppTest' lifecycle helpers that need a
running 'QApplication': the 'tearDown' widget disposal (with and without a
'setUp' snapshot) and '_runMethod' for a passing and a raising method.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import contextlib
import io
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _Probe(AppTest):
  """An 'AppTest' with a passing and a raising method for '_runMethod'."""

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
    probe.tearDown()  # __persistent_widgets__ is None -> set()

  def run_teardown_disposes_new_widget(self) -> None:
    """A top-level widget opened after 'setUp' is disposed by 'tearDown'
    (the disposal loop runs; the widget's C++ object is freed, so it is not
    inspected afterward)."""
    probe = _Probe('test_pass')
    probe.setUp()
    widget = QWidget()
    widget.show()
    probe.tearDown()

  def run_teardown_keeps_preopen_widget(self) -> None:
    """A top-level widget already open at 'setUp' is left alone by
    'tearDown' (the skip branch of the disposal loop)."""
    widget = QWidget()
    widget.show()
    probe = _Probe('test_pass')
    probe.setUp()  # snapshots 'widget' into __persistent_widgets__
    probe.tearDown()  # 'widget' is in preopen -> skipped, not disposed
    self.assertTrue(widget.isVisible())
    widget.hide()
    widget.deleteLater()

  def run_run_method_pass(self) -> None:
    """'_runMethod' returns True for a passing method."""
    self.assertTrue(_Probe._runMethod('test_pass'))

  def run_run_method_fail(self) -> None:
    """'_runMethod' returns False for a raising method and prints its
    traceback (captured here so it does not clutter the report)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(
        buffer
        ):
      result = _Probe._runMethod('test_raise')
    self.assertFalse(result)
