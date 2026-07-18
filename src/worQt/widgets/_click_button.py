"""
ClickButton subclasses 'PaintButton' and recognises click and hold
sequences from the raw mouse events, dispatching each as a Qt signal.

The recogniser is an explicit three-phase state machine: 'IDLE',
'PRESSING' (a button is down) and 'WAITING' (a click landed, waiting for
the next). A 'Click Sequence' is a run of same-button clicks; a 'Hold
Sequence' is such a run whose final press is held into the hold band.

Every timing and drift threshold is a labelled default in the 'DEFAULT
VALUES' block; a subclass customises the recogniser by overriding any of
them. The drift for a whole sequence is measured from the first click's
point (the anchor).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, overload, TypeVar

from PySide6.QtCore import (QTimer,
                            QElapsedTimer,
                            Signal,
                            SignalInstance,
                            QEvent,
                            QObject)
from PySide6.QtGui import QMouseEvent
from worktoy.desc import Field
from worktoy.keenum import KeeNum, Kee
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException, MissingVariable

from ..utils import MouseButtonNum
from ..utils.geom import Point2D, Vector2D
from . import PaintButton

T = TypeVar('T')

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, Any, TypeAlias, Union, Optional, Mapping

  Meta: TypeAlias = Type[QObject]
  Sig: TypeAlias = Union[Signal, SignalInstance]
  MaybeObject: TypeAlias = Optional[QObject]
  ClickSequence: TypeAlias = tuple[MouseButtonNum, ...]


  # @formatter:off
  class __cpp_wyd__:
    @overload
    def __get__(self, instance: None, owner: Meta) -> Signal: ...
    @overload
    def __get__(self, instance: QObject, owner: Meta) -> SignalInstance: ...
    def __get__(self, instance: MaybeObject, owner: Meta) -> Sig: ...
  ClickDict: TypeAlias = Mapping[MouseButtonNum, __cpp_wyd__]
  # @formatter:on
else:
  __cpp_wyd__ = object


class ClickPhase(KeeNum):
  """The three phases of the click/hold recogniser."""

  IDLE = Kee[int](0)  # nothing collected, no button down
  PRESSING = Kee[int](1)  # a button is currently held down
  WAITING = Kee[int](2)  # a click landed, waiting for the next


class ClickButton(PaintButton):
  """
  ClickButton subclasses 'PaintButton' and recognises click and hold
  sequences as an explicit state machine.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DEFAULT VALUES   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Subclasses customise the recogniser by overriding any of these.
  #
  #  Duration bands — how long the final button stays down (milliseconds,
  #  press to release):
  #    below pressLimit ......... a click, added to the sequence
  #    pressLimit .. holdLimit .. rejected: 'pressRejected' (dead zone 1)
  #    holdLimit .. holdMax ..... a hold, dispatched on release
  #    holdMax and beyond ....... rejected: 'holdTooLong'   (dead zone 2)
  __press_time_limit__: int = 250  # a click must release before this
  __hold_time_limit__: int = 750  # a hold must pass this ('_holdArmed')
  __hold_max_limit__: int = 1500  # holding past this is rejected
  #
  #  Sequence wait — how long to wait after a release for the next click
  #  before the collected Click Sequence is dispatched (milliseconds).
  __sequential_time_limit__: int = 400
  #
  #  Drift limits — squared pixel distance the cursor may wander from the
  #  first-click anchor. Down: exceeding cancels (regret). Waiting up:
  #  exceeding dispatches the collected clicks at once.
  __press_move_limit__: int = 3 ** 2  # while a button is down
  __sequential_move_limit__: int = 3 ** 2  # while waiting for the next

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __invalid_state__: Optional[bool] = None
  __move_point__: Optional[Point2D] = None  # first-click drift anchor
  __press_clock__: Optional[QElapsedTimer] = None  # times the live press
  __hold_timer__: Optional[QTimer] = None
  __hold_max_timer__: Optional[QTimer] = None
  __sequential_timer__: Optional[QTimer] = None
  __click_sequence__: Optional[tuple[MouseButtonNum, ...]] = None
  __click_phase__ = ClickPhase.IDLE

  #  Public Variables
  movePoint: Field[Point2D] = Field()
  holdTimer: Field[QTimer] = Field()
  holdMaxTimer: Field[QTimer] = Field()
  sequentialTimer: Field[QTimer] = Field()
  clickSequence: Field[ClickSequence] = Field()
  hasClicks: Field[bool] = Field()

  #  Virtual Variables
  moving: Field[bool] = Field()
  phase: Field[ClickPhase] = Field()
  singleClickDict: Field[ClickDict] = Field()
  singleHoldDict: Field[ClickDict] = Field()
  doubleClickDict: Field[ClickDict] = Field()
  doubleHoldDict: Field[ClickDict] = Field()
  tripleClickDict: Field[ClickDict] = Field()
  tripleHoldDict: Field[ClickDict] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  multiClick = Signal(tuple)
  multiHold = Signal(tuple)

  leftClick = Signal()
  rightClick = Signal()
  middleClick = Signal()
  forwardClick = Signal()
  backClick = Signal()

  leftHold = Signal()
  rightHold = Signal()
  middleHold = Signal()
  forwardHold = Signal()
  backHold = Signal()

  leftDoubleClick = Signal()
  rightDoubleClick = Signal()
  middleDoubleClick = Signal()
  forwardDoubleClick = Signal()
  backDoubleClick = Signal()

  leftDoubleHold = Signal()
  rightDoubleHold = Signal()
  middleDoubleHold = Signal()
  forwardDoubleHold = Signal()
  backDoubleHold = Signal()

  leftTripleClick = Signal()
  rightTripleClick = Signal()
  middleTripleClick = Signal()
  forwardTripleClick = Signal()
  backTripleClick = Signal()

  leftTripleHold = Signal()
  rightTripleHold = Signal()
  middleTripleHold = Signal()
  forwardTripleHold = Signal()
  backTripleHold = Signal()

  #  Private feedback: the hold band was entered while still holding. It is
  #  exposed for subclasses that want to animate the armed hold; the public
  #  '*Hold' dispatch only happens on release.
  _holdArmed = Signal(tuple)

  #  Rejection signals (payload: the partial sequence), one per reason so a
  #  subclass can animate or sound each rejection distinctly.
  pressRejected = Signal(tuple)  # dead zone 1: too slow to click
  holdTooLong = Signal(tuple)  # dead zone 2: held past holdMax
  moveRegret = Signal(tuple)  # drifted away while a button was down
  buttonMismatch = Signal(tuple)  # a different button interrupted the run

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @movePoint.GET
  def _getMovePoint(self, ) -> Point2D:
    if self.__move_point__ is None:
      raise MissingVariable(self, '__move_point__', Point2D)
    if isinstance(self.__move_point__, Point2D):
      return self.__move_point__
    name, value = '__move_point__', self.__move_point__
    raise TypeException(name, value, Point2D)

  @moving.GET
  def _getMoving(self, ) -> bool:
    return False if self.__move_point__ is None else True

  @phase.GET
  def _getPhase(self, ) -> ClickPhase:
    return self.__click_phase__

  def _pressClock(self, ) -> QElapsedTimer:
    """The elapsed-time clock timing the live press. Started on every
    press, read on release to place the press in a duration band."""
    if self.__press_clock__ is None:
      self.__press_clock__ = QElapsedTimer()
    return self.__press_clock__

  def _createHoldTimer(self) -> None:
    holdTimer: QTimer = QTimer(self, )
    QTimer.setSingleShot(holdTimer, True)
    QTimer.setInterval(holdTimer, self.__hold_time_limit__)
    QTimer.timeout.__get__(holdTimer, QTimer).connect(self._onHoldArmed)
    self.__hold_timer__ = holdTimer

  def _createHoldMaxTimer(self) -> None:
    holdMaxTimer: QTimer = QTimer(self, )
    QTimer.setSingleShot(holdMaxTimer, True)
    QTimer.setInterval(holdMaxTimer, self.__hold_max_limit__)
    QTimer.timeout.__get__(holdMaxTimer, QTimer).connect(self._onHoldTooLong)
    self.__hold_max_timer__ = holdMaxTimer

  def _createSequentialTimer(self) -> None:
    sequentialTimer: QTimer = QTimer(self, )
    QTimer.setSingleShot(sequentialTimer, True)
    QTimer.setInterval(sequentialTimer, self.__sequential_time_limit__)
    QTimer.timeout.__get__(sequentialTimer, QTimer).connect(
        self._onSequentialExpired)
    self.__sequential_timer__ = sequentialTimer

  @holdTimer.GET
  def _getHoldTimer(self, **kwargs) -> QTimer:
    if self.__hold_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createHoldTimer()
      return self._getHoldTimer(_recursion=True)
    if isinstance(self.__hold_timer__, QTimer):
      return self.__hold_timer__
    name, value = '__hold_timer__', self.__hold_timer__
    raise TypeException(name, value, QTimer)

  @holdMaxTimer.GET
  def _getHoldMaxTimer(self, **kwargs) -> QTimer:
    if self.__hold_max_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createHoldMaxTimer()
      return self._getHoldMaxTimer(_recursion=True)
    if isinstance(self.__hold_max_timer__, QTimer):
      return self.__hold_max_timer__
    name, value = '__hold_max_timer__', self.__hold_max_timer__
    raise TypeException(name, value, QTimer)

  @sequentialTimer.GET
  def _getSequentialTimer(self, **kwargs) -> QTimer:
    if self.__sequential_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createSequentialTimer()
      return self._getSequentialTimer(_recursion=True)
    if isinstance(self.__sequential_timer__, QTimer):
      return self.__sequential_timer__
    name, value = '__sequential_timer__', self.__sequential_timer__
    raise TypeException(name, value, QTimer)

  @clickSequence.GET
  def _getClickSequence(self, ) -> ClickSequence:
    return maybe(self.__click_sequence__, ())

  @hasClicks.GET
  def _getHasClicks(self, ) -> bool:
    return True if self.clickSequence else False

  @singleClickDict.GET
  def _getSingleClickDict(self, ) -> ClickDict:
    return {
      MouseButtonNum.LEFT   : self.leftClick,
      MouseButtonNum.RIGHT  : self.rightClick,
      MouseButtonNum.MIDDLE : self.middleClick,
      MouseButtonNum.FORWARD: self.forwardClick,
      MouseButtonNum.BACK   : self.backClick,
    }

  @singleHoldDict.GET
  def _getSingleHoldDict(self, ) -> ClickDict:
    return {
      MouseButtonNum.LEFT   : self.leftHold,
      MouseButtonNum.RIGHT  : self.rightHold,
      MouseButtonNum.MIDDLE : self.middleHold,
      MouseButtonNum.FORWARD: self.forwardHold,
      MouseButtonNum.BACK   : self.backHold,
    }

  @doubleClickDict.GET
  def _getDoubleClickDict(self, ) -> ClickDict:
    return {
      MouseButtonNum.LEFT   : self.leftDoubleClick,
      MouseButtonNum.RIGHT  : self.rightDoubleClick,
      MouseButtonNum.MIDDLE : self.middleDoubleClick,
      MouseButtonNum.FORWARD: self.forwardDoubleClick,
      MouseButtonNum.BACK   : self.backDoubleClick,
    }

  @doubleHoldDict.GET
  def _getDoubleHoldDict(self, ) -> ClickDict:
    return {
      MouseButtonNum.LEFT   : self.leftDoubleHold,
      MouseButtonNum.RIGHT  : self.rightDoubleHold,
      MouseButtonNum.MIDDLE : self.middleDoubleHold,
      MouseButtonNum.FORWARD: self.forwardDoubleHold,
      MouseButtonNum.BACK   : self.backDoubleHold,
    }

  @tripleClickDict.GET
  def _getTripleClickDict(self, ) -> ClickDict:
    return {
      MouseButtonNum.LEFT   : self.leftTripleClick,
      MouseButtonNum.RIGHT  : self.rightTripleClick,
      MouseButtonNum.MIDDLE : self.middleTripleClick,
      MouseButtonNum.FORWARD: self.forwardTripleClick,
      MouseButtonNum.BACK   : self.backTripleClick,
    }

  @tripleHoldDict.GET
  def _getTripleHoldDict(self, ) -> ClickDict:
    return {
      MouseButtonNum.LEFT   : self.leftTripleHold,
      MouseButtonNum.RIGHT  : self.rightTripleHold,
      MouseButtonNum.MIDDLE : self.middleTripleHold,
      MouseButtonNum.FORWARD: self.forwardTripleHold,
      MouseButtonNum.BACK   : self.backTripleHold,
    }

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  STATE MACHINE   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _registerClick(self, button: MouseButtonNum) -> None:
    """Append 'button' to the sequence, or reject the run with
    'buttonMismatch' when a different button interrupts it. Sole guardian
    of the one-button-per-sequence invariant, so everything downstream may
    assume a single repeated button."""
    if not button:
      raise ValueError('Cannot register click of no button!')
    existing = self.clickSequence
    if existing and existing[0] != button:
      return self._reject(self.buttonMismatch)  # different button abandons
    self.__click_sequence__ = (*existing, button)
    return None

  def _reset(self, ) -> None:
    """Return the recogniser to 'IDLE': drop the sequence and the anchor,
    stop every timer."""
    self.__click_sequence__ = None
    self.__move_point__ = None
    self.__click_phase__ = ClickPhase.IDLE
    self._stopTimers()

  def _stopTimers(self, ) -> None:
    """Stop the hold, hold-max and sequential timers."""
    QTimer.stop(self.holdTimer)
    QTimer.stop(self.holdMaxTimer)
    QTimer.stop(self.sequentialTimer)

  def _reject(self, signal: SignalInstance) -> None:
    """Emit rejection 'signal' with the partial sequence, then reset."""
    signal.emit(self.clickSequence)
    return self._reset()

  def _emitClicks(self, ) -> None:
    """Dispatch the collected Click Sequence through 'multiClick' and, for
    a run of one, two or three, the matching per-button tier signal. Then
    reset. The run is a single repeated button by the '_registerClick'
    invariant."""
    if not self.hasClicks:
      raise NotImplementedError
    self.multiClick.emit(self.clickSequence)
    clickDict = {
      1: self.singleClickDict,
      2: self.doubleClickDict,
      3: self.tripleClickDict,
    }.get(len(self.clickSequence))
    if clickDict is not None:
      clickDict[self.clickSequence[0]].emit()
    return self._reset()

  def _emitHolds(self, ) -> None:
    """Dispatch the collected Hold Sequence through 'multiHold' and the
    matching per-button tier signal, then reset."""
    if not self.hasClicks:
      raise NotImplementedError
    self.multiHold.emit(self.clickSequence)
    holdDict = {
      1: self.singleHoldDict,
      2: self.doubleHoldDict,
      3: self.tripleHoldDict,
    }.get(len(self.clickSequence))
    if holdDict is not None:
      holdDict[self.clickSequence[0]].emit()
    return self._reset()

  def _onHoldArmed(self, ) -> None:
    """The hold timer reached 'holdLimit' while the button is still down:
    the press has entered the hold band. Fire the private '_holdArmed' for
    animation; the public dispatch waits for the release."""
    self._holdArmed.emit(self.clickSequence)

  def _onHoldTooLong(self, ) -> None:
    """The button has been held past 'holdMax' without releasing: reject
    the run as dead zone 2."""
    self._reject(self.holdTooLong)

  def _onSequentialExpired(self, ) -> None:
    """No further click arrived within the wait window: dispatch the
    collected Click Sequence."""
    self._emitClicks()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def event(self, e: QEvent) -> bool:
    #  Qt delivers the second press of a double click as a
    #  'MouseButtonDblClick' event; feed it to 'mousePressEvent' as an
    #  ordinary press so the recogniser sees every press uniformly.
    if e.type() == QEvent.Type.MouseButtonDblClick:
      self.mousePressEvent(e)
      return True
    return super().event(e)

  def mousePressEvent(self, e: QMouseEvent) -> None:
    super().mousePressEvent(e)
    if (not self.hovered) or self.__invalid_state__:
      return None
    QTimer.stop(self.sequentialTimer)  # a new press ends the wait
    fresh = not self.hasClicks
    self._registerClick(MouseButtonNum.fromEvent(e))
    if not self.hasClicks:  # rejected (different button): already reset
      return None
    if fresh:  # first press of the run anchors the drift reference
      self.__move_point__ = Point2D(e.position())
    self._pressClock().start()
    self.__click_phase__ = ClickPhase.PRESSING
    QTimer.start(self.holdTimer)
    return QTimer.start(self.holdMaxTimer)

  def mouseReleaseEvent(self, e: QMouseEvent) -> None:
    super().mouseReleaseEvent(e)
    if (not self.hovered) or self.__invalid_state__:
      return None
    if self.phase is not ClickPhase.PRESSING:
      return None  # spurious release with no press in flight
    elapsed = self._pressClock().elapsed()
    QTimer.stop(self.holdTimer)
    QTimer.stop(self.holdMaxTimer)
    if elapsed < self.__press_time_limit__:  # a click: await the next
      self.__click_phase__ = ClickPhase.WAITING
      return QTimer.start(self.sequentialTimer)
    if elapsed < self.__hold_time_limit__:  # dead zone 1
      return self._reject(self.pressRejected)
    if elapsed < self.__hold_max_limit__:  # a hold
      return self._emitHolds()
    return self._reject(self.holdTooLong)  # dead zone 2 (edge)

  def mouseMoveEvent(self, e: QMouseEvent) -> None:
    super().mouseMoveEvent(e)
    if not self.moving:
      return None
    drift = Vector2D(self.movePoint, self.assignedRectPosition)
    if self.phase is ClickPhase.PRESSING:  # regret cancels a held button
      if drift.magSqr > self.__press_move_limit__:
        return self._reject(self.moveRegret)
      return None
    if self.phase is ClickPhase.WAITING:  # completing the click sequence
      if drift.magSqr > self.__sequential_move_limit__:
        return self._emitClicks()
    return None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _invalidateState(self, ) -> None:
    if self.__invalid_state__:
      self.__invalid_state__ = False

  def _validateState(self, ) -> None:
    if not self.__invalid_state__:
      self.__invalid_state__ = True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    super().initUI()
    self.enter.connect(self._invalidateState)
    self.leave.connect(self._validateState)
