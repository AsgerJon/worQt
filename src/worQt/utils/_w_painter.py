"""
WPainter subclasses 'QPainter' and expands it with a few drawing
operations eliminating boilerplate code. Please note that the constructor
is preserved along with 'begin' and 'end'. Thus, the lifecycle is the same
as that of 'QPainter'.
"""
#  Apache-2.0 license
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
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException
from worktoy.desc import Field

from ..mixin import MixinBase
from .geom import Rect, RoundedRect, Color
from . import WPainterPath

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
    from ._w_font import WFont  # lazy: avoids pulling the font system in
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
    The 'fillBetween' method fills the area between two nested rects with
    'color' - the ring a box model paints for a border or a padding. The
    two may come in either order. Equal rects have nothing between them,
    so nothing is painted; rects with the same edges but different corner
    radii leave the corners between them, which are filled.
    """
    outer, inner = self._nestRects(outer, inner)
    fillPath = self._rectPath(outer).subtracted(self._rectPath(inner))
    self.setBrush(color.fillBrush)
    return self.drawPath(fillPath)

  @staticmethod
  def _cornerRadii(rect: Rect) -> int:
    """
    The '_cornerRadii' method returns how rounded 'rect' is: the sum of its
    corner radii, 0 for a plain 'Rect'.
    """
    if isinstance(rect, RoundedRect):
      return rect.hr + rect.vr
    return 0

  @classmethod
  def _nestRects(cls, first: Rect, second: Rect) -> tuple[Rect, Rect]:
    """
    The '_nestRects' method returns the two rects as '(outer, inner)'. Two
    rects with the same edges each contain the other; then the less rounded
    one, covering more area, is the outer one. Deciding this once, rather
    than swapping and asking again, is what keeps equal rects from
    swapping forever.
    """
    firstHolds = True if second in first else False
    secondHolds = True if first in second else False
    if firstHolds and secondHolds:
      if cls._cornerRadii(first) <= cls._cornerRadii(second):
        return first, second
      return second, first
    if firstHolds:
      return first, second
    if secondHolds:
      return second, first
    infoSpec = """'%s.fillBetween' needs one rect to contain the other, but
    received: '%s' and '%s'!"""
    info = infoSpec % (cls.__name__, str(first), str(second))
    raise ValueError(textFmt(info))

  @staticmethod
  def _rectPath(rect: Rect) -> QPainterPath:
    """
    The '_rectPath' method returns the outline of 'rect' as a path, with
    its corner radii when it is a 'RoundedRect'.
    """
    path = QPainterPath()
    if isinstance(rect, RoundedRect):
      path.addRoundedRect(rect.Q, rect.hr, rect.vr)
    elif isinstance(rect, Rect):
      path.addRoundedRect(rect.Q, 0, 0)
    else:  # pragma: no cover  # 'in' has already refused a non-'Rect'
      raise TypeException('rect', rect, Rect, RoundedRect)
    return path

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
