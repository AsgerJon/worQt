"""
AbstractPaintMeLike provides a base class for widget paint operations.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPaintEvent, QPainter
from PySide6.QtWidgets import QWidget
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Type, Any, Optional, Callable

  WidgetClass: TypeAlias = Type[QWidget]
  WidgetObject: TypeAlias = Optional[QWidget]
  PaintOp: TypeAlias = Callable[[QPainter, QPaintEvent], QPaintEvent]


class AbstractPaintMeLike(BaseObject):
  """
  AbstractPaintMeLike provides a base class for widget paint operations.
  It defines the interface for painting widgets with custom styles.
  """

  def __get__(self, instance: WidgetObject, owner: WidgetClass, ) -> Any:
    """
    Returns a bound method for the widget instance created by the
    'paintMeLike' factory implementation.
    """
    if instance is None:
      return self
    return self.paintMeLike(instance)

  def paintMeLike(self, widget: WidgetObject) -> PaintOp:
    """
    Factory creating the paint operation for the widget. Subclasses
    should implement this method to return a callable paint operation.
    """
   