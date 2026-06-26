"""
PaintButton subclasses 'LabelWidget' and expands the painting of the
label with button related states. It does not implement any button
functionality other than painting.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal, Slot, QTimer
from PySide6.QtGui import QMouseEvent, QEventPoint
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute.control_flow import SkipSet

from . import LabelWidget
from ..utils import ButtonStateFlags, MouseButtonNum
from ..utils.geom import Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union

  MaybeBool: TypeAlias = Optional[bool]
  BoolField: TypeAlias = Union[bool, Field]
  MaybeQEventPoint: TypeAlias = Optional[QEventPoint]
  MaybePoint2D: TypeAlias = Optional[Point2D]
  Point2DField: TypeAlias = Union[Point2D, Field]
  ButtonStateField: TypeAlias = Union[ButtonStateFlags, Field]
  MouseButtonField: TypeAlias = Union[MouseButtonNum, Field]
  MaybeMouseButton: TypeAlias = Optional[MouseButtonNum]
  MaybeTimer: TypeAlias = Optional[QTimer]
  TimerField: TypeAlias = Union[QTimer, Field]


class PaintButton(LabelWidget):
  """
  PaintButton subclasses 'LabelWidget' and expands the painting of the
  label with button related states. It does not implement any button
  functionality other than painting.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_hovered__ = False
  __fallback_pressed__ = False
  __fallback_disabled__ = False

  #  Private Variables
  __mouse_hovered__: MaybeBool = None
  __mouse_pressed__: MaybeBool = None
  __mouse_disabled__: MaybeBool = None
  __event_point__: MaybeQEventPoint = None

  #  Public Variables
  hovered: BoolField = Field()
  pressed: BoolField = Field()
  button: MouseButtonField = Field()
  disabled: BoolField = Field()
  state: ButtonStateField = Field()

  #  Virtual Variables
  cursorPosition: Point2DField = Field()
  assignedRectPosition: Point2DField = Field()
  contentRectPosition: Point2DField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cursorPosition.GET
  def _getCursorPosition(self, ) -> QEventPoint:
    if self.__event_point__ is None:
      return Point2D(-1, -1)
    qPoint = QEventPoint.position(self.__event_point__)
    return Point2D(qPoint.x(), qPoint.y())

  @assignedRectPosition.GET
  def _getAssignedRectPosition(self, ) -> Point2D:
    """
    Getter-function for the cursor position relative to the assigned
    rectangle.
    """
    if self.__event_point__ is None:
      return Point2D(-1, -1)
    qPoint = QEventPoint.position(self.__event_point__)
    return Point2D(qPoint.x(), qPoint.y())

  @contentRectPosition.GET
  def _getContentRectPosition(self, ) -> Point2D:
    """
    Getter-function for the cursor position relative to the content
    rectangle.
    """
    if self.__event_point__ is None:
      return Point2D(-1, -1)
    paintX = self.assignedRectPosition.x - self.paintView.left
    paintY = self.assignedRectPosition.y - self.paintView.top
    paintPoint = Point2D(paintX, paintY)
    if paintPoint in self.paintView:
      return paintPoint
    return Point2D(-1, -1)

  @hovered.GET
  def _getHovered(self, ) -> bool:
    return maybe(self.__mouse_hovered__, self.__fallback_hovered__)

  @pressed.GET
  def _getPressed(self, ) -> bool:
    return True if self.button else False

  @disabled.GET
  def _getDisabled(self, ) -> bool:
    return maybe(self.__mouse_disabled__, self.__fallback_disabled__)

  @button.GET
  def _getButton(self, ) -> MouseButtonNum:
    if self.hovered:
      return MouseButtonNum.fromApp()
    return MouseButtonNum.NULL

  @state.GET
  def _getState(self, ) -> ButtonStateFlags:
    index = 0
    if self.disabled:
      index += 4
    if self.pressed:
      index += 2
    elif self.hovered:
      index += 1
    return ButtonStateFlags(index)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @disabled.SET
  def _setDisabled(self, disabledFlag: bool) -> None:
    """
    Setter-function for the disabled state of the button.

    Parameters
    ----------
    disabledFlag : bool
      When this value is 'True' the button will be disabled.
    """
    self.__mouse_disabled__ = disabledFlag

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @disabled.preSet
  def _preSetDisabled(self, disabledFlag: bool) -> None:
    if self.__mouse_disabled__ == disabledFlag:
      raise SkipSet

  @disabled.onSet
  def _onSetDisabled(self, disabledFlag: bool) -> None:
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  enter = Signal()
  leave = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SLOTS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Slot()
  def enable(self) -> None:
    if self.__mouse_disabled__:
      self.__mouse_disabled__ = False
      self.update()

  @Slot()
  def disable(self, ) -> None:
    if not self.__mouse_disabled__:
      self.__mouse_disabled__ = True
      self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  hover = Signal(bool)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    super().mouseMoveEvent(event)
    self.__event_point__, *_ = (*QMouseEvent.points(event), None)
    assignedRectPoint = Point2D(QEventPoint.position(self.__event_point__))
    if assignedRectPoint in self.paintView:
      if not self.__mouse_hovered__:
        self.__mouse_hovered__ = True
        self.hover.emit(True)
        self.enter.emit()
        self.update()
    else:
      if self.__mouse_hovered__:
        self.__mouse_hovered__ = False
        self.hover.emit(False)
        self.leave.emit()
        self.update()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    super().mousePressEvent(event)
    self.update()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    super().mouseReleaseEvent(event)
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  'PaintButton' needs no '__init__': the inherited 'LabelWidget'
  #  constructor dispatcher already does everything, including the
  #  finalizer that enables mouse tracking.
