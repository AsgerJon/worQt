"""
HitPicker subclasses 'PaintedWidget' and is the cue ball's face as the
cue sees it, the point to strike chosen on it with the mouse.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QSize, Signal
from PySide6.QtGui import QBrush, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import Color
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from .. import Cue

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QMouseEvent, QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect


class PaintHitPicker(AbstractPaintOp):
  """
  PaintHitPicker subclasses 'AbstractPaintOp' and paints a 'HitPicker':
  the cue ball's face, lit from above; a dashed ring where a tip would
  miscue; a faint mark where it rolls at once; and the point chosen, a
  chalk blue spot.
  """

  #  Annotations
  widget: HitPicker

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the face and the point."""
    widget = self.widget
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    centre, radius = widget.faceCentre(), widget.faceRadius()
    light = QPointF(centre.x() - 0.35 * radius, centre.y() - 0.4 * radius)
    shade = QRadialGradient(light, 1.5 * radius)
    shade.setColorAt(0.0, widget.ballColor.Q.lighter(115))
    shade.setColorAt(1.0, widget.ballColor.Q.darker(160))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(shade))
    painter.drawEllipse(centre, radius, radius)
    ring = QPen(widget.ringColor.Q, 1.0, Qt.PenStyle.DashLine)
    painter.setPen(ring)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    limit = Cue().limit * radius
    painter.drawEllipse(centre, limit, limit)
    painter.drawLine(QPointF(centre.x() - radius, centre.y()),
                     QPointF(centre.x() + radius, centre.y()))
    painter.drawLine(QPointF(centre.x(), centre.y() - radius),
                     QPointF(centre.x(), centre.y() + radius))
    roll = widget.pointOf(Cue().rollHeight(), 0.0)
    painter.setPen(QPen(widget.ringColor.Q, 1.5))
    painter.drawEllipse(roll, 3.0, 3.0)
    spot = widget.pointOf(widget.top, widget.side)
    painter.setPen(QPen(widget.spotEdgeColor.Q, 1.5))
    painter.setBrush(QBrush(widget.spotColor.Q))
    size = 0.09 * radius
    painter.drawEllipse(spot, size, size)
    return rect


class HitPicker(PaintedWidget):
  """
  HitPicker subclasses 'PaintedWidget' and is the cue ball's face as the
  cue sees it, the shooter's right to the right: a click or a drag
  chooses the point to strike, 'top' up from the middle and 'side' to the
  right, each a share of the radius, kept where the cue would not
  miscue; 'hitChanged' tells of each change, top first. 'centre' takes
  the middle again. The face is painted 'ballColor'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_ring_color__ = Color(120, 110, 95)
  __fallback_spot_color__ = Color(47, 111, 208)
  __fallback_spot_edge_color__ = Color(20, 40, 80)
  __fallback_ball_color__ = Color(242, 236, 217)
  __fallback_size__ = 180  # pixels across

  #  Private Variables
  __hit_top__: float = 0.0
  __hit_side__: float = 0.0
  __hit_color__: Color | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  pickerOp = PaintHitPicker()

  #  Virtual Variables
  top: Field[float] = Field()
  side: Field[float] = Field()
  ballColor: Field[Color] = Field()
  ringColor: Field[Color] = Field()
  spotColor: Field[Color] = Field()
  spotEdgeColor: Field[Color] = Field()

  #  Signals
  hitChanged = Signal(float, float)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @top.GET
  def _getTop(self, ) -> float:
    """The 'top' getter returns how far up from the middle the point
    is, a share of the radius."""
    return self.__hit_top__

  @side.GET
  def _getSide(self, ) -> float:
    """The 'side' getter returns how far right of the middle the point
    is, a share of the radius."""
    return self.__hit_side__

  @ballColor.GET
  def _getBallColor(self, ) -> Color:
    """The 'ballColor' getter returns the face's colour."""
    if self.__hit_color__ is None:
      return self.__fallback_ball_color__
    return self.__hit_color__

  @ringColor.GET
  def _getRingColor(self, ) -> Color:
    return self.__fallback_ring_color__

  @spotColor.GET
  def _getSpotColor(self, ) -> Color:
    return self.__fallback_spot_color__

  @spotEdgeColor.GET
  def _getSpotEdgeColor(self, ) -> Color:
    return self.__fallback_spot_edge_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @ballColor.SET
  def _setBallColor(self, color: Color) -> None:
    """The 'ballColor' setter paints the face 'color'."""
    self.__hit_color__ = color
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    size = self.__fallback_size__
    return QSize(size, size)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(120, 120)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A press chooses the point under it."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    self.choose(event.position())

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """A drag moves the point along."""
    if not event.buttons() & Qt.MouseButton.LeftButton:
      return PaintedWidget.mouseMoveEvent(self, event)
    self.choose(event.position())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def faceCentre(self, ) -> QPointF:
    """The 'faceCentre' method returns where the face's middle is."""
    return QPointF(0.5 * self.width(), 0.5 * self.height())

  def faceRadius(self, ) -> float:
    """The 'faceRadius' method returns the face's radius in pixels."""
    return 0.5 * min(self.width(), self.height()) - 6.0

  def pointOf(self, top: float, side: float) -> QPointF:
    """The 'pointOf' method returns where on the widget the point 'top'
    and 'side' is."""
    centre, radius = self.faceCentre(), self.faceRadius()
    return QPointF(centre.x() + side * radius, centre.y() - top * radius)

  def hitAt(self, point: QPointF) -> tuple[float, float]:
    """The 'hitAt' method returns the point to strike, 'top' and
    'side', under 'point' on the widget, kept where the cue would not
    miscue."""
    centre, radius = self.faceCentre(), self.faceRadius()
    side = (point.x() - centre.x()) / radius
    top = (centre.y() - point.y()) / radius
    return Cue().hitOf(top, side)

  def choose(self, point: QPointF) -> None:
    """The 'choose' method chooses the point under 'point'."""
    self.setHit(*self.hitAt(point))

  def setHit(self, top: float, side: float) -> None:
    """The 'setHit' method chooses the point 'top' and 'side', kept
    where the cue would not miscue, and tells of it."""
    top, side = Cue().hitOf(top, side)
    if (top, side) == (self.__hit_top__, self.__hit_side__):
      return
    self.__hit_top__, self.__hit_side__ = top, side
    self.update()
    self.hitChanged.emit(top, side)

  def centre(self, ) -> None:
    """The 'centre' method chooses the middle again."""
    self.setHit(0.0, 0.0)
