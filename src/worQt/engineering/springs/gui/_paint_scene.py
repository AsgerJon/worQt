"""
PaintScene subclasses 'AbstractPaintOp' and paints a 'SceneView': a
system of springs in space, in perspective.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtGui import QRadialGradient

from ....paint_ops import AbstractPaintOp
from ._space import Vector, across, add, scaled, sub

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from ._scene_view import SceneView

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_ACCENT = QColor(229, 192, 123)
_HOVER = QColor(200, 204, 212)
_GRID = QColor(50, 53, 58)
_AXIS = QColor(66, 70, 77)
_SLACK = (175, 178, 186)  # a spring at rest
_PULLED = (224, 108, 117)  # a spring pulled
_PUSHED = (97, 175, 239)  # a spring pushed
_BALL = ((222, 232, 246), (118, 152, 196), (38, 52, 74))
_BLOCK = (QColor(88, 92, 100), QColor(138, 142, 150))
_COILS = 9  # turns of a spring drawn
_COIL = 0.035  # m: the radius of a spring drawn
_ENDS = 0.12  # of a spring's length straight at either end
_GRID_STEP = 0.5  # m between the floor's lines
_TUBE = QColor(120, 130, 150)  # a component's tube
_RAIL = QColor(120, 128, 140)  # a fixed component's rail past its tip
_AXLE_COLOR = QColor(152, 195, 121)  # a hinged component's axle
_AXLE = 0.18  # m: how far a hinge's axle reaches either side
_RAIL_REACH = 1.2  # m: how far a point's rail is drawn either side
_TABLE_REACH = 0.4  # m: how far a point's table is drawn either side


def _mixed(first: tuple, second: tuple, share: float) -> QColor:
  """The colour 'share' of the way from 'first' to 'second'."""
  return QColor(*[round(a + (b - a) * share) for a, b in zip(first,
                                                               second)])


class PaintScene(AbstractPaintOp):
  """
  PaintScene subclasses 'AbstractPaintOp' and paints a 'SceneView', back
  to front: the floor, its lines every half metre, the balls' shadows on
  it, fainter the higher a ball is; the rail of a point moving along
  one axis and the table of one moving along two; then the springs,
  dampers, components and points, the furthest first: a spring a coil
  coloured by how it is stretched, warm pulled and cool pushed, a
  damper a cylinder and its rod, a component a tube with its spring
  inside, its rail past its tip when fixed, its axle when hinged, a ball
  shaded as if lit from the top left, an anchor a block, each point
  named; what is selected accented, what is under the mouse lit; and in
  the corner how long it has moved.
  """

  #  Annotations
  widget: SceneView

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the scene, back to front."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    places = widget.positions()
    self._paintFloor(painter, places)
    self._paintShadows(painter, places)
    self._paintGuides(painter)
    for _, kind, index in self._order(places):
      if kind == 'point':
        self._paintPoint(painter, places, index)
      elif kind == 'spring':
        self._paintSpring(painter, places, index)
      elif kind == 'damper':
        self._paintDamper(painter, places, index)
      else:
        self._paintComponent(painter, places, index)
    self._paintCaption(painter)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _order(self, places: list[Vector]) -> list[tuple[float, str, int]]:
    """The parts, the furthest from the eye first."""
    widget = self.widget
    out = []
    for index, place in enumerate(places):
      seen = widget.project(place)
      if seen is not None:
        out.append((seen[1], 'point', index))
    for kind in ('spring', 'damper', 'component'):
      for index, link in enumerate(widget.partsOf(kind)):
        middle = scaled(add(places[link[0]], places[link[1]]), 0.5)
        seen = widget.project(middle)
        if seen is not None:
          out.append((seen[1], kind, index))
    return sorted(out)[::-1]

  def _accent(self, part: tuple[str, int]) -> QColor | None:
    """The colour 'part' is accented in: selected or under the mouse;
    'None' if neither."""
    widget = self.widget
    if part in widget.selection:
      return _ACCENT
    if part == widget.hovered:
      return _HOVER
    return None

  def _seenLine(self, start: Vector, end: Vector) -> QLineF | None:
    """The line from 'start' to 'end' as seen, or 'None' if an end is
    behind the eye."""
    first = self.widget.project(start)
    second = self.widget.project(end)
    if first is None or second is None:
      return None
    return QLineF(first[0], second[0])

  def _paintFloor(self, painter: WPainter, places: list[Vector]) -> None:
    """The floor at z nought, its lines every half metre about what is
    shown, those through nought a little lighter."""
    target = self.widget.target
    reach = max([abs(p[axis] - target[axis]) for p in places
                 for axis in (0, 1)] + [1.0])
    count = math.ceil(1.4 * reach / _GRID_STEP) + 1
    middle = [round(target[axis] / _GRID_STEP) for axis in (0, 1)]
    low = [(m - count) * _GRID_STEP for m in middle]
    high = [(m + count) * _GRID_STEP for m in middle]
    for step in range(2 * count + 1):
      for axis in (0, 1):
        value = low[axis] + step * _GRID_STEP
        color = _AXIS if abs(value) < 1e-9 else _GRID
        painter.setPen(QPen(color, 1.0))
        other = 1 - axis
        for piece in range(8):
          ends = []
          for share in (piece / 8, (piece + 1) / 8):
            point = [0.0, 0.0, 0.0]
            point[axis] = value
            point[other] = low[other] + share * (high[other] - low[other])
            ends.append((*point,))
          line = self._seenLine(*ends)
          if line is not None:
            painter.drawLine(line)

  def _paintShadows(self, painter: WPainter, places: list[Vector]) -> None:
    """Each ball's shadow on the floor, under it, fainter the higher it
    is."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    for index, place in enumerate(places):
      point = widget.system.points[index]
      if point.pinned or place[2] <= 0.0:
        continue
      radius = widget.ballRadius(index)
      corners = []
      for step in range(20):
        turn = 2 * math.pi * step / 20
        spot = (place[0] + radius * math.cos(turn),
                place[1] + radius * math.sin(turn), 0.0)
        seen = widget.project(spot)
        if seen is None:
          break
        corners.append(seen[0])
      if len(corners) < 20:
        continue
      alpha = round(min(max(120.0 - 30.0 * place[2], 30.0), 120.0))
      painter.setBrush(QBrush(QColor(0, 0, 0, alpha)))
      painter.drawPolygon(QPolygonF(corners))

  def _paintGuides(self, painter: WPainter) -> None:
    """The rail of each point moving along one axis, and the table of
    each moving along two, through where it was set up."""
    widget = self.widget
    pen = QPen(_RAIL, 1.4)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for point in widget.system.points:
      axes = ['xyz'.index(axis) for axis in point.moves]
      if len(axes) == 1:
        reach = [0.0, 0.0, 0.0]
        reach[axes[0]] = _RAIL_REACH
        line = self._seenLine(sub(point.at, (*reach,)),
                              add(point.at, (*reach,)))
        if line is not None:
          painter.drawLine(line)
      if len(axes) != 2:
        continue
      corners = []
      for first, second in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        corner = [*point.at]
        corner[axes[0]] += first * _TABLE_REACH
        corner[axes[1]] += second * _TABLE_REACH
        seen = widget.project((*corner,))
        if seen is None:
          break
        corners.append(seen[0])
      if len(corners) == 4:
        painter.drawPolygon(QPolygonF(corners))

  def _paintSpring(self, painter: WPainter, places: list[Vector],
                   index: int) -> None:
    """The spring of 'index', a coil, coloured by how it is
    stretched."""
    spring = self.widget.system.springs[index]
    start, end = places[spring.first], places[spring.second]
    color = self._accent(('spring', index)) or self._stretchColor(
        start, end, spring.rest)
    self._paintCoil(painter, start, end, _COIL, color)

  def _paintCoil(self, painter: WPainter, start: Vector, end: Vector,
                 radius: float, color: QColor) -> None:
    """A coil of 'radius' from 'start' to 'end', in 'color'."""
    widget = self.widget
    axis = sub(end, start)
    first, second = across(axis)
    coil = [start, add(start, scaled(axis, _ENDS))]
    samples = _COILS * 12
    for step in range(samples + 1):
      share = step / samples
      turn = 2 * math.pi * _COILS * share
      middle = add(start, scaled(axis, _ENDS + (1 - 2 * _ENDS) * share))
      out = add(scaled(first, radius * math.cos(turn)),
                scaled(second, radius * math.sin(turn)))
      coil.append(add(middle, out))
    coil += [add(start, scaled(axis, 1 - _ENDS)), end]
    seen = [widget.project(point) for point in coil]
    if any(point is None for point in seen):
      return
    painter.setPen(QPen(color, 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPolyline(QPolygonF([point[0] for point in seen]))

  @staticmethod
  def _stretchColor(start: Vector, end: Vector, rest: float) -> QColor:
    """The colour of a spring from 'start' to 'end' of 'rest' length:
    grey at rest, warmer the more it is pulled, cooler the more it is
    pushed."""
    share = (math.dist(start, end) - rest) / max(rest, 0.05)
    share = min(max(share, -1.0), 1.0)
    tint = _PULLED if share > 0 else _PUSHED
    return _mixed(_SLACK, tint, abs(share))

  def _paintComponent(self, painter: WPainter, places: list[Vector],
                      index: int) -> None:
    """The component of 'index': a rod, a tube from its base to its
    tip with its spring inside; fixed, its rail on past its tip; hinged,
    its axle through its base."""
    widget = self.widget
    component = widget.system.components[index]
    start, end = places[component.base], places[component.tip]
    seen = widget.project(scaled(add(start, end), 0.5))
    if seen is None:
      return
    focal, depth = widget.focal(), seen[1]
    accent = self._accent(('component', index))
    if component.turning == 'fixed':
      rail = add(end, scaled(sub(end, start), 0.25))
      line = self._seenLine(start, rail)
      if line is not None:
        painter.setPen(QPen(_RAIL, max(focal * 0.008 / depth, 1.0)))
        painter.drawLine(line)
    if component.turning == 'hinge':
      reach = scaled(component.axis, _AXLE)
      line = self._seenLine(sub(start, reach), add(start, reach))
      if line is not None:
        axle = QPen(_AXLE_COLOR, max(focal * 0.014 / depth, 2.0))
        axle.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(axle)
        painter.drawLine(line)
    line = self._seenLine(start, end)
    if line is not None:
      width = min(max(focal * 0.07 / depth, 5.0), 26.0)
      tube = QColor(accent or _TUBE)
      tube.setAlpha(110)
      pen = QPen(tube, width)
      pen.setCapStyle(Qt.PenCapStyle.FlatCap)
      painter.setPen(pen)
      painter.drawLine(line)
    color = accent or self._stretchColor(start, end, component.rest)
    self._paintCoil(painter, start, end, 0.6 * _COIL, color)

  def _paintDamper(self, painter: WPainter, places: list[Vector],
                   index: int) -> None:
    """The damper of 'index': a cylinder from its first point, a rod into
    it from its second."""
    widget = self.widget
    damper = widget.system.dampers[index]
    start, end = places[damper.first], places[damper.second]
    axis = sub(end, start)

    def along(share: float) -> Vector:
      return add(start, scaled(axis, share))

    seen = widget.project(along(0.4))
    if seen is None:
      return
    focal, depth = widget.focal(), seen[1]
    accent = self._accent(('damper', index))
    rod = QPen(accent or QColor(190, 194, 202),
               max(focal * 0.012 / depth, 1.5))
    rod.setCapStyle(Qt.PenCapStyle.FlatCap)
    for low, high in ((0.0, 0.12), (0.45, 1.0)):
      line = self._seenLine(along(low), along(high))
      if line is not None:
        painter.setPen(rod)
        painter.drawLine(line)
    body = self._seenLine(along(0.12), along(0.58))
    if body is None:
      return
    width = min(max(focal * 0.05 / depth, 4.0), 22.0)
    pen = QPen(accent or QColor(92, 99, 112), width)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.drawLine(body)
    shine = QPen(QColor(138, 146, 160), max(width / 4, 1.0))
    shine.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(shine)
    painter.drawLine(body.translated(-width / 5, -width / 5))

  def _paintPoint(self, painter: WPainter, places: list[Vector],
                  index: int) -> None:
    """The point of 'index': a ball shaded as if lit from the top left,
    or an anchor's block, and its name."""
    widget = self.widget
    seen = widget.project(places[index])
    if seen is None:
      return
    centre, depth = seen
    radius = max(widget.focal() * widget.ballRadius(index) / depth, 3.0)
    box = QRectF(centre.x() - radius, centre.y() - radius, 2 * radius,
                 2 * radius)
    accent = self._accent(('point', index))
    if widget.system.points[index].pinned:
      self._paintBlock(painter, box)
    else:
      self._paintBall(painter, box)
    if accent is not None:
      painter.setPen(QPen(accent, 2.0))
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawEllipse(box.adjusted(-3.0, -3.0, 3.0, 3.0))
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    label = QRectF(box.right() + 4.0, box.top() - 12.0, 40.0, 16.0)
    painter.drawText(label, _LEFT, 'P%d' % (index + 1))

  def _paintBall(self, painter: WPainter, box: QRectF) -> None:
    """A ball filling 'box', lit from the top left."""
    light, body, shade = _BALL
    radius = box.width() / 2
    focus = QPointF(box.center().x() - 0.35 * radius,
                    box.center().y() - 0.35 * radius)
    gradient = QRadialGradient(focus, 1.4 * radius, focus)
    gradient.setColorAt(0.0, QColor(*light))
    gradient.setColorAt(0.45, QColor(*body))
    gradient.setColorAt(1.0, QColor(*shade))
    painter.setPen(self.emptyPen)
    painter.setBrush(QBrush(gradient))
    painter.drawEllipse(box)

  def _paintBlock(self, painter: WPainter, box: QRectF) -> None:
    """An anchor's block filling 'box', hatched."""
    face, edge = _BLOCK
    painter.setPen(QPen(edge, 1.0))
    painter.setBrush(QBrush(face))
    painter.drawRect(box)
    painter.setClipRect(box)
    step = max(box.width() / 3, 3.0)
    offset = 0.0
    while offset < 2 * box.width():
      painter.drawLine(QLineF(box.left() + offset, box.top(),
                              box.left() + offset - box.height(),
                              box.bottom()))
      offset += step
    painter.setClipping(False)

  def _paintCaption(self, painter: WPainter) -> None:
    """How long the system has moved, in the corner, or that it is set
    up; and if its steps cannot keep up, that it is slowed."""
    widget = self.widget
    motion = widget.motion
    words = 'Set up'
    if motion is not None:
      words = 't = %.2f s' % motion.time
      if motion.slowed:
        words += ' · slowed: a spring too stiff to keep up with'
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    painter.drawText(QRectF(14.0, 10.0, 600.0, 18.0), _LEFT, words)
