"""
PaintLabel subclasses 'AbstractPaintOp' and provides a text printing
operation.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from types import FunctionType
from typing import TYPE_CHECKING

from PySide6.QtGui import QPainter, QPaintEvent, QFontMetrics
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.waitaminute import TypeException, VariableNotNone

from ..utils import WFont, WPainter, Color
from ..utils.geom import Rect
from . import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Optional, Callable
  from abc import ABC

  from ..widgets import LabelWidget

  MaybeFont: TypeAlias = Optional[QFont]
  WFontBox: TypeAlias = Union[WFont, AttriBox]
  Painter: TypeAlias = Union[QPainter, WPainter]
  TextGetter: TypeAlias = Callable[[QWidget], str]
  MaybeStr: TypeAlias = Optional[str]
  MetricsField: TypeAlias = Union[QFontMetrics, Field]
  ColorBox: TypeAlias = Union[AttriBox, Color]
else:
  abstractmethod, ABC = lambda func: func, object


class PaintLabel(AbstractPaintOp, ABC):  # ABC type-checking only
  """
  PaintLabel subclasses 'AbstractPaintOp' and provides a text printing
  operation.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: LabelWidget

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __old_font__: MaybeFont = None
  __text_key__: MaybeStr = None

  #  Public Variables

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def prepare(self, painter: Painter, ) -> Painter:
    __old_font__ = painter.font()
    self.__paint_device__ = painter.device()
    self.__device_type__ = type(self.__paint_device__)
    return painter

  def reset(self, painter: Painter) -> Painter:
    if isinstance(self.__old_font__, QFont):
      painter.setFont(self.__old_font__)
    elif self.__old_font__ is None:
      painter.setFont(QFont())
    else:
      raise TypeException('__old_font__', self.__old_font__, QFont, WFont)
    painter.__paint_device__ = None
    painter.__device_type__ = None
    return painter

  def paint(self, painter: Painter, rect: Rect, event: QPaintEvent) -> Rect:
    if not isinstance(painter, QPainter):
      raise TypeException('painter', painter, QPainter, WPainter)
    if not isinstance(rect, Rect):
      raise TypeException('rect', rect, Rect)
    if not isinstance(event, QPaintEvent):
      raise TypeException('event', event, QPaintEvent)
    painter.setPen(self.widget.emptyPen)
    # painter.setBrush(self.widget.paddingsColor.fillBrush)
    # painter.drawRoundedRect(rect.Q, self.widget.xr, self.widget.yr)
    # painter.setBrush(self.widget.emptyBrush)
    painter.setFont(self.widget.font)
    painter.printLabel(self._getDeviceText(), rect)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def TEXT(self, textGetter: TextGetter, ) -> TextGetter:
    """
    This method provides a decorator indicating the source of the text to
    be printed.

    Parameters
    ----------
    textGetter: TextGetter
      The function decorated by this method should return the text to be
      printed. It should be a bound method of the owning widget class. No
      arguments will be passed to it and is assumed to be a bound instance
      method. The name of the method is registered rather than the method
      object itself. During painting, the method is retrieved from the
      class passed to the '__get__' method. This allows seamless
      transition between subclasses.
    """
    if self.__text_key__ is not None:
      raise VariableNotNone('__text_key__', self.__text_key__)
    if not callable(textGetter):
      raise TypeException('textGetter', textGetter, FunctionType)
    self.__text_key__ = textGetter.__name__
    return textGetter

  def _getDeviceText(self, ) -> str:
    """
    This method retrieves the text to be printed from the owning widget.
    """
    textGetter = getattr(self.device, self.__text_key__)
    return textGetter()
