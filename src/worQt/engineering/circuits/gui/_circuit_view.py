"""
CircuitView subclasses 'PaintedWidget' and shows an electric circuit
running: its parts as their symbols, coloured by voltage, the current
flowing through them as dots.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from .. import Bit, Chip, Circuit, Clock, Node, Run, Source, Transistor
from .._chips import HIGH
from . import PaintCircuit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtCore import QEvent
  from PySide6.QtGui import QKeyEvent, QMouseEvent

Part = tuple[str, int]


def _segmentGap(p: QPointF, a: QPointF, b: QPointF) -> float:
  """How far 'p' is from the segment from 'a' to 'b', in pixels."""
  dx, dy = b.x() - a.x(), b.y() - a.y()
  span = dx * dx + dy * dy
  share = 0.0
  if span > 0:
    share = ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / span
  share = min(max(share, 0.0), 1.0)
  return math.hypot(p.x() - a.x() - share * dx, p.y() - a.y() - share * dy)


class CircuitView(PaintedWidget):
  """
  CircuitView subclasses 'PaintedWidget' and shows a 'circuit' running,
  'run', fitted to the view on its grid: each part as its symbol
  between its nodes, those in parallel a step aside, its wires and
  leads coloured by their voltage, red above nought, blue below, grey
  at nought; the current flowing as dots, moving as fast as it flows;
  each part's name and value beside it, a meter's reading; a lamp
  glowing as much as the power it takes.

  A click selects a node or a part, Ctrl and a click selects more
  besides, a click on nothing selects nothing, emitting
  'selectionChanged'. A node dragged goes where it is dragged, to the
  grid, its parts with it; dropped on another node, it is joined into
  it. Delete removes what is selected, the parts on a node with it;
  each emitting 'circuitEdited'. The view keeps still while a node is
  dragged. A chip is drawn as a box among its pins, its inputs' leads
  to its left, its outputs' to its right; dragged by its box, all its
  pins move with it. The first nodes and parts, as many as 'locked'
  says, are fixed: never dragged nor removed, though a node may be
  dropped on them. A transistor is drawn between its collector and its
  emitter, its base lead from its base node to the symbol, with dots of
  its own.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_room__ = 90.0  # pixels around the circuit for its labels
  __fallback_scales__ = (24.0, 72.0)  # pixels a grid step, least, most
  __fallback_aside__ = 1.5  # grid steps a part in parallel is drawn aside
  __fallback_reach__ = 7.0  # pixels from a thing still picking it
  __fallback_spacing__ = 16.0  # pixels between the dots of a current
  __fallback_pace__ = 60.0  # pixels a second the greatest current moves
  __fallback_memory__ = 2.0  # s the greatest current is half forgotten
  __fallback_chip_width__ = 58.0  # pixels: a chip's box
  __fallback_chip_row__ = 20.0  # pixels: a row of a chip's pins

  #  Private Variables
  __shown_circuit__: Circuit | None = None
  __shown_run__: Run | None = None
  __selected_parts__: tuple[Part, ...] = ()
  __hovered_part__: Part | None = None
  __view_place__: tuple[float, float, float] | None = None
  __drag_node__: int | None = None
  __drag_chip__: tuple[int, int, int] | None = None
  __merge_node__: int | None = None
  __locked_parts__: tuple[int, int] = (0, 0)
  __dot_charges__: tuple[float, ...] | None = None
  __dot_offsets__: list | None = None
  __dot_most__: float = 0.0

  #  Public Variables
  boxModelOp = PaintBoxModel()
  circuitOp = PaintCircuit()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 174, 182),
  )
  readingFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      11,
      Color(220, 222, 228),
  )

  #  Virtual Variables
  circuit: Field[Circuit] = Field()
  run: Field[Run] = Field()
  selection: Field[tuple[Part, ...]] = Field()
  selected: Field[Part] = Field()
  hovered: Field[Part] = Field()
  merging: Field[int] = Field()
  locked: Field[tuple[int, int]] = Field()
  offsets: Field[tuple[float, ...]] = Field()

  #  Signals
  circuitEdited = Signal(object)
  selectionChanged = Signal(object)
  refused = Signal(str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @circuit.GET
  def _getCircuit(self, ) -> Circuit:
    """The 'circuit' getter returns the circuit shown."""
    if self.__shown_circuit__ is None:
      self.__shown_circuit__ = Circuit()
    return self.__shown_circuit__

  @run.GET
  def _getRun(self, ) -> Run:
    """The 'run' getter returns the circuit running, its voltages and
    currents shown."""
    if self.__shown_run__ is None:
      self.__shown_run__ = Run(self.circuit)
    return self.__shown_run__

  @selection.GET
  def _getSelection(self, ) -> tuple[Part, ...]:
    """The 'selection' getter returns the parts selected, the last
    selected last: each ('node', index) or ('part', index)."""
    return self.__selected_parts__

  @selected.GET
  def _getSelected(self, ) -> Part | None:
    """The 'selected' getter returns what was selected last, or
    'None'."""
    return self.__selected_parts__[-1] if self.__selected_parts__ else None

  @hovered.GET
  def _getHovered(self, ) -> Part | None:
    """The 'hovered' getter returns what is under the mouse, or
    'None'."""
    return self.__hovered_part__

  @locked.GET
  def _getLocked(self, ) -> tuple[int, int]:
    """The 'locked' getter returns how many of the first nodes and of the
    first parts are fixed: never dragged nor removed."""
    return self.__locked_parts__

  @merging.GET
  def _getMerging(self, ) -> int | None:
    """The 'merging' getter returns the node the node dragged would be
    joined into, dropped now, or 'None'."""
    return self.__merge_node__

  @offsets.GET
  def _getOffsets(self, ) -> tuple[float, ...]:
    """The 'offsets' getter returns how far along each part its dots
    have moved, in pixels, within a spacing of them, then along each
    transistor's base lead."""
    count = 2 * len(self.circuit.parts)
    return (*(self.__dot_offsets__ or [0.0] * count),)

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @circuit.SET
  def _setCircuit(self, circuit: Circuit) -> None:
    """The 'circuit' setter shows 'circuit', letting go of what is
    selected it has no more; the run is set apart."""
    self.__shown_circuit__ = circuit
    kept = (*[part for part in self.__selected_parts__
              if part[1] < len(self.partsOf(part[0]))],)
    if kept != self.__selected_parts__:
      self._setSelection(kept)
    if self.__drag_node__ is None and self.__drag_chip__ is None:
      self.__view_place__ = None
    self.update()

  @locked.SET
  def _setLocked(self, locked: tuple[int, int]) -> None:
    """The 'locked' setter fixes the first nodes and parts, as many as
    'locked' says."""
    nodes, parts = locked
    self.__locked_parts__ = (int(nodes), int(parts))
    self.update()

  @run.SET
  def _setRun(self, run: Run) -> None:
    """The 'run' setter shows 'run', the dots where they were for the
    parts it shares with the run before."""
    count = 2 * len(run.circuit.parts)
    offsets = self.__dot_offsets__ or []
    if len(offsets) != count:
      self.__dot_offsets__ = [0.0] * count
    self.__dot_charges__ = (*run.charges, *run.baseCharges)
    self.__shown_run__ = run
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(1000, 600)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(400, 300)

  def resizeEvent(self, event) -> None:
    """Fits the circuit to the view anew."""
    PaintedWidget.resizeEvent(self, event)
    self.__view_place__ = None

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """Selects what is under the mouse, Ctrl adding it, taking hold of a
    node to drag it; on nothing, selects nothing."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    part = self.partAt(event.position())
    if part is None:
      return self.select(None)
    if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
      return self.toggle(part)
    self.select(part)
    if part[0] == 'node' and not self.isLocked(part):
      self.__drag_node__ = part[1]
    if part[0] == 'part' and not self.isLocked(part):
      if isinstance(self.circuit.parts[part[1]], Chip):
        x, y = self.toGrid(event.position())
        self.__drag_chip__ = (part[1], round(x), round(y))

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """Drags the node held, or marks what is under the mouse."""
    where = event.position()
    if self.__drag_node__ is not None:
      return self.dragTo(where)
    if self.__drag_chip__ is not None:
      return self.dragChip(where)
    hovered = self.partAt(where)
    if hovered != self.__hovered_part__:
      self.__hovered_part__ = hovered
      self.update()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Lets go of the node dragged, joining it into the node it is on,
    and fits the circuit to the view anew."""
    if self.__drag_chip__ is not None:
      self.__drag_chip__ = None
      self.__view_place__ = None
      return self.update()
    if self.__drag_node__ is None:
      return
    self.drop()

  def leaveEvent(self, event: QEvent) -> None:
    self.__hovered_part__ = None
    self.update()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Delete removes what is selected."""
    if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
      self.removeSelected()
      return
    PaintedWidget.keyPressEvent(self, event)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  @overload.finalize
  def __init__(self, *args) -> None:
    self.setMouseTracking(True)
    self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def partsOf(self, kind: str) -> tuple:
    """The 'partsOf' method returns the circuit's nodes, for 'node', or
    its parts, for 'part'."""
    return self.circuit.nodes if kind == 'node' else self.circuit.parts

  def place(self, ) -> tuple[float, float, float]:
    """The 'place' method returns how the circuit is fitted to the view:
    the pixels to a step of the grid, and where x and y nought are, in
    pixels."""
    if self.__view_place__ is None:
      self.__view_place__ = self._fitted()
    return self.__view_place__

  def toScreen(self, x: float, y: float) -> QPointF:
    """The 'toScreen' method returns the pixel at 'x' and 'y' on the
    grid."""
    scale, left, bottom = self.place()
    return QPointF(left + x * scale, bottom - y * scale)

  def toGrid(self, pixel: QPointF) -> tuple[float, float]:
    """The 'toGrid' method returns where 'pixel' is on the grid."""
    scale, left, bottom = self.place()
    return (pixel.x() - left) / scale, (bottom - pixel.y()) / scale

  def pathOf(self, index: int) -> list[QPointF]:
    """The 'pathOf' method returns the line the part of 'index' is drawn
    along, from its first node to its second: straight, or out a step
    aside, along and back, if it is in parallel with another."""
    circuit = self.circuit
    part = circuit.parts[index]
    a, b = circuit.nodes[part.first], circuit.nodes[part.second]
    start, end = self.toScreen(*a), self.toScreen(*b)
    side = circuit.side(index)
    if not side:
      return [start, end]
    ax, ay = self.asideOf(index)
    reach = side * self.__fallback_aside__ * self.place()[0]
    shift = (ax * reach, ay * reach)
    return [start, QPointF(start.x() + shift[0], start.y() + shift[1]),
            QPointF(end.x() + shift[0], end.y() + shift[1]), end]

  def bodyOf(self, index: int) -> tuple[QPointF, float, float, float]:
    """The 'bodyOf' method returns where the symbol of the part of
    'index' goes: its middle, the way it runs on the screen, a unit
    vector, and how long the line it is on is, in pixels."""
    path = self.pathOf(index)
    a, b = (path[0], path[1]) if len(path) == 2 else (path[1], path[2])
    long = max(math.hypot(b.x() - a.x(), b.y() - a.y()), 1e-9)
    middle = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
    return middle, (b.x() - a.x()) / long, (b.y() - a.y()) / long, long

  def asideOf(self, index: int) -> tuple[float, float]:
    """The 'asideOf' method returns the way the part of 'index' is drawn
    aside if it is in parallel with another, on the screen, a unit
    vector: to the left of the line from its lower node to its
    higher."""
    circuit = self.circuit
    part = circuit.parts[index]
    a, b = circuit.nodes[part.first], circuit.nodes[part.second]
    low, high = (a, b) if part.first < part.second else (b, a)
    long = math.hypot(high.x - low.x, high.y - low.y)
    return -(high.y - low.y) / long, -(high.x - low.x) / long

  def baseSide(self, index: int) -> float:
    """The 'baseSide' method returns the side of the transistor of
    'index' its base is on: 1 to the left of the line from its collector
    to its emitter on the screen, -1 to the right."""
    middle, ux, uy, _ = self.bodyOf(index)
    base = self.toScreen(*self.circuit.nodes[self.circuit.parts[index].base])
    away = (base.x() - middle.x()) * uy - (base.y() - middle.y()) * ux
    return -1.0 if away > 0 else 1.0

  def baseLead(self, index: int) -> tuple[QPointF, QPointF] | None:
    """The 'baseLead' method returns the base lead of the transistor of
    'index', from its base node to where it meets the symbol, or 'None'
    for any other part."""
    if not isinstance(self.circuit.parts[index], Transistor):
      return None
    middle, ux, uy, _ = self.bodyOf(index)
    side = self.baseSide(index)
    reach = 18.0 * side
    meets = QPointF(middle.x() - uy * reach, middle.y() + ux * reach)
    base = self.toScreen(*self.circuit.nodes[self.circuit.parts[index].base])
    return base, meets

  def labelSide(self, index: int) -> tuple[float, float]:
    """The 'labelSide' method returns the side of the part of 'index'
    its name goes on, on the screen, a unit vector: away from a
    transistor's base, else away from the parts in parallel with it,
    else away from the middle of the circuit."""
    circuit = self.circuit
    part = circuit.parts[index]
    if isinstance(part, Chip):
      return 0.0, -1.0
    middle, ux, uy, _ = self.bodyOf(index)
    if isinstance(part, Transistor):
      side = self.baseSide(index)
      return uy * side, -ux * side
    pair = {part.first, part.second}
    others = [circuit.side(i) for i, p in enumerate(circuit.parts)
              if i != index and {p.first, p.second} == pair]
    side = circuit.side(index)
    if others:
      ax, ay = self.asideOf(index)
      if side == 0:
        sign = -1.0 if min(others) > 0 else 1.0
      else:
        sign = 1.0 if side > 0 else -1.0
      return sign * ax, sign * ay
    nodes = circuit.nodes
    centre = self.toScreen(sum(n.x for n in nodes) / len(nodes),
                           sum(n.y for n in nodes) / len(nodes))
    nx, ny = -uy, ux
    away = (middle.x() - centre.x()) * nx + (middle.y() - centre.y()) * ny
    if away < 0 or (abs(away) < 1e-6 and ny > 0):
      return -nx, -ny
    return nx, ny

  def partAt(self, pixel: QPointF) -> Part | None:
    """The 'partAt' method returns what is drawn under 'pixel': a node,
    else a part, or 'None'."""
    reach = self.__fallback_reach__
    for index, node in enumerate(self.circuit.nodes):
      seen = self.toScreen(*node)
      if math.hypot(seen.x() - pixel.x(), seen.y() - pixel.y()) <= reach:
        return 'node', index
    for index in range(len(self.circuit.parts)):
      if isinstance(self.circuit.parts[index], Chip):
        if self.chipBox(index).adjusted(-reach, -reach, reach,
                                        reach).contains(pixel):
          return 'part', index
        pairs = self.chipLeads(index)
      else:
        path = self.pathOf(index)
        lead = self.baseLead(index)
        pairs = [*zip(path[:-1], path[1:])] + ([lead] if lead else [])
      for a, b in pairs:
        if _segmentGap(pixel, a, b) <= reach + 3.0:
          return 'part', index
    return None

  def select(self, part: Part | None) -> None:
    """The 'select' method selects 'part' alone, or nothing for
    'None'."""
    self._setSelection(() if part is None else (part,))

  def toggle(self, part: Part) -> None:
    """The 'toggle' method adds 'part' to what is selected, or takes it
    away if it is among it."""
    parts = [p for p in self.__selected_parts__ if p != part]
    if len(parts) == len(self.__selected_parts__):
      parts.append(part)
    self._setSelection((*parts,))

  def selectedOf(self, kind: str) -> tuple[int, ...]:
    """The 'selectedOf' method returns the nodes, for 'node', or the
    parts, for 'part', selected, in the order selected."""
    return (*[index for k, index in self.selection if k == kind],)

  def isLocked(self, part: Part) -> bool:
    """The 'isLocked' method tells whether 'part', ('node', index) or
    ('part', index), is fixed."""
    nodes, parts = self.locked
    kind, index = part
    return True if index < (nodes if kind == 'node' else parts) else False

  def removeSelected(self, ) -> None:
    """The 'removeSelected' method removes the parts and the nodes
    selected, and the parts on those nodes, emitting 'circuitEdited';
    those fixed stay."""
    free = [part for part in self.selection if not self.isLocked(part)]
    if not free:
      return
    circuit = self.circuit
    for index in sorted(i for k, i in free if k == 'part')[::-1]:
      circuit = circuit.withoutPart(index)
    for index in sorted(i for k, i in free if k == 'node')[::-1]:
      circuit = circuit.withoutNode(index)
    self._setSelection(())
    self.circuit = circuit
    self.circuitEdited.emit(circuit)

  def dragTo(self, pixel: QPointF) -> None:
    """The 'dragTo' method takes the node held to the point of the grid
    under 'pixel', emitting 'circuitEdited'; onto another node, it marks
    that node to join it into when dropped."""
    index = self.__drag_node__
    if index is None:
      return
    x, y = self.toGrid(pixel)
    spot = Node(float(round(x)) + 0.0, float(round(y)) + 0.0)
    circuit = self.circuit
    other = circuit.at(*spot)
    if other is not None and other != index:
      if self.__merge_node__ != other:
        self.__merge_node__ = other
        self.update()
      return
    self.__merge_node__ = None
    if circuit.nodes[index] == spot:
      return self.update()
    moved = circuit.withNode(index, spot)
    self.circuit = moved
    self.circuitEdited.emit(moved)

  def chipBox(self, index: int) -> QRectF:
    """The 'chipBox' method returns the box the chip of 'index' is drawn
    as: about the middle of its pins, as tall as its rows of pins."""
    part = self.circuit.parts[index]
    spec = part.spec
    points = [self.toScreen(*self.circuit.nodes[pin]) for pin in part.pins]
    x = sum(p.x() for p in points) / len(points)
    y = sum(p.y() for p in points) / len(points)
    rows = max(len(spec.ins), len(spec.outs))
    width = self.__fallback_chip_width__
    height = rows * self.__fallback_chip_row__ + 14.0
    if self.chipNamed(index):
      height += 18.0
    return QRectF(x - width / 2, y - height / 2, width, height)

  def isBus(self, node: int) -> bool:
    """The 'isBus' method tells whether the node of 'node' is a bus of
    four bits."""
    return True if self.circuit.widths()[node] > 1 else False

  def chipNamed(self, index: int) -> bool:
    """The 'chipNamed' method tells whether the box of the chip of
    'index' names its pins: any chip more than a gate."""
    spec = self.circuit.parts[index].spec
    pins = len(spec.ins) + len(spec.outs)
    wide = any(width > 1 for width in spec.widths)
    return True if spec.memory or pins > 3 or wide else False

  def chipPin(self, index: int, pin: int) -> QPointF:
    """The 'chipPin' method returns where the lead of the pin of 'pin'
    meets the box of the chip of 'index': an input on its left, an
    output on its right, spaced down it."""
    spec = self.circuit.parts[index].spec
    box = self.chipBox(index)
    count = len(spec.ins)
    side, place = (box.left(), pin) if pin < count else (box.right(),
                                                        pin - count)
    rows = len(spec.ins) if pin < count else len(spec.outs)
    head = 18.0 if self.chipNamed(index) else 0.0
    step = (box.height() - 14.0 - head) / rows
    return QPointF(side, box.top() + head + 7.0 + (place + 0.5) * step)

  def chipLeads(self, index: int) -> list[tuple[QPointF, QPointF]]:
    """The 'chipLeads' method returns the leads of the chip of 'index',
    each from its pin's node to where it meets the box."""
    part = self.circuit.parts[index]
    return [(self.toScreen(*self.circuit.nodes[node]),
             self.chipPin(index, pin))
            for pin, node in enumerate(part.pins)]

  def dragChip(self, pixel: QPointF) -> None:
    """The 'dragChip' method moves every pin of the chip held by as many
    steps of the grid as the mouse has moved, unless a pin would land on
    another node or is fixed, emitting 'circuitEdited'."""
    index, startX, startY = self.__drag_chip__
    x, y = self.toGrid(pixel)
    dx, dy = round(x) - startX, round(y) - startY
    if not dx and not dy:
      return
    circuit = self.circuit
    pins = set(circuit.parts[index].pins)
    nodes = [*circuit.nodes]
    for pin in pins:
      if self.isLocked(('node', pin)):
        return
      node = circuit.nodes[pin]
      spot = Node(node.x + dx, node.y + dy)
      other = circuit.at(*spot)
      if other is not None and other not in pins:
        return
      nodes[pin] = spot
    try:
      moved = circuit.withNodes(*nodes)
    except ValueError:
      return
    self.__drag_chip__ = (index, startX + dx, startY + dy)
    self.circuit = moved
    self.circuitEdited.emit(moved)

  def drop(self, ) -> None:
    """The 'drop' method lets go of the node held: onto another node, it
    is joined into it, selected, emitting 'circuitEdited'; and fits the
    circuit to the view anew."""
    index, other = self.__drag_node__, self.__merge_node__
    self.__drag_node__ = None
    self.__merge_node__ = None
    self.__view_place__ = None
    if index is not None and other is not None:
      try:
        merged = self.circuit.merged(other, index)
      except ValueError as exception:
        self.refused.emit(str(exception))
        return self.update()
      self.circuit = merged
      self.select(('node', other - (1 if other > index else 0)))
      self.circuitEdited.emit(merged)
    self.update()

  def flow(self, speed: float) -> None:
    """The 'flow' method moves each part's dots on as far as the charge
    it has let through since last, at 'speed' times real time: the
    greatest current lately at a pace, the others slower as they are
    smaller, never so far a frame that they seem to turn back."""
    run = self.run
    charges = (*run.charges, *run.baseCharges)
    before = self.__dot_charges__ or charges
    self.__dot_charges__ = charges
    if len(before) != len(charges):
      return
    seconds = (run.latest.time - self._previousTime()) / max(speed, 1e-12)
    largest = max([abs(i) for i in (*run.currents, *run.bases)] + [0.0])
    fade = 0.5 ** (max(seconds, 0.0) / self.__fallback_memory__)
    self.__dot_most__ = max(largest, self.__dot_most__ * fade, 1e-12)
    gain = self.__fallback_pace__ / (self.__dot_most__ * max(speed, 1e-12))
    spacing = self.__fallback_spacing__
    offsets = self.__dot_offsets__
    if offsets is None or len(offsets) != len(charges):
      offsets = [0.0] * len(charges)
    for k, (now, then) in enumerate(zip(charges, before)):
      move = (now - then) * gain
      move = min(max(move, -0.4 * spacing), 0.4 * spacing)
      offsets[k] = (offsets[k] + move) % spacing
    self.__dot_offsets__ = offsets
    self.update()

  def flowing(self, index: int) -> bool:
    """The 'flowing' method tells whether a current worth showing flows
    through the part of 'index', or, past the parts, into the base of
    the transistor of 'index' less their count."""
    run = self.run
    currents = (*run.currents, *run.bases)
    current = abs(currents[index])
    return True if current > 1e-4 * self.__dot_most__ + 1e-12 else False

  def shownCurrent(self, index: int) -> float:
    """The 'shownCurrent' method returns the current through the part of
    'index' as it is read: out of the plus pole of a source, from the
    first node to the second through any other part."""
    current = self.run.currents[index]
    if isinstance(self.circuit.parts[index], Source):
      return -current
    return current

  def voltageScale(self, ) -> float:
    """The 'voltageScale' method returns the voltage drawn fully red or
    blue: the greatest source's, 5 V where there is logic, at least a
    volt."""
    parts = self.circuit.parts
    logic = [HIGH for p in parts if isinstance(p, (Bit, Clock, Chip))]
    return max([abs(p.voltage) for p in parts if isinstance(p, Source)]
               + logic + [1.0])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _previousTime(self, ) -> float:
    """The time of the run's sample before the latest."""
    samples = self.run.samples
    return samples[-2].time if len(samples) > 1 else samples[-1].time

  def _fitted(self, ) -> tuple[float, float, float]:
    """The pixels to a grid step and where nought is, the circuit as
    large as fits, room around it, in the middle."""
    nodes = self.circuit.nodes or (Node(0.0, 0.0),)
    low = [min(n[k] for n in nodes) for k in (0, 1)]
    high = [max(n[k] for n in nodes) for k in (0, 1)]
    wide, tall = max(high[0] - low[0], 1.0), max(high[1] - low[1], 1.0)
    room = self.__fallback_room__
    least, most = self.__fallback_scales__
    scale = min((self.width() - 2 * room) / wide,
                (self.height() - 2 * room) / tall, most)
    scale = max(scale, least)
    left = (self.width() - (high[0] + low[0]) * scale) / 2
    bottom = (self.height() + (high[1] + low[1]) * scale) / 2
    return scale, left, bottom

  def _setSelection(self, parts: tuple[Part, ...]) -> None:
    """Selects 'parts' and emits 'selectionChanged'."""
    if parts == self.__selected_parts__:
      return
    self.__selected_parts__ = parts
    self.selectionChanged.emit(self.selected)
    self.update()
