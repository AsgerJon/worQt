"""
UnfoldedMap subclasses 'PaintedWidget' and is the table unfolded, seen
from above: the table among its mirrored copies, the balls in each, and
the arc of the English across them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy
from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtGui import QBrush, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import Color, WFont
from ....utils.font_nums import FontWeightNum, GenericFamilyNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from .. import Ball, Hit, Run, Unfolded
from .._phrasebook import ENGLISH, Phrasebook

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QMouseEvent, QPaintEvent

  from .. import Crossing, Fan
  from .._unfolded import Way
  from ....utils import WPainter
  from ....utils.geom import Rect

_CENTRE = Qt.AlignmentFlag.AlignCenter
_MARGIN = 14  # pixels round the map
_CAPTION = 22  # pixels the words under the map take
_GLYPH = 8.0  # pixels across a crossing's number, half of it
_STRIDE = 3.0  # pixels at least between the arc's points as drawn


class PaintUnfoldedMap(AbstractPaintOp):
  """
  PaintUnfoldedMap subclasses 'AbstractPaintOp' and paints an
  'UnfoldedMap': the copies of the table, the table itself the
  brightest and rimmed; every cushion's line, its diamonds on it; the
  balls in every copy, mirrored as the copy is, the cue ball on the table
  itself ringed; on a fanned map, the fans of where the balls may go
  after the arc meets a ball, and a ghost of the cue ball there; the
  arc, each cushion it crosses numbered; and a line of words under it.
  """

  #  Annotations
  widget: UnfoldedMap

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the map."""
    widget = self.widget
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.drawPixmap(0, 0, self._backdrop())
    if widget.runs():
      self._paintRuns(painter)
    else:
      self._paintFans(painter)
    self._paintArc(painter)
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    bottom = widget.height() - _CAPTION - 4.0
    painter.drawText(QRectF(0.0, bottom, float(widget.width()),
                            float(_CAPTION)), _CENTRE, widget.caption())
    return rect

  def _backdrop(self, ) -> QPixmap:
    """Returns the copies, the diamonds and the balls painted once, as
    long as neither they nor the widget's size change: aiming paints
    only the arc and the fans over them."""
    widget = self.widget
    ratio = widget.devicePixelRatioF()
    key = (widget.unfolded, widget.width(), widget.height(), ratio,
           widget.balls, widget.cueName)
    kept = widget.__map_backdrop__
    if kept is not None and kept[0] == key:
      return kept[1]
    pixmap = QPixmap(max(int(widget.width() * ratio), 1),
                     max(int(widget.height() * ratio), 1))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try:
      painter.setRenderHint(QPainter.RenderHint.Antialiasing)
      self._paintCopies(painter)
      self._paintDiamonds(painter)
      self._paintBalls(painter)
    finally:
      painter.end()
    widget.__map_backdrop__ = (key, pixmap)
    return pixmap

  def _paintCopies(self, painter: WPainter) -> None:
    """Paints the copies, the table itself brightest and rimmed, and the
    cushions' lines between them."""
    widget = self.widget
    unfolded = widget.unfolded
    painter.setPen(QPen(widget.lineColor.Q, 1.0))
    for i, j in unfolded.copies():
      fill = widget.clothColor if (i, j) == (0, 0) else widget.copyColor
      painter.setBrush(QBrush(fill.Q))
      painter.drawRect(widget.rectOf(*unfolded.corners(i, j)))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(widget.rimColor.Q, 2.0))
    painter.drawRect(widget.rectOf(*unfolded.corners(0, 0)))

  def _paintDiamonds(self, painter: WPainter) -> None:
    """Paints the diamonds on every cushion's line of every copy, as
    round dots."""
    widget = self.widget
    unfolded, table = widget.unfolded, widget.unfolded.table
    reach = unfolded.reach()
    painter.setPen(QPen(widget.diamondColor.Q, 3.2, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap))
    places = [(reach, y) for y in _shares(table.length, 8)]
    places += [(table.width - reach, y) for y in _shares(table.length, 8)]
    places += [(x, reach) for x in _shares(table.width, 4)]
    places += [(x, table.length - reach) for x in _shares(table.width, 4)]
    dots = QPolygonF([widget.pointOf(*unfolded.imageOf(x, y, i, j))
                      for i, j in unfolded.copies() for x, y in places])
    painter.drawPoints(dots)

  def _paintBalls(self, painter: WPainter) -> None:
    """Paints the balls in every copy, mirrored as the copy is, fainter
    in the copies than on the table itself; the cue ball there
    ringed."""
    widget = self.widget
    unfolded = widget.unfolded
    size = max(unfolded.table.radius * widget.scale(), 3.5)
    for ball in widget.balls:
      color = widget.colorOf(ball.name)
      for i, j in unfolded.copies():
        real = (i, j) == (0, 0)
        brush = color.Q
        if not real:
          brush.setAlphaF(0.7)
        painter.setBrush(QBrush(brush))
        ringed = real and ball.name == widget.cueName
        edge = widget.rimColor if ringed else widget.ballEdgeColor
        painter.setPen(QPen(edge.Q, 1.5 if ringed else 0.8))
        place = unfolded.imageOf(ball.x, ball.y, i, j)
        painter.drawEllipse(widget.pointOf(*place), size, size)

  def _paintRuns(self, painter: WPainter) -> None:
    """Paints the shot as the engine played it: on a fanned map, with
    the aim off to either side played too, each ball that moves filled
    faintly from its way off to either side to its way as aimed; the
    other balls' ways as aimed, each in its colour, a ring where it
    stops; and a ghost of the cue ball where it first meets a ball."""
    widget = self.widget
    runs = widget.runs()
    run = runs[0]
    painter.save()
    painter.setClipRect(widget.rectOf(*widget.unfolded.bounds()))
    moved = [name for name, _ in run.ways if run.moved(name)]
    if widget.fanned and len(runs) == 3:
      for name in moved:
        aimed = self._screenOf(run, name)
        fill = widget.colorOf(name).Q
        fill.setAlphaF(widget.__fan_alpha__)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(fill))
        for side in runs[1:]:
          edge = self._screenOf(side, name)
          painter.drawPolygon(_polygonOf(numpy.vstack((edge, aimed[::-1]))),
                              Qt.FillRule.WindingFill)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for name in moved:
      if name == run.cue:
        continue
      aimed = self._screenOf(run, name)
      line = widget.colorOf(name).Q
      line.setAlphaF(0.9)
      painter.setPen(QPen(line, 2.0, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
      painter.drawPolyline(_polygonOf(aimed))
      painter.setBrush(QBrush(widget.paddingsColor.Q))
      painter.drawEllipse(QPointF(*aimed[-1]), 4.0, 4.0)
      painter.setBrush(Qt.BrushStyle.NoBrush)
    hit = widget.hit()
    if hit is not None:
      size = max(widget.unfolded.table.radius * widget.scale(), 3.5)
      ghost = widget.colorOf(widget.cueName).Q
      ghost.setAlphaF(0.35)
      painter.setBrush(QBrush(ghost))
      painter.setPen(QPen(widget.arcColor.Q, 1.0, Qt.PenStyle.DashLine))
      painter.drawEllipse(widget.pointOf(hit.x, hit.y), size, size)
    painter.restore()

  def _screenOf(self, run: Run, name: str) -> numpy.ndarray:
    """Returns the way of the ball 'name' in 'run' on the widget, from
    when it sets off, as '__run_points__' points evenly apart in time:
    a ball met lies on the table itself till then, not in the copy it
    is met in."""
    widget = self.widget
    way = run.wayOf(name)
    first = next((k for k, sample in enumerate(way) if sample[2] > 0.0), 0)
    way = way[first:]
    count = widget.__run_points__
    picks = numpy.linspace(0, len(way) - 1, count).round().astype(int)
    return numpy.array([widget.pointOf(way[k][0], way[k][1]).toTuple()
                        for k in picks])

  def _paintFans(self, painter: WPainter) -> None:
    """Paints, where the arc meets a ball, a ghost of the cue ball, and
    the fans of where the two balls may go: each filled faintly from
    each of its ways one standard deviation off to the way as aimed (a
    cue ball near a half-ball hit, the 30 degree rule at its most, turns
    less either way, so both lie on one side), a way drawn half way
    between, the way as aimed bright."""
    widget = self.widget
    hit, fan = widget.hit(), widget.fan()
    if hit is None or fan is None:
      return
    painter.save()
    painter.setClipRect(widget.rectOf(*widget.unfolded.bounds()))
    for paths, name in ((fan.struck, hit.name), (fan.cue, widget.cueName)):
      one, aimed, other = (numpy.array([widget.pointOf(*place).toTuple()
                                        for place in path])
                           for path in paths)
      color = widget.colorOf(name)
      fill = color.Q
      fill.setAlphaF(widget.__fan_alpha__)
      painter.setPen(Qt.PenStyle.NoPen)
      painter.setBrush(QBrush(fill))
      for edge in (one, other):
        painter.drawPolygon(_polygonOf(numpy.vstack((edge, aimed[::-1]))),
                            Qt.FillRule.WindingFill)
      painter.setBrush(Qt.BrushStyle.NoBrush)
      for edge in (one, other):
        for share in (0.0, 0.5):
          line = color.Q
          line.setAlphaF(0.15 + 0.3 * share)
          painter.setPen(QPen(line, 1.2))
          painter.drawPolyline(_polygonOf(edge + share * (aimed - edge)))
      line = color.Q
      line.setAlphaF(0.9)
      painter.setPen(QPen(line, 1.8, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
      painter.drawPolyline(_polygonOf(aimed))
    painter.restore()
    size = max(widget.unfolded.table.radius * widget.scale(), 3.5)
    ghost = widget.colorOf(widget.cueName).Q
    ghost.setAlphaF(0.35)
    painter.setBrush(QBrush(ghost))
    painter.setPen(QPen(widget.arcColor.Q, 1.0, Qt.PenStyle.DashLine))
    painter.drawEllipse(widget.pointOf(hit.x, hit.y), size, size)

  def _paintArc(self, painter: WPainter) -> None:
    """Paints the arc from the cue ball, and each cushion it crosses
    numbered in order."""
    widget = self.widget
    points = widget.arc()
    if len(points) < 2:
      return
    apart = widget.unfolded.step * widget.scale()
    stride = max(1, int(_STRIDE / max(apart, 1e-9)))
    kept = list(points[::stride])
    if kept[-1] != points[-1]:
      kept.append(points[-1])
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(widget.arcColor.Q, 2.2, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap))
    painter.drawPolyline(QPolygonF([widget.pointOf(*place)
                                    for place in kept]))
    end = points[-1]
    if (widget.hit() is None or widget.runs()) and _inside(
        widget.unfolded.bounds(), *end):
      painter.setBrush(QBrush(widget.paddingsColor.Q))
      painter.drawEllipse(widget.pointOf(*end), 4.5, 4.5)
    painter.setFont(widget.numberFont)
    for number, crossing in enumerate(widget.crossings(), 1):
      centre = widget.pointOf(crossing.x, crossing.y)
      painter.setPen(QPen(widget.arcColor.Q, 1.2))
      painter.setBrush(QBrush(widget.paddingsColor.Q))
      painter.drawEllipse(centre, _GLYPH, _GLYPH)
      painter.setPen(widget.numberFont.color.Q)
      painter.drawText(QRectF(centre.x() - _GLYPH, centre.y() - _GLYPH,
                              2.0 * _GLYPH, 2.0 * _GLYPH), _CENTRE,
                       str(number))


def _onMap(low: tuple, way: Way) -> tuple[tuple, tuple]:
  """Returns the places of 'way' and the states there, as far as the
  map 'low' holds them, the first past its edge kept."""
  places, states = [], []
  for x, y, speed, spin in way:
    places.append((x, y))
    states.append((speed, spin))
    if not (low[0] <= x <= low[2] and low[1] <= y <= low[3]):
      break
  return tuple(places), tuple(states)


def _inside(low: tuple, x: float, y: float) -> bool:
  """Tells whether 'x', 'y' lies on the map 'low'."""
  return low[0] < x < low[2] and low[1] < y < low[3]


def _polygonOf(points: numpy.ndarray) -> QPolygonF:
  """Returns the places 'points', a row each, as a polygon."""
  return QPolygonF([QPointF(float(x), float(y)) for x, y in points])


def _shares(span: float, count: int) -> list[float]:
  """Returns the places dividing 'span' into 'count' equal parts, the
  ends left out."""
  return [span * k / count for k in range(1, count)]


class UnfoldedMap(PaintedWidget):
  """
  UnfoldedMap subclasses 'PaintedWidget' and is the table unfolded, as
  'Unfolded' has it, seen from above as the view from above has it: the
  table's length across, its head to the right. Each cushion's line is
  where the shot meets that cushion; the copies beyond show every ball
  mirrored as the copy is. How many copies it shows is its 'unfolded's;
  a full map shows 7 by 7. 'showShot' tells it the balls, the cue ball,
  and the aim, the
  side and the speed of the shot being set up: while there is an aim,
  the arc of the English leaves the cue ball along it, straight without
  side, bending the way of the English, each cushion it crosses
  numbered; each way ends where its ball would stop, a ring where the
  cue ball's does. The cue ball's way, up to the first ball it meets,
  is the engine's ('showWay': the shot played on the table, unfolded;
  the user: "just calculate the main expected path"), once it comes;
  till then the estimate 'Unfolded' makes, table by table, the caption
  saying so, or, once the engine is at it ('showWorking'), that the
  shot is being worked out. A drag on the map turns the aim about the
  cue ball by as much as the pointer turns about it from where it was
  pressed, told by 'aimDragged'; a press alone changes nothing. A
  'fanned' map, the full one, ends the arc where it first meets a ball,
  a ghost of the cue ball there, and fans out where the two may go, as
  'Unfolded.fanOf' has it, filled from the ways one standard deviation
  off to the way as aimed, that drawn bright; the cue ball's roll as
  it meets the ball from how it was struck, 'top'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(25, 26, 29)
  __fallback_cloth_color__ = Color(21, 147, 210)
  __fallback_copy_color__ = Color(14, 76, 110)
  __fallback_line_color__ = Color(201, 180, 138)
  __fallback_rim_color__ = Color(229, 192, 123)
  __fallback_diamond_color__ = Color(240, 214, 150)
  __fallback_arc_color__ = Color(255, 236, 180)
  __fallback_ball_edge_color__ = Color(20, 20, 22)
  __fan_alpha__ = 0.16  # how strongly a fan is filled
  __run_points__ = 360  # points a ball's way as the engine played it
  __ball_colors__ = {
    'white': Color(242, 236, 217),
    'yellow': Color(245, 178, 27),
    'red': Color(224, 38, 45),
  }

  #  Private Variables
  __map_unfolded__: Unfolded = Unfolded()
  __map_balls__: tuple = ()
  __map_kegler__: bool = False
  __map_book__: Phrasebook = ENGLISH
  __map_cue__: str = 'white'
  __map_aim__: tuple | None = None
  __map_top__: float = 0.0
  __map_side__: float = 0.0
  __map_fanned__: bool = False
  __map_figure__: tuple | None = None
  __map_runs__: tuple | None = None
  __map_working__: tuple | None = None
  __map_frame__: tuple | None = None
  __map_backdrop__: tuple | None = None
  __map_speed__: float = 3000.0
  #  While dragging: the pointer's and the aim's angles as pressed.
  __map_grab__: tuple | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  mapOp = PaintUnfoldedMap()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 170, 170),
  )
  numberFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      8,
      Color(255, 236, 180),
  )

  #  Virtual Variables
  unfolded: Field[Unfolded] = Field()
  balls: Field[tuple] = Field()
  cueName: Field[str] = Field()
  aim: Field[tuple] = Field()
  top: Field[float] = Field()
  side: Field[float] = Field()
  fanned: Field[bool] = Field()
  speed: Field[float] = Field()
  clothColor: Field[Color] = Field()
  copyColor: Field[Color] = Field()
  lineColor: Field[Color] = Field()
  rimColor: Field[Color] = Field()
  diamondColor: Field[Color] = Field()
  arcColor: Field[Color] = Field()
  ballEdgeColor: Field[Color] = Field()

  #  Signals
  aimDragged = Signal(float, float)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @unfolded.GET
  def _getUnfolded(self, ) -> Unfolded:
    """The 'unfolded' getter returns the table unfolded as the map
    shows it, how many copies each way."""
    return self.__map_unfolded__

  @balls.GET
  def _getBalls(self, ) -> tuple[Ball, ...]:
    """The 'balls' getter returns the balls as they lie."""
    return self.__map_balls__

  @cueName.GET
  def _getCueName(self, ) -> str:
    """The 'cueName' getter returns the cue ball's name."""
    return self.__map_cue__

  @aim.GET
  def _getAim(self, ) -> tuple[float, float] | None:
    """The 'aim' getter returns the way the shot is aimed, along the
    cloth as the table has it; 'None' while none is."""
    return self.__map_aim__

  @top.GET
  def _getTop(self, ) -> float:
    """The 'top' getter returns how far up from the middle the cue ball
    is struck, a share of the radius."""
    return self.__map_top__

  @fanned.GET
  def _getFanned(self, ) -> bool:
    """The 'fanned' getter tells whether the map shows where the balls
    may go after the arc meets a ball."""
    return self.__map_fanned__

  @side.GET
  def _getSide(self, ) -> float:
    """The 'side' getter returns how far right of the middle the cue
    ball is struck, a share of the radius."""
    return self.__map_side__

  @speed.GET
  def _getSpeed(self, ) -> float:
    """The 'speed' getter returns how fast the cue ball is sent, in
    mm/s."""
    return self.__map_speed__

  @clothColor.GET
  def _getClothColor(self, ) -> Color:
    return self.__fallback_cloth_color__

  @copyColor.GET
  def _getCopyColor(self, ) -> Color:
    return self.__fallback_copy_color__

  @lineColor.GET
  def _getLineColor(self, ) -> Color:
    return self.__fallback_line_color__

  @rimColor.GET
  def _getRimColor(self, ) -> Color:
    return self.__fallback_rim_color__

  @diamondColor.GET
  def _getDiamondColor(self, ) -> Color:
    return self.__fallback_diamond_color__

  @arcColor.GET
  def _getArcColor(self, ) -> Color:
    return self.__fallback_arc_color__

  @ballEdgeColor.GET
  def _getBallEdgeColor(self, ) -> Color:
    return self.__fallback_ball_edge_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @unfolded.SET
  def _setUnfolded(self, unfolded: Unfolded) -> None:
    """The 'unfolded' setter has the map show 'unfolded', as many
    copies each way as it has."""
    self.__map_unfolded__ = unfolded
    self.update()

  @fanned.SET
  def _setFanned(self, fanned: bool) -> None:
    """The 'fanned' setter has the map show, or not, where the balls
    may go after the arc meets a ball."""
    self.__map_fanned__ = True if fanned else False
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(480, 440)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(280, 260)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A press takes hold of the aim, leaving it as it is."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    self.grabAt(event.position())

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """A drag turns the aim as the pointer turns about the cue ball."""
    if self.__map_grab__ is None:
      return PaintedWidget.mouseMoveEvent(self, event)
    self.dragTo(event.position())

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """A release lets go of the aim."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mouseReleaseEvent(self, event)
    self.__map_grab__ = None

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

  def showShot(self, balls: tuple[Ball, ...], cueName: str,
               aim: tuple[float, float] | None, top: float, side: float,
               speed: float) -> None:
    """The 'showShot' method shows 'balls', 'cueName' the cue ball, and
    the arc of a shot along 'aim', struck 'top' and 'side', at 'speed'
    mm/s, or none while 'aim' is 'None'; painted again only if any of it
    changed."""
    shot = (tuple(balls), cueName, aim, top, side, speed)
    if shot == (self.__map_balls__, self.__map_cue__, self.__map_aim__,
                self.__map_top__, self.__map_side__, self.__map_speed__):
      return
    (self.__map_balls__, self.__map_cue__, self.__map_aim__,
     self.__map_top__, self.__map_side__, self.__map_speed__) = shot
    self.update()

  def shotKey(self, ) -> tuple:
    """The 'shotKey' method returns what the shot shown is: the balls,
    the cue ball, the aim, the point struck and the speed."""
    return (self.balls, self.cueName, self.aim, self.top, self.side,
            self.speed)

  def showRuns(self, key: tuple, runs: tuple[Run, ...],
               words: str) -> None:
    """The 'showRuns' method has the map draw the shot 'key', as
    'shotKey' has it, as the engine played it: 'runs', the shot as
    aimed, then, once played, the aim off one standard deviation of the
    'spread' to the one side and to the other; 'words', the referee's
    call on the shot as aimed. Shown while the shot stays that."""
    self.__map_runs__ = (key, tuple(runs), words)
    self.update()

  def showWay(self, key: tuple, way: Way) -> None:
    """The 'showWay' method has the map draw the cue ball's way as the
    engine played it, 'way', as 'Unfolded.wayOf' gives it, the cue ball
    alone, for the shot 'key'."""
    run = Run(1.0, self.cueName, ((self.cueName, tuple(way)),), ())
    self.showRuns(key, (run,), '')

  def showWorking(self, key: tuple) -> None:
    """The 'showWorking' method tells the map the engine is playing the
    shot 'key', as 'shotKey' has it: the caption says so meanwhile."""
    self.__map_working__ = key
    self.update()

  def working(self, ) -> bool:
    """The 'working' method tells whether the engine is playing the
    shot shown, not yet played."""
    return (self.__map_working__ == self.shotKey()
            and self.engineWay() is None)

  def runs(self, ) -> tuple[Run, ...]:
    """The 'runs' method returns the shot shown as the engine played
    it, as aimed first, then off to either side once played; none while
    it is not known."""
    kept = self.__map_runs__
    if kept is None or self.aim is None or kept[0] != self.shotKey():
      return ()
    return kept[1]

  def engineWay(self, ) -> Way | None:
    """The 'engineWay' method returns the cue ball's way as the engine
    played the shot shown, 'None' while it is not known."""
    runs = self.runs()
    return runs[0].wayOf(runs[0].cue) if runs else None

  def cueBall(self, ) -> Ball | None:
    """The 'cueBall' method returns the cue ball, 'None' if it is not
    among the balls."""
    for ball in self.balls:
      if ball.name == self.cueName:
        return ball
    return None

  def figure(self, ) -> tuple[tuple, Hit | None, Fan | None, tuple]:
    """The 'figure' method returns what the map draws of the shot: the
    arc, ended where it meets a ball on a fanned map; that hit; the fan
    from it; and where the arc crosses a cushion's line inside the map;
    reckoned again only when the shot or the map changed."""
    key = (self.unfolded, self.balls, self.cueName, self.aim, self.top,
           self.side, self.speed, self.fanned, self.engineWay() is None)
    if self.__map_figure__ is not None and self.__map_figure__[0] == key:
      return self.__map_figure__[1]
    figure = self._figured()
    self.__map_figure__ = (key, figure)
    return figure

  def arc(self, ) -> tuple[tuple[float, float], ...]:
    """The 'arc' method returns the arc of the English from the cue ball
    along the aim, as 'Unfolded.arcOf' has it, on a fanned map ended
    where it meets a ball; empty while there is no aim or no cue
    ball."""
    return self.figure()[0]

  def hit(self, ) -> Hit | None:
    """The 'hit' method returns where the arc first meets a ball, on a
    fanned map; 'None' if it meets none, or the map is not fanned."""
    return self.figure()[1]

  def fan(self, ) -> Fan | None:
    """The 'fan' method returns where the balls may go after the hit,
    on a fanned map; 'None' without a hit."""
    return self.figure()[2]

  def crossings(self, ) -> tuple[Crossing, ...]:
    """The 'crossings' method returns where the arc crosses a cushion's
    line, in order, inside the map."""
    return self.figure()[3]

  def setWords(self, book: Phrasebook) -> None:
    """The 'setWords' method has the caption speak 'book's
    language."""
    self.__map_book__ = book
    self.update()

  def caption(self, ) -> str:
    """The 'caption' method returns the words under the map."""
    book = self.__map_book__
    if self.__map_kegler__:
      book = book.kegler()
    if self.aim is None or self.cueBall() is None:
      return book.said('map.empty')
    count = len(self.crossings())
    if self.engineWay() is None:
      if self.working():
        return book.said('map.working')
      return book.said('map.estimate')
    words = self.__map_runs__[2]
    if words:
      return words
    cushions = book.counted('count.cushion', count)
    hit = self.hit()
    if hit is not None:
      return book.said('map.meets', book.theBall(hit.name), cushions,
                       '%.2f' % self.unfolded.spread)
    side = self.side
    if abs(side) < 1e-9:
      english = book.said('map.straight')
    else:
      way = 'map.right' if side > 0.0 else 'map.left'
      english = book.said(way, '%.2f' % abs(side))
    return book.said('map.guide', english, cushions)

  def colorOf(self, name: str) -> Color:
    """The 'colorOf' method returns the colour of the ball 'name': in
    keglebillard the marked white, 'yellow', a pale grey to tell it from
    the white."""
    if self.__map_kegler__ and name == 'yellow':
      return Color(207, 207, 207)
    return self.__ball_colors__.get(name, self.__fallback_arc_color__)

  def setKegler(self, kegler: bool) -> None:
    """The 'setKegler' method draws keglebillard's balls, the marked
    white pale grey, or three-cushion's."""
    self.__map_kegler__ = True if kegler else False
    self.update()

  def scale(self, ) -> float:
    """The 'scale' method returns how many pixels a mm of the map takes,
    the whole map fitting inside the margins, the words under it."""
    return self._frame()[1]

  def pointOf(self, x: float, y: float) -> QPointF:
    """The 'pointOf' method returns where on the widget the place 'x'
    across and 'y' along the table unfolded is: along to the right,
    across downwards, the map in the middle."""
    low, scale, left, top = self._frame()
    return QPointF(left + (y - low[1]) * scale, top + (x - low[0]) * scale)

  def placeAt(self, point: QPointF) -> tuple[float, float]:
    """The 'placeAt' method returns the place on the table unfolded,
    'x' across and 'y' along, under 'point' on the widget."""
    low, scale, left, top = self._frame()
    return (low[0] + (point.y() - top) / scale,
            low[1] + (point.x() - left) / scale)

  def grabAt(self, point: QPointF) -> None:
    """The 'grabAt' method takes hold of the aim with the pointer at
    'point', leaving the aim as it is: what a drag on turns it from. Not
    while there is no aim, nor at the cue ball itself."""
    self.__map_grab__ = None
    aim, pointer = self.__map_aim__, self._pointerAngle(point)
    if aim is None or pointer is None:
      return
    self.__map_grab__ = (pointer, math.atan2(aim[1], aim[0]))

  def dragTo(self, point: QPointF) -> None:
    """The 'dragTo' method tells, by 'aimDragged', the aim taken hold
    of, turned about the cue ball by as much as the pointer has turned
    about it since, now at 'point'; a pointer pressed on the aim line
    and dragged onto any copy's image of a ball aims at that image."""
    grab, pointer = self.__map_grab__, self._pointerAngle(point)
    if grab is None or pointer is None:
      return
    turn = grab[1] + pointer - grab[0]
    self.aimDragged.emit(math.cos(turn), math.sin(turn))

  def rectOf(self, lowX: float, lowY: float, highX: float,
             highY: float) -> QRectF:
    """The 'rectOf' method returns where on the widget the stretch from
    'lowX', 'lowY' to 'highX', 'highY' of the map is."""
    return QRectF(self.pointOf(lowX, lowY), self.pointOf(highX, highY))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _pointerAngle(self, point: QPointF) -> float | None:
    """Returns the way from the cue ball to the place under 'point', an
    angle on the table; 'None' without a cue ball, or at it."""
    ball = self.cueBall()
    if ball is None:
      return None
    x, y = self.placeAt(point)
    if math.hypot(x - ball.x, y - ball.y) <= 1.0:
      return None
    return math.atan2(y - ball.y, x - ball.x)

  def _frame(self, ) -> tuple[tuple, float, float, float]:
    """Returns the map's bounds, its pixels a mm, and where its top
    left corner is on the widget; reckoned again only when the map or
    the widget's size changed."""
    key = (self.unfolded, self.width(), self.height())
    if self.__map_frame__ is not None and self.__map_frame__[0] == key:
      return self.__map_frame__[1]
    low = self.unfolded.bounds()
    width = max(self.width() - 2.0 * _MARGIN, 1.0)
    height = max(self.height() - 2.0 * _MARGIN - _CAPTION, 1.0)
    scale = min(width / (low[3] - low[1]), height / (low[2] - low[0]))
    across, along = (low[2] - low[0]) * scale, (low[3] - low[1]) * scale
    left = 0.5 * (self.width() - along)
    top = _MARGIN + 0.5 * (self.height() - 2.0 * _MARGIN - _CAPTION
                           - across)
    frame = (low, scale, left, top)
    self.__map_frame__ = (key, frame)
    return frame

  def _figuredRun(self, run: Run) -> tuple[tuple, Hit | None, None,
                                            tuple]:
    """Reckons the cue ball's way, its first hit and its crossings, up
    to the second ball it meets, from 'run', the shot as the engine
    played it."""
    unfolded = self.unfolded
    way = run.wayOf(run.cue)
    points, _ = _onMap(unfolded.bounds(), way)
    upto = len(points)
    if len(run.meets) > 1:
      upto = min(upto, int(run.meets[1][0] * run.rate) + 1)
    crossings = unfolded.crossingsOf(points[:upto])
    hit = None
    if run.meets and self.fanned:
      k = min(int(run.meets[0][0] * run.rate), len(way) - 1)
      x, y = way[k][:2]
      hit = Hit(x, y, 0.0, 0.0, run.meets[0][1], x, y, 0.0, 0.0, k)
    low = unfolded.bounds()
    inside = tuple(crossing for crossing in crossings
                   if low[0] < crossing.x < low[2]
                   and low[1] < crossing.y < low[3])
    return points, hit, None, inside

  def _figured(self, ) -> tuple[tuple, Hit | None, Fan | None, tuple]:
    """Reckons the arc, the hit, the fan and the crossings, as 'figure'
    returns them."""
    ball, aim, unfolded = self.cueBall(), self.aim, self.unfolded
    if ball is None or aim is None:
      return (), None, None, ()
    state = unfolded.stateOf(self.top, self.side, self.speed)
    runs = self.runs()
    if runs and runs[0].meets is not None and len(runs[0].ways) > 1:
      return self._figuredRun(runs[0])
    way = self.engineWay()
    states = None
    if way is None:
      points = unfolded.arcOf(ball.x, ball.y, aim[0], aim[1], self.side,
                              self.speed, state)
    else:
      points, states = _onMap(unfolded.bounds(), way)
    hit, fan = None, None
    if self.fanned:
      hit = unfolded.hitOf(points, unfolded.imagesOf(self.balls,
                                                     self.cueName))
    if hit is not None:
      points = points[:hit.index] + ((hit.x, hit.y),)
    crossings = unfolded.crossingsOf(points)
    if hit is not None:
      if states is None:
        met = unfolded.stateAfter(points, state)
      else:
        met = states[max(hit.index - 1, 0)]
      fan = unfolded.fanOf(hit, met, self.side, self.speed)
    low = unfolded.bounds()
    inside = tuple(crossing for crossing in crossings
                   if low[0] < crossing.x < low[2]
                   and low[1] < crossing.y < low[3])
    return points, hit, fan, inside
