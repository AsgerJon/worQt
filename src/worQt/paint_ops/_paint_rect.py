"""
PaintRect subclasses 'AbstractPaintOp' from 'worQt.paint_ops' and provides
a paint operation filling a 'Rect' object with a given color.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QPaintEvent, QBrush
from icecream import ic
from worktoy.desc import Field

from . import AbstractPaintOp
from ..utils import WPainter
from ..utils.geom import Rect

if TYPE_CHECKING:  # pragma: no cover
  from typing import Union, TypeAlias

  BrushField: TypeAlias = Union[QBrush, Field]


class PaintRect(AbstractPaintOp):
  """
  PaintRect subclasses 'AbstractPaintOp' from 'worQt.paint_ops' and provides
  a paint operation filling a 'Rect' object with a given color.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  fillBrush: BrushField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @fillBrush.GET
  def _getFillBrush(self, ) -> QBrush:
    return self.widget.backgroundColor.fillBrush

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def prepare(self, painter: WPainter) -> WPainter:
    painter.setPen(self.emptyPen)
    painter.setBrush(self.widget.backgroundColor.fillBrush)
    return painter

  def reset(self, painter: WPainter) -> WPainter:
    painter.setPen(self.emptyPen)
    painter.setBrush(self.emptyBrush)
    return painter

  def paint(self, painter: WPainter, rect: Rect, event: QPaintEvent) -> Rect:
    """
    This method paints the 'rect' with the color of the widget, returning the
    'rect' aligned according to the alignments of the widget.
    """
    painter.drawRoundedRect(rect.Q, self.widget.xr, self.widget.yr)
    return rect
