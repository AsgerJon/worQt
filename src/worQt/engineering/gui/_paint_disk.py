"""
PaintDisk subclasses 'AbstractPaintOp' and paints the disk of a
'DiskWidget', with its supports, loads, dimensions and handles.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF

from ...paint_ops import AbstractPaintOp
from .._numbers import formatNumber
from . import GripNum
from ._glyphs import PLATE, TRIANGLE, HALF_BASE, ROLLER, HATCH, HANDLE
from ._glyphs import unit, dot

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ...utils import WPainter, Color
  from ...utils.geom import Rect
  from .. import Disk, Support, Load, Rebar, StrutTie
  from . import DiskWidget

_CENTER = Qt.AlignmentFlag.AlignCenter
_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_ARROW = 36.0  # pixels: how long a load's arrows are
_ARROW_GAP = 28.0  # pixels: about how far apart a line load's arrows are
_HEAD = 8.0  # pixels: how long an arrow's head is
_DIMENSION = 44.0  # pixels: how far out of the disk a dimension line is
_RESIZING = (GripNum.LENGTH, GripNum.HEIGHT, GripNum.CORNER)
_ENDS = (GripNum.SUPPORT_START, GripNum.SUPPORT_END)


def _magnitude(value: float) -> str:
  """A force or an intensity as it is read off a drawing."""
  return '%.4g' % abs(value)


class PaintDisk(AbstractPaintOp):
  """
  PaintDisk subclasses 'AbstractPaintOp' and paints the disk of a
  'DiskWidget' to scale: the disk filled in its colour and outlined; each
  support as a bearing plate on its stretch with a triangle beyond it, on
  rollers where it sets one displacement and on hatched ground where it
  sets both; each load as arrows onto its stretch, one for a short
  stretch and a row for a long one, labelled with the force or the force
  per metre; and the length and the height as dimension lines.

  Over the disk it paints its reinforcement, named, and its tied arch:
  each strut a band as wide as it needs to be at nu fc with its force,
  the tie with its force, dashed red where no reinforcement makes it,
  and, top left, what the arch carries.

  What is selected is drawn in the accent colour, with its handles: the
  disk's on its right edge, its top edge and its top right corner, a
  support's at the ends of its plate. What the mouse is over is drawn
  lighter. A dimension held against the least a side may be is drawn red
  and says so.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: DiskWidget

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """
    The 'paint' method paints the background in 'rect', then the disk,
    its supports, its loads, its dimensions and the handles of what is
    selected.
    """
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    disk = widget.disk
    if disk is None:
      return rect
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    box = widget.diskRect()
    painter.fillRect(box, widget.diskColor.fillBrush)
    painter.setPen(self._partColor(GripNum.DISK, -1, widget.edgeColor).Q)
    painter.setBrush(self.emptyBrush)
    painter.drawRect(box)
    model = widget.strutTie
    if model.applicable:
      self._paintStruts(painter, model)
      self._paintTie(painter, model)
    for index, rebar in enumerate(disk.rebars):
      color = self._partColor(GripNum.REBAR, index, widget.steelColor)
      self._paintRebar(painter, rebar, color)
    for index, support in enumerate(disk.supports):
      color = self._partColor(GripNum.SUPPORT, index, widget.supportColor)
      self._paintSupport(painter, support, color)
    levels = {}  # how many load labels each edge holds so far
    for index, load in enumerate(disk.loads):
      level = levels.get(load.edge, 0)
      color = self._partColor(GripNum.LOAD, index, widget.loadColor)
      self._paintLoad(painter, load, level, color)
      levels[load.edge] = level + 1
    self._paintDimensions(painter, disk, box)
    self._paintHandles(painter)
    self._paintVerdict(painter, model)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # \___________
  #  Emphasis  ]
  # /¨¨¨¨¨¨¨¨¨¨¨

  def _partColor(self, kind: GripNum, index: int, color: Color) -> Color:
    """The colour of a part: the accent colour while it is selected,
    lighter while the mouse is over it, else 'color'."""
    widget, selection = self.widget, self.widget.selection
    if selection.kind is kind and selection.index == index:
      return widget.accentColor
    hover = widget.hoverGrip
    if widget.dragGrip is None and hover is not None:
      if hover.kind is kind and hover.index == index:
        return widget.hoverColor
    return color

  def _atWall(self, kinds: tuple) -> bool:
    """Whether a drag of one of 'kinds' holds the disk at the least a
    side may be."""
    grip = self.widget.dragGrip
    if grip is None or grip.kind not in kinds:
      return False
    return True if self.widget.atWall else False

  # \_____________________
  #  Struts, ties, bars  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _paintStruts(self, painter: WPainter, model: StrutTie) -> None:
    """Each strut as a band as wide as it needs to be at nu fc, its
    force beside it, and the nodes where the members meet."""
    widget, scale = self.widget, self.widget.diskScale()
    color = widget.strutColor
    fill, edge = QColor(color.Q), QColor(color.Q)
    fill.setAlpha(55)
    edge.setAlpha(150)
    for member in model.members:
      if member.kind != 'strut':
        continue
      start = widget.toScreen(*member.start)
      end = widget.toScreen(*member.end)
      side = unit(end - start)
      normal = QPointF(-side.y(), side.x())
      half = max(member.width * scale, 3.0) / 2
      band = QPolygonF(
          [
            start + normal * half, end + normal * half,
            end - normal * half, start - normal * half
          ]
          )
      painter.setPen(edge)
      painter.setBrush(fill)
      painter.drawPolygon(band)
      middle = (start + end) * 0.5
      inward = widget.diskRect().center() - middle
      if dot(normal, inward) < 0:
        normal = normal * -1.0
      label = 'C = %s kN' % _magnitude(member.force)
      metrics = widget.font.metrics
      reach = half + 6.0 + abs(normal.x()) * metrics.horizontalAdvance(
          label
      ) / 2 + abs(normal.y()) * metrics.height() / 2
      self._paintText(painter, middle + normal * reach, label, color)
    painter.setPen(self.emptyPen)
    painter.setBrush(widget.textColor.fillBrush)
    for node in model.nodes:
      painter.drawEllipse(widget.toScreen(*node), 3.0, 3.0)

  def _paintTie(self, painter: WPainter, model: StrutTie) -> None:
    """The tie, its force above it; dashed red where nothing makes it."""
    widget = self.widget
    tie = [member for member in model.members if member.kind == 'tie'][0]
    start, end = widget.toScreen(*tie.start), widget.toScreen(*tie.end)
    missing = True if model.tieCapacity <= 0 else False
    color = widget.loadColor if missing else widget.tieColor
    if missing:
      pen = QPen(color.Q, 2.5)
      pen.setStyle(Qt.PenStyle.DashLine)
    else:
      band = QColor(color.Q)
      band.setAlpha(110)
      pen = QPen(band, 7.0)
      pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(start, end)
    label = 'tie needed' if missing else 'T = %s kN' % _magnitude(tie.force)
    middle = (start + end) * 0.5 - QPointF(0.0, 12.0)
    self._paintText(painter, middle, label, color)

  def _paintRebar(
      self, painter: WPainter, rebar: Rebar,
      color: Color
      ) -> None:
    """The bars as a line, named at their start."""
    widget = self.widget
    start = widget.toScreen(*rebar.start)
    end = widget.toScreen(*rebar.end)
    pen = QPen(color.Q, 3.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(start, end)
    place = start + (end - start) * 0.25 + QPointF(0.0, -12.0)
    self._paintText(painter, place, rebar.name, color)

  def _paintVerdict(self, painter: WPainter, model: StrutTie) -> None:
    """What the tied arch carries, top left: green where it carries the
    loads, red where it does not."""
    widget = self.widget
    color = widget.textColor
    if model.applicable:
      color = widget.tieColor if model.factor >= 1 else widget.loadColor
    box = QRectF(12.0, 8.0, widget.width() - 24.0, 20.0)
    painter.setFont(widget.font)
    painter.setPen(color.Q)
    painter.drawText(box, _LEFT, widget.verdict())

  # \___________
  #  Supports  ]
  # /¨¨¨¨¨¨¨¨¨¨¨

  def _paintSupport(
      self, painter: WPainter, support: Support,
      color: Color
      ) -> None:
    """A bearing plate on the stretch, its triangle beyond, and the
    rollers or the hatched ground it stands on."""
    start, end, out = self.widget.stretchOnScreen(support)
    side = unit(end - start)
    plate = QPolygonF(
        [
          start, end, end + out * PLATE,
          start + out * PLATE
        ]
        )
    painter.setPen(self.emptyPen)
    painter.setBrush(color.fillBrush)
    painter.drawPolygon(plate)
    apex = (start + end) * 0.5 + out * PLATE
    base = apex + out * TRIANGLE
    triangle = QPolygonF(
        [
          apex, base + side * HALF_BASE,
          base - side * HALF_BASE
        ]
        )
    painter.setPen(color.solidPen)
    painter.setBrush(self.emptyBrush)
    painter.drawPolygon(triangle)
    both = True if support.setsX and support.setsY else False
    ground = base if both else self._paintRollers(painter, base, out, side)
    reach = side * (HALF_BASE + 4.0)
    painter.drawLine(ground - reach, ground + reach)
    if both:
      self._paintHatch(painter, ground - reach, ground + reach, out, side)

  def _paintRollers(
      self, painter: WPainter, base: QPointF, out: QPointF,
      side: QPointF
      ) -> QPointF:
    """Two rollers under the triangle; returns where the ground is."""
    for offset in (-HALF_BASE / 2, HALF_BASE / 2):
      center = base + side * offset + out * ROLLER
      painter.drawEllipse(center, ROLLER, ROLLER)
    return base + out * (2 * ROLLER)

  def _paintHatch(
      self, painter: WPainter, left: QPointF, right: QPointF,
      out: QPointF, side: QPointF
      ) -> None:
    """Short strokes beyond the ground line, as on fixed ground."""
    count = 5
    for index in range(count):
      start = left + (right - left) * (index / (count - 1))
      painter.drawLine(start, start + (out - side) * HATCH)

  # \________
  #  Loads  ]
  # /¨¨¨¨¨¨¨¨

  def _paintLoad(
      self, painter: WPainter, load: Load, level: int,
      color: Color
      ) -> None:
    """Arrows onto the stretch along the force, and its label beyond
    them, stacked out past the labels of the loads before it on the same
    edge by 'level' lines."""
    magnitude = math.hypot(load.fx, load.fy)
    if not magnitude:
      return
    start, end, out = self.widget.stretchOnScreen(load)
    along = QPointF(load.fx / magnitude, -load.fy / magnitude)
    span = end - start
    count = max(1, round(math.hypot(span.x(), span.y()) / _ARROW_GAP))
    pushes = True if dot(along, out) < 0 else False
    tails = []
    for index in range(count):
      onEdge = start + span * ((index + 0.5) / count)
      if pushes:
        tip, tail = onEdge, onEdge - along * _ARROW
      else:
        tail = onEdge + out * (_HEAD + 2.0)
        tip = tail + along * _ARROW
      self._paintArrow(painter, tail, tip, along, color)
      tails.append(tail if pushes else tip)
    if count > 1:
      painter.setPen(color.solidPen)
      painter.drawLine(tails[0], tails[-1])
      qx, qy = load.intensity
      label = 'q = %s kN/m' % _magnitude(math.hypot(qx, qy))
    else:
      label = 'F = %s kN' % _magnitude(magnitude)
    lineHeight = self.widget.font.metrics.height() + 2.0
    anchor = (tails[0] + tails[-1]) * 0.5 + out * (level * lineHeight)
    self._paintLabel(painter, anchor, out, label, color)

  def _paintArrow(
      self, painter: WPainter, tail: QPointF, tip: QPointF,
      along: QPointF, color: Color
      ) -> None:
    """A line from 'tail' to 'tip' with a filled head at 'tip'."""
    painter.setPen(color.solidPen)
    painter.drawLine(tail, tip)
    back = along * -_HEAD
    normal = QPointF(-along.y(), along.x()) * (_HEAD / 2)
    head = QPolygonF([tip, tip + back + normal, tip + back - normal])
    painter.setBrush(color.fillBrush)
    painter.drawPolygon(head)

  # \______________________
  #  Dimensions, handles  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _paintDimensions(
      self, painter: WPainter, disk: Disk,
      box: QRectF
      ) -> None:
    """The length below the disk and the height left of it, each on a
    dimension line with ticks at its ends."""
    widget = self.widget
    kinds = (GripNum.LENGTH, GripNum.CORNER)
    color = widget.loadColor if self._atWall(kinds) else widget.textColor
    painter.setPen(color.solidPen)
    below = box.bottom() + _DIMENSION
    left, right = QPointF(box.left(), below), QPointF(box.right(), below)
    self._paintDimensionLine(painter, left, right)
    length = self._sideText(disk.length, disk.leastSide, kinds)
    self._paintText(
      painter, QPointF(box.center().x(), below + 12.0),
      length, color
      )
    kinds = (GripNum.HEIGHT, GripNum.CORNER)
    color = widget.loadColor if self._atWall(kinds) else widget.textColor
    painter.setPen(color.solidPen)
    beside = box.left() - _DIMENSION
    bottom = QPointF(beside, box.bottom())
    top = QPointF(beside, box.top())
    self._paintDimensionLine(painter, bottom, top)
    height = self._sideText(disk.height, disk.leastSide, kinds)
    painter.save()
    painter.translate(beside - 12.0, box.center().y())
    painter.rotate(-90.0)
    self._paintText(painter, QPointF(0.0, 0.0), height, color)
    painter.restore()

  def _sideText(self, side: float, least: float, kinds: tuple) -> str:
    """A side as its dimension reads: '6 m', or '1.2 m = 4 t' when a
    drag holds it at the least it may be."""
    text = '%s m' % formatNumber(side)
    if self._atWall(kinds) and abs(side - least) < 1e-9:
      return '%s = 4 t' % text
    return text

  def _paintDimensionLine(
      self, painter: WPainter, start: QPointF,
      end: QPointF
      ) -> None:
    """A thin line with a slanted tick at each end."""
    painter.drawLine(start, end)
    tick = QPointF(4.0, -4.0)
    for point in (start, end):
      painter.drawLine(point - tick, point + tick)

  def _paintHandles(self, painter: WPainter) -> None:
    """The handles of what is selected: the disk's, or a support's at the
    ends of its plate; the one the mouse is on lighter."""
    widget, kind = self.widget, self.widget.selection.kind
    if kind is GripNum.DISK:
      kinds, places = _RESIZING, widget.handlePoint
    elif kind is GripNum.SUPPORT:
      kinds, places = _ENDS, widget.supportEndPoint
    else:
      return
    grip = widget.hoverGrip if widget.dragGrip is None else widget.dragGrip
    for handle in kinds:
      held = True if grip is not None and grip.kind is handle else False
      square = QRectF(0.0, 0.0, HANDLE, HANDLE)
      square.moveCenter(places(handle))
      painter.setPen(widget.accentColor.solidPen)
      fill = widget.accentColor if held else widget.paddingsColor
      painter.setBrush(fill.fillBrush)
      painter.drawRect(square)

  # \_________
  #  Labels  ]
  # /¨¨¨¨¨¨¨¨¨

  def _paintLabel(
      self, painter: WPainter, anchor: QPointF, out: QPointF,
      text: str, color: Color
      ) -> None:
    """'text' wholly beyond 'anchor' along 'out', clear of what ends
    there, reading along the edge: turned upright beside the left and
    the right."""
    reach = self.widget.font.metrics.height() / 2 + 4.0
    center = anchor + out * reach
    if abs(out.y()) > abs(out.x()):
      return self._paintText(painter, center, text, color)
    painter.save()
    painter.translate(center)
    painter.rotate(-90.0)
    self._paintText(painter, QPointF(0.0, 0.0), text, color)
    painter.restore()

  def _paintText(
      self, painter: WPainter, center: QPointF, text: str,
      color: Color
      ) -> None:
    """'text' centred on 'center', in the widget's font and 'color'."""
    font = self.widget.font
    width = font.metrics.horizontalAdvance(text) + 4.0
    height = font.metrics.height()
    box = QRectF(
      center.x() - width / 2, center.y() - height / 2,
      width, height
      )
    painter.setFont(font)
    painter.setPen(color.Q)
    painter.drawText(box, _CENTER, text)
