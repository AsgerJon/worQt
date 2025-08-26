"""
CursorHover provides a flag descriptor indicating whether the cursor
presently hovers the mouse area of the owning widget. Owning widgets
should have 'mouseTracking' enabled.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QMouseEvent, QPointerEvent
from worktoy.core import Object
from worktoy.mcls import BaseObject
from typing import TYPE_CHECKING

from ...events import CursorMove
from ...geometry import Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Any, Type, TypeAlias

  from .. import BaseWidget as Widget

  WidgetType: TypeAlias = Type[Widget]


class _Hovered(BaseObject):
  """
  _Hovered provides a flag descriptor indicating whether the cursor
  presently hovers the mouse area of the owning widget. Owning widgets
  should have 'mouseTracking' enabled.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __is_hovered__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setIsHovered(self, value: bool) -> None:
    self.__is_hovered__ = True if value else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __bool__(self, ) -> bool:
    return True if self.__is_hovered__ else False


class CursorHover(Object):
  """
  This class provides the descriptor protocol
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: WidgetType, name: str) -> None:
    Object.__set_name__(self, owner, name)
    owner.registerMoveCallback(self._update)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, *args, **kwargs) -> _Hovered:
    pvtName = self.getPrivateName()
    if hasattr(self.instance, pvtName):
      return getattr(self.instance, pvtName)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, pvtName, _Hovered())
    return self.__instance_get__(*args, _recursion=True, **kwargs)

  def _update(self, widget: Widget, event_: QMouseEvent, **kwargs) -> None:
    pvtName = self.getPrivateName()
    try:
      oldValue = getattr(widget, pvtName)
    except AttributeError as attributeError:
      if kwargs.get('_recursion', False):
        raise RecursionError from attributeError
      setattr(widget, pvtName, _Hovered())
      return self._update(widget, event_, _recursion=True)
    else:
      point = Point2D(QPointerEvent.points(event_)[0])
      area = widget.getMouseArea()
      newValue = True if point in area else False
      if newValue == oldValue:
        return
      setattr(widget, pvtName, newValue)
      widget.notifyEnter(event_) if newValue else widget.notifyLeave(event_)
