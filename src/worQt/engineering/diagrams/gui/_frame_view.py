"""
FrameView subclasses 'PaintedWidget' and shows a plane frame, its loads
and reactions, and one of its section force diagrams.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QSize, Signal
from PySide6.QtGui import QPolygonF
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ..._numbers import snapTo
from .. import Analysis, Frame, LineLoad, Node, PointLoad
from . import PaintFrame

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtCore import QEvent
  from PySide6.QtGui import QKeyEvent, QMouseEvent

Part = tuple[str, int]
_KINDS = ('N', 'V', 'M', 'shape')


def _segmentGap(p: QPointF, a: QPointF, b: QPointF) -> float:
  """How far 'p' is from the segment from 'a' to 'b', in pixels."""
  dx, dy = b.x() - a.x(), b.y() - a.y()
  span = dx * dx + dy * dy
  share = 0.0
  if span > 0:
    share = ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / span
  share = min(max(share, 0.0), 1.0)
  return math.hypot(p.x() - a.x() - share * dx, p.y() - a.y() - share * dy)


class FrameView(PaintedWidget):
  """
  FrameView subclasses 'PaintedWidget' and shows a plane 'frame' to
  scale, fitted to the view: its members, hinged ends as rings, its
  nodes, its supports, its loads, and, held, its reactions, green, and
  the diagram chosen, 'kind': 'N', 'V' or 'M' along each member, M on
  the side it pulls, with its values at the ends, the jumps and the
  peaks, or the 'shape' it bends to, enlarged. 'analysis' is the frame
  reckoned.

  A click selects a node, a member, a support or a load, Ctrl and a
  click selects more besides, a click on nothing selects nothing,
  emitting 'selectionChanged'. A node dragged goes where it is dragged,
  to the decimetre, its members with it; a load dragged slides along its
  member, to the half decimetre; Delete removes what is selected, what
  is on it with it; each emitting 'frameEdited'. The view keeps still
  while something is dragged.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_room__ = 110.0  # pixels around the frame for what is on it
  __fallback_arrow__ = 44.0  # pixels: a point load's arrow
  __fallback_band__ = 40.0  # pixels: the greatest line load's arrows
  __fallback_turn__ = 16.0  # pixels: a moment's arc
  __fallback_reach__ = 7.0  # pixels from a thing still picking it
  __fallback_snap__ = (0.1, 0.05)  # m: a node, a load along a member

  #  Private Variables
  __shown_frame__: Frame | None = None
  __shown_analysis__: Analysis | None = None
  __shown_kind__: str = 'M'
  __selected_parts__: tuple[Part, ...] = ()
  __hovered_part__: Part | None = None
  __view_place__: tuple[float, float, float] | None = None
  __drag_part__: tuple[Part, float] | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  frameOp = PaintFrame()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 174, 182),
  )

  #  Virtual Variables
  frame: Field[Frame] = Field()
  analysis: Field[Analysis] = Field()
  kind: Field[str] = Field()
  selection: Field[tuple[Part, ...]] = Field()
  selected: Field[Part] = Field()
  hovered: Field[Part] = Field()

  #  Signals
  frameEdited = Signal(object)
  selectionChanged = Signal(object)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @frame.GET
  def _getFrame(self, ) -> Frame:
    """The 'frame' getter returns the frame shown."""
    if self.__shown_frame__ is None:
      self.__shown_frame__ = Frame()
    return self.__shown_frame__

  @analysis.GET
  def _getAnalysis(self, ) -> Analysis:
    """The 'analysis' getter returns the frame shown, reckoned."""
    if self.__shown_analysis__ is None:
      self.__shown_analysis__ = Analysis(self.frame)
    return self.__shown_analysis__

  @kind.GET
  def _getKind(self, ) -> str:
    """The 'kind' getter returns the diagram shown: 'N', 'V', 'M' or
    'shape'."""
    return self.__shown_kind__

  @selection.GET
  def _getSelection(self, ) -> tuple[Part, ...]:
    """The 'selection' getter returns the parts selected, the last
    selected last."""
    return self.__selected_parts__

  @selected.GET
  def _getSelected(self, ) -> Part | None:
    """The 'selected' getter returns the part selected last, or
    'None'."""
    return self.__selected_parts__[-1] if self.__selected_parts__ else None

  @hovered.GET
  def _getHovered(self, ) -> Part | None:
    """The 'hovered' getter returns the part under the mouse, or
    'None'."""
    return self.__hovered_part__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @frame.SET
  def _setFrame(self, frame: Frame) -> None:
    """The 'frame' setter shows 'frame', reckoned, letting go of the
    parts selected it has no more."""
    self.__shown_frame__ = frame
    self.__shown_analysis__ = Analysis(frame)
    kept = (*[part for part in self.__selected_parts__
              if part[1] < len(self.partsOf(part[0]))],)
    if kept != self.__selected_parts__:
      self._setSelection(kept)
    if self.__drag_part__ is None:
      self.__view_place__ = None
    self.update()

  @kind.SET
  def _setKind(self, kind: str) -> None:
    """The 'kind' setter shows the diagram 'kind'."""
    if kind not in _KINDS:
      raise ValueError('a diagram is N, V, M or the shape, not %r' % kind)
    self.__shown_kind__ = kind
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(1000, 700)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(400, 300)

  def resizeEvent(self, event) -> None:
    """Fits the frame to the view anew."""
    PaintedWidget.resizeEvent(self, event)
    self.__view_place__ = None

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """Selects the part under the mouse, Ctrl adding it, taking hold of
    a node or a load to drag it; on nothing, selects nothing."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    where = event.position()
    part = self.partAt(where)
    if part is None:
      return self.select(None)
    if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
      return self.toggle(part)
    self.select(part)
    if part[0] in ('node', 'load'):
      self.__drag_part__ = (part, self._grip(part, where))

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """Drags the part held, or marks the part under the mouse."""
    where = event.position()
    if self.__drag_part__ is not None:
      return self._dragTo(where)
    hovered = self.partAt(where)
    if hovered != self.__hovered_part__:
      self.__hovered_part__ = hovered
      self.update()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Lets go of the part dragged, fitting the frame to the view
    anew."""
    if self.__drag_part__ is not None:
      self.__drag_part__ = None
      self.__view_place__ = None
      self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.__hovered_part__ = None
    self.update()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Delete removes the parts selected."""
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
    """The 'partsOf' method returns the frame's parts of 'kind': 'node',
    'member', 'support' or 'load'."""
    frame = self.frame
    return {'node'   : frame.nodes, 'member': frame.members,
            'support': frame.supports, 'load': frame.loads}[kind]

  def place(self, ) -> tuple[float, float, float]:
    """The 'place' method returns how the frame is fitted to the view:
    the pixels to a metre, and where x and y nought are, in pixels."""
    if self.__view_place__ is None:
      self.__view_place__ = self._fitted()
    return self.__view_place__

  def toScreen(self, x: float, y: float) -> QPointF:
    """The 'toScreen' method returns the pixel at 'x' and 'y', in m."""
    scale, left, bottom = self.place()
    return QPointF(left + x * scale, bottom - y * scale)

  def toFrame(self, pixel: QPointF) -> tuple[float, float]:
    """The 'toFrame' method returns where 'pixel' is in the frame, in
    m."""
    scale, left, bottom = self.place()
    return (pixel.x() - left) / scale, (bottom - pixel.y()) / scale

  def across(self, member: int) -> tuple[float, float]:
    """The 'across' method returns the side of the member of index
    'member' to its left as it runs, on the screen, a unit vector."""
    tx, ty = self.frame.direction(member)
    return -ty, -tx

  def memberEnds(self, member: int) -> tuple[QPointF, QPointF]:
    """The 'memberEnds' method returns where the member of index 'member'
    starts and ends on the screen."""
    frame = self.frame
    first = frame.nodes[frame.members[member].first]
    second = frame.nodes[frame.members[member].second]
    return self.toScreen(*first), self.toScreen(*second)

  def loadPoint(self, load: tuple) -> QPointF:
    """The 'loadPoint' method returns where a point load or a moment is
    on the screen."""
    return self.toScreen(*self.frame.pointAt(load.member, load.at))

  def arrowOf(self, load: PointLoad) -> tuple[QPointF, QPointF]:
    """The 'arrowOf' method returns where a point load's arrow starts
    and where it points, at the member."""
    head = self.loadPoint(load)
    size = math.hypot(load.right, load.down) or 1.0
    dx, dy = load.right / size, load.down / size
    long = self.__fallback_arrow__
    return QPointF(head.x() - dx * long, head.y() - dy * long), head

  def bandOf(self, load: LineLoad) -> list[tuple[QPointF, QPointF]]:
    """The 'bandOf' method returns a line load's arrows, each where it
    starts and where it points, at the member, as long as the load is
    there, the greatest line load's the longest."""
    frame = self.frame
    most = max([max(abs(other.first), abs(other.last))
                for other in frame.loads
                if isinstance(other, LineLoad)] + [1e-12])
    dx, dy = (0.0, 1.0) if load.direction == 'down' else (1.0, 0.0)
    count = max(2, int(math.ceil((load.end - load.start)
                                 * self.place()[0] / 28.0)) + 1)
    out = []
    for k in range(count):
      s = load.start + (load.end - load.start) * k / (count - 1)
      head = self.toScreen(*frame.pointAt(load.member, s))
      long = self.__fallback_band__ * load.intensity(s) / most
      out.append((QPointF(head.x() - dx * long, head.y() - dy * long),
                  head))
    return out

  def partAt(self, pixel: QPointF) -> Part | None:
    """The 'partAt' method returns the part drawn under 'pixel': a load,
    a node, a support or a member, in that order, or 'None'."""
    reach = self.__fallback_reach__
    for index, load in enumerate(self.frame.loads):
      if self._loadHit(load, pixel):
        return 'load', index
    for index, node in enumerate(self.frame.nodes):
      seen = self.toScreen(*node)
      if math.hypot(seen.x() - pixel.x(), seen.y() - pixel.y()) <= reach:
        return 'node', index
    for index, support in enumerate(self.frame.supports):
      seen = self.toScreen(*self.frame.nodes[support.node])
      if (abs(pixel.x() - seen.x()) <= 16.0
          and 0.0 <= pixel.y() - seen.y() <= 26.0):
        return 'support', index
    for index in range(len(self.frame.members)):
      if _segmentGap(pixel, *self.memberEnds(index)) <= reach:
        return 'member', index
    return None

  def select(self, part: Part | None) -> None:
    """The 'select' method selects 'part' alone, or nothing for
    'None'."""
    self._setSelection(() if part is None else (part,))

  def toggle(self, part: Part) -> None:
    """The 'toggle' method adds 'part' to the parts selected, or takes it
    away if it is among them."""
    parts = [p for p in self.__selected_parts__ if p != part]
    if len(parts) == len(self.__selected_parts__):
      parts.append(part)
    self._setSelection((*parts,))

  def selectedOf(self, kind: str) -> tuple[int, ...]:
    """The 'selectedOf' method returns the parts of 'kind' selected, in
    the order selected."""
    return (*[index for k, index in self.selection if k == kind],)

  def removeSelected(self, ) -> None:
    """The 'removeSelected' method removes the parts selected, and what
    is on them, emitting 'frameEdited'."""
    if not self.selection:
      return
    frame = self.frame
    for kind, method in (('load', 'withoutLoad'),
                         ('support', 'withoutSupport'),
                         ('member', 'withoutMember'),
                         ('node', 'withoutNode')):
      for index in sorted(self.selectedOf(kind))[::-1]:
        frame = getattr(frame, method)(index)
    self._setSelection(())
    self.frame = frame
    self.frameEdited.emit(frame)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _fitted(self, ) -> tuple[float, float, float]:
    """The pixels to a metre and where nought is, the frame as large as
    fits, room around it, in the middle."""
    nodes = self.frame.nodes or (Node(0.0, 0.0),)
    low = [min(n[k] for n in nodes) for k in (0, 1)]
    high = [max(n[k] for n in nodes) for k in (0, 1)]
    wide, tall = max(high[0] - low[0], 1.0), max(high[1] - low[1], 1.0)
    room = self.__fallback_room__
    scale = min((self.width() - 2 * room) / wide,
                (self.height() - 2 * room) / tall)
    scale = max(scale, 1.0)
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

  def _loadHit(self, load: tuple, pixel: QPointF) -> bool:
    """Whether 'pixel' is on the load drawn, but not on its member,
    which a click there selects."""
    reach = self.__fallback_reach__
    if _segmentGap(pixel, *self.memberEnds(load.member)) <= reach:
      return False
    if isinstance(load, PointLoad):
      return _segmentGap(pixel, *self.arrowOf(load)) <= reach
    if isinstance(load, LineLoad):
      band = self.bandOf(load)
      outline = [tail for tail, _ in band] + [head for _, head in
                                              band][::-1]
      if QPolygonF(outline).containsPoint(pixel,
                                          Qt.FillRule.OddEvenFill):
        return True
      return any(_segmentGap(pixel, *arrow) <= reach for arrow in band)
    centre = self.loadPoint(load)
    gap = math.hypot(pixel.x() - centre.x(), pixel.y() - centre.y())
    return abs(gap - self.__fallback_turn__) <= reach

  def _grip(self, part: Part, pixel: QPointF) -> float:
    """Where a line load is taken hold of, along its member from its
    start, so it slides as held."""
    kind, index = part
    if kind != 'load':
      return 0.0
    load = self.frame.loads[index]
    if not isinstance(load, LineLoad):
      return 0.0
    return self._along(load.member, pixel) - load.start

  def _along(self, member: int, pixel: QPointF) -> float:
    """How far along the member of index 'member' 'pixel' is, square to
    it, in m."""
    frame = self.frame
    x, y = self.toFrame(pixel)
    start = frame.nodes[frame.members[member].first]
    tx, ty = frame.direction(member)
    return (x - start.x) * tx + (y - start.y) * ty

  def _dragTo(self, pixel: QPointF) -> None:
    """Takes the part held to under 'pixel': a node there, to the
    decimetre; a load along its member, to the half decimetre."""
    (kind, index), grip = self.__drag_part__
    frame = self.frame
    nodeSnap, loadSnap = self.__fallback_snap__
    try:
      if kind == 'node':
        x, y = self.toFrame(pixel)
        moved = frame.withNode(index, Node(snapTo(x, nodeSnap),
                                           snapTo(y, nodeSnap)))
      else:
        load = frame.loads[index]
        long = frame.length(load.member)
        at = snapTo(self._along(load.member, pixel) - grip, loadSnap)
        if isinstance(load, LineLoad):
          at = min(max(at, 0.0), long - (load.end - load.start))
        else:
          at = min(max(at, 0.0), long)
        moved = frame.withLoad(index, load.movedTo(at))
    except ValueError:
      return
    if moved.nodes == frame.nodes and moved.loads == frame.loads:
      return
    self.frame = moved
    self.frameEdited.emit(moved)
