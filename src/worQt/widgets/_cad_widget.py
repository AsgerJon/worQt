"""
CADWidget is the canvas for the drawing app. It renders a 'CADScene' of
elements - anchor points, infinite module lines and dimensions - under a
world-to-screen transform with adjustable zoom. The mouse wheel zooms in and
out around the cursor; a hover callback reports the world coordinate under
the pointer. World 'y' points up, screen 'y' points down (the transform
flips it). Module lines are drawn as prominent super-gridlines.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
from worktoy.desc import AttriBox

from ._base_widget import BaseWidget
from ..cad.draw import (
  CADScene,
  AnchorPoint,
  ModuleLine,
  Member,
  Dimension,
  AngularDimension,
)

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable
  from PySide6.QtGui import QPaintEvent, QWheelEvent, QMouseEvent, QKeyEvent


class CADWidget(BaseWidget):
  """
  A zoomable canvas rendering a 'CADScene'. 'scale' is pixels per world
  unit; 'panX'/'panY' is the world point shown at the viewport centre.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __min_scale__ = 0.1
  __max_scale__ = 4000.0
  __default_scale__ = 1.0  # pixels per mm at the default view (1 px = 1 mm)
  __point_radius__ = 4.0
  __anchor_radius__ = 5.0  # the crossed-circle anchor marker, in pixels
  __fit_padding__ = 0.08  # fraction of span left as margin when refitting
  __glow_radius_factor__ = 3.5  # point glow disc, in point radii
  __glow_width_factor__ = 3.0  # line glow stroke, in point radii
  __halo_pad__ = 3.0  # extra pixels of the bright outline barrier
  __min_drag_px__ = 3.0  # ignore press-drag gestures shorter than this
  __snap_px__ = 10.0  # object-snap pixel tolerance (pulls onto a segment)
  __perp_tol_px__ = 2.0  # 'on the module line' tolerance for the perp lock
  __grid_color__ = '#2a3628'  # near-black gridlines, more green / less blue
  __module_color__ = '#6f9a58'  # prominent super-gridline (a bold grid hue)
  __module_sel_color__ = '#a6e07a'  # a selected module line, brighter still
  __anchor_color__ = '#c678dd'  # reference-node colour (distinct from items)
  __member_color__ = '#61afef'  # structural member (solid, load-bearing)
  __support_color__ = '#56b6c2'  # support / boundary-condition symbols
  __load_color__ = '#e06c75'  # nodal load (force) arrows
  __load_len__ = 34.0  # committed load arrow length, in pixels
  __disp_color__ = '#d19a66'  # prescribed support-displacement arrows
  __dim_color__ = '#ffd24a'  # prominent colour for interim dimensions
  __dim_font_pt__ = 11  # larger font for interim dimension text

  #  Private Variables
  __on_hover__ = None  # Callable[[float, float], None]
  __on_drag__ = None  # Callable[[str, tuple, tuple], None] mid-gesture
  __on_view_changed__ = None  # Callable[[], None] after zoom/pan/grid change
  __selected__ = None  # the emphasised item, or None
  __active_kind__ = 'Anchor'  # the kind the mouse adds
  __on_request_add__ = None  # Callable[[str, list], None]
  __dragging__ = False
  __drag_start__ = None  # world (x, y) of the press
  __drag_current__ = None  # world (x, y) under the pointer mid-drag
  __mode__ = 'navigate'  # 'navigate' (pan), 'draw' (create), 'select' (pick)
  __panning__ = False
  __pan_anchor__ = None  # world point grabbed at the start of a pan
  __hover_world__ = None  # snapped grid node under the pointer, or None
  __on_pick__ = None  # Callable[[int], None] when an item is clicked
  __on_delete__ = None  # Callable[[], None] on the Delete key
  __on_support__ = None  # Callable[[AnchorPoint], None] in support mode
  __on_load__ = None  # Callable[[AnchorPoint, float, float], None] load set
  __load_anchor__ = None  # anchor being loaded mid-drag, or None
  __load_current__ = None  # world point under the pointer while loading
  __on_displace__ = None  # Callable[[AnchorPoint, float, float], None] disp
  __support_anchor__ = None  # anchor pressed in support mode (click or drag)
  __support_press__ = None  # press screen pos, to tell a click from a drag
  __support_current__ = None  # world tip while dragging a displacement
  __on_request_member__ = None  # Callable[[AnchorPoint, AnchorPoint], None]
  __member_start__ = None  # the anchor a member is being dragged from
  __member_current__ = None  # world point under the pointer mid-member-drag
  __angle_points__ = None  # collected world points while placing an angle
  __click_anchor__ = None  # press screen pos, to tell clicks from drags
  __perp_origin__ = None  # dimension start, when locked perpendicular
  __perp_normals__ = None  # module-line normals available to lock onto

  #  Public Variables
  scene = AttriBox[CADScene]()
  scale = AttriBox[float](1.0)  # pixels per mm
  panX = AttriBox[float](0.0)
  panY = AttriBox[float](0.0)
  showGrid = AttriBox[bool](True)
  snapToGrid = AttriBox[bool](True)
  gridTargetPx = AttriBox[float](24.0)  # aim for ~this pixel spacing per cell

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def worldToScreen(self, wx: float, wy: float) -> QPointF:
    """Map a world coordinate to its pixel position in the widget."""
    sx = (wx - self.panX) * self.scale + self.width() / 2
    sy = self.height() / 2 - (wy - self.panY) * self.scale
    return QPointF(sx, sy)

  def screenToWorld(self, sx: float, sy: float) -> tuple:
    """Map a pixel position in the widget back to a world coordinate."""
    wx = (sx - self.width() / 2) / self.scale + self.panX
    wy = self.panY - (sy - self.height() / 2) / self.scale
    return (wx, wy)

  def gridStep(self, ) -> float:
    """
    The grid spacing in world units (mm). It is the fixed on-screen target
    spacing divided by the current pixels-per-mm, so the *pixel* spacing of
    the grid stays constant across zoom while the *millimetre* spacing
    changes - i.e. zooming rescales what one cell measures, not how dense
    the grid looks.
    """
    return self.gridTargetPx / self.scale

  def viewFactor(self, ) -> float:
    """
    The view factor: millimetres represented by one screen pixel, i.e.
    '1 / scale'. It is 1 at the default view (1 px = 1 mm) and grows as the
    view zooms out.
    """
    return 1.0 / self.scale

  def snap(self, wx: float, wy: float) -> tuple:
    """Snap a world coordinate to the nearest grid node when snapping is on."""
    if not self.snapToGrid:
      return (wx, wy)
    step = self.gridStep()
    return (round(wx / step) * step, round(wy / step) * step)

  def setShowGrid(self, show: bool) -> None:
    """Show or hide the gridlines."""
    self.showGrid = True if show else False
    self.update()

  def setSnap(self, enabled: bool) -> None:
    """Enable or disable snapping mouse gestures to the grid."""
    self.snapToGrid = True if enabled else False
    if not self.snapToGrid:
      self.__hover_world__ = None  # drop the snap-line highlight
    self.update()

  def setGridTargetPx(self, pixels: float) -> None:
    """Set the target on-screen spacing per grid cell, then repaint."""
    self.gridTargetPx = float(pixels)
    self.update()
    self._viewChanged()

  def setViewChangedCallback(self, callback: Callable) -> None:
    """Register a callback invoked after any zoom, pan or grid change."""
    self.__on_view_changed__ = callback

  def _viewChanged(self, ) -> None:
    """Notify that the view (scale, pan or grid spacing) has changed."""
    if self.__on_view_changed__ is not None:
      self.__on_view_changed__()

  def _worldAt(self, pos: QPointF) -> tuple:
    """
    The world coordinate under a screen position. With snapping on, the
    pointer is pulled onto the nearest reference - a node first (an anchor
    point or a module-line intersection), then an infinite module line, then
    a dimension segment - and only otherwise rounded to the grid.
    """
    if self.snapToGrid:
      onNode = self._snapToNode(pos)
      if onNode is not None:
        return onNode
      onModule = self._snapToModuleLine(pos)
      if onModule is not None:
        return onModule
      onSegment = self._snapToSegment(pos)
      if onSegment is not None:
        return onSegment
    wx, wy = self.screenToWorld(pos.x(), pos.y())
    return self.snap(wx, wy)

  def _moduleLines(self, ) -> list:
    """Every module line in the scene."""
    return [item for item in self.scene if isinstance(item, ModuleLine)]

  @staticmethod
  def _lineIntersection(m1: ModuleLine, m2: ModuleLine) -> tuple:
    """The world intersection of two module lines, or None if parallel."""
    dx1, dy1 = m1.direction()
    dx2, dy2 = m2.direction()
    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < 1e-9:
      return None
    t = ((m2.x - m1.x) * dy2 - (m2.y - m1.y) * dx2) / denom
    return (m1.x + t * dx1, m1.y + t * dy1)

  def _snapNodes(self, ) -> list:
    """
    The world nodes to snap to: every anchor point, plus every intersection
    of two module lines (the grid crossings the layout is anchored on).
    """
    modules = self._moduleLines()
    nodes = [(item.x, item.y) for item in self.scene
             if isinstance(item, AnchorPoint)]
    for i in range(len(modules)):
      for j in range(i + 1, len(modules)):
        hit = self._lineIntersection(modules[i], modules[j])
        if hit is not None:
          nodes.append(hit)
    return nodes

  def _snapToNode(self, pos: QPointF) -> tuple:
    """
    The exact world coordinate of the reference node nearest 'pos', within
    the object-snap pixel tolerance, or None. Node snaps win over all others.
    """
    best, bestDistance = None, self.__snap_px__
    for wx, wy in self._snapNodes():
      screen = self.worldToScreen(wx, wy)
      distance = math.hypot(pos.x() - screen.x(), pos.y() - screen.y())
      if distance <= bestDistance:
        best, bestDistance = (wx, wy), distance
    return best

  def _snapToModuleLine(self, pos: QPointF) -> tuple:
    """
    The world point on the infinite module line nearest 'pos', within the
    snap tolerance, or None. Unlike a segment, the whole infinite line snaps.
    """
    best, bestDistance = None, self.__snap_px__
    for module in self._moduleLines():
      dx, dy = module.direction()
      a = self.worldToScreen(module.x, module.y)
      b = self.worldToScreen(module.x + dx, module.y + dy)
      point, distance = self._closestOnLine(pos, a, b)
      if distance <= bestDistance:
        best, bestDistance = point, distance
    if best is None:
      return None
    return self.screenToWorld(best.x(), best.y())

  def _snapSegments(self, ) -> list:
    """
    World endpoint pairs '((x1, y1), (x2, y2))' of every dimension segment:
    the body of a linear dimension and each arm of an angular dimension - the
    finite straight geometry the canvas also hit-tests against.
    """
    segments = []
    for item in self.scene:
      if isinstance(item, (Member, Dimension)):
        segments.append(((item.x1, item.y1), (item.x2, item.y2)))
      elif isinstance(item, AngularDimension):
        vertex = (item.vx, item.vy)
        segments.append((vertex, (item.ax, item.ay)))
        segments.append((vertex, (item.bx, item.by)))
    return segments

  def _perpNormalsAt(self, start: tuple) -> list:
    """
    The unit normals of every module line that 'start' lies on (within a
    tight pixel tolerance). When a dimension begins on a module line, these
    are the directions it may lock to so it measures perpendicular to it.
    """
    normals = []
    startScreen = self.worldToScreen(start[0], start[1])
    for module in self._moduleLines():
      dx, dy = module.direction()
      a = self.worldToScreen(module.x, module.y)
      b = self.worldToScreen(module.x + dx, module.y + dy)
      _, distance = self._closestOnLine(startScreen, a, b)
      if distance <= self.__perp_tol_px__:
        normals.append((-dy, dx))  # unit normal of a unit direction
    return normals

  def _applyPerp(self, current: tuple) -> tuple:
    """
    Project 'current' onto the line through the dimension's start along the
    module normal best aligned with the drag, so the dimension measures
    perpendicular to the module line it started on. A no-op when not locked.
    """
    if not self.__perp_normals__:
      return current
    ox, oy = self.__perp_origin__
    dirX, dirY = current[0] - ox, current[1] - oy
    best, bestScore = None, -1.0
    for nx, ny in self.__perp_normals__:
      score = abs(dirX * nx + dirY * ny)
      if score >= bestScore:
        best, bestScore = (nx, ny), score
    nx, ny = best
    t = dirX * nx + dirY * ny
    return (ox + t * nx, oy + t * ny)

  def _snapToSegment(self, pos: QPointF) -> tuple:
    """
    The world point on the straight segment nearest the screen position
    'pos', within the object-snap pixel tolerance, or None when none is
    close enough. Proximity is measured in pixels, so the pull is the same
    at any zoom; the returned point lies exactly on the segment (ends too).
    """
    best, bestDistance = None, self.__snap_px__
    for a, b in self._snapSegments():
      screenA = self.worldToScreen(a[0], a[1])
      screenB = self.worldToScreen(b[0], b[1])
      point, distance = self._closestOnSegment(pos, screenA, screenB)
      if distance <= bestDistance:
        best, bestDistance = point, distance
    if best is None:
      return None
    return self.screenToWorld(best.x(), best.y())

  def _applyScaleAt(self, newScale: float, sx: float, sy: float) -> None:
    """
    Set the zoom to 'newScale' (clamped), keeping the world point under the
    pixel '(sx, sy)' fixed under that pixel.
    """
    beforeX, beforeY = self.screenToWorld(sx, sy)
    self.scale = max(self.__min_scale__, min(self.__max_scale__, newScale))
    afterX, afterY = self.screenToWorld(sx, sy)
    self.panX += beforeX - afterX
    self.panY += beforeY - afterY
    self.update()
    self._viewChanged()

  def zoomAt(self, factor: float, sx: float, sy: float) -> None:
    """Multiply the zoom by 'factor' about the pixel '(sx, sy)'."""
    self._applyScaleAt(self.scale * factor, sx, sy)

  @staticmethod
  def _levelToScale(level: int) -> float:
    """
    Map an integer zoom level to a scale on the integer-factor ladder:
    level 0 -> 1, level n>0 -> (n+1) px/mm, level n<0 -> 1/(1-n) px/mm
    (so 1/2, 1/3, ... i.e. 2, 3, ... mm/px when zoomed out).
    """
    if level >= 0:
      return float(level + 1)
    return 1.0 / (1 - level)

  @staticmethod
  def _scaleToLevel(scale: float) -> int:
    """The nearest integer-factor ladder level for a scale."""
    if scale >= 1.0:
      return int(round(scale)) - 1
    return -(int(round(1.0 / scale)) - 1)

  @staticmethod
  def _snapScaleDown(scale: float) -> float:
    """The largest ladder scale not exceeding 'scale' (keeps fits contained)."""
    if scale >= 1.0:
      return float(math.floor(scale))
    return 1.0 / math.ceil(1.0 / scale)

  def resetView(self, ) -> None:
    """Restore the default zoom and re-centre on the world origin."""
    self.scale = self.__default_scale__
    self.panX = 0.0
    self.panY = 0.0
    self.update()
    self._viewChanged()

  def visibleWorldRect(self, ) -> tuple:
    """The currently visible world rectangle as '(minX, minY, maxX, maxY)'."""
    minX, minY = self.screenToWorld(0.0, self.height())
    maxX, maxY = self.screenToWorld(self.width(), 0.0)
    return (minX, minY, maxX, maxY)

  @staticmethod
  def _itemBounds(item: object) -> tuple:
    """
    The world bounding box of 'item', or 'None' for an item with no finite
    extent. A module line is infinite, so it returns 'None' and never drives
    auto-fit (it is always visible across the whole view anyway).
    """
    if isinstance(item, AnchorPoint):
      return (item.x, item.y, item.x, item.y)
    if isinstance(item, (Member, Dimension)):
      return (min(item.x1, item.x2), min(item.y1, item.y2),
              max(item.x1, item.x2), max(item.y1, item.y2))
    if isinstance(item, AngularDimension):
      xs = (item.vx, item.ax, item.bx)
      ys = (item.vy, item.ay, item.by)
      return (min(xs), min(ys), max(xs), max(ys))
    return None

  def fitWorldRect(self, minX: float, minY: float,
                   maxX: float, maxY: float) -> None:
    """
    Zoom and pan so the world rectangle fits the viewport with a margin.
    The scale is clamped to its configured bounds.
    """
    width, height = self.width(), self.height()
    if width <= 0 or height <= 0:
      return
    pad = self.__fit_padding__
    spanX, spanY = maxX - minX, maxY - minY
    minX, maxX = minX - spanX * pad, maxX + spanX * pad
    minY, maxY = minY - spanY * pad, maxY + spanY * pad
    spanX, spanY = maxX - minX, maxY - minY
    if spanX < 1e-9:
      spanX = 1.0
    if spanY < 1e-9:
      spanY = 1.0
    scale = self._snapScaleDown(min(width / spanX, height / spanY))
    self.scale = max(self.__min_scale__, min(self.__max_scale__, scale))
    self.panX = (minX + maxX) / 2
    self.panY = (minY + maxY) / 2
    self.update()
    self._viewChanged()

  def ensureContains(self, item: object) -> None:
    """
    If 'item' falls outside the current view, zoom out (never in) so the
    union of the current view and the item is visible, with padding. A
    fully-visible item leaves the view unchanged.
    """
    bounds = self._itemBounds(item)
    if bounds is None:
      return
    iMinX, iMinY, iMaxX, iMaxY = bounds
    vMinX, vMinY, vMaxX, vMaxY = self.visibleWorldRect()
    inside = (iMinX >= vMinX and iMaxX <= vMaxX
              and iMinY >= vMinY and iMaxY <= vMaxY)
    if inside:
      return
    self.fitWorldRect(min(iMinX, vMinX), min(iMinY, vMinY),
                      max(iMaxX, vMaxX), max(iMaxY, vMaxY))

  def fitAll(self, ) -> None:
    """
    Zoom and pan so every item in the scene is visible (zoom-to-extents).
    With nothing to show, restore the default view instead.
    """
    bounds = None
    for item in self.scene:
      itemBounds = self._itemBounds(item)
      if itemBounds is None:
        continue
      if bounds is None:
        bounds = itemBounds
      else:
        bounds = (
          min(bounds[0], itemBounds[0]), min(bounds[1], itemBounds[1]),
          max(bounds[2], itemBounds[2]), max(bounds[3], itemBounds[3]))
    if bounds is None:
      self.resetView()
      return
    self.fitWorldRect(bounds[0], bounds[1], bounds[2], bounds[3])

  def setHoverCallback(self, callback: Callable) -> None:
    """Register a callback invoked with the world coords under the mouse."""
    self.__on_hover__ = callback
    self.setMouseTracking(True)

  def setSelected(self, item: object) -> None:
    """Emphasise 'item' (or clear the emphasis when 'item' is None)."""
    self.__selected__ = item
    self.update()

  def setActiveKind(self, kind: str) -> None:
    """Set the item kind the mouse will add ('Anchor', 'Module', ...)."""
    self.__active_kind__ = kind
    self.__angle_points__ = None  # abandon any half-placed angle
    self.__perp_normals__ = None  # drop any perpendicular lock
    self.__load_anchor__ = None  # abandon any half-set load
    self.__member_start__ = None  # abandon any half-drawn member

  def _addAnglePoint(self, point: tuple) -> None:
    """Collect a click for an angular dimension; emit it on the third."""
    if self.__angle_points__ is None:
      self.__angle_points__ = []
    self.__angle_points__.append(point)
    if len(self.__angle_points__) >= 3:
      points = self.__angle_points__
      self.__angle_points__ = None
      if self.__on_request_add__ is not None:
        self.__on_request_add__('Angle', points)
    self.update()

  def activeKind(self, ) -> str:
    """The item kind currently selected for creation."""
    return self.__active_kind__

  def setMode(self, mode: str) -> None:
    """Set the canvas mode (navigate/draw/select/support/load)."""
    self.__mode__ = mode
    self.__angle_points__ = None
    self.__perp_normals__ = None
    self.__load_anchor__ = None
    self.__support_anchor__ = None
    self.__member_start__ = None
    self._updateCursor()

  def _updateCursor(self, ) -> None:
    """Show a cursor symbol for the active mode (and panning) state."""
    if self.__mode__ in ('draw', 'load'):
      self.setCursor(Qt.CursorShape.CrossCursor)
    elif self.__mode__ in ('select', 'support'):
      self.setCursor(Qt.CursorShape.PointingHandCursor)
    elif self.__panning__:
      self.setCursor(Qt.CursorShape.ClosedHandCursor)
    else:
      self.setCursor(Qt.CursorShape.OpenHandCursor)

  def setPickCallback(self, callback: Callable) -> None:
    """Register a callback invoked with the index of a clicked item."""
    self.__on_pick__ = callback

  def setDeleteCallback(self, callback: Callable) -> None:
    """Register a callback invoked when the Delete key is pressed."""
    self.__on_delete__ = callback

  def setSupportCallback(self, callback: Callable) -> None:
    """Register a callback for the anchor clicked in support mode."""
    self.__on_support__ = callback

  def setLoadCallback(self, callback: Callable) -> None:
    """Register a callback for a load: 'callback(anchor, fx, fy)'."""
    self.__on_load__ = callback

  def setDisplaceCallback(self, callback: Callable) -> None:
    """Register a settlement callback: 'callback(anchor, dx, dy)'."""
    self.__on_displace__ = callback

  def _forceTip(self, pos: QPointF, anchor: AnchorPoint) -> tuple:
    """
    The world tip of a force or displacement dragged out of 'anchor'. With
    snapping on the vector is snapped to the nearest axis (pure horizontal or
    pure vertical), so forces and settlements come out axis-aligned.
    """
    wx, wy = self.screenToWorld(pos.x(), pos.y())
    fx, fy = wx - anchor.x, wy - anchor.y
    if self.snapToGrid:
      if abs(fx) >= abs(fy):
        fy = 0.0
      else:
        fx = 0.0
    return (anchor.x + fx, anchor.y + fy)

  def _anchorAt(self, pos: QPointF) -> object:
    """The anchor point nearest 'pos' within tolerance, or None."""
    best, bestDistance = None, self.__snap_px__
    for item in self.scene:
      if isinstance(item, AnchorPoint):
        screen = self.worldToScreen(item.x, item.y)
        distance = math.hypot(pos.x() - screen.x(), pos.y() - screen.y())
        if distance <= bestDistance:
          best, bestDistance = item, distance
    return best

  def _itemAt(self, screenPos: QPointF) -> object:
    """The scene item nearest the screen position within a tolerance."""
    tolerance = 8.0
    best, bestDistance = None, tolerance
    for item in self.scene:
      distance = self._screenDistanceTo(item, screenPos)
      if distance is not None and distance <= bestDistance:
        best, bestDistance = item, distance
    return best

  def _screenDistanceTo(self, item: object, p: QPointF) -> float:
    """Screen-space distance from 'p' to 'item' (None if not applicable)."""
    if isinstance(item, AnchorPoint):
      q = self.worldToScreen(item.x, item.y)
      return math.hypot(p.x() - q.x(), p.y() - q.y())
    if isinstance(item, ModuleLine):
      dx, dy = item.direction()
      a = self.worldToScreen(item.x, item.y)
      b = self.worldToScreen(item.x + dx, item.y + dy)
      _, distance = self._closestOnLine(p, a, b)  # infinite line
      return distance
    if isinstance(item, (Member, Dimension)):
      a = self.worldToScreen(item.x1, item.y1)
      b = self.worldToScreen(item.x2, item.y2)
      return self._pointSegment(p, a, b)
    if isinstance(item, AngularDimension):
      v = self.worldToScreen(item.vx, item.vy)
      a = self.worldToScreen(item.ax, item.ay)
      b = self.worldToScreen(item.bx, item.by)
      return min(self._pointSegment(p, v, a), self._pointSegment(p, v, b))
    return None

  @staticmethod
  def _closestOnSegment(p: QPointF, a: QPointF, b: QPointF) -> tuple:
    """The point on segment 'a'-'b' nearest 'p', and the distance to it."""
    abx, aby = b.x() - a.x(), b.y() - a.y()
    apx, apy = p.x() - a.x(), p.y() - a.y()
    denom = abx * abx + aby * aby
    t = 0.0 if denom < 1e-9 else max(
        0.0, min(1.0, (apx * abx + apy * aby) / denom))
    closest = QPointF(a.x() + t * abx, a.y() + t * aby)
    return closest, math.hypot(p.x() - closest.x(), p.y() - closest.y())

  @staticmethod
  def _closestOnLine(p: QPointF, a: QPointF, b: QPointF) -> tuple:
    """
    The point on the INFINITE line through 'a' and 'b' nearest 'p', and the
    distance to it. Like '_closestOnSegment' but 't' is not clamped to the
    segment, so the projection runs the full length of the line.
    """
    abx, aby = b.x() - a.x(), b.y() - a.y()
    denom = abx * abx + aby * aby
    if denom < 1e-9:
      return a, math.hypot(p.x() - a.x(), p.y() - a.y())
    t = ((p.x() - a.x()) * abx + (p.y() - a.y()) * aby) / denom
    closest = QPointF(a.x() + t * abx, a.y() + t * aby)
    return closest, math.hypot(p.x() - closest.x(), p.y() - closest.y())

  @staticmethod
  def _pointSegment(p: QPointF, a: QPointF, b: QPointF) -> float:
    """Distance from point 'p' to the segment 'a'-'b' in screen pixels."""
    _, distance = CADWidget._closestOnSegment(p, a, b)
    return distance

  def setAddCallback(self, callback: Callable) -> None:
    """Register a callback invoked as 'callback(kind, vertices)' on a gesture."""
    self.__on_request_add__ = callback

  def setMemberCallback(self, callback: Callable) -> None:
    """Register a member callback: 'callback(anchorA, anchorB)'."""
    self.__on_request_member__ = callback

  def setDragCallback(self, callback: Callable) -> None:
    """Register a callback invoked as 'callback(kind, start, end)' mid-drag."""
    self.__on_drag__ = callback

  def _gestureVertices(self, kind: str, start: tuple, end: tuple) -> list:
    """
    World vertices for a press-drag gesture from 'start' to 'end'. A module
    line uses the press as its origin and the drag direction as its angle; a
    dimension spans the two points. Returns None for an unsupported kind.
    """
    if start is None or end is None:
      return None
    (sx, sy), (ex, ey) = start, end
    if kind in ('Module', 'Dimension'):
      return [(sx, sy), (ex, ey)]
    return None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PAINTING   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _paintGrid(self, painter: QPainter) -> None:
    """CAD faint gridlines at the current grid spacing across the view."""
    step = self.gridStep()
    minX, minY, maxX, maxY = self.visibleWorldRect()
    painter.setPen(QPen(QColor(self.__grid_color__), 1))
    startX = math.floor(minX / step) * step
    for i in range(int((maxX - startX) / step) + 1):
      x = startX + i * step
      painter.drawLine(self.worldToScreen(x, minY),
                       self.worldToScreen(x, maxY))
    startY = math.floor(minY / step) * step
    for i in range(int((maxY - startY) / step) + 1):
      y = startY + i * step
      painter.drawLine(self.worldToScreen(minX, y),
                       self.worldToScreen(maxX, y))
    self._paintSnapLines(painter, minX, minY, maxX, maxY)

  def _paintSnapLines(self, painter: QPainter, minX: float, minY: float,
                      maxX: float, maxY: float) -> None:
    """
    Mark, with a slightly shifted shade of the same hue as the grid (not a
    bright glow), the gridlines through the snapped point under the pointer -
    and, while dragging a line/region, also those through the start point.
    """
    nodes = []
    if self.__hover_world__ is not None:
      nodes.append(self.__hover_world__)
    if self.snapToGrid and self.__dragging__ and self.__drag_start__:
      nodes.append(self.__drag_start__)
    if not nodes:
      return
    base = QColor(self.__grid_color__)
    hue, saturation, value, _ = base.getHsv()
    shade = QColor.fromHsv(hue, saturation, min(255, int(value * 1.6)))
    painter.setPen(QPen(shade, 1))
    for hx, hy in nodes:
      painter.drawLine(self.worldToScreen(hx, minY),
                       self.worldToScreen(hx, maxY))
      painter.drawLine(self.worldToScreen(minX, hy),
                       self.worldToScreen(maxX, hy))

  def _paintAxes(self, painter: QPainter) -> None:
    """CAD faint x and y axes through the world origin."""
    painter.setPen(QPen(QColor('#3a3f4b'), 1))
    origin = self.worldToScreen(0.0, 0.0)
    painter.drawLine(QPointF(0, origin.y()),
                     QPointF(self.width(), origin.y()))
    painter.drawLine(QPointF(origin.x(), 0),
                     QPointF(origin.x(), self.height()))

  def _paintAnchor(self, painter: QPainter, item: AnchorPoint) -> None:
    """Render an anchor (crossed circle) plus its support symbol, if any."""
    p = self.worldToScreen(item.x, item.y)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(self.__anchor_color__), 1.5))
    radius = self.__anchor_radius__
    painter.drawEllipse(p, radius, radius)
    painter.drawLine(QPointF(p.x() - radius, p.y()),
                     QPointF(p.x() + radius, p.y()))
    painter.drawLine(QPointF(p.x(), p.y() - radius),
                     QPointF(p.x(), p.y() + radius))
    if item.supportKind() != 'free':
      self._paintSupport(painter, p, item.supportKind())
    if item.dispX or item.dispY:
      self._paintDisplacement(painter, item)
    if item.loadX or item.loadY:
      self._paintLoad(painter, item)

  def _paintDisplacement(self, painter: QPainter, item: AnchorPoint) -> None:
    """
    CAD the committed prescribed displacement on 'item' as a dashed,
    fixed-length arrow along '(dispX, dispY)' - the imposed settlement that
    forces the node off equilibrium - labelled with its magnitude.
    """
    dx, dy = item.dispX, item.dispY
    magnitude = math.hypot(dx, dy)
    if magnitude < 1e-9:
      return
    node = self.worldToScreen(item.x, item.y)
    toward = self.worldToScreen(item.x + dx, item.y + dy)
    deltaX, deltaY = toward.x() - node.x(), toward.y() - node.y()
    length = math.hypot(deltaX, deltaY) or 1.0
    unitX, unitY = deltaX / length, deltaY / length
    tip = QPointF(node.x() + unitX * self.__load_len__,
                  node.y() + unitY * self.__load_len__)
    pen = QPen(QColor(self.__disp_color__), 2, Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.drawLine(node, tip)
    self._arrowHead(painter, tip, unitX, unitY, self.__disp_color__)
    font = painter.font()
    font.setPointSize(self.__dim_font_pt__ - 1)
    font.setBold(False)
    painter.setFont(font)
    painter.drawText(QPointF(tip.x() + 4, tip.y() + 12),
                     'd %.4g' % magnitude)

  def _paintDisplacePreview(self, painter: QPainter) -> None:
    """The rubber-band settlement arrow while a displacement is dragged."""
    anchor = self.__support_anchor__
    node = self.worldToScreen(anchor.x, anchor.y)
    tip = self.worldToScreen(self.__support_current__[0],
                             self.__support_current__[1])
    deltaX, deltaY = tip.x() - node.x(), tip.y() - node.y()
    length = math.hypot(deltaX, deltaY)
    if length < 1.0:
      return  # still a click, not a drag: nothing to preview yet
    pen = QPen(QColor(self.__disp_color__), 2, Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.drawLine(node, tip)
    self._arrowHead(painter, tip, deltaX / length, deltaY / length,
                    self.__disp_color__)
    dx = self.__support_current__[0] - anchor.x
    dy = self.__support_current__[1] - anchor.y
    painter.drawText(QPointF(tip.x() + 5, tip.y() + 12),
                     'd %.4g' % math.hypot(dx, dy))

  def _paintLoad(self, painter: QPainter, item: AnchorPoint) -> None:
    """
    CAD the committed nodal load on 'item' as a fixed-length force arrow
    along '(loadX, loadY)', labelled with its magnitude in N. The arrow is a
    constant pixel length (so it shows at any zoom or magnitude); the number
    carries the actual value.
    """
    fx, fy = item.loadX, item.loadY
    magnitude = math.hypot(fx, fy)
    if magnitude < 1e-9:
      return
    node = self.worldToScreen(item.x, item.y)
    toward = self.worldToScreen(item.x + fx, item.y + fy)
    deltaX, deltaY = toward.x() - node.x(), toward.y() - node.y()
    length = math.hypot(deltaX, deltaY) or 1.0
    unitX, unitY = deltaX / length, deltaY / length
    tip = QPointF(node.x() + unitX * self.__load_len__,
                  node.y() + unitY * self.__load_len__)
    painter.setPen(QPen(QColor(self.__load_color__), 2))
    painter.drawLine(node, tip)
    self._arrowHead(painter, tip, unitX, unitY, self.__load_color__)
    font = painter.font()
    font.setPointSize(self.__dim_font_pt__ - 1)
    font.setBold(False)
    painter.setFont(font)
    painter.drawText(QPointF(tip.x() + 4, tip.y() - 4), '%.4g N' % magnitude)

  def _paintLoadPreview(self, painter: QPainter) -> None:
    """The rubber-band force arrow while a load is dragged from a node."""
    anchor = self.__load_anchor__
    node = self.worldToScreen(anchor.x, anchor.y)
    tip = self.worldToScreen(self.__load_current__[0],
                             self.__load_current__[1])
    pen = QPen(QColor(self.__load_color__), 2, Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.drawLine(node, tip)
    deltaX, deltaY = tip.x() - node.x(), tip.y() - node.y()
    length = math.hypot(deltaX, deltaY)
    if length > 1.0:
      self._arrowHead(painter, tip, deltaX / length, deltaY / length,
                      self.__load_color__)
    fx = self.__load_current__[0] - anchor.x
    fy = self.__load_current__[1] - anchor.y
    painter.drawText(QPointF(tip.x() + 5, tip.y() - 5),
                     '%.4g N' % math.hypot(fx, fy))

  def _paintSupport(self, painter: QPainter, node: QPointF,
                    kind: str) -> None:
    """
    CAD a support symbol at 'node': a triangle for the held direction, with
    ground hatching for a pin or roller circles for a roller. 'rollerV' holds
    the horizontal DOF (triangle to the side); the others, vertical.
    """
    normalX, normalY = (-1.0, 0.0) if kind == 'rollerV' else (0.0, 1.0)
    sideX, sideY = -normalY, normalX  # base direction, across the triangle
    size, half = 14.0, 9.0
    base = QPointF(node.x() + normalX * size, node.y() + normalY * size)
    cornerA = QPointF(base.x() + sideX * half, base.y() + sideY * half)
    cornerB = QPointF(base.x() - sideX * half, base.y() - sideY * half)
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(self.__support_color__), 1.5))
    painter.drawPolygon(QPolygonF([node, cornerA, cornerB]))
    if kind == 'pinned':
      for offset in (-0.7, -0.1, 0.5):  # ground hatching beyond the base
        start = QPointF(base.x() + sideX * half * offset,
                        base.y() + sideY * half * offset)
        painter.drawLine(start, QPointF(start.x() + normalX * 5 - sideX * 4,
                                        start.y() + normalY * 5 - sideY * 4))
    else:
      for offset in (-0.45, 0.45):  # roller circles beyond the base
        centre = QPointF(base.x() + sideX * half * offset + normalX * 4,
                         base.y() + sideY * half * offset + normalY * 4)
        painter.drawEllipse(centre, 3.0, 3.0)
    painter.restore()

  def _infiniteEnds(self, a: QPointF, b: QPointF) -> tuple:
    """Two screen points spanning the widget along the line through a, b."""
    dx, dy = b.x() - a.x(), b.y() - a.y()
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    reach = (self.width() + self.height()) * 2.0
    return (QPointF(a.x() - ux * reach, a.y() - uy * reach),
            QPointF(a.x() + ux * reach, a.y() + uy * reach))

  def _paintModuleLine(self, painter: QPainter, item: ModuleLine,
                       selected: bool) -> None:
    """Render a module line as an infinite, prominent super-gridline."""
    dx, dy = item.direction()
    a = self.worldToScreen(item.x, item.y)
    b = self.worldToScreen(item.x + dx, item.y + dy)
    first, second = self._infiniteEnds(a, b)
    if selected:
      painter.setPen(QPen(QColor(self.__module_sel_color__), 2.5))
    else:
      painter.setPen(QPen(QColor(self.__module_color__), 1.5))
    painter.drawLine(first, second)

  def _paintModuleLines(self, painter: QPainter) -> None:
    """Paint every module line beneath the real items, like a bolder grid."""
    for item in self.scene:
      if isinstance(item, ModuleLine):
        self._paintModuleLine(painter, item, item is self.__selected__)

  def _paintMember(self, painter: QPainter, item: Member) -> None:
    """Render a structural member as a solid, load-bearing line."""
    painter.setPen(QPen(QColor(self.__member_color__), 3))
    a = self.worldToScreen(item.x1, item.y1)
    b = self.worldToScreen(item.x2, item.y2)
    painter.drawLine(a, b)

  def _paintMemberPreview(self, painter: QPainter) -> None:
    """The rubber-band member while it is being dragged between two nodes."""
    start = self.__member_start__
    a = self.worldToScreen(start.x, start.y)
    b = self.worldToScreen(self.__member_current__[0],
                           self.__member_current__[1])
    pen = QPen(QColor(self.__member_color__), 2, Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.drawLine(a, b)

  def _paintItem(self, painter: QPainter, item: object) -> None:
    """Dispatch an item to the painter for its type (modules drawn apart)."""
    if isinstance(item, AnchorPoint):
      self._paintAnchor(painter, item)
    elif isinstance(item, Member):
      self._paintMember(painter, item)
    elif isinstance(item, Dimension):
      self._paintDimensionItem(painter, item)
    elif isinstance(item, AngularDimension):
      self._paintAngularItem(painter, item)

  def _paintAngularItem(self, painter: QPainter, item: AngularDimension) -> None:
    """Render a committed angular dimension: two arms, an arc and the value."""
    painter.setPen(QPen(QColor(self.__dim_color__), 1))
    font = painter.font()
    font.setPointSize(self.__dim_font_pt__ - 1)
    font.setBold(False)
    painter.setFont(font)
    v = self.worldToScreen(item.vx, item.vy)
    a = self.worldToScreen(item.ax, item.ay)
    b = self.worldToScreen(item.bx, item.by)
    painter.drawLine(v, a)
    painter.drawLine(v, b)
    aQt = math.degrees(math.atan2(-(a.y() - v.y()), a.x() - v.x()))
    bQt = math.degrees(math.atan2(-(b.y() - v.y()), b.x() - v.x()))
    span = (bQt - aQt + 180.0) % 360.0 - 180.0
    radius = 36.0
    rect = QRectF(v.x() - radius, v.y() - radius, 2 * radius, 2 * radius)
    painter.drawArc(rect, int(round(aQt * 16)), int(round(span * 16)))
    midRad = math.radians(aQt + span / 2.0)
    painter.drawText(
        QPointF(v.x() + (radius + 12) * math.cos(midRad),
                v.y() - (radius + 12) * math.sin(midRad)),
        '%.1f deg' % (item.angle(),))

  def _paintAnglePreview(self, painter: QPainter) -> None:
    """Show the angle points collected so far, with rays to the pointer."""
    points = [self.worldToScreen(x, y) for x, y in self.__angle_points__]
    painter.setPen(QPen(QColor('#e5c07b'), 1, Qt.PenStyle.DashLine))
    painter.setBrush(QBrush(QColor('#e5c07b')))
    for q in points:
      painter.drawEllipse(q, 3, 3)
    vertex = points[0]
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for q in points[1:]:
      painter.drawLine(vertex, q)
    if self.__hover_world__ is not None:
      painter.drawLine(vertex, self.worldToScreen(*self.__hover_world__))

  def _paintDimensionItem(self, painter: QPainter, item: Dimension) -> None:
    """Render a committed linear dimension between its two points."""
    painter.setPen(QPen(QColor(self.__dim_color__), 1))
    font = painter.font()
    font.setPointSize(self.__dim_font_pt__ - 1)
    font.setBold(False)
    painter.setFont(font)
    a = self.worldToScreen(item.x1, item.y1)
    b = self.worldToScreen(item.x2, item.y2)
    length = math.hypot(item.x2 - item.x1, item.y2 - item.y1)
    self._linearDimension(painter, a, b, '%.2f mm' % (length,))

  def _paintGlow(self, painter: QPainter, item: object) -> None:
    """Paint a soft warm light behind the selected item."""
    glow = QColor(255, 224, 130, 90)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if isinstance(item, AnchorPoint):
      painter.setPen(Qt.PenStyle.NoPen)
      painter.setBrush(QBrush(glow))
      radius = self.__anchor_radius__ * self.__glow_radius_factor__
      painter.drawEllipse(self.worldToScreen(item.x, item.y), radius, radius)
      return
    pen = QPen(glow, self.__point_radius__ * self.__glow_width_factor__)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    if isinstance(item, (Member, Dimension)):
      a = self.worldToScreen(item.x1, item.y1)
      b = self.worldToScreen(item.x2, item.y2)
      painter.drawLine(a, b)
    elif isinstance(item, AngularDimension):
      v = self.worldToScreen(item.vx, item.vy)
      painter.drawLine(v, self.worldToScreen(item.ax, item.ay))
      painter.drawLine(v, self.worldToScreen(item.bx, item.by))

  def _paintHalo(self, painter: QPainter, item: object) -> None:
    """Paint a bright outline barrier around the selected item."""
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor('#ffe082'), 1.5))
    if isinstance(item, AnchorPoint):
      radius = self.__anchor_radius__ + self.__halo_pad__
      painter.drawEllipse(self.worldToScreen(item.x, item.y), radius, radius)
    elif isinstance(item, (Member, Dimension)):
      a = self.worldToScreen(item.x1, item.y1)
      b = self.worldToScreen(item.x2, item.y2)
      painter.drawLine(a, b)
    elif isinstance(item, AngularDimension):
      v = self.worldToScreen(item.vx, item.vy)
      painter.drawLine(v, self.worldToScreen(item.ax, item.ay))
      painter.drawLine(v, self.worldToScreen(item.bx, item.by))

  def _paintPreview(self, painter: QPainter) -> None:
    """CAD the in-progress module/dimension rubber band and its readout."""
    start, current = self.__drag_start__, self.__drag_current__
    if start is None or current is None:
      return
    a = self.worldToScreen(start[0], start[1])
    b = self.worldToScreen(current[0], current[1])
    painter.setPen(QPen(QColor('#e5c07b'), 1, Qt.PenStyle.DashLine))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if self.__active_kind__ == 'Module':
      first, second = self._infiniteEnds(a, b)  # preview the infinite line
      painter.drawLine(first, second)
      return
    if self.__active_kind__ == 'Member':
      painter.drawLine(a, b)  # solid member rubber band
      return
    if self.__active_kind__ == 'Dimension':
      painter.drawLine(a, b)
      if self.__perp_normals__:
        self._paintPerpMark(painter, a, b)  # show the perpendicular lock
      self._paintDimensions(painter)

  def _paintPerpMark(self, painter: QPainter,
                     a: QPointF, b: QPointF) -> None:
    """A small right-angle square at 'a' between the dimension and the
    module line, signalling that the dimension is locked perpendicular."""
    deltaX, deltaY = b.x() - a.x(), b.y() - a.y()
    length = math.hypot(deltaX, deltaY)
    if length < 1.0:
      return
    unitX, unitY = deltaX / length, deltaY / length
    perpX, perpY = -unitY, unitX  # along the module line, in screen space
    size = 9.0
    corner = QPointF(a.x() + unitX * size, a.y() + unitY * size)
    elbow = QPointF(corner.x() + perpX * size, corner.y() + perpY * size)
    foot = QPointF(a.x() + perpX * size, a.y() + perpY * size)
    painter.save()
    painter.setPen(QPen(QColor(self.__module_sel_color__), 1.5))
    painter.drawLine(corner, elbow)
    painter.drawLine(elbow, foot)
    painter.restore()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TECHNICAL DIMENSIONS   # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _paintDimensions(self, painter: QPainter) -> None:
    """Annotate the dimension gesture like a technical drawing: the two
    coordinates, the linear dimension and the angle from the horizontal."""
    (sx, sy), (ex, ey) = self.__drag_start__, self.__drag_current__
    painter.setPen(QPen(QColor(self.__dim_color__), 1))
    font = painter.font()
    font.setPointSize(self.__dim_font_pt__)
    font.setBold(True)
    painter.setFont(font)
    start = self.worldToScreen(sx, sy)
    current = self.worldToScreen(ex, ey)
    length = math.hypot(ex - sx, ey - sy)
    reach = math.hypot(current.x() - start.x(),
                       current.y() - start.y()) or 1.0
    unitX = (current.x() - start.x()) / reach
    unitY = (current.y() - start.y()) / reach
    self._coordLabel(painter,
                     QPointF(start.x() - unitX * 16, start.y() - unitY * 16),
                     sx, sy, unitX < 0)
    self._coordLabel(painter,
                     QPointF(current.x() + unitX * 16,
                             current.y() + unitY * 16),
                     ex, ey, unitX >= 0)
    self._linearDimension(painter, start, current, '%.2f mm' % (length,))
    angle = math.degrees(math.atan2(ey - sy, ex - sx))
    self._angleDimension(painter, start, current, angle)

  def _coordLabel(self, painter: QPainter, anchor: QPointF,
                  x: float, y: float, leftAlign: bool = True) -> None:
    """
    Label a point with its world coordinate near 'anchor'. With 'leftAlign'
    the text starts at the anchor; otherwise it ends there (so labels can be
    placed clear of the line on either side).
    """
    text = '(%.2f, %.2f)' % (x, y)
    if leftAlign:
      position = QPointF(anchor.x() + 6, anchor.y() - 6)
    else:
      width = painter.fontMetrics().horizontalAdvance(text)
      position = QPointF(anchor.x() - width - 6, anchor.y() - 6)
    painter.drawText(position, text)

  def _arrowHead(self, painter: QPainter, tip: QPointF, dirX: float,
                 dirY: float, color: str = None) -> None:
    """A small filled arrowhead at 'tip' pointing along '(dirX, dirY)'."""
    fill = self.__dim_color__ if color is None else color
    size, half = 8.0, 3.0
    baseX, baseY = tip.x() - dirX * size, tip.y() - dirY * size
    perpX, perpY = -dirY, dirX
    wing1 = QPointF(baseX + perpX * half, baseY + perpY * half)
    wing2 = QPointF(baseX - perpX * half, baseY - perpY * half)
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(fill)))
    painter.drawPolygon(QPolygonF([tip, wing1, wing2]))
    painter.restore()

  def _linearDimension(self, painter: QPainter, a: QPointF, b: QPointF,
                       text: str) -> None:
    """A dimension line (offset, with extension lines, arrows and value)."""
    deltaX, deltaY = b.x() - a.x(), b.y() - a.y()
    length = math.hypot(deltaX, deltaY)
    if length < 1.0:
      return
    unitX, unitY = deltaX / length, deltaY / length
    normalX, normalY = -unitY, unitX  # perpendicular, picks the offset side
    off = 26.0
    a2 = QPointF(a.x() + normalX * off, a.y() + normalY * off)
    b2 = QPointF(b.x() + normalX * off, b.y() + normalY * off)
    painter.drawLine(QPointF(a.x() + normalX * 3, a.y() + normalY * 3),
                     QPointF(a2.x() + normalX * 5, a2.y() + normalY * 5))
    painter.drawLine(QPointF(b.x() + normalX * 3, b.y() + normalY * 3),
                     QPointF(b2.x() + normalX * 5, b2.y() + normalY * 5))
    painter.drawLine(a2, b2)
    self._arrowHead(painter, a2, -unitX, -unitY)
    self._arrowHead(painter, b2, unitX, unitY)
    angle = math.degrees(math.atan2(deltaY, deltaX))
    if angle > 90.0:
      angle -= 180.0
    elif angle < -90.0:
      angle += 180.0
    textWidth = painter.fontMetrics().horizontalAdvance(text)
    painter.save()
    painter.translate(QPointF((a2.x() + b2.x()) / 2, (a2.y() + b2.y()) / 2))
    painter.rotate(angle)
    painter.drawText(QPointF(-textWidth / 2, -4), text)
    painter.restore()

  def _angleDimension(self, painter: QPainter, vertex: QPointF,
                      other: QPointF, angleDeg: float) -> None:
    """An arc from the horizontal at 'vertex' to the line, with the value."""
    if math.hypot(other.x() - vertex.x(), other.y() - vertex.y()) < 1.0:
      return
    radius = 34.0
    painter.drawLine(vertex, QPointF(vertex.x() + radius, vertex.y()))
    rect = QRectF(vertex.x() - radius, vertex.y() - radius,
                  2 * radius, 2 * radius)
    painter.drawArc(rect, 0, int(round(angleDeg * 16)))
    midRad = math.radians(angleDeg / 2.0)
    painter.drawText(
        QPointF(vertex.x() + (radius + 12) * math.cos(midRad),
                vertex.y() - (radius + 12) * math.sin(midRad)),
        '%.1f deg' % (angleDeg,))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintEvent(self, event: QPaintEvent) -> None:
    """Paint the background, axes, every item and any in-progress gesture."""
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(self.rect(), QColor('#1e1e1e'))
    if self.showGrid:
      self._paintGrid(painter)
    self._paintModuleLines(painter)  # super-gridlines, over the faint grid
    self._paintAxes(painter)
    for item in self.scene:
      if isinstance(item, ModuleLine):
        continue  # already drawn as a super-gridline
      selected = item is self.__selected__
      if selected:
        self._paintGlow(painter, item)
      self._paintItem(painter, item)
      if selected:
        self._paintHalo(painter, item)
    if self.__dragging__:
      self._paintPreview(painter)
    if self.__angle_points__:
      self._paintAnglePreview(painter)
    if self.__load_anchor__ is not None:
      self._paintLoadPreview(painter)
    if self.__support_anchor__ is not None:
      self._paintDisplacePreview(painter)
    if self.__member_start__ is not None:
      self._paintMemberPreview(painter)
    painter.end()

  def wheelEvent(self, event: QWheelEvent) -> None:
    """Zoom by whole rungs of the integer-factor ladder, about the cursor."""
    steps = event.angleDelta().y() / 120.0
    if not steps:
      return
    delta = int(round(steps)) or (1 if steps > 0 else -1)
    target = self._levelToScale(self._scaleToLevel(self.scale) + delta)
    pos = event.position()
    self._applyScaleAt(target, pos.x(), pos.y())
    event.accept()

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """Pan in navigate mode, grow a gesture in draw mode, else just hover."""
    pos = event.position()
    if self.__panning__:
      cur = self.screenToWorld(pos.x(), pos.y())
      anchorX, anchorY = self.__pan_anchor__
      self.panX += anchorX - cur[0]
      self.panY += anchorY - cur[1]
      self.update()
      if self.__on_hover__ is not None:
        self.__on_hover__(anchorX, anchorY)
      return
    if self.__load_anchor__ is not None:  # dragging a force out of a node
      self.__load_current__ = self._forceTip(pos, self.__load_anchor__)
      self.update()
      return
    if self.__support_anchor__ is not None:  # dragging a settlement out
      self.__support_current__ = self._forceTip(pos, self.__support_anchor__)
      self.update()
      return
    if self.__member_start__ is not None:  # dragging a member to a node
      target = self._anchorAt(pos)
      if target is not None:  # snap the preview to a candidate end node
        self.__member_current__ = (target.x, target.y)
      else:
        self.__member_current__ = self.screenToWorld(pos.x(), pos.y())
      self.update()
      return
    wx, wy = self._worldAt(pos)
    #  Track the snapped grid node so its two gridlines can be highlighted;
    #  only repaint when it actually changes (i.e. crossing a grid cell).
    node = (wx, wy) if self.snapToGrid else None
    if node != self.__hover_world__:
      self.__hover_world__ = node
      self.update()
    if self.__dragging__:
      current = (wx, wy)
      if self.__active_kind__ == 'Dimension':
        current = self._applyPerp(current)  # perpendicular lock, if any
      self.__drag_current__ = current
      self.update()
      if self.__on_drag__ is not None:
        self.__on_drag__(
            self.__active_kind__, self.__drag_start__, self.__drag_current__)
    elif self.__on_hover__ is not None:
      self.__on_hover__(wx, wy)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """Pan (navigate), pick an item (select), or begin a gesture (draw)."""
    if event.button() != Qt.MouseButton.LeftButton:
      return
    pos = event.position()
    if self.__mode__ == 'navigate':
      self.__panning__ = True
      self.__pan_anchor__ = self.screenToWorld(pos.x(), pos.y())
      self._updateCursor()
      event.accept()
      return
    if self.__mode__ == 'select':
      item = self._itemAt(pos)
      #  Clicking empty space, or the already-selected item, deselects (-1).
      if item is None or item is self.__selected__:
        index = -1
      else:
        index = self.scene.items.index(item)
      if self.__on_pick__ is not None:
        self.__on_pick__(index)
      event.accept()
      return
    if self.__mode__ == 'support':
      anchor = self._anchorAt(pos)
      if anchor is not None:  # a click cycles; a drag sets a settlement
        self.__support_anchor__ = anchor
        self.__support_press__ = pos
        self.__support_current__ = (anchor.x, anchor.y)
        self.update()
      event.accept()
      return
    if self.__mode__ == 'load':
      anchor = self._anchorAt(pos)
      if anchor is not None:  # drag a force out of this node
        self.__load_anchor__ = anchor
        self.__load_current__ = (anchor.x, anchor.y)
        self.update()
      event.accept()
      return
    if self.__active_kind__ == 'Member':  # drag from one anchor to another
      anchor = self._anchorAt(pos)
      if anchor is not None:
        self.__member_start__ = anchor
        self.__member_current__ = (anchor.x, anchor.y)
        self.update()
      event.accept()
      return
    if self.__active_kind__ in ('Module', 'Dimension'):
      self.__drag_start__ = self._worldAt(pos)
      self.__drag_current__ = self.__drag_start__
      self.__dragging__ = True
      self.__perp_origin__ = self.__drag_start__
      #  A dimension begun on a module line locks perpendicular to it.
      if self.__active_kind__ == 'Dimension':
        self.__perp_normals__ = self._perpNormalsAt(self.__drag_start__)
      else:
        self.__perp_normals__ = None
      self.update()
      event.accept()
      return
    if self.__active_kind__ == 'Angle':
      self.__click_anchor__ = pos
      event.accept()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Finish a pan, a press-drag gesture, or place an angle click."""
    if event.button() != Qt.MouseButton.LeftButton:
      return
    if self.__panning__:
      self.__panning__ = False
      self._updateCursor()
      event.accept()
      return
    if self.__load_anchor__ is not None:  # finish setting a nodal load
      anchor = self.__load_anchor__
      fx = self.__load_current__[0] - anchor.x
      fy = self.__load_current__[1] - anchor.y
      self.__load_anchor__ = None
      self.__load_current__ = None
      self.update()
      if self.__on_load__ is not None:
        self.__on_load__(anchor, fx, fy)
      event.accept()
      return
    if self.__support_anchor__ is not None:  # click cycles, drag displaces
      anchor = self.__support_anchor__
      press = self.__support_press__
      moved = (abs(event.position().x() - press.x())
               + abs(event.position().y() - press.y()))
      dx = self.__support_current__[0] - anchor.x
      dy = self.__support_current__[1] - anchor.y
      self.__support_anchor__ = None
      self.__support_press__ = None
      self.__support_current__ = None
      self.update()
      if moved < self.__min_drag_px__:
        if self.__on_support__ is not None:
          self.__on_support__(anchor)  # a click: cycle the support kind
      elif self.__on_displace__ is not None:
        self.__on_displace__(anchor, dx, dy)  # a drag: prescribed settlement
      event.accept()
      return
    if self.__member_start__ is not None:  # finish a member at an anchor
      start = self.__member_start__
      target = self._anchorAt(event.position())
      self.__member_start__ = None
      self.__member_current__ = None
      self.update()
      if (target is not None and target is not start
          and self.__on_request_member__ is not None):
        self.__on_request_member__(start, target)
      event.accept()
      return
    if self.__active_kind__ == 'Angle' and self.__click_anchor__ is not None:
      anchor = self.__click_anchor__
      self.__click_anchor__ = None
      moved = (abs(event.position().x() - anchor.x())
               + abs(event.position().y() - anchor.y()))
      if moved < self.__min_drag_px__:
        self._addAnglePoint(self._worldAt(event.position()))
      event.accept()
      return
    if not self.__dragging__:
      return
    self.__dragging__ = False
    start, end = self.__drag_start__, self.__drag_current__
    self.__drag_start__ = None
    self.__drag_current__ = None
    self.__perp_normals__ = None  # release the perpendicular lock
    self.__perp_origin__ = None
    self.update()
    if not self._draggedFarEnough(start, end):
      return  # a click, not a drag: ignore the zero-size gesture
    vertices = self._gestureVertices(self.__active_kind__, start, end)
    if vertices and self.__on_request_add__ is not None:
      self.__on_request_add__(self.__active_kind__, vertices)
    event.accept()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Delete the selected item on Delete/Backspace when the canvas has focus."""
    if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
      if self.__on_delete__ is not None:
        self.__on_delete__()
      event.accept()
      return
    super().keyPressEvent(event)

  def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
    """Place an anchor point at a left double-click in anchor draw mode."""
    if event.button() != Qt.MouseButton.LeftButton:
      return
    if self.__mode__ != 'draw' or self.__active_kind__ != 'Anchor':
      return
    wx, wy = self._worldAt(event.position())
    if self.__on_request_add__ is not None:
      self.__on_request_add__('Anchor', [(wx, wy)])
    event.accept()

  def _draggedFarEnough(self, start: tuple, end: tuple) -> bool:
    """True when the gesture moved enough pixels to count as a drag."""
    if start is None or end is None:
      return False
    a, b = self.worldToScreen(*start), self.worldToScreen(*end)
    return abs(a.x() - b.x()) + abs(a.y() - b.y()) >= self.__min_drag_px__
