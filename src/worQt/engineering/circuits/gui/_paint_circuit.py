"""
PaintCircuit subclasses 'AbstractPaintOp' and paints a 'CircuitView':
an electric circuit running, its parts as their symbols.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen
from PySide6.QtGui import QPolygonF, QRadialGradient

from ....paint_ops import AbstractPaintOp
from .. import Ammeter, Bit, BusIn, BusProbe, Capacitor, Chip, Clock
from .. import Coil, Diode, Lamp, Led, Probe, Resistor, Source, Switch
from .. import Transistor, Voltmeter, Wire
from .._si import microfarads, si

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from ._circuit_view import CircuitView

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_CENTER = Qt.AlignmentFlag.AlignCenter
_ACCENT = QColor(229, 192, 123)
_HOVER = QColor(220, 222, 228)
_BODY = QColor(190, 194, 202)
_NAME = QColor(140, 144, 152)
_GRID = QColor(48, 50, 55)
_DOT = QColor(255, 214, 102)
_GLOW = (255, 214, 102)
_RED = (255, 72, 60)
_TROUBLE = QColor(224, 108, 117)
#  The voltage colours: nought, above nought and below
_NOUGHT = (128, 132, 140)
_PLUS = (232, 98, 86)
_MINUS = (86, 150, 238)
_BODY_LENGTH = 36.0  # pixels a symbol takes along its part
_THIN, _THICK = 2.5, 5.0  # pixels: a wire's pen, a bus's


def portOf(spec: object, bit: int) -> int:
  """The 'portOf' function returns the port the bit of 'bit' of a chip
  of 'spec' is in, -1 for none."""
  if bit < 0:
    return -1
  for port, (_, width) in enumerate((*spec.ins, *spec.outs)):
    if bit < width:
      return port
    bit -= width
  return -1


class PaintCircuit(AbstractPaintOp):
  """
  PaintCircuit subclasses 'AbstractPaintOp' and paints a 'CircuitView',
  back to front: a dot at each point of the grid; each part, its leads
  coloured by the voltage of their nodes and its symbol between, as
  drawn at school: a wire a line, a source long and short plates, the
  long its plus pole, or a circle with a wave if it alternates, a
  resistor a box, a lamp a crossed circle glowing, a capacitor two
  plates, a coil its turns, a switch its lever, closed or open, a meter
  a circle with its letter, a diode a triangle to a bar, a light
  emitting diode with arrows, glowing red, a transistor a circle with
  its base bar, the arrow on its emitter; the dots of the current; the
  nodes, larger where three parts or more meet; each part's name, value
  and a meter's reading; and in the corner what the colours mean, or
  why the circuit cannot be reckoned. What is selected is accented,
  what is under the mouse lit.
  """

  #  Annotations
  widget: CircuitView

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the circuit, back to front."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setFont(widget.font)
    self._paintGrid(painter)
    for index in range(len(widget.circuit.parts)):
      self._paintPart(painter, index)
    for index in range(2 * len(widget.circuit.parts)):
      self._paintDots(painter, index)
    self._paintNodes(painter)
    for index in range(len(widget.circuit.parts)):
      self._paintLabel(painter, index)
    self._paintCaption(painter)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def voltageColor(self, voltage: float) -> QColor:
    """The 'voltageColor' method returns the colour of 'voltage': grey
    at nought, red above, blue below, fully at the greatest source's
    voltage."""
    share = voltage / self.widget.voltageScale()
    share = min(max(share, -1.0), 1.0)
    far = _PLUS if share > 0 else _MINUS
    share = abs(share)
    return QColor(*[int(round(a + (b - a) * share))
                    for a, b in zip(_NOUGHT, far)])

  def _ends(self, index: int) -> tuple[QColor, QColor]:
    """The colours of the voltages at the first and second nodes of the
    part of 'index'."""
    widget = self.widget
    part = widget.circuit.parts[index]
    voltages = widget.run.voltages
    return (self.voltageColor(voltages[part.first]),
            self.voltageColor(voltages[part.second]))

  def _bodyColor(self, index: int) -> QColor:
    """The colour of the symbol of the part of 'index': accented if
    selected, lit under the mouse, red if it is the trouble."""
    widget = self.widget
    part = ('part', index)
    if widget.run.problemPart == index:
      return _TROUBLE
    if part in widget.selection:
      return _ACCENT
    if part == widget.hovered:
      return _HOVER
    return _BODY

  def _paintGrid(self, painter: WPainter) -> None:
    """A dot at each point of the grid."""
    widget = self.widget
    left, top = widget.toGrid(QPointF(0.0, 0.0))
    right, bottom = widget.toGrid(QPointF(widget.width(), widget.height()))
    painter.setPen(QPen(_GRID, 2.0))
    for x in range(math.floor(left), math.ceil(right) + 1):
      for y in range(math.floor(bottom), math.ceil(top) + 1):
        painter.drawPoint(widget.toScreen(float(x), float(y)))

  def _bodyLength(self, index: int) -> float:
    """How long the symbol of the part of 'index' is, in pixels: its
    own, or less on a short line."""
    _, _, _, long = self.widget.bodyOf(index)
    return min(_BODY_LENGTH, max(long - 10.0, 12.0))

  def _paintPart(self, painter: WPainter, index: int) -> None:
    """The part of 'index': its leads in the colours of their nodes, and
    its symbol between; a chip its box."""
    widget = self.widget
    if isinstance(widget.circuit.parts[index], Chip):
      return self._paintChip(painter, index)
    path = widget.pathOf(index)
    middle, ux, uy, _ = widget.bodyOf(index)
    half = self._bodyLength(index) / 2
    first, second = self._ends(index)
    start = QPointF(middle.x() - ux * half, middle.y() - uy * half)
    end = QPointF(middle.x() + ux * half, middle.y() + uy * half)
    part = widget.circuit.parts[index]
    bus = widget.isBus(part.first) or widget.isBus(part.second)
    pen = QPen(first, _THICK if bus else _THIN)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    halfway = len(path) // 2
    painter.drawPolyline(QPolygonF([*path[:halfway], start]))
    pen.setColor(second)
    painter.setPen(pen)
    painter.drawPolyline(QPolygonF([end, *path[halfway:]]))
    lead = widget.baseLead(index)
    if lead is not None:
      part = widget.circuit.parts[index]
      pen.setColor(self.voltageColor(widget.run.voltages[part.base]))
      painter.setPen(pen)
      painter.drawLine(QLineF(*lead))
    painter.save()
    painter.translate(middle)
    painter.rotate(math.degrees(math.atan2(uy, ux)))
    self._paintSymbol(painter, index, half)
    painter.restore()

  def _gradientPen(self, index: int, half: float, width: float) -> QPen:
    """A pen of the colour of the part's first node at its symbol's
    start, of its second's at its end."""
    first, second = self._ends(index)
    gradient = QLinearGradient(QPointF(-half, 0.0), QPointF(half, 0.0))
    gradient.setColorAt(0.0, first)
    gradient.setColorAt(1.0, second)
    pen = QPen(QBrush(gradient), width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pen

  def _paintSymbol(self, painter: WPainter, index: int,
                   half: float) -> None:
    """The symbol of the part of 'index', along x from '-half' to 'half'
    about nought, its first node to the left."""
    widget = self.widget
    part = widget.circuit.parts[index]
    first, second = self._ends(index)
    body = self._bodyColor(index)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if isinstance(part, (Wire, Ammeter)) or (isinstance(part, Switch)
                                             and part.closed):
      wide = _THICK if self.widget.isBus(part.first) else _THIN
      painter.setPen(self._gradientPen(index, half, wide))
      painter.drawLine(QLineF(-half, 0.0, half, 0.0))
    if isinstance(part, Wire):
      if body is not _BODY:
        painter.setPen(QPen(body, 1.2))
        painter.drawLine(QLineF(-half, -5.0, half, -5.0))
        painter.drawLine(QLineF(-half, 5.0, half, 5.0))
      return
    if isinstance(part, Resistor):
      return self._paintResistor(painter, index, half, body)
    if isinstance(part, Lamp):
      return self._paintLamp(painter, index, half, body)
    if isinstance(part, Capacitor):
      return self._paintCapacitor(painter, half, body, first, second)
    if isinstance(part, Coil):
      return self._paintCoil(painter, index, half, body)
    if isinstance(part, Switch):
      return self._paintSwitch(painter, index, half, body, first, second)
    if isinstance(part, Source):
      return self._paintSource(painter, index, half, body, first, second)
    if isinstance(part, (Diode, Led)):
      return self._paintDiode(painter, index, half, body)
    if isinstance(part, Transistor):
      return self._paintTransistor(painter, index, half, body)
    if isinstance(part, (Bit, Clock, BusIn, BusProbe)):
      return self._paintLogicSource(painter, index, half, body, first,
                                    second)
    self._paintMeter(painter, index, half, body, first, second)

  def _paintLogicSource(self, painter: WPainter, index: int, half: float,
                        body: QColor, first: QColor,
                        second: QColor) -> None:
    """A logic input or a clock: a box, a plus by its first lead, its
    level written upright over a bit after, a clock's ticks drawn in
    it."""
    size = min(11.0, half)
    self._leads(painter, half, size, first, second)
    painter.setPen(QPen(body, 2.0))
    painter.setBrush(QBrush(self.widget.paddingsColor.Q))
    painter.drawRect(QRectF(-size, -size, 2 * size, 2 * size))
    self._plus(painter, QPointF(-size - 6.0, -9.0), _BODY)
    if isinstance(self.widget.circuit.parts[index], Clock):
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawPolyline(QPolygonF([
        QPointF(-7.0, 4.0), QPointF(-7.0, -4.0), QPointF(0.0, -4.0),
        QPointF(0.0, 4.0), QPointF(7.0, 4.0), QPointF(7.0, -4.0)]))

  def _paintChip(self, painter: WPainter, index: int) -> None:
    """A chip: its leads in the colours of their nodes, its box, as the
    IEC draws it, its symbol at the top, a ring at each inverted output,
    a wedge at a clock input, and its pins' names where it has more than
    a gate's."""
    widget = self.widget
    part = widget.circuit.parts[index]
    spec = part.spec
    voltages = widget.run.voltages
    pen = QPen(_BODY, 2.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    for node, (start, end) in zip(part.pins, widget.chipLeads(index)):
      pen.setColor(self.voltageColor(voltages[node]))
      pen.setWidthF(_THICK if widget.isBus(node) else _THIN)
      painter.setPen(pen)
      painter.drawLine(QLineF(start, end))
    box = widget.chipBox(index)
    body = self._bodyColor(index)
    painter.setPen(QPen(body, 2.0))
    painter.setBrush(QBrush(widget.paddingsColor.Q))
    painter.drawRect(box)
    count = len(spec.ins)
    if spec.inverted:
      for pin in range(count, len(part.pins)):
        at = widget.chipPin(index, pin)
        painter.drawEllipse(QPointF(at.x() + 4.0, at.y()), 4.0, 4.0)
    clock = portOf(spec, spec.clock)
    if clock >= 0:
      at = widget.chipPin(index, clock)
      painter.drawPolyline(QPolygonF([
        QPointF(at.x(), at.y() - 5.0), QPointF(at.x() + 7.0, at.y()),
        QPointF(at.x(), at.y() + 5.0)]))
    painter.setFont(widget.readingFont)
    painter.setPen(body)
    named = widget.chipNamed(index)
    top = box.top() + 2.0 if named else box.top()
    tall = 18.0 if named else box.height()
    painter.drawText(QRectF(box.left(), top, box.width(), tall), _CENTER,
                     spec.symbol)
    if not named:
      return
    painter.setFont(widget.font)
    painter.setPen(_NAME)
    names = [name for name, _ in (*spec.ins, *spec.outs)]
    for pin, name in enumerate(names):
      at = widget.chipPin(index, pin)
      inside = 9.0 if pin == clock else 4.0
      if pin < count:
        area = QRectF(at.x() + inside, at.y() - 8.0, 30.0, 16.0)
        painter.drawText(area, _LEFT, name)
      else:
        area = QRectF(at.x() - 34.0, at.y() - 8.0, 30.0, 16.0)
        painter.drawText(area, _RIGHT, name)

  def _paintDiode(self, painter: WPainter, index: int, half: float,
                  body: QColor) -> None:
    """A diode: a triangle pointing the way it lets current through, to
    a bar; a light emitting diode with two arrows out, glowing red as
    much as its current is of what it is made for."""
    widget = self.widget
    part = widget.circuit.parts[index]
    first, second = self._ends(index)
    size = min(7.0, half)
    self._leads(painter, half, size, first, second)
    if isinstance(part, Led):
      share = min(max(widget.run.currents[index] / part.current, 0.0), 1.5)
      if share > 0.005:
        reach = 10.0 + 18.0 * min(share, 1.0)
        glow = QRadialGradient(QPointF(0.0, 0.0), reach)
        glow.setColorAt(0.0, QColor(*_RED, int(round(230 * min(share,
                                                                1.0)))))
        glow.setColorAt(1.0, QColor(*_RED, 0))
        painter.setPen(self.emptyPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QPointF(0.0, 0.0), reach, reach)
      painter.setPen(QPen(body, 1.4))
      for x in (-3.0, 3.0):
        painter.drawLine(QLineF(x, -10.0, x + 5.0, -16.0))
        painter.drawLine(QLineF(x + 5.0, -16.0, x + 1.5, -15.5))
        painter.drawLine(QLineF(x + 5.0, -16.0, x + 4.5, -12.5))
    painter.setPen(self._gradientPen(index, size, 2.0) if body is _BODY
                   else QPen(body, 2.0))
    painter.setBrush(QBrush(widget.paddingsColor.Q))
    painter.drawPolygon(QPolygonF([QPointF(-size, -size),
                                   QPointF(-size, size),
                                   QPointF(size, 0.0)]))
    painter.drawLine(QLineF(size, -size, size, size))

  def _paintTransistor(self, painter: WPainter, index: int, half: float,
                       body: QColor) -> None:
    """A transistor: a circle, the base bar on the side of its base,
    the collector and the emitter slanting off it to their leads, an
    arrow on the emitter pointing out, as an NPN's does."""
    widget = self.widget
    part = widget.circuit.parts[index]
    first, second = self._ends(index)
    side = widget.baseSide(index)
    reach = min(10.0, half)
    self._leads(painter, half, reach, first, second)
    painter.setPen(QPen(body, 2.0))
    painter.setBrush(QBrush(widget.paddingsColor.Q))
    painter.drawEllipse(QPointF(0.0, 4.0 * side), 14.0, 14.0)
    base = self.voltageColor(widget.run.voltages[part.base])
    painter.setPen(QPen(base, 2.5))
    painter.drawLine(QLineF(0.0, 9.0 * side, 0.0, 18.0 * side))
    bar = QPen(body, 3.0)
    bar.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(bar)
    painter.drawLine(QLineF(-7.0, 9.0 * side, 7.0, 9.0 * side))
    painter.setPen(QPen(first, 2.0))
    painter.drawLine(QLineF(-reach, 0.0, -4.0, 9.0 * side))
    painter.setPen(QPen(second, 2.0))
    painter.drawLine(QLineF(4.0, 9.0 * side, reach, 0.0))
    tip = QPointF(reach - 1.0, 1.5 * side)
    painter.setPen(self.emptyPen)
    painter.setBrush(QBrush(body))
    painter.drawPolygon(QPolygonF([
      tip, QPointF(tip.x() - 7.0, tip.y() + 1.0 * side),
      QPointF(tip.x() - 3.5, tip.y() + 6.0 * side)]))

  def _leads(self, painter: WPainter, half: float, inner: float,
             first: QColor, second: QColor) -> None:
    """The leads within the symbol, from its ends to 'inner' either side
    of nought, in the colours of the part's nodes."""
    painter.setPen(QPen(first, 2.5))
    painter.drawLine(QLineF(-half, 0.0, -inner, 0.0))
    painter.setPen(QPen(second, 2.5))
    painter.drawLine(QLineF(inner, 0.0, half, 0.0))

  def _paintResistor(self, painter: WPainter, index: int, half: float,
                     body: QColor) -> None:
    """A resistor: a box, its outline coloured from one node's voltage
    to the other's, the drop across it."""
    widget = self.widget
    box = QRectF(-half, -6.0, 2 * half, 12.0)
    painter.setBrush(QBrush(widget.paddingsColor.Q))
    painter.setPen(self._gradientPen(index, half, 2.2))
    painter.drawRect(box)
    if body is not _BODY:
      painter.setPen(QPen(body, 1.2))
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawRect(box.adjusted(-3.0, -3.0, 3.0, 3.0))

  def _paintLamp(self, painter: WPainter, index: int, half: float,
                 body: QColor) -> None:
    """A lamp: a crossed circle, glowing as much as the power it takes
    is of the power it is made for."""
    widget = self.widget
    part = widget.circuit.parts[index]
    first, second = self._ends(index)
    radius = min(11.0, half)
    self._leads(painter, half, radius, first, second)
    current = widget.run.currents[index]
    share = min(current * current * part.resistance / part.power, 1.5)
    if share > 0.005:
      reach = radius + 6.0 + 18.0 * min(share, 1.0)
      glow = QRadialGradient(QPointF(0.0, 0.0), reach)
      strength = int(round(220 * min(share, 1.0)))
      glow.setColorAt(0.0, QColor(*_GLOW, strength))
      glow.setColorAt(1.0, QColor(*_GLOW, 0))
      painter.setPen(self.emptyPen)
      painter.setBrush(QBrush(glow))
      painter.drawEllipse(QPointF(0.0, 0.0), reach, reach)
    fill = QColor(*_GLOW, int(round(160 * min(share, 1.0))))
    painter.setBrush(QBrush(fill) if share > 0.005 else QBrush(
      widget.paddingsColor.Q))
    painter.setPen(QPen(body, 2.0))
    painter.drawEllipse(QPointF(0.0, 0.0), radius, radius)
    cross = radius * 0.7071
    painter.drawLine(QLineF(-cross, -cross, cross, cross))
    painter.drawLine(QLineF(-cross, cross, cross, -cross))

  def _paintCapacitor(self, painter: WPainter, half: float, body: QColor,
                      first: QColor, second: QColor) -> None:
    """A capacitor: two plates across, each of its node's colour."""
    gap = 4.0
    self._leads(painter, half, gap, first, second)
    for x, color in ((-gap, first), (gap, second)):
      pen = QPen(color if body is _BODY else body, 3.0)
      pen.setCapStyle(Qt.PenCapStyle.FlatCap)
      painter.setPen(pen)
      painter.drawLine(QLineF(x, -12.0, x, 12.0))

  def _paintCoil(self, painter: WPainter, index: int, half: float,
                 body: QColor) -> None:
    """A coil: four turns, coloured from one node's voltage to the
    other's."""
    turns = 4
    width = 2 * half / turns
    pen = self._gradientPen(index, half, 2.2)
    if body is not _BODY:
      pen = QPen(body, 2.2)
    painter.setPen(pen)
    for k in range(turns):
      box = QRectF(-half + k * width, -width / 2 - 2.0, width,
                   width + 4.0)
      painter.drawArc(box, 0, 180 * 16)

  def _paintSwitch(self, painter: WPainter, index: int, half: float,
                   body: QColor, first: QColor, second: QColor) -> None:
    """A switch: its two contacts and its lever, across them closed, up
    and away open."""
    part = self.widget.circuit.parts[index]
    reach = min(13.0, half)
    self._leads(painter, half, reach, first, second)
    if not part.closed:
      lever = QPen(body, 2.5)
      lever.setCapStyle(Qt.PenCapStyle.RoundCap)
      painter.setPen(lever)
      angle = math.radians(-30.0)
      long = 2 * reach + 2.0
      painter.drawLine(QLineF(-reach, 0.0,
                              -reach + long * math.cos(angle),
                              long * math.sin(angle)))
    elif body is not _BODY:
      painter.setPen(QPen(body, 1.2))
      painter.drawLine(QLineF(-reach, -5.0, reach, -5.0))
    painter.setPen(QPen(body, 1.6))
    painter.setBrush(QBrush(self.widget.paddingsColor.Q))
    for x in (-reach, reach):
      painter.drawEllipse(QPointF(x, 0.0), 2.6, 2.6)

  def _plus(self, painter: WPainter, at: QPointF, color: QColor) -> None:
    """A little plus at 'at'."""
    painter.setPen(QPen(color, 1.4))
    painter.drawLine(QLineF(at.x() - 3.0, at.y(), at.x() + 3.0, at.y()))
    painter.drawLine(QLineF(at.x(), at.y() - 3.0, at.x(), at.y() + 3.0))

  def _paintSource(self, painter: WPainter, index: int, half: float,
                   body: QColor, first: QColor, second: QColor) -> None:
    """A source: steady, a long plate, its plus pole, and a short thick
    one, its minus; alternating, a circle with a wave in it."""
    part = self.widget.circuit.parts[index]
    if part.frequency > 0:
      return self._paintCircle(painter, half, body, first, second, 'wave')
    gap = 3.5
    self._leads(painter, half, gap, first, second)
    pen = QPen(body if body is not _BODY else first, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.drawLine(QLineF(-gap, -13.0, -gap, 13.0))
    pen = QPen(body if body is not _BODY else second, 5.0)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.drawLine(QLineF(gap, -7.0, gap, 7.0))
    self._plus(painter, QPointF(-gap - 8.0, -11.0), _BODY)

  def _paintMeter(self, painter: WPainter, index: int, half: float,
                  body: QColor, first: QColor, second: QColor) -> None:
    """A meter: a circle, its letter written upright over it after."""
    self._paintCircle(painter, half, body, first, second, '')

  def _paintCircle(self, painter: WPainter, half: float, body: QColor,
                   first: QColor, second: QColor, inside: str) -> None:
    """A circle across the line, a plus by its first lead, and a wave in
    it for 'wave'."""
    radius = min(12.0, half)
    self._leads(painter, half, radius, first, second)
    painter.setPen(QPen(body, 2.0))
    painter.setBrush(QBrush(self.widget.paddingsColor.Q))
    painter.drawEllipse(QPointF(0.0, 0.0), radius, radius)
    self._plus(painter, QPointF(-radius - 6.0, -9.0), _BODY)
    if inside == 'wave':
      wave = [QPointF(-0.6 * radius + 1.2 * radius * k / 16,
                      -0.35 * radius * math.sin(2 * math.pi * k / 16))
              for k in range(17)]
      painter.setBrush(Qt.BrushStyle.NoBrush)
      painter.drawPolyline(QPolygonF(wave))

  def _paintDots(self, painter: WPainter, index: int) -> None:
    """The dots of the current through the part of 'index', moving along
    it as the current flows, from its first node to its second when it
    is positive; none across a capacitor's gap."""
    widget = self.widget
    if not widget.flowing(index):
      return
    count = len(widget.circuit.parts)
    path = widget.pathOf(index) if index < count else [
      *(widget.baseLead(index - count) or ())]
    if len(path) < 2:
      return
    lengths = [math.hypot(b.x() - a.x(), b.y() - a.y())
               for a, b in zip(path[:-1], path[1:])]
    total = sum(lengths)
    middle = total / 2
    kind = type(widget.circuit.parts[index % count])
    gap = 7.0 if kind is Capacitor and index < count else -1.0
    spacing = widget.__fallback_spacing__
    s = widget.offsets[index] % spacing
    painter.setPen(self.emptyPen)
    painter.setBrush(QBrush(_DOT))
    while s < total:
      if abs(s - middle) > gap:
        painter.drawEllipse(self._along(path, lengths, s), 2.3, 2.3)
      s += spacing

  @staticmethod
  def _along(path: list[QPointF], lengths: list[float],
             s: float) -> QPointF:
    """The point 's' pixels along 'path'."""
    last = len(lengths) - 1
    for k, long in enumerate(lengths):
      if s <= long or k == last:
        a, b = path[k], path[k + 1]
        share = s / long if long > 0 else 0.0
        return QPointF(a.x() + (b.x() - a.x()) * share,
                       a.y() + (b.y() - a.y()) * share)
      s -= long
    return path[-1]

  def _paintNodes(self, painter: WPainter) -> None:
    """The nodes: a square at a fixed one, a ring at a loose end, a small
    dot where two parts meet, a larger where three or more do; the node
    a dragged node would join ringed."""
    widget = self.widget
    circuit = widget.circuit
    voltages = widget.run.voltages
    for index, node in enumerate(circuit.nodes):
      seen = widget.toScreen(*node)
      count = len(circuit.joined(index))
      color = self.voltageColor(voltages[index])
      part = ('node', index)
      if part in widget.selection:
        color = _ACCENT
      elif part == widget.hovered:
        color = _HOVER
      if widget.isLocked(part):
        painter.setPen(QPen(color, 1.6))
        painter.setBrush(QBrush(widget.paddingsColor.Q))
        painter.drawRect(QRectF(seen.x() - 4.0, seen.y() - 4.0, 8.0, 8.0))
      elif count < 2:
        painter.setPen(QPen(color, 2.0))
        painter.setBrush(QBrush(widget.paddingsColor.Q))
        painter.drawEllipse(seen, 4.0, 4.0)
      else:
        painter.setPen(self.emptyPen)
        painter.setBrush(QBrush(color))
        size = 4.5 if count > 2 or color in (_ACCENT, _HOVER) else 2.5
        painter.drawEllipse(seen, size, size)
      if widget.merging == index:
        painter.setPen(QPen(_ACCENT, 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(seen, 10.0, 10.0)

  def valueOf(self, index: int) -> str:
    """The 'valueOf' method returns what the part of 'index' is, in
    words: '4.5 V', '100 Ω', '1000 µF'; a meter what it reads."""
    widget = self.widget
    part = widget.circuit.parts[index]
    if isinstance(part, Source):
      words = si(part.voltage, 'V')
      if part.frequency > 0:
        words += ' ~ %s' % si(part.frequency, 'Hz')
      if part.resistance > 0:
        words += ', %s inside' % si(part.resistance, 'Ω')
      return words
    if isinstance(part, Resistor):
      return si(part.resistance, 'Ω')
    if isinstance(part, Lamp):
      return '%s %s' % (si(part.voltage, 'V'), si(part.power, 'W'))
    if isinstance(part, Capacitor):
      return microfarads(part.capacitance)
    if isinstance(part, Coil):
      return si(part.inductance, 'H')
    if isinstance(part, Ammeter):
      return si(widget.run.currents[index], 'A')
    if isinstance(part, Voltmeter):
      return si(widget.run.drops[index], 'V')
    if isinstance(part, Diode):
      return si(part.voltage, 'V')
    if isinstance(part, Led):
      return '%s %s' % (si(part.voltage, 'V'), si(part.current, 'A'))
    if isinstance(part, Transistor):
      return 'β %g' % part.gain
    if isinstance(part, Clock):
      return si(part.frequency, 'Hz')
    if isinstance(part, Chip):
      return part.kind
    return ''

  def _paintLabel(self, painter: WPainter, index: int) -> None:
    """The name of the part of 'index' and its value beside it, a
    meter's letter in it and its reading, larger, beside it; a wire
    unnamed."""
    widget = self.widget
    part = widget.circuit.parts[index]
    if isinstance(part, Wire):
      return
    if isinstance(part, Chip):
      box = widget.chipBox(index)
      painter.setFont(widget.font)
      painter.setPen(_NAME)
      painter.drawText(QRectF(box.left() - 20.0, box.top() - 18.0,
                              box.width() + 40.0, 16.0), _CENTER,
                       '%s %s' % (widget.circuit.label(index), part.kind))
      return
    middle, _, _, _ = widget.bodyOf(index)
    nx, ny = widget.labelSide(index)
    meter = isinstance(part, (Ammeter, Voltmeter))
    if meter:
      painter.setPen(self._bodyColor(index))
      painter.setFont(widget.readingFont)
      painter.drawText(QRectF(middle.x() - 12.0, middle.y() - 10.0, 24.0,
                              20.0), _CENTER, part.letter)
    if isinstance(part, (Bit, Probe, BusIn, BusProbe)):
      self._paintLevel(painter, index, middle)
    name = widget.circuit.label(index)
    value = self.valueOf(index)
    lines = [(name, widget.font, _NAME)]
    if value:
      font = widget.readingFont if meter else widget.font
      lines.append((value, font, _HOVER if meter else _NAME))
    height = 16.0 * len(lines)
    reach = 22.0 if abs(nx) > 0.5 else 18.0 + height / 2
    if isinstance(part, Lamp):
      reach += 12.0
    at = QPointF(middle.x() + nx * reach, middle.y() + ny * reach)
    top = at.y() - height / 2
    for words, font, color in lines:
      painter.setFont(font)
      painter.setPen(color)
      width = font.metrics.horizontalAdvance(words) + 8.0
      left = at.x() - width / 2
      if abs(nx) > 0.5:
        left = at.x() - (width if nx < 0 else 0.0) + (4.0 if nx < 0 else
                                                       -4.0)
      painter.drawText(QRectF(left, top, width, 16.0), _CENTER, words)
      top += 16.0
    painter.setFont(widget.font)

  def _paintLevel(self, painter: WPainter, index: int,
                  middle: QPointF) -> None:
    """A logic input's level, '1' or '0', upright in its box; a probe's
    in a circle lit red when it reads high."""
    widget = self.widget
    part = widget.circuit.parts[index]
    if isinstance(part, BusIn):
      words = str(part.value)
    elif isinstance(part, BusProbe):
      value = widget.run.values[part.first]
      words = '?' if value is None else str(value)
    elif isinstance(part, Bit):
      words = '1' if part.high else '0'
    else:
      high = widget.run.drops[index] > 2.5
      painter.setPen(QPen(self._bodyColor(index), 2.0))
      fill = QColor(*_RED, 200) if high else widget.paddingsColor.Q
      painter.setBrush(QBrush(fill))
      painter.drawEllipse(middle, 11.0, 11.0)
      words = '1' if high else '0'
    painter.setFont(widget.readingFont)
    painter.setPen(_HOVER)
    painter.drawText(QRectF(middle.x() - 12.0, middle.y() - 10.0, 24.0,
                            20.0), _CENTER, words)

  def _paintCaption(self, painter: WPainter) -> None:
    """What the colours and the dots mean, in the corner, or why the
    circuit cannot be reckoned."""
    widget = self.widget
    network = widget.run.network
    box = QRectF(14.0, 10.0, widget.width() - 28.0, 18.0)
    painter.setFont(widget.font)
    if network.problem:
      painter.setPen(_TROUBLE)
      words = 'Short circuit: %s.' % network.problem
      if network.problemPart is None:
        words = 'The circuit cannot be reckoned.'
      painter.drawText(box, _LEFT, words)
      return
    painter.setPen(widget.font.color.Q)
    words = ('Voltage: red above nought, blue below, at %s fully · dots: '
             'the current, from plus to minus' % si(widget.voltageScale(),
                                                    'V'))
    painter.drawText(box, _LEFT, words)
