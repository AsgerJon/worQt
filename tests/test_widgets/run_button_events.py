"""
RunButtonEvents subclasses 'WidgetTest' and drives the button widgets'
mouse-event handlers with synthesized 'QMouseEvent's against a rendered
widget (so 'paintView' is populated): 'PaintButton' hover tracking and the
enable/disable edges, and 'ClickButton' press/move/release, the timer
expiries, double-click, and the state wiring in 'initUI'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtTest import QTest

from worQt.widgets import PaintButton, ClickButton
from worQt.utils import MouseButtonNum
from worQt.utils.geom import Point2D

from . import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

_LEFT = Qt.MouseButton.LeftButton
_NONE = Qt.MouseButton.NoButton
_NOMOD = Qt.KeyboardModifier.NoModifier


def _mouse(eventType, x, y, button=_NONE, buttons=_NONE) -> QMouseEvent:
  """Build a 'QMouseEvent' at the given local position."""
  return QMouseEvent(eventType, QPointF(x, y), button, buttons, _NOMOD)


def _rendered(widgetType):
  """A widget sized and rendered once, so 'paintView' is populated."""
  widget = widgetType()
  widget.resize(200, 200)
  widget.render(QPixmap(widget.size()))
  return widget


class RunButtonEvents(WidgetTest):
  """Tests for the button mouse-event handlers."""

  # \____________________________ PaintButton

  def run_hover_enter_and_leave(self) -> None:
    """Moving into the content rect hovers; moving out un-hovers."""
    button = _rendered(PaintButton)
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    self.assertTrue(button.hovered)
    self.assertEqual(button.cursorPosition.x, center.x)
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, -99, -99))
    self.assertFalse(button.hovered)

  def run_button_while_hovered(self) -> None:
    """While hovered with no button held, 'button' is the null button."""
    button = _rendered(PaintButton)
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    self.assertIs(button.button, MouseButtonNum.NULL)

  def run_press_release_repaint(self) -> None:
    """The base press/release handlers run without error."""
    button = _rendered(PaintButton)
    button.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, 5, 5, _LEFT))
    button.mouseReleaseEvent(
        _mouse(QEvent.Type.MouseButtonRelease, 5, 5, _LEFT))

  def run_disabled_skip_and_slot_edges(self) -> None:
    """Disabled re-set is skipped; enable/disable no-op when unchanged."""
    button = PaintButton()
    button.enable()  # already enabled -> no-op branch
    button.disabled = True
    button.disabled = True  # same value -> SkipSet
    self.assertTrue(button.disabled)
    button.disable()  # already disabled -> no-op branch
    button.enable()
    self.assertFalse(button.disabled)

  # \____________________________ ClickButton

  def run_click_press_starts_timers(self) -> None:
    """A press while hovered registers a click and starts the timers."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, center.x, center.y, _LEFT, _LEFT))
    self.assertTrue(button.hasClicks)
    self.assertTrue(button.pressTimer.isActive())
    self.assertTrue(button.holdTimer.isActive())

  def run_click_release_starts_sequential(self) -> None:
    """A release after a valid press starts the sequential timer."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, center.x, center.y, _LEFT, _LEFT))
    button.mouseReleaseEvent(
        _mouse(QEvent.Type.MouseButtonRelease, center.x, center.y, _LEFT))
    self.assertTrue(button.sequentialTimer.isActive())

  def run_sequential_expiry_emits_click(self) -> None:
    """The sequential timeout emits the accumulated single click."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    fired = []
    button.leftClick.connect(lambda: fired.append(True))
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, center.x, center.y, _LEFT, _LEFT))
    button.mouseReleaseEvent(
        _mouse(QEvent.Type.MouseButtonRelease, center.x, center.y, _LEFT))
    button._onSequentialExpired()
    self.assertEqual(fired, [True])

  def run_hold_expiry_emits_hold(self) -> None:
    """The hold timeout emits the hold signal for the registered click."""
    button = ClickButton()
    fired = []
    button.leftHold.connect(lambda: fired.append(True))
    button._registerClick(MouseButtonNum.LEFT)
    button._onHoldExpired()
    self.assertEqual(fired, [True])

  def run_move_while_pressed_invalidates(self) -> None:
    """Moving far enough while pressed cancels the in-progress click."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, center.x, center.y, _LEFT, _LEFT))
    button.mouseMoveEvent(
        _mouse(QEvent.Type.MouseMove, center.x + 50, center.y + 50,
               _NONE, _LEFT))
    self.assertFalse(button.hasClicks)

  def run_double_click_routes_through_press(self) -> None:
    """A double-click runs the press handler (twice, via Qt's default and
    the explicit call), which self-cancels back to no pending clicks."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mouseDoubleClickEvent(
        _mouse(QEvent.Type.MouseButtonDblClick, center.x, center.y,
               _LEFT, _LEFT))
    self.assertFalse(button.hasClicks)

  def run_press_when_not_hovered_ignored(self) -> None:
    """A press outside the content rect registers nothing."""
    button = _rendered(ClickButton)
    button.initUI()
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, -50, -50, _LEFT, _LEFT))
    self.assertFalse(button.hasClicks)

  def run_release_while_hovered_no_clicks(self) -> None:
    """A release while hovered but with no pending click is dropped."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mouseReleaseEvent(
        _mouse(QEvent.Type.MouseButtonRelease, center.x, center.y, _LEFT))
    self.assertFalse(button.hasClicks)

  def run_release_after_press_timer_expired(self) -> None:
    """A release once the press timer is no longer active cancels the
    pending click rather than starting the sequential timer."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, center.x, center.y, _LEFT, _LEFT))
    QTimer.stop(button.pressTimer)
    button.mouseReleaseEvent(
        _mouse(QEvent.Type.MouseButtonRelease, center.x, center.y, _LEFT))
    self.assertFalse(button.hasClicks)

  def run_move_while_holding_invalidates(self) -> None:
    """A far move while only the hold timer is active cancels the click."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, center.x, center.y, _LEFT, _LEFT))
    QTimer.stop(button.pressTimer)  # leave only the hold timer active
    button.mouseMoveEvent(
        _mouse(QEvent.Type.MouseMove, center.x + 50, center.y + 50,
               _NONE, _LEFT))
    self.assertFalse(button.hasClicks)

  def run_move_during_sequential_emits(self) -> None:
    """A far move while the sequential timer is active emits the click."""
    button = _rendered(ClickButton)
    button.initUI()
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mousePressEvent(
        _mouse(QEvent.Type.MouseButtonPress, center.x, center.y, _LEFT, _LEFT))
    button.mouseReleaseEvent(
        _mouse(QEvent.Type.MouseButtonRelease, center.x, center.y, _LEFT))
    self.assertTrue(button.sequentialTimer.isActive())
    button.mouseMoveEvent(
        _mouse(QEvent.Type.MouseMove, center.x + 50, center.y + 50))
    self.assertFalse(button.hasClicks)

  def run_move_within_limit_keeps_timers(self) -> None:
    """A move smaller than the cancel threshold leaves the active timers
    running (the 'within limit, do not cancel' branches), both while the
    press/hold timers are active and while the sequential timer is."""
    pressing = _rendered(ClickButton)
    pressing.initUI()
    pressing.pressTimer.start()
    pressing.holdTimer.start()
    pressing.__move_point__ = Point2D(-1, -1)  # zero-length move below limit
    pressing.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, -50, -50))
    self.assertTrue(pressing.pressTimer.isActive())
    self.assertTrue(pressing.holdTimer.isActive())
    sequencing = _rendered(ClickButton)
    sequencing.initUI()
    sequencing.sequentialTimer.start()
    sequencing.__move_point__ = Point2D(-1, -1)
    sequencing.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, -50, -50))
    self.assertTrue(sequencing.sequentialTimer.isActive())

  # \____________________________ PaintButton state

  def run_hover_repeated_and_state(self) -> None:
    """A second move inside keeps the hover (no re-enter), and the resulting
    state is the hovered state."""
    button = _rendered(PaintButton)
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    button.mouseMoveEvent(
        _mouse(QEvent.Type.MouseMove, center.x, center.y))  # no re-enter
    self.assertTrue(button.hovered)
    self.assertEqual(button.state.name, 'HOVERED')

  def run_content_rect_position_in_view(self) -> None:
    """With the cursor placed so its box-relative position lands inside the
    paint view, 'contentRectPosition' returns that position."""
    button = _rendered(PaintButton)
    view = button.paintView
    x = 2 * view.left if view.left else view.center.x
    y = 2 * view.top if view.top else view.center.y
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, x, y))
    point = button.contentRectPosition
    self.assertNotEqual((point.x, point.y), (-1, -1))

  def run_move_out_while_not_hovered(self) -> None:
    """An outward move while not hovered makes no state change."""
    button = _rendered(PaintButton)
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, -99, -99))
    self.assertFalse(button.hovered)

  def run_pressed_state(self) -> None:
    """While hovered with the left button physically down, the button is
    pressed and reports the pressed state."""
    button = _rendered(PaintButton)
    button.show()
    QTest.qWait(10)
    center = button.paintView.center
    button.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, center.x, center.y))
    QTest.mousePress(button, _LEFT, _NOMOD, button.rect().center())
    try:
      self.assertTrue(button.pressed)
      self.assertEqual(button.state.name, 'PRESSED')
    finally:
      QTest.mouseRelease(button, _LEFT, _NOMOD, button.rect().center())
      button.close()
