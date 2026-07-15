"""
WidgetTest subclasses 'AppTest' and adds the gesture surface for
event-based widget testing. It shows widgets in live windows through
'LiveWindow' and synthesises mouse and keyboard events delivered with
'QApplication.sendEvent', so the events pass through 'App.notify' exactly
as real input would and reach the same handlers. Because delivery never
goes through the windowing system's cursor, the gestures behave
identically in the authentic and the headless fallback modes.

The higher-level gestures ('click', 'hold', 'doubleClick') move into the
widget first so it registers as hovered, matching how the worQt button
widgets gate their input, then compose the waiters: 'hold' presses, waits
real milliseconds and releases, because 'ClickButton' distinguishes a
click from a hold purely by elapsed time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from worktoy.waitaminute import TypeException

from . import AppTest
from .primitives import SignalSpy, SignalWaiter, ConditionWaiter, LiveWindow
from ..utils import MouseButtonNum
from ..utils.geom import Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable, TypeAlias, Union

  from PySide6.QtCore import SignalInstance

  Point: TypeAlias = Union[Point2D, QPoint, QPointF, None]
  Button: TypeAlias = Union[Qt.MouseButton, MouseButtonNum]
  Predicate: TypeAlias = Callable[[], bool]

_LEFT = Qt.MouseButton.LeftButton
_NONE = Qt.MouseButton.NoButton
_NO_MOD = Qt.KeyboardModifier.NoModifier


class WidgetTest(AppTest):
  """
  WidgetTest subclasses 'AppTest' and provides the gesture surface for
  event-based widget testing: 'showLive' to render a widget in a real
  window, 'spy'/'waitSignal'/'waitUntil'/'wait' to observe reactions, and
  the mouse ('move', 'press', 'release', 'click', 'doubleClick', 'hold')
  and keyboard ('key', 'typeText') gestures that synthesise input.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showLive(self, widget: QWidget) -> QWidget:
    """The 'showLive' method shows 'widget' as a real window, blocking
    until it is exposed and painted, and returns it."""
    return LiveWindow(widget).show()

  def spy(self, signal: SignalInstance) -> SignalSpy:
    """The 'spy' method returns a 'SignalSpy' recording every emission of
    'signal'."""
    return SignalSpy(signal)

  def waitSignal(
      self, signal: SignalInstance, timeout: int = 1000
  ) -> SignalWaiter:
    """The 'waitSignal' method returns a 'SignalWaiter' context manager
    that blocks until 'signal' fires or 'timeout' milliseconds elapse."""
    return SignalWaiter(signal, timeout)

  def waitUntil(self, predicate: Predicate, timeout: int = 1000) -> bool:
    """The 'waitUntil' method blocks until 'predicate' holds or 'timeout'
    milliseconds elapse, returning whether the predicate held."""
    return ConditionWaiter(predicate, timeout).wait()

  def wait(self, ms: int) -> None:
    """The 'wait' method spins the event loop for 'ms' milliseconds."""
    QTest.qWait(ms)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _resolveButton(button: Button) -> Qt.MouseButton:
    """The '_resolveButton' method maps a 'MouseButtonNum' to its 'Qt'
    value, leaving a plain 'Qt.MouseButton' unchanged."""
    if isinstance(button, MouseButtonNum):
      return button.value
    return button

  @staticmethod
  def _localPoint(widget: QWidget, point: Point) -> QPoint:
    """The '_localPoint' method normalises a target point to a
    widget-local 'QPoint', defaulting to the widget's centre."""
    if point is None:
      return widget.rect().center()
    if isinstance(point, Point2D):
      return point.Q
    if isinstance(point, QPointF):
      return point.toPoint()
    if isinstance(point, QPoint):
      return point
    raise TypeException('point', point, Point2D, QPoint, QPointF)

  def _sendMouse(self, widget, kind, point, button, buttons) -> None:
    """The '_sendMouse' method builds one 'QMouseEvent' at a widget-local
    point and delivers it through the application."""
    localPoint = self._localPoint(widget, point)
    localPos = QPointF(localPoint)
    globalPos = QPointF(widget.mapToGlobal(localPoint))
    button = self._resolveButton(button)
    buttons = self._resolveButton(buttons)
    event = QMouseEvent(kind, localPos, globalPos, button, buttons, _NO_MOD)
    QApplication.sendEvent(widget, event)

  def move(self, widget: QWidget, point: Point = None) -> None:
    """The 'move' method delivers a mouse-move to 'widget', so a widget
    that tracks the cursor updates its hovered state."""
    self._sendMouse(widget, QEvent.Type.MouseMove, point, _NONE, _NONE)

  def press(
      self, widget: QWidget, point: Point = None, button: Button = _LEFT
  ) -> None:
    """The 'press' method delivers a mouse-button-press to 'widget'."""
    kind = QEvent.Type.MouseButtonPress
    self._sendMouse(widget, kind, point, button, button)

  def release(
      self, widget: QWidget, point: Point = None, button: Button = _LEFT
  ) -> None:
    """The 'release' method delivers a mouse-button-release to 'widget'."""
    kind = QEvent.Type.MouseButtonRelease
    self._sendMouse(widget, kind, point, button, _NONE)

  def click(
      self, widget: QWidget, point: Point = None, button: Button = _LEFT
  ) -> None:
    """The 'click' method moves into 'widget', then presses and releases,
    so a hover-gated widget registers the click."""
    self.move(widget, point)
    self.press(widget, point, button)
    self.release(widget, point, button)

  def doubleClick(
      self, widget: QWidget, point: Point = None, button: Button = _LEFT
  ) -> None:
    """The 'doubleClick' method delivers a press, release, double-click and
    release, the sequence Qt sends for a real double click."""
    self.move(widget, point)
    self.press(widget, point, button)
    self.release(widget, point, button)
    kind = QEvent.Type.MouseButtonDblClick
    self._sendMouse(widget, kind, point, button, button)
    self.release(widget, point, button)

  def hold(
      self,
      widget: QWidget,
      ms: int,
      point: Point = None,
      button: Button = _LEFT,
  ) -> None:
    """The 'hold' method presses, waits 'ms' real milliseconds, then
    releases, so a widget that times its press registers a hold."""
    self.move(widget, point)
    self.press(widget, point, button)
    self.wait(ms)
    self.release(widget, point, button)

  def key(
      self,
      widget: QWidget,
      keyCode: Qt.Key,
      modifiers: Qt.KeyboardModifier = _NO_MOD,
      text: str = '',
  ) -> None:
    """The 'key' method delivers a key-press and key-release to 'widget'."""
    press = QKeyEvent(QEvent.Type.KeyPress, keyCode, modifiers, text)
    release = QKeyEvent(QEvent.Type.KeyRelease, keyCode, modifiers, text)
    QApplication.sendEvent(widget, press)
    QApplication.sendEvent(widget, release)

  def typeText(self, widget: QWidget, text: str) -> None:
    """The 'typeText' method delivers each character of 'text' to 'widget'
    as a key-press and key-release carrying that character."""
    for char in text:
      self.key(widget, Qt.Key.Key_unknown, _NO_MOD, char)
