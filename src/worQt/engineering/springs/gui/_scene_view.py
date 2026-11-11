"""
SceneView subclasses 'PaintedWidget' and shows a system of springs in
space, seen from where the mouse turns it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ..._numbers import snapTo
from .. import Motion, System
from . import PaintScene
from ._space import Vector, add, cross, dot, length, scaled, sub, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtCore import QEvent
  from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent

Part = tuple[str, int]


class SceneView(PaintedWidget):
  """
  SceneView subclasses 'PaintedWidget' and shows a 'system' of springs
  in space, in perspective, over a floor at z nought, each mass a ball
  as large as its weight, casting its shadow on the floor, each anchor a
  block, each spring a coil coloured by how it is stretched, warm pulled
  and cool pushed, each damper a dashpot, each component a rod with its
  spring inside; or, given a 'motion', the system as it moves.

  The mouse works as in any 3D view: a drag across the space turns it,
  about what is shown, the wheel comes nearer or goes back; a click
  selects a point, a spring, a damper or a component, Ctrl and a click
  selects more besides, a click on nothing selects nothing. Set up, a
  point dragged goes where it is dragged, square to the view, to the
  centimetre, and Delete removes what is selected, each emitting
  'systemEdited'; moving, 'live', a point dragged is pulled by the hand
  as its guides let it, and flung as it is let go. The selection,
  'selection', the last selected last among them, emits
  'selectionChanged'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_view_angle__ = math.radians(40.0)  # across the shorter side
  __fallback_turn_rate__ = math.radians(0.4)  # a pixel's drag turns
  __fallback_pick_reach__ = 7.0  # pixels from a line still picking it
  __fallback_ball__ = 0.06  # m: the radius of a ball of a kilogram
  __fallback_block__ = 0.09  # m: how wide an anchor's block is
  __fallback_snap__ = 0.01  # m: a point set up goes to the centimetre

  #  Private Variables
  __shown_system__: System | None = None
  __shown_motion__: Motion | None = None
  __scene_live__: bool = False
  __selected_parts__: tuple[Part, ...] = ()
  __hovered_part__: Part | None = None
  __camera_angles__: tuple[float, float] = (math.radians(-60.0),
                                            math.radians(18.0))
  __camera_reach__: tuple[Vector, float] = ((0.0, 0.0, 1.0), 4.0)
  __drag_point__: tuple[int, Vector] | None = None
  __turn_start__: tuple[QPointF, float, float, bool] | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  sceneOp = PaintScene()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 174, 182),
  )

  #  Virtual Variables
  system: Field[System] = Field()
  motion: Field[Motion] = Field()
  live: Field[bool] = Field()
  editable: Field[bool] = Field()
  selection: Field[tuple[Part, ...]] = Field()
  selected: Field[Part] = Field()
  hovered: Field[Part] = Field()
  yaw: Field[float] = Field()
  pitch: Field[float] = Field()
  target: Field[Vector] = Field()
  distance: Field[float] = Field()

  #  Signals
  systemEdited = Signal(object)
  selectionChanged = Signal(object)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @system.GET
  def _getSystem(self, ) -> System:
    """The 'system' getter returns the system as set up."""
    if self.__shown_system__ is None:
      self.__shown_system__ = System()
      self.fit()
    return self.__shown_system__

  @motion.GET
  def _getMotion(self, ) -> Motion | None:
    """The 'motion' getter returns the system moving, or 'None' as it is
    set up."""
    return self.__shown_motion__

  @live.GET
  def _getLive(self, ) -> bool:
    """The 'live' getter tells whether the motion is running, so a point
    dragged is held by the hand."""
    return self.__scene_live__

  @editable.GET
  def _getEditable(self, ) -> bool:
    """The 'editable' getter tells whether the system may be changed: as
    it is set up, not moving."""
    return True if self.motion is None else False

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

  @yaw.GET
  def _getYaw(self, ) -> float:
    """The 'yaw' getter returns how far round the view is turned about
    the upright, in radians."""
    return self.__camera_angles__[0]

  @pitch.GET
  def _getPitch(self, ) -> float:
    """The 'pitch' getter returns how far above the floor the view looks
    down from, in radians."""
    return self.__camera_angles__[1]

  @target.GET
  def _getTarget(self, ) -> Vector:
    """The 'target' getter returns what the view looks at and turns
    about, in m."""
    return self.__camera_reach__[0]

  @distance.GET
  def _getDistance(self, ) -> float:
    """The 'distance' getter returns how far the eye is from what it
    looks at, in m."""
    return self.__camera_reach__[1]

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @system.SET
  def _setSystem(self, system: System) -> None:
    """The 'system' setter shows 'system' as set up, letting go of the
    parts selected that it has no more."""
    first = self.__shown_system__ is None
    self.__shown_system__ = system
    kept = (*[part for part in self.__selected_parts__
              if part[1] < len(self.partsOf(part[0]))],)
    if kept != self.__selected_parts__:
      self._setSelection(kept)
    if first:
      self.fit()
    self.update()

  @motion.SET
  def _setMotion(self, motion: Motion | None) -> None:
    """The 'motion' setter shows 'motion', or the system as set up for
    'None'."""
    self.__shown_motion__ = motion
    self.__drag_point__ = None
    self.update()

  @live.SET
  def _setLive(self, live: bool) -> None:
    """The 'live' setter says whether the motion is running."""
    self.__scene_live__ = True if live else False

  @yaw.SET
  def _setYaw(self, yaw: float) -> None:
    """The 'yaw' setter turns the view about the upright."""
    self.__camera_angles__ = (float(yaw) % (2 * math.pi), self.pitch)
    self.update()

  @pitch.SET
  def _setPitch(self, pitch: float) -> None:
    """The 'pitch' setter tilts the view, at most nearly straight down
    or up."""
    most = math.radians(85.0)
    self.__camera_angles__ = (self.yaw, min(max(float(pitch), -most),
                                            most))
    self.update()

  @distance.SET
  def _setDistance(self, distance: float) -> None:
    """The 'distance' setter takes the eye nearer or further."""
    self.__camera_reach__ = (self.target, min(max(distance, 0.2), 500.0))
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(900, 620)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(320, 260)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """Selects the part under the mouse, Ctrl adding it to the parts
    selected, taking hold of a point to drag it; on nothing, takes hold
    of the space, to turn it."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    where = event.position()
    part = self.partAt(where)
    if part is None:
      self.__turn_start__ = (where, self.yaw, self.pitch, False)
      self.setCursor(Qt.CursorShape.ClosedHandCursor)
      return
    adding = event.modifiers() & Qt.KeyboardModifier.ControlModifier
    if adding:
      return self.toggle(part)
    self.select(part)
    if part[0] == 'point' and (self.editable or self.live):
      self.__drag_point__ = (part[1], self.positions()[part[1]])

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """Drags the point held, or turns the space, or marks the part under
    the mouse."""
    where = event.position()
    if self.__drag_point__ is not None:
      return self._dragTo(where)
    if self.__turn_start__ is not None:
      start, yaw, pitch, _ = self.__turn_start__
      rate = self.__fallback_turn_rate__
      self.__turn_start__ = (start, yaw, pitch, True)
      self.yaw = yaw - (where.x() - start.x()) * rate
      self.pitch = pitch + (where.y() - start.y()) * rate
      return
    hovered = self.partAt(where)
    if hovered != self.__hovered_part__:
      self.__hovered_part__ = hovered
      self.update()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Lets go: of the point dragged, flinging it if it moves; of the
    space, which, only clicked, selects nothing."""
    if self.__drag_point__ is not None:
      index, _ = self.__drag_point__
      self.__drag_point__ = None
      if self.motion is not None:
        self.motion.release(index)
      return
    if self.__turn_start__ is not None:
      turned = self.__turn_start__[3]
      self.__turn_start__ = None
      self.setCursor(Qt.CursorShape.ArrowCursor)
      if not turned:
        self.select(None)

  def wheelEvent(self, event: QWheelEvent) -> None:
    """The wheel comes nearer or goes back."""
    steps = event.angleDelta().y() / 120.0
    self.distance = self.distance * 0.85 ** steps
    event.accept()

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

  def positions(self, ) -> list[Vector]:
    """The 'positions' method returns where the points are shown: as
    they move, or as they are set up."""
    if self.motion is not None:
      rows = self.motion.positions.tolist()
    else:
      rows = self.system.positions().tolist()
    return [(*row,) for row in rows]

  def partsOf(self, kind: str) -> tuple:
    """The 'partsOf' method returns the system's parts of 'kind':
    'point', 'spring', 'damper' or 'component'."""
    system = self.system
    return {'point' : system.points, 'spring': system.springs,
            'damper': system.dampers, 'component': system.components}[kind]

  def fit(self, ) -> None:
    """The 'fit' method looks at the whole system, from far enough to
    see it all."""
    places = self.positions() or [(0.0, 0.0, 1.0)]
    low = [min(p[axis] for p in places) for axis in range(3)]
    high = [max(p[axis] for p in places) for axis in range(3)]
    middle = scaled(add((*low,), (*high,)), 0.5)
    radius = max(max(length(sub(p, middle)) for p in places), 0.6)
    distance = 1.3 * radius / math.sin(self.__fallback_view_angle__ / 2)
    self.__camera_reach__ = (middle, distance)
    self.update()

  def showsAll(self, ) -> bool:
    """The 'showsAll' method tells whether every point is seen, inside
    the view, a little in from its edges."""
    margin = 24.0
    for place in self.positions():
      seen = self.project(place)
      if seen is None:
        return False
      pixel = seen[0]
      if not (margin <= pixel.x() <= self.width() - margin
              and margin <= pixel.y() <= self.height() - margin):
        return False
    return True

  def camera(self, ) -> tuple[Vector, Vector, Vector, Vector]:
    """The 'camera' method returns where the eye is, and its right, up
    and forward, unit vectors."""
    yaw, pitch = self.yaw, self.pitch
    back = (math.cos(pitch) * math.cos(yaw),
            math.cos(pitch) * math.sin(yaw), math.sin(pitch))
    eye = add(self.target, scaled(back, self.distance))
    forward = scaled(back, -1.0)
    right = unit(cross(forward, (0.0, 0.0, 1.0)))
    return eye, right, cross(right, forward), forward

  def focal(self, ) -> float:
    """The 'focal' method returns the pixels a thing a metre across a
    metre away is."""
    side = max(min(self.width(), self.height()), 1)
    return 0.5 * side / math.tan(self.__fallback_view_angle__ / 2)

  def project(self, point: Vector) -> tuple[QPointF, float] | None:
    """The 'project' method returns the pixel 'point' is seen at and how
    deep it is, in m, or 'None' behind the eye."""
    eye, right, up, forward = self.camera()
    away = sub(point, eye)
    depth = dot(away, forward)
    if depth < 0.05:
      return None
    focal = self.focal()
    x = self.width() / 2 + focal * dot(away, right) / depth
    y = self.height() / 2 - focal * dot(away, up) / depth
    return QPointF(x, y), depth

  def pointUnder(self, pixel: QPointF, through: Vector) -> Vector:
    """The 'pointUnder' method returns the point under 'pixel' in the
    plane square to the view 'through' a point."""
    eye, right, up, forward = self.camera()
    focal = self.focal()
    across = (pixel.x() - self.width() / 2) / focal
    rise = (self.height() / 2 - pixel.y()) / focal
    ray = add(forward, add(scaled(right, across), scaled(up, rise)))
    depth = dot(sub(through, eye), forward)
    return add(eye, scaled(ray, depth / dot(ray, forward)))

  def ballRadius(self, index: int) -> float:
    """The 'ballRadius' method returns how large the point of 'index' is
    drawn, in m: a ball as large as its mass, or an anchor's block."""
    point = self.system.points[index]
    if point.pinned:
      return self.__fallback_block__ / 2
    return self.__fallback_ball__ * point.mass ** (1 / 3)

  def partAt(self, pixel: QPointF) -> Part | None:
    """The 'partAt' method returns the part drawn under 'pixel', the
    nearest the eye first, or 'None'."""
    places = self.positions()
    found = []
    for index, place in enumerate(places):
      seen = self.project(place)
      if seen is None:
        continue
      centre, depth = seen
      reach = self.focal() * self.ballRadius(index) / depth + 3.0
      gap = math.hypot(centre.x() - pixel.x(), centre.y() - pixel.y())
      if gap <= reach:
        found.append((depth, 0, ('point', index)))
    for kind in ('spring', 'damper', 'component'):
      for index, link in enumerate(self.partsOf(kind)):
        hit = self._lineHit(pixel, places[link[0]], places[link[1]])
        if hit is not None:
          found.append((hit, 1, (kind, index)))
    return min(found)[2] if found else None

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

  def selectedPoints(self, ) -> tuple[int, ...]:
    """The 'selectedPoints' method returns the points selected, in the
    order selected."""
    return (*[index for kind, index in self.selection if kind == 'point'],)

  def removeSelected(self, ) -> None:
    """The 'removeSelected' method removes the parts selected, set up,
    the springs and dampers on a point removed with it."""
    if not self.editable or not self.selection:
      return
    system = self.system
    for kind, method in (('spring', 'withoutSpring'),
                         ('damper', 'withoutDamper'),
                         ('component', 'withoutComponent'),
                         ('point', 'withoutPoint')):
      chosen = sorted(i for k, i in self.selection if k == kind)[::-1]
      for index in chosen:
        system = getattr(system, method)(index)
    self._setSelection(())
    self.system = system
    self.systemEdited.emit(system)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setSelection(self, parts: tuple[Part, ...]) -> None:
    """Selects 'parts' and emits 'selectionChanged'."""
    if parts == self.__selected_parts__:
      return
    self.__selected_parts__ = parts
    self.selectionChanged.emit(self.selected)
    self.update()

  def _lineHit(self, pixel: QPointF, start: Vector,
               end: Vector) -> float | None:
    """How deep the line from 'start' to 'end' is where it passes within
    reach of 'pixel', or 'None' if it does not."""
    first, second = self.project(start), self.project(end)
    if first is None or second is None:
      return None
    (a, near), (b, far) = first, second
    dx, dy = b.x() - a.x(), b.y() - a.y()
    span = dx * dx + dy * dy
    share = 0.0
    if span > 0:
      share = ((pixel.x() - a.x()) * dx + (pixel.y() - a.y()) * dy) / span
    share = min(max(share, 0.0), 1.0)
    x, y = a.x() + share * dx, a.y() + share * dy
    reach = self.__fallback_pick_reach__
    if math.hypot(pixel.x() - x, pixel.y() - y) > reach:
      return None
    return near + share * (far - near)

  def _dragTo(self, pixel: QPointF) -> None:
    """Takes the point dragged to under 'pixel', square to the view:
    set up, it goes there, to the centimetre; moving, the hand holds it
    there."""
    index, through = self.__drag_point__
    at = self.pointUnder(pixel, through)
    if self.motion is not None:
      self.motion.hold(index, at)
      return
    snap = self.__fallback_snap__
    at = (*[snapTo(value, snap) for value in at],)
    point = self.system.points[index]
    if at == point.at:
      return
    edited = self.system.withPoint(index, point.movedTo(at))
    self.system = edited
    self.systemEdited.emit(edited)
