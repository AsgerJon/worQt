"""
ClickButton subclasses 'PaintButton' and implements button functionality
and logic.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Signal, SignalInstance
from PySide6.QtGui import QMouseEvent
from icecream import ic
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException, MissingVariable

from ..utils import MouseButtonNum
from ..utils.geom import Point2D, Vector2D
from . import PaintButton

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union, Mapping

  MaybeBool: TypeAlias = Optional[bool]
  MaybePoint2D: TypeAlias = Optional[Point2D]
  Point2DField: TypeAlias = Union[Point2D, Field]
  MaybeTimer: TypeAlias = Optional[QTimer]
  TimerField: TypeAlias = Union[QTimer, Field]
  BoolField: TypeAlias = Union[bool, Field]

  ClickSequence: TypeAlias = tuple[MouseButtonNum, ...]
  ClickSequenceField: TypeAlias = Union[ClickSequence, Field]
  MaybeClickSequence: TypeAlias = Optional[ClickSequence]

  __cpp_wyd__: TypeAlias = Union[Signal, SignalInstance]
  ClickDict: TypeAlias = Mapping[MouseButtonNum, __cpp_wyd__]
  ClickDictField: TypeAlias = Union[ClickDict, Field]


class ClickButton(PaintButton):
  """
  ClickButton subclasses 'PaintButton' and implements button functionality
  and logic.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  # --- Time limits
  __press_time_limit__: int = 250  # Milliseconds
  __hold_time_limit__: int = 750  # Milliseconds
  __sequential_time_limit__: int = 400  # Milliseconds
  # --- Move limits
  __press_move_limit__: int = 3 ** 2  # Move limit (squared)
  __hold_move_limit__: int = 3 ** 2  # Move limit (squared)
  __sequential_move_limit__: int = 3 ** 2  # Move limit (squared)

  #  Private Variables
  __invalid_state__: MaybeBool = None
  __move_point__: MaybePoint2D = None
  __press_timer__: MaybeTimer = None
  __hold_timer__: MaybeTimer = None
  __sequential_timer__: MaybeTimer = None
  __click_sequence__: MaybeClickSequence = None

  #  Public Variables
  movePoint: Point2DField = Field()
  pressTimer: TimerField = Field()
  holdTimer: TimerField = Field()
  sequentialTimer: TimerField = Field()
  clickSequence: ClickSequenceField = Field()
  hasClicks: BoolField = Field()

  #  Virtual Variables
  moving: BoolField = Field()
  singleClickDict: ClickDictField = Field()
  singleHoldDict: ClickDictField = Field()
  doubleClickDict: ClickDictField = Field()
  doubleHoldDict: ClickDictField = Field()

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

  def _createPressTimer(self) -> None:
    self.__press_timer__ = QTimer(self, )
    QTimer.setSingleShot(self.__press_timer__, True)
    self.__press_timer__.setInterval(self.__press_time_limit__)
    self.__press_timer__.timeout.connect(self._onPressExpired)

  def _createHoldTimer(self) -> None:
    self.__hold_timer__ = QTimer(self, )
    QTimer.setSingleShot(self.__hold_timer__, True)
    self.__hold_timer__.setInterval(self.__hold_time_limit__)
    self.__hold_timer__.timeout.connect(self._onHoldExpired)

  def _createSequentialTimer(self) -> None:
    self.__sequential_timer__ = QTimer(self, )
    QTimer.setSingleShot(self.__sequential_timer__, True)
    self.__sequential_timer__.setInterval(self.__sequential_time_limit__)
    self.__sequential_timer__.timeout.connect(self._onSequentialExpired)

  @pressTimer.GET
  def _getPressTimer(self, **kwargs) -> QTimer:
    if self.__press_timer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPressTimer()
      return self._getPressTimer(_recursion=True)
    if isinstance(self.__press_timer__, QTimer):
      return self.__press_timer__
    name, value = '__press_timer__', self.__press_timer__
    raise TypeException(name, value, QTimer)

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _registerClick(self, button: MouseButtonNum) -> None:
    """
    This method registers a click of the given button. This is done by
    appending the button to the 'clickSequence' and starting the
    'sequentialTimer' to wait for a potential next click in the sequence.
    """
    if not button:
      raise ValueError('Cannot register click of no button!')
    existing = self._getClickSequence()
    for existingButton in existing:
      return self._invalidateClicks()
    self.__click_sequence__ = (*existing, button)
    return None

  def _clearClickSequence(self, ) -> None:
    """
    This method clears the stored click sequence. This is done by setting
    the 'clickSequence' to an empty tuple and stopping the 'sequentialTimer'.
    """
    self.__click_sequence__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _onPressExpired(self, ) -> None:
    """
    The press time limit ensures that no click occurs if the user holds
    the button for too long. The state of the press timer indicates
    whether a normal click is in progress. Upon timeout, the user may be
    attempting to issue a 'press-hold' action. Thus, this method connected
    to the 'timeout' signal of the 'pressTimer', does not actually do
    anything in this base implementation.
    """

  def _onPressMoved(self, ) -> None:
    """
    This method is called when the user moves the mouse while still
    holding down the mouse button. This allows the user to cancel a click
    before releasing the mouse button, if the initial press was in error.
    Thus, this method invokes the '_invalidateClicks' method.
    """
    self._invalidateClicks()

  def _onHoldExpired(self, ) -> None:
    """
    This method is called when the user has held the mouse button long
    enough to have indicated for the press-hold action.
    """
    self._emitHolds()

  def _onHoldMoved(self, ) -> None:
    """
    This method is called when the user moves the mouse while still
    holding the button. This cancels the ongoing user input.
    """
    self._invalidateClicks()

  def _onSequentialExpired(self, ) -> None:
    """
    This method is called when the time limit for waiting for the next
    click in a sequential click like doubleclick expires. This means that
    this emits the stored clicks.
    """
    self._emitClicks()

  def _onSequentialMoved(self, ) -> None:
    """
    If while waiting for a potential next click in a sequence, the user
    moves the mouse, this is understood as the user having now issued the
    desired sequence of clicks. Thus, this method emits the stored clicks
    as a sequence, *without* the user having to wait for the sequence
    timer to expire.
    """
    self._emitClicks()

  def _invalidateClicks(self, ) -> None:
    """
    This method stops all timers and removes all ongoing click actions.
    """
    self._clearClickSequence()
    self._stopTimers()
    self.__move_point__ = None

  def _emitClicks(self, ) -> None:
    """
    This method emits the stored sequence of clicks. These may be single,
    double or any number of clicks. Further, these need not be the same
    button (defined by the 'MouseButtonNum') but must *not* be 'no button'.
    """
    if not self.hasClicks:
      raise NotImplementedError
    self.multiClick.emit(self.clickSequence)
    if len(self.clickSequence) > 2:
      return self._invalidateClicks()
    firstButton, lastButton = self.clickSequence[0], self.clickSequence[-1]
    if firstButton != lastButton:
      return self._invalidateClicks()
    if len(self.clickSequence) == 2:
      clickDict = self.doubleClickDict
    else:
      clickDict = self.singleClickDict
    clickDict[firstButton].emit()
    return self._invalidateClicks()

  def _emitHolds(self, ) -> None:
    """
    This method does the same as '_emitClicks' but for hold actions.
    """
    if not self.hasClicks:
      raise NotImplementedError
    self.multiHold.emit(self.clickSequence)
    if len(self.clickSequence) > 2:
      return self._invalidateClicks()
    firstButton, lastButton = self.clickSequence[0], self.clickSequence[-1]
    if firstButton != lastButton:
      return self._invalidateClicks()
    if len(self.clickSequence) == 2:
      holdDict = self.doubleHoldDict
    else:
      holdDict = self.singleHoldDict
    holdDict[firstButton].emit()
    return self._invalidateClicks()

  def _stopTimers(self, ) -> None:
    """
    This method stops all timers.
    """
    QTimer.stop(self.pressTimer)
    QTimer.stop(self.holdTimer)
    QTimer.stop(self.sequentialTimer)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def mouseMoveEvent(self, e: QMouseEvent) -> None:
    super().mouseMoveEvent(e)
    if self.moving:
      move = Vector2D(self.movePoint, self.contentRectPosition)
      if QTimer.isActive(self.pressTimer):
        if move.magSqr > self.__press_move_limit__:
          return self._onPressMoved()
      if QTimer.isActive(self.holdTimer):
        if move.magSqr > self.__hold_move_limit__:
          return self._onHoldMoved()
      if QTimer.isActive(self.sequentialTimer):
        if move.magSqr > self.__sequential_move_limit__:
          return self._onSequentialMoved()
    return None

  def mouseDoubleClickEvent(self, e: QMouseEvent, ) -> None:
    super().mouseDoubleClickEvent(e)
    return self.mousePressEvent(e)

  def mousePressEvent(self, e: QMouseEvent) -> None:
    super().mousePressEvent(e)
    if (not self.hovered) or self.__invalid_state__:
      return None
    self._stopTimers()
    button = MouseButtonNum.fromEvent(e)
    self._registerClick(button)
    self.__move_point__ = Point2D(e)
    self.pressTimer.start()
    return self.holdTimer.start()

  def mouseReleaseEvent(self, e: QMouseEvent) -> None:
    super().mouseReleaseEvent(e)
    if (not self.hovered) or self.__invalid_state__:
      return None
    if not self.hasClicks:
      return self._invalidateClicks()
    if not self.pressTimer.isActive():
      return self._invalidateClicks()
    self._stopTimers()
    return self.sequentialTimer.start()

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
