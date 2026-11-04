"""
RunButtonEvents subclasses 'WidgetTest' and drives the button widgets
through real input against actually rendered windows, using the gesture
surface inherited from 'worQt.qtest.WidgetTest': 'showLive' renders the
widget so 'paintView' is populated, the mouse gestures deliver events
through the application (so they reach the same handlers real input would),
and 'spy'/'waitSignal' observe the reactions - including the timer-driven
click, double-click and hold emissions - without poking handlers or faking
timers.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from worQt.widgets import PaintButton, ClickButton
from worQt.utils import MouseButtonNum
from worQt.utils.geom import Point2D

from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

_LEFT = Qt.MouseButton.LeftButton
_NOMOD = Qt.KeyboardModifier.NoModifier
_RIGHT = MouseButtonNum.RIGHT

#  Comfortably past the sequential (400 ms) and hold (750 ms) timers, so
#  the timer-driven emissions land within the wait.
_CLICK_WAIT = 1500
_HOLD_MS = 900
#  Longer than the press timer (250 ms) but shorter than the hold timer,
#  to land inside the press-expired-but-still-holding window.
_AFTER_PRESS_MS = 350


class RunButtonEvents(WidgetTest):
  """Event-driven tests for 'PaintButton' and 'ClickButton'."""

  def _live(self, widgetType: type) -> Any:
    """Builds a widget, renders it in a real window so 'paintView' is
    populated, wires its logic through 'initUI', and returns it."""
    widget = widgetType()
    widget.resize(200, 200)
    self.showLive(widget)
    widget.initUI()
    return widget

  # \____________________________ PaintButton hover and state

  def run_hover_enter_and_leave(self) -> None:
    """Moving into the content rect hovers and fires 'enter'; moving out
    un-hovers and fires 'leave'."""
    button = self._live(PaintButton)
    enterSpy = self.spy(button.enter)
    leaveSpy = self.spy(button.leave)
    self.move(button, button.paintView.center)
    self.assertTrue(button.hovered)
    self.assertEqual(enterSpy.count, 1)
    self.move(button, Point2D(-50, -50))
    self.assertFalse(button.hovered)
    self.assertEqual(leaveSpy.count, 1)

  def run_button_null_while_hovered(self) -> None:
    """While hovered with no physical button down, 'button' is NULL."""
    button = self._live(PaintButton)
    self.move(button, button.paintView.center)
    self.assertIs(button.button, MouseButtonNum.NULL)

  def run_hover_state_is_flag(self) -> None:
    """A hovered button reports the HOVERED state."""
    button = self._live(PaintButton)
    self.move(button, button.paintView.center)
    self.assertEqual(button.state.name, 'HOVERED')

  def run_content_rect_position_in_view(self) -> None:
    """A move onto the content rect gives a real 'contentRectPosition'."""
    button = self._live(PaintButton)
    self.move(button, button.paintView.center)
    point = button.contentRectPosition
    self.assertNotEqual((point.x, point.y), (-1, -1))

  def run_pressed_state_authentic(self) -> None:
    """A physical press over the content reports pressed and the PRESSED
    state. It uses 'QTest' because 'pressed' reads the live application
    mouse state, which only real input drives, so it needs authentic mode.
    """
    button = self._live(PaintButton)
    center = button.paintView.center
    self.move(button, center)
    QTest.mousePress(button, _LEFT, _NOMOD, center.Q)
    try:
      self.assertTrue(button.pressed)
      self.assertEqual(button.state.name, 'PRESSED')
    finally:
      QTest.mouseRelease(button, _LEFT, _NOMOD, center.Q)

  def run_disabled_slot_edges(self) -> None:
    """Enable/disable are no-ops when already in the state, and re-setting
    'disabled' to its current value is skipped."""
    button = self._live(PaintButton)
    button.enable()  # already enabled -> no-op branch
    button.disabled = True
    button.disabled = True  # same value -> SkipSet
    self.assertTrue(button.disabled)
    button.disable()  # already disabled -> no-op branch
    button.enable()
    self.assertFalse(button.disabled)

  # \____________________________ ClickButton press and release

  def run_press_starts_timers(self) -> None:
    """A press while hovered registers a click and starts the timers."""
    button = self._live(ClickButton)
    center = button.paintView.center
    self.move(button, center)
    self.press(button, center)
    self.assertTrue(button.hasClicks)
    self.assertTrue(button.pressTimer.isActive())
    self.assertTrue(button.holdTimer.isActive())

  def run_release_starts_sequential(self) -> None:
    """A release after a valid press starts the sequential timer."""
    button = self._live(ClickButton)
    center = button.paintView.center
    self.move(button, center)
    self.press(button, center)
    self.release(button, center)
    self.assertTrue(button.sequentialTimer.isActive())

  def run_press_when_not_hovered_ignored(self) -> None:
    """A press outside the content rect registers nothing."""
    button = self._live(ClickButton)
    self.press(button, Point2D(-50, -50))
    self.assertFalse(button.hasClicks)

  # \____________________________ ClickButton emissions

  def run_click_emits_left_click(self) -> None:
    """A left click emits 'leftClick' once the sequential timer resolves."""
    button = self._live(ClickButton)
    with self.waitSignal(button.leftClick, _CLICK_WAIT) as waiter:
      self.click(button, button.paintView.center)
    self.assertTrue(waiter.caught)

  def run_click_emits_multi_click(self) -> None:
    """A left click also emits 'multiClick' carrying the click sequence."""
    button = self._live(ClickButton)
    multiSpy = self.spy(button.multiClick)
    with self.waitSignal(button.leftClick, _CLICK_WAIT):
      self.click(button, button.paintView.center)
    self.assertEqual(multiSpy.count, 1)
    self.assertEqual(multiSpy.args, ((MouseButtonNum.LEFT,),))

  def run_right_click_emits_right_click(self) -> None:
    """A right click emits 'rightClick', so the button argument routes."""
    button = self._live(ClickButton)
    center = button.paintView.center
    with self.waitSignal(button.rightClick, _CLICK_WAIT) as waiter:
      self.click(button, center, _RIGHT)
    self.assertTrue(waiter.caught)

  def run_double_click_emits_double_click(self) -> None:
    """A double click emits 'leftDoubleClick'."""
    button = self._live(ClickButton)
    with self.waitSignal(button.leftDoubleClick, _CLICK_WAIT) as waiter:
      self.doubleClick(button, button.paintView.center)
    self.assertTrue(waiter.caught)

  def run_hold_emits_left_hold(self) -> None:
    """Holding the button past the hold timer emits 'leftHold'."""
    button = self._live(ClickButton)
    holdSpy = self.spy(button.leftHold)
    self.hold(button, _HOLD_MS, button.paintView.center)
    self.assertEqual(holdSpy.count, 1)

  def run_triple_click_emits_triple_click(self) -> None:
    """Three same-button clicks accumulate to a length-three sequence that
    the sequential timer resolves into 'leftTripleClick'."""
    button = self._live(ClickButton)
    center = button.paintView.center
    with self.waitSignal(button.leftTripleClick, _CLICK_WAIT) as waiter:
      self.click(button, center)
      self.click(button, center)
      self.click(button, center)
    self.assertTrue(waiter.caught)

  def run_triple_click_emits_multi_click(self) -> None:
    """A triple click also reports the full three-click sequence through the
    generalized 'multiClick' signal."""
    button = self._live(ClickButton)
    center = button.paintView.center
    multiSpy = self.spy(button.multiClick)
    with self.waitSignal(button.leftTripleClick, _CLICK_WAIT):
      self.click(button, center)
      self.click(button, center)
      self.click(button, center)
    self.assertEqual(multiSpy.count, 1)
    self.assertEqual(
        multiSpy.args,
        ((MouseButtonNum.LEFT, MouseButtonNum.LEFT, MouseButtonNum.LEFT),),
    )

  def run_double_press_hold_emits_double_hold(self) -> None:
    """A click followed by a same-button press-hold emits 'leftDoubleHold':
    the first click registers, then the held second press reaches the hold
    timer at a sequence of length two."""
    button = self._live(ClickButton)
    center = button.paintView.center
    holdSpy = self.spy(button.leftDoubleHold)
    self.click(button, center)
    self.hold(button, _HOLD_MS, center)
    self.assertEqual(holdSpy.count, 1)

  # \____________________________ ClickButton move handling

  def run_small_move_keeps_timers(self) -> None:
    """A move below the cancel threshold leaves the timers running."""
    button = self._live(ClickButton)
    center = button.paintView.center
    self.move(button, center)
    self.press(button, center)
    self.move(button, Point2D(center.x + 1, center.y + 1))
    self.assertTrue(button.pressTimer.isActive())
    self.assertTrue(button.holdTimer.isActive())

  def run_far_move_while_pressed_cancels(self) -> None:
    """A move past the cancel threshold cancels the in-progress click."""
    button = self._live(ClickButton)
    center = button.paintView.center
    self.move(button, center)
    self.press(button, center)
    self.move(button, Point2D(center.x + 50, center.y + 50))
    self.assertFalse(button.hasClicks)

  def run_far_move_while_holding_cancels(self) -> None:
    """Once the press timer has expired, a far move while only the hold
    timer runs still cancels the click."""
    button = self._live(ClickButton)
    center = button.paintView.center
    self.move(button, center)
    self.press(button, center)
    self.wait(_AFTER_PRESS_MS)  # press timer expires, hold timer runs on
    self.move(button, Point2D(center.x + 50, center.y + 50))
    self.assertFalse(button.hasClicks)

  def run_release_after_press_window_cancels(self) -> None:
    """A release once the press timer is no longer active cancels the
    pending click rather than starting the sequential timer."""
    button = self._live(ClickButton)
    center = button.paintView.center
    self.move(button, center)
    self.press(button, center)
    self.wait(_AFTER_PRESS_MS)  # press timer expires
    self.release(button, center)
    self.assertFalse(button.hasClicks)

  def run_move_during_sequential_emits(self) -> None:
    """A far move while the sequential timer is active emits the click at
    once, without waiting for the timer."""
    button = self._live(ClickButton)
    center = button.paintView.center
    clickSpy = self.spy(button.leftClick)
    self.move(button, center)
    self.press(button, center)
    self.release(button, center)
    self.assertTrue(button.sequentialTimer.isActive())
    self.move(button, Point2D(center.x + 50, center.y + 50))
    self.assertEqual(clickSpy.count, 1)
