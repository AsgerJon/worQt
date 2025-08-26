"""
CursorEvent subclasses 'AbstractEvent' and encapsulates the cursor event
in the custom event system. Instances respect the 'getMouseArea' method
of the owning widget.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtGui import QPointerEvent, QEventPoint
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import VariableNotNone, TypeException

from . import AbstractEvent
from ..geometry import Point2D, Vector2D, Rect
from ..nums import KeyMod

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class CursorEvent(AbstractEvent):
  """
  CursorEvent subclasses 'AbstractEvent' and encapsulates the cursor event
  in the custom event system. Instances respect the 'getMouseArea' method
  of the owning widget.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_point__ = Point2D(-1, -1)
  __fallback_velocity__ = Vector2D(0, 0)
  __fallback_state__ = QEventPoint.State.Unknown

  #  Private Variables
  __cursor_point__ = None
  __cursor_velocity__ = None
  __cursor_state__ = None
  __mouse_area__ = None
  __widget_area__ = None

  #  Public Variables
  point = Field()
  velocity = Field()
  state = Field()
  mouseArea = Field()
  widgetArea = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @point.GET
  def _getPoint(self) -> Point2D:
    if self.__cursor_point__ is None:
      return self.__fallback_point__
    x = self.point.x - self.mouseArea.x
    y = self.point.y - self.mouseArea.y
    return Point2D(x, y)

  @velocity.GET
  def _getVelocity(self) -> Vector2D:
    return maybe(self.__cursor_velocity__, self.__fallback_velocity__)

  @state.GET
  def _getState(self) -> QEventPoint.State:
    return maybe(self.__cursor_state__, self.__fallback_state__)

  @mouseArea.GET
  def _getMouseArea(self) -> Rect:
    return self.__mouse_area__

  @widgetArea.GET
  def _getWidgetArea(self) -> Rect:
    return self.__widget_area__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mouseArea.SET
  def _setMouseArea(self, area: Rect) -> None:
    if self.__mouse_area__ is not None:
      raise VariableNotNone('__mouse_area__', self.__mouse_area__)
    if not isinstance(area, Rect):
      raise TypeException('__mouse_area__', self.__mouse_area__, Rect)
    self.__mouse_area__ = area

  @widgetArea.SET
  def _setWidgetArea(self, area: Rect) -> None:
    if self.__widget_area__ is not None:
      raise VariableNotNone('__widget_area__', self.__widget_area__)
    if not isinstance(area, Rect):
      raise TypeException('__widget_area__', self.__widget_area__, Rect)
    self.__widget_area__ = area

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def fromQEvent(cls, event_: QEvent) -> Self:
    if not isinstance(event_, QPointerEvent):
      raise NotImplementedError('TODO: expected pointer event')
    eventType = QEvent.type(event_)
    self = cls()
    #  Setting values defined on AbstractEvent
    self.timeStamp = event_.timestamp()
    self.eventType = eventType
    self.keyboardModifiers = KeyMod.fromQ(event_.modifiers())
    #  --- END of AbstractEvent values ---
    eventPoint = QPointerEvent.points(event_)[0]
    self.__cursor_point__ = Point2D(eventPoint.position())
    self.__cursor_velocity__ = Vector2D(eventPoint.velocity())
    self.__cursor_state__ = eventPoint.state()
    return self
