"""
PaintBoxModel subclasses 'AbstractPaintOp' and paints the box model.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPainter, QPaintEvent
from icecream import ic
from worktoy.desc import Field, AttriBox
from worktoy.waitaminute import TypeException

from ..utils.geom import InSets, Color, Rect, Size, RoundedRect, Point2D
from ..utils.qee_num import SizePolicy, ColorNum, SizingMode
from ..waitaminute.events import InvalidSizePolicy
from . import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union
  from ..utils import WPainter

  IntBox: TypeAlias = Union[int, AttriBox]
  Painter: TypeAlias = Union[QPainter, WPainter]
  InSetsField: TypeAlias = Union[InSets, Field]
  WColorField: TypeAlias = Union[Color, Field]
  Keys: TypeAlias = tuple[str, str, str, str, str]
  Rects: TypeAlias = tuple[Rect, Rect, Rect, Rect]


class PaintBoxModel(AbstractPaintOp):
  """
  PaintBoxModel subclasses 'AbstractPaintOp' and paints the box model.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  rx: IntBox = AttriBox[int](8)
  ry: IntBox = AttriBox[int](8)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _paintIntrinsic(self, view: Rect) -> Rects:
    """
    This method paints the box model intrinsically around the required
    size of the widget, returning the 'viewRect' aligned according to the
    alignments of the widget.
    """
    contentRect = self.widget.align.apply(view, self.widget.reqSize)
    paddedRect = contentRect + self.widget.paddingsDims
    borderedRect = paddedRect + self.widget.bordersDims
    marginedRect = borderedRect + self.widget.marginsDims
    return marginedRect, borderedRect, paddedRect, contentRect

  def _paintExtrinsic(self, view: Rect) -> Rects:
    """
    This method paints the box model extrinsically around the 'viewRect',
    returning the 'viewRect' aligned according to the alignments of the
    widget.
    """
    marginedRect: Rect = Rect(view)
    borderedRect: Rect = marginedRect - self.widget.marginsDims
    paddedRect: Rect = borderedRect - self.widget.bordersDims
    availableRect: Rect = paddedRect - self.widget.paddingsDims
    contentSize = self.widget.reqSize
    contentRect = self.widget.align.apply(availableRect, contentSize)
    return marginedRect, borderedRect, paddedRect, contentRect

  def _paintRects(self, view: Rect) -> Rects:
    extrinsicRects = self._paintExtrinsic(view)
    intrinsicRects = self._paintIntrinsic(view)
    rectDict: dict[SizingMode, Rects] = {
      SizingMode.INTRINSIC: intrinsicRects,
      SizingMode.EXTRINSIC: extrinsicRects,
      }
    lefts = (*(r.left for r in rectDict[self.widget.hMode]),)
    tops = (*(r.top for r in rectDict[self.widget.vMode]),)
    rights = (*(r.right for r in rectDict[self.widget.hMode]),)
    bottoms = (*(r.bottom for r in rectDict[self.widget.vMode]),)
    marginedRect = Rect(lefts[0], tops[0], rights[0], bottoms[0])
    borderedRect = Rect(lefts[1], tops[1], rights[1], bottoms[1])
    paddedRect = Rect(lefts[2], tops[2], rights[2], bottoms[2])
    contentRect = Rect(lefts[3], tops[3], rights[3], bottoms[3])
    return marginedRect, borderedRect, paddedRect, contentRect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def prepare(self, painter: Painter) -> Painter:
    self.__paint_device__ = painter.device()
    self.__device_type__ = type(self.__paint_device__)
    return painter

  def reset(self, painter: Painter) -> Painter:
    self.__paint_device__ = None
    self.__device_type__ = None
    return painter

  def paint(self, painter: WPainter, view: Rect, e: QPaintEvent) -> Rect:
    rects: Rects = self._paintRects(view)
    xr, yr = self.widget.xr, self.widget.yr
    roundedRects = (*(RoundedRect(r, xr, yr) for r in rects),)
    marginedRect, borderedRect, paddedRect, contentRect = roundedRects
    painter.setPen(self.emptyPen)
    painter.fillBetween(marginedRect, borderedRect, self.widget.marginsColor)
    painter.fillBetween(borderedRect, paddedRect, self.widget.bordersColor)
    painter.fillBetween(paddedRect, contentRect, self.widget.paddingsColor)
    return contentRect
