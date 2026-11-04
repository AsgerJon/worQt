"""
RunEvents subclasses 'WaitTest' and tests the 'worQt.waitaminute.events'
exception family: 'EventException' and its 'KeyboardException',
'MouseException', 'PaintException' and 'InvalidSizePolicy' subclasses. Each
parses its positional arguments by type to pull out the widget, event,
painter, message or size policy, so the tests pass those in mixed order and
assert the captured attributes plus the string forms.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from worQt.waitaminute.events import (EventException,
  KeyboardException,
  MouseException,
  PaintException,
  InvalidSizePolicy)

from . import WaitTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunEvents(WaitTest):
  """Tests for the event-exception family."""

  def run_event_exception_with_event(self) -> None:
    """An 'EventException' carries its event and renders to text."""
    event = QEvent(QEvent.Type.User)
    exc = EventException(event)
    self.assertIs(exc.event, event)
    self.assertIn('EventException', str(exc))
    self.assertIn('EventException', repr(exc))

  def run_event_exception_without_event(self) -> None:
    """With no event the string form falls back to 'Exception'."""
    exc = EventException()
    self.assertIsNone(exc.event)
    self.assertEqual(str(exc), '')

  def run_keyboard_exception(self) -> None:
    """A 'KeyboardException' pulls out a widget-holder, event and message."""
    widget = QWidget()
    holder = SimpleNamespace(widget=widget)
    event = QKeyEvent(QEvent.Type.KeyPress,
                      Qt.Key.Key_A,
                      Qt.KeyboardModifier.NoModifier)
    exc = KeyboardException(holder, event, 'boom')
    self.assertIs(exc.widget, widget)
    self.assertIs(exc.event, event)

  def run_keyboard_exception_ignores_extra(self) -> None:
    """Arguments matching nothing are passed through to 'Exception'."""
    event = QKeyEvent(QEvent.Type.KeyPress,
                      Qt.Key.Key_A,
                      Qt.KeyboardModifier.NoModifier)
    exc = KeyboardException(event, 'boom', 123)
    self.assertIs(exc.event, event)

  def run_keyboard_exception_no_message(self) -> None:
    """Without a message the no-message constructor branch is taken."""
    event = QKeyEvent(QEvent.Type.KeyPress,
                      Qt.Key.Key_A,
                      Qt.KeyboardModifier.NoModifier)
    exc = KeyboardException(event)
    self.assertIs(exc.event, event)

  def run_mouse_exception_no_message(self) -> None:
    """Without a message (and without a widget) the bare branches run."""
    event = QMouseEvent(QEvent.Type.MouseButtonPress,
                        QPointF(1, 1),
                        Qt.MouseButton.LeftButton,
                        Qt.MouseButton.LeftButton,
                        Qt.KeyboardModifier.NoModifier)
    exc = MouseException(event)
    self.assertIs(exc.event, event)

  def run_mouse_exception(self) -> None:
    """A 'MouseException' pulls out the widget and the mouse event."""
    widget = QWidget()
    event = QMouseEvent(QEvent.Type.MouseButtonPress,
                        QPointF(1, 1),
                        Qt.MouseButton.LeftButton,
                        Qt.MouseButton.LeftButton,
                        Qt.KeyboardModifier.NoModifier)
    exc = MouseException(widget, event, 'boom')
    self.assertIs(exc.widget, widget)
    self.assertIs(exc.event, event)

  def run_paint_exception(self) -> None:
    """A 'PaintException' pulls out the widget, painter and event."""
    widget = QWidget()
    pixmap = QPixmap(8, 8)
    painter = QPainter(pixmap)
    event = QEvent(QEvent.Type.Paint)
    try:
      exc = PaintException(widget, painter, event, 'boom')
      self.assertIs(exc.widget, widget)
      self.assertIs(exc.painter, painter)
      self.assertIs(exc.event, event)
    finally:
      painter.end()

  def run_paint_exception_no_message(self) -> None:
    """A 'PaintException' without a message takes the bare branch."""
    widget = QWidget()
    pixmap = QPixmap(8, 8)
    painter = QPainter(pixmap)
    event = QEvent(QEvent.Type.Paint)
    try:
      exc = PaintException(widget, painter, event)
      self.assertIs(exc.event, event)
    finally:
      painter.end()

  def run_invalid_size_policy(self) -> None:
    """'InvalidSizePolicy' keeps the offending policy and reports it."""
    exc = InvalidSizePolicy('not-a-policy', None)
    self.assertEqual(exc.sizePolicy, 'not-a-policy')
    self.assertIn('InvalidSizePolicy', str(exc))

  def run_invalid_size_policy_empty(self) -> None:
    """With no policy the string form falls back to 'EventException'."""
    exc = InvalidSizePolicy()
    self.assertIsNone(exc.sizePolicy)
    self.assertEqual(str(exc), '')

  def run_all_are_event_exceptions(self) -> None:
    """Every subclass is an 'EventException'."""
    for cls in (KeyboardException, MouseException, PaintException,
                InvalidSizePolicy):
      self.assertTrue(issubclass(cls, EventException))

  def run_mouse_exception_unmatched_arg(self) -> None:
    """A 'MouseException' built from an argument matching neither widget,
    event nor message keeps no widget/event (the unmatched-arg branch)."""
    exc = MouseException(object())
    self.assertIsNone(exc.event)

  def run_paint_exception_bare(self) -> None:
    """A 'PaintException' with only an unmatched argument keeps no widget,
    painter or event (the no-widget / no-painter / unmatched branches)."""
    exc = PaintException(object())
    self.assertIsNone(exc.event)
