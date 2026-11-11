"""
PaintFrame subclasses 'AbstractPaintOp' and paints a 'FrameView': a
plane frame, its loads and reactions, and a section force diagram.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF

from ....paint_ops import AbstractPaintOp
from .. import LineLoad, PointLoad

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from ._frame_view import FrameView

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_CENTER = Qt.AlignmentFlag.AlignCenter
_ACCENT = QColor(229, 192, 123)
_HOVER = QColor(220, 222, 228)
_MEMBER = QColor(190, 194, 202)
_SUPPORT = QColor(150, 154, 162)
_LOAD = QColor(224, 108, 117)
_REACTION = QColor(152, 195, 121)
_GRID = QColor(52, 55, 60)
_SHAPE = QColor(220, 222, 228)
#  Each diagram's colour, and the side it is drawn on: M on the side it
#  pulls, the others on the left as the member runs
_DIAGRAMS = {
  'N': (QColor(198, 120, 221), 1.0),
  'V': (QColor(152, 195, 121), 1.0),
  'M': (QColor(97, 175, 239), -1.0),
}
_UNITS = {'N': 'kN', 'V': 'kN', 'M': 'kNm'}
_WORDS = {
  'N': 'N, kN, tension positive',
  'V': 'V, kN',
  'M': 'M, kNm, drawn on the side it pulls',
}


def _number(value: float) -> str:
  """'value' written briefly: '36.6', '-5.84', '120'."""
  if abs(value) >= 100:
    return '%.0f' % value
  if abs(value) >= 10:
    return '%.1f' % value
  return '%.2f' % value


class PaintFrame(AbstractPaintOp):
  """
  PaintFrame subclasses 'AbstractPaintOp' and paints a 'FrameView', back
  to front: dots every metre; the diagram shown, filled, along each
  member; the members, a ring where hinged, and the nodes, each named;
  the supports under their nodes; the loads in red, a point load an
  arrow, a line load its arrows as long as it is there, a moment an arc;
  the reactions in green; the diagram's values; or the shape the frame
  bends to, dashed, enlarged; and in the corner what is shown, or why
  the frame is not held. What is selected is accented, what is under
  the mouse lit.
  """

  #  Annotations
  widget: FrameView

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the frame, back to front."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setFont(widget.font)
    self._paintGrid(painter)
    held = not widget.analysis.held
    if held and widget.kind in _DIAGRAMS:
      self._paintDiagram(painter)
    self._paintMembers(painter)
    self._paintSupports(painter)
    self._paintLoads(painter)
    if held:
      self._paintReactions(painter)
      if widget.kind == 'shape':
        self._paintShape(painter)
    self._paintCaption(painter)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _color(self, part: tuple[str, int], color: QColor) -> QColor:
    """'color', or the accent if 'part' is selected, lit if under the
    mouse."""
    widget = self.widget
    if part in widget.selection:
      return _ACCENT
    if part == widget.hovered:
      return _HOVER
    return color

  @staticmethod
  def _arrow(painter: WPainter, tail: QPointF, head: QPointF,
             color: QColor) -> None:
    """An arrow from 'tail' to 'head', in 'color'."""
    painter.setPen(QPen(color, 1.8))
    painter.drawLine(QLineF(tail, head))
    angle = math.atan2(head.y() - tail.y(), head.x() - tail.x())
    for turn in (math.radians(155), math.radians(-155)):
      painter.drawLine(QLineF(head, QPointF(
        head.x() + 9.0 * math.cos(angle + turn),
        head.y() + 9.0 * math.sin(angle + turn))))

  @staticmethod
  def _arc(painter: WPainter, centre: QPointF, radius: float,
           anticlockwise: bool, color: QColor) -> None:
    """An arc about 'centre', three quarters round, its arrow turning
    anticlockwise or not."""
    painter.setPen(QPen(color, 1.8))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    box = QRectF(centre.x() - radius, centre.y() - radius, 2 * radius,
                 2 * radius)
    painter.drawArc(box, 45 * 16, 270 * 16)
    end = math.radians(-45.0)
    tip = QPointF(centre.x() + radius * math.cos(end),
                  centre.y() - radius * math.sin(end))
    sense = 1.0 if anticlockwise else -1.0
    heading = end + sense * math.pi / 2
    for turn in (math.radians(150), math.radians(-150)):
      painter.drawLine(QLineF(tip, QPointF(
        tip.x() + 8.0 * math.cos(heading + turn),
        tip.y() - 8.0 * math.sin(heading + turn))))

  def _label(self, painter: WPainter, at: QPointF, text: str,
             color: QColor) -> None:
    """'text' in 'color', centred at 'at'."""
    painter.setPen(color)
    painter.drawText(QRectF(at.x() - 40.0, at.y() - 9.0, 80.0, 18.0),
                     _CENTER, text)

  def _paintGrid(self, painter: WPainter) -> None:
    """A dot every metre, or every five when the metres are small."""
    widget = self.widget
    scale = widget.place()[0]
    step = 1.0 if scale >= 18 else 5.0
    left, top = widget.toFrame(QPointF(0.0, 0.0))
    right, bottom = widget.toFrame(QPointF(widget.width(),
                                           widget.height()))
    painter.setPen(QPen(_GRID, 2.0))
    x = math.floor(left / step) * step
    while x <= right:
      y = math.floor(bottom / step) * step
      while y <= top:
        painter.drawPoint(widget.toScreen(x, y))
        y += step
      x += step

  def _diagramScale(self, ) -> float:
    """The pixels to a kN or kNm of the diagram shown, its greatest value
    a twelfth of the view."""
    widget = self.widget
    most = abs(widget.analysis.most(widget.kind)[0])
    if most < 1e-9:
      return 0.0
    return 0.085 * min(widget.width(), widget.height()) / most

  def _curve(self, member: int, scale: float) -> list[QPointF]:
    """The diagram shown along the member of index 'member', as
    pixels."""
    widget = self.widget
    frame = widget.frame
    _, side = _DIAGRAMS[widget.kind]
    nx, ny = widget.across(member)
    out = []
    for s, value in widget.analysis.diagram(member, widget.kind):
      base = widget.toScreen(*frame.pointAt(member, s))
      reach = side * value * scale
      out.append(QPointF(base.x() + nx * reach, base.y() + ny * reach))
    return out

  def _paintDiagram(self, painter: WPainter) -> None:
    """The diagram shown along each member, filled from the member to
    its curve, and its values at the ends, the jumps and the peaks."""
    widget = self.widget
    scale = self._diagramScale()
    if not scale:
      return
    color, side = _DIAGRAMS[widget.kind]
    fill = QColor(color)
    fill.setAlpha(55)
    placed = []
    for member in range(len(widget.frame.members)):
      start, end = widget.memberEnds(member)
      curve = self._curve(member, scale)
      painter.setPen(self.emptyPen)
      painter.setBrush(QBrush(fill))
      painter.drawPolygon(QPolygonF([start, *curve, end]))
      painter.setPen(QPen(color, 1.5))
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawPolyline(QPolygonF(curve))
      self._paintMarks(painter, member, scale, side, placed)

  def _paintMarks(self, painter: WPainter, member: int, scale: float,
                  side: float, placed: list[QRectF]) -> None:
    """The values of the diagram shown along the member of index
    'member', where they are worth writing and there is room."""
    widget = self.widget
    nx, ny = widget.across(member)
    for s, value in widget.analysis.marks(member, widget.kind):
      base = widget.toScreen(*widget.frame.pointAt(member, s))
      out = side * (1.0 if value >= 0 else -1.0)
      reach = side * value * scale + out * 12.0
      at = QPointF(base.x() + nx * reach, base.y() + ny * reach)
      box = QRectF(at.x() - 22.0, at.y() - 8.0, 44.0, 16.0)
      if any(box.intersects(other) for other in placed):
        continue
      placed.append(box)
      self._label(painter, at, _number(value), _HOVER)

  def _paintMembers(self, painter: WPainter) -> None:
    """The members, a ring at a hinged end, the nodes and their
    names."""
    widget = self.widget
    frame = widget.frame
    for index, member in enumerate(frame.members):
      start, end = widget.memberEnds(index)
      color = self._color(('member', index), _MEMBER)
      pen = QPen(color, 3.5)
      pen.setCapStyle(Qt.PenCapStyle.RoundCap)
      painter.setPen(pen)
      painter.drawLine(QLineF(start, end))
      long = max(math.hypot(end.x() - start.x(), end.y() - start.y()), 1.0)
      ux, uy = (end.x() - start.x()) / long, (end.y() - start.y()) / long
      for hinged, at, sense in ((member.startHinge, start, 1.0),
                                (member.endHinge, end, -1.0)):
        if not hinged:
          continue
        ring = QPointF(at.x() + sense * 9.0 * ux, at.y() + sense * 9.0 * uy)
        painter.setPen(QPen(color, 2.0))
        painter.setBrush(QBrush(widget.paddingsColor.Q))
        painter.drawEllipse(ring, 5.0, 5.0)
      middle = QPointF((start.x() + end.x()) / 2,
                       (start.y() + end.y()) / 2)
      nx, ny = widget.across(index)
      self._label(painter, QPointF(middle.x() - nx * 14.0,
                                   middle.y() - ny * 14.0),
                  'M%d' % (index + 1), QColor(110, 114, 122))
    for index, node in enumerate(frame.nodes):
      seen = widget.toScreen(*node)
      color = self._color(('node', index), _MEMBER)
      painter.setPen(self.emptyPen)
      painter.setBrush(QBrush(color))
      painter.drawEllipse(seen, 4.5, 4.5)
      self._label(painter, QPointF(seen.x() - 16.0, seen.y() - 14.0),
                  'N%d' % (index + 1), QColor(140, 144, 152))

  def _paintSupports(self, painter: WPainter) -> None:
    """Each support under its node: a pin a triangle, a roller a
    triangle on wheels, a fixed end a wall, each hatched."""
    widget = self.widget
    for index, support in enumerate(widget.frame.supports):
      p = widget.toScreen(*widget.frame.nodes[support.node])
      color = self._color(('support', index), _SUPPORT)
      painter.setPen(QPen(color, 1.6))
      painter.setBrush(Qt.BrushStyle.NoBrush)
      x, y = p.x(), p.y()
      ground = y + 18.0
      if support.kind == 'pin':
        painter.drawPolygon(QPolygonF([p, QPointF(x - 10, ground),
                                       QPointF(x + 10, ground)]))
      elif support.kind == 'roller':
        painter.drawPolygon(QPolygonF([p, QPointF(x - 9, y + 12),
                                       QPointF(x + 9, y + 12)]))
        painter.drawEllipse(QPointF(x - 5, y + 15), 3.0, 3.0)
        painter.drawEllipse(QPointF(x + 5, y + 15), 3.0, 3.0)
      else:
        ground = y + 3.0
        painter.setPen(QPen(color, 3.0))
      painter.drawLine(QLineF(x - 15, ground, x + 15, ground))
      painter.setPen(QPen(color, 1.0))
      for k in range(6):
        left = x - 15 + 6 * k
        painter.drawLine(QLineF(left, ground, left - 5, ground + 6))

  def _paintLoads(self, painter: WPainter) -> None:
    """The loads: a point load an arrow, a line load its arrows and the
    line along their tails, a moment an arc; each named by its size."""
    widget = self.widget
    for index, load in enumerate(widget.frame.loads):
      color = self._color(('load', index), _LOAD)
      if isinstance(load, PointLoad):
        tail, head = widget.arrowOf(load)
        self._arrow(painter, tail, head, color)
        size = math.hypot(load.right, load.down)
        self._label(painter, QPointF(tail.x(), tail.y() - 10.0),
                    '%s kN' % _number(size), color)
      elif isinstance(load, LineLoad):
        band = widget.bandOf(load)
        for tail, head in band:
          if math.hypot(head.x() - tail.x(), head.y() - tail.y()) > 3.0:
            self._arrow(painter, tail, head, color)
        painter.setPen(QPen(color, 1.4))
        painter.drawPolyline(QPolygonF([tail for tail, _ in band]))
        words = '%s kN/m' % _number(load.first)
        if abs(load.first - load.last) > 1e-9:
          words = '%s–%s kN/m' % (_number(load.first), _number(load.last))
        tail = band[len(band) // 2][0]
        self._label(painter, QPointF(tail.x(), tail.y() - 10.0), words,
                    color)
      else:
        centre = widget.loadPoint(load)
        self._arc(painter, centre, 16.0, load.moment > 0, color)
        self._label(painter, QPointF(centre.x(), centre.y() - 28.0),
                    '%s kNm' % _number(abs(load.moment)), color)

  def _paintReactions(self, painter: WPainter) -> None:
    """What each support pushes with, in green: along x and y an arrow
    each, turning an arc, each named by its size."""
    widget = self.widget
    frame = widget.frame
    for support, (rx, ry, turning) in zip(frame.supports,
                                          widget.analysis.reactions):
      p = widget.toScreen(*frame.nodes[support.node])
      if abs(ry) > 1e-9:
        low, high = QPointF(p.x(), p.y() + 70.0), QPointF(p.x(),
                                                         p.y() + 32.0)
        tail, head = (low, high) if ry > 0 else (high, low)
        self._arrow(painter, tail, head, _REACTION)
        self._label(painter, QPointF(p.x() + 34.0, p.y() + 58.0),
                    '%s kN' % _number(abs(ry)), _REACTION)
      if abs(rx) > 1e-9:
        far, near = QPointF(p.x() - 62.0, p.y() + 24.0), QPointF(
          p.x() - 20.0, p.y() + 24.0)
        tail, head = (far, near) if rx > 0 else (near, far)
        self._arrow(painter, tail, head, _REACTION)
        self._label(painter, QPointF(p.x() - 42.0, p.y() + 10.0),
                    '%s kN' % _number(abs(rx)), _REACTION)
      if abs(turning) > 1e-9:
        self._arc(painter, p, 28.0, turning > 0, _REACTION)
        self._label(painter, QPointF(p.x() + 44.0, p.y() - 26.0),
                    '%s kNm' % _number(abs(turning)), _REACTION)

  def _paintShape(self, painter: WPainter) -> None:
    """The shape the frame bends to, dashed, enlarged so its greatest
    move is a twelfth of the frame."""
    widget = self.widget
    factor = self.shapeFactor()
    if not factor:
      return
    pen = QPen(_SHAPE, 2.0)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for member in range(len(widget.frame.members)):
      points = [widget.toScreen(x + factor * u, y + factor * v)
                for x, y, u, v in widget.analysis.shape(member)]
      painter.drawPolyline(QPolygonF(points))

  def shapeFactor(self, ) -> float:
    """The 'shapeFactor' method returns how many times the shape is
    enlarged, its greatest move a twelfth of the frame."""
    widget = self.widget
    frame = widget.frame
    most = self.greatestMove()
    if most < 1e-15:
      return 0.0
    xs = [n.x for n in frame.nodes]
    ys = [n.y for n in frame.nodes]
    size = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    return size / 12 / most

  def greatestMove(self, ) -> float:
    """The 'greatestMove' method returns how far the frame moves at
    most, in m."""
    widget = self.widget
    return max([math.hypot(u, v) for member in
                range(len(widget.frame.members))
                for _, _, u, v in widget.analysis.shape(member)] + [0.0])

  def _paintCaption(self, painter: WPainter) -> None:
    """What is shown, in the corner, or why the frame is not held."""
    widget = self.widget
    analysis = widget.analysis
    box = QRectF(14.0, 10.0, widget.width() - 28.0, 18.0)
    if analysis.held:
      painter.setPen(_ACCENT)
      painter.drawText(box, _LEFT, 'Not held: %s.' % analysis.held)
      return
    painter.setPen(widget.font.color.Q)
    if widget.kind == 'shape':
      words = 'Shape, enlarged %.0f times · moves at most %.2f mm' % (
        self.shapeFactor(), 1000 * self.greatestMove())
    else:
      value, member, s = analysis.most(widget.kind)
      words = '%s · greatest %s %s in M%d, %.2f m along' % (
        _WORDS[widget.kind], _number(value), _UNITS[widget.kind],
        member + 1, s)
    painter.drawText(box, _LEFT, words)
