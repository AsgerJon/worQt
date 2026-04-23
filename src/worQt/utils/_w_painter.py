"""
WPainter subclasses 'QPainter' and expands it with a few drawing
operations eliminating boilerplate code. Please note that the constructor
is preserved along with 'begin' and 'end'. Thus, the lifecycle is the same
as that of 'QPainter'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRectF, QRect, Qt
from PySide6.QtGui import (QPainter,
  QPainterPath,
  QColor,
  QBrush,
  QFont,
  QTextOption, QPaintDevice)
from icecream import ic
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException
from worktoy.desc import Field

from ..mixin import MixinBase
from .geom import Rect, RoundedRect, Color
from . import WFont, WPainterPath

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union

  from ..widgets import PaintedWidget

  RectLike: TypeAlias = Union[RoundedRect, Rect, QRect, QRectF]
  Path: TypeAlias = Union[WPainterPath, QPainterPath]
  Color: TypeAlias = Union[Color, QColor, QBrush]
  Device: TypeAlias = Union[QPaintDevice, PaintedWidget]
  DeviceField: TypeAlias = Union[Device, Field]


class WPainter(QPainter, MixinBase):
  """
  WPainter subclasses 'QPainter' and expands it with a few drawing
  operations eliminating boilerplate code. Please note that the constructor
  is preserved along with 'begin' and 'end'. Thus, the lifecycle is the same
  as that of 'QPainter'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  paintDevice: DeviceField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @paintDevice.GET
  def _getPaintDevice(self) -> Device:
    """
    Returns the paint device to be used for painting. If the 'paintDevice'
    field is not set, this method will raise a 'ValueError'.
    """
    device = QPainter.device(self, )
    if isinstance(device, QPaintDevice):
      return device
    raise TypeException('device', device, QPaintDevice)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CUSTOM PAINTING OPERATIONS   # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setFont(self, font: WFont, ) -> None:
    """
    Reimplementation taking effect on 'WFont' instances, otherwise falling
    back to 'QFont.setFont'.

    Parameters
    ----------

    font: WFont or QFont
      The font to set. If a 'WFont' instance is passed, this method will
      also set the pen to the one provided by the 'WFont.pen' attribute.
    """
    if isinstance(font, WFont):
      QPainter.setFont(self, font)
      return QPainter.setPen(self, font.pen)
    if isinstance(font, QFont):
      return QPainter.setFont(self, font)
    raise TypeException('font', font, QFont, WFont)

  def fillBetween(
      self,
      outer: RectLike,
      inner: RectLike,
      color: Color,
      ) -> None:
    """
    Fills the area between two rectangles. The inner rectangle is subtracted
    from the outer rectangle, and the resulting area is filled with the
    current brush.
    """
    if outer in inner:
      return self.fillBetween(inner, outer, color)
    if inner not in outer:
      infoSpec = """'%s.fillBetween' requires non-intersecting rectangles, 
      but received: '%s' and '%s'!"""
      info = infoSpec % (type(self).__name__, str(outer), str(inner))
      raise ValueError(textFmt(info))
    innerQRect = inner.Q
    outerQRect = outer.Q
    innerPath = QPainterPath()
    if isinstance(inner, RoundedRect):
      innerPath.addRoundedRect(inner.Q, inner.hr, inner.vr)
    elif isinstance(inner, Rect):
      innerPath.addRoundedRect(inner.Q, 0, 0)
    else:
      raise TypeException('inner', inner, Rect, RoundedRect)
    outerPath = QPainterPath()
    if isinstance(outer, RoundedRect):
      outerPath.addRoundedRect(outer.Q, outer.hr, outer.vr)
    elif isinstance(outer, Rect):
      outerPath.addRoundedRect(outer.Q, 0, 0)
    else:
      raise TypeException('outer', outer, Rect, RoundedRect)
    fillPath = outerPath.subtracted(innerPath)
    self.setBrush(color.fillBrush)
    return self.drawPath(fillPath)

  def fillPath(self, path: Path, color: Color = None) -> None:
    """
    Fills the given path with the given color.
    """
    return QPainter.fillPath(self, path, color)

  def printLabel(self, label: str, rect: Rect) -> Rect:
    """
    Prints the given label within the given rectangle, using the current font
    and pen. The text is aligned according to the alignment of the rectangle.
    """
    if not isinstance(rect, Rect):
      raise TypeException('rect', rect, Rect)
    textOption = QTextOption()
    textOption.setAlignment(self.paintDevice.textAlign.Q)
    textOption.setWrapMode(self.paintDevice.wrapMode)
    qRect = QRect(rect.Q)
    self.drawText(qRect, label, textOption)
    return rect
