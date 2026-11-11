"""
CylinderView subclasses 'PaintedWidget' and shows the whole cylinder from
the side, turned about its axis by dragging, its stones and cracks seen
through its paste.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import torch
from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from ....paint_ops import PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from .. import Cylinder, Lattice3D, PhaseNum, Stone, UniaxialTest
from . import PaintCylinder, CRACK_LEAST

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QMouseEvent

_PLATEN = PhaseNum.PLATEN.index
_LIGHT = torch.tensor([-0.45, 0.55, -0.7]).double()
_LIGHT = _LIGHT / _LIGHT.norm()  # towards the light, from the top left
_AMBIENT = 0.35  # of the light a face turned away from it still has


class CylinderView(PaintedWidget):
  """
  CylinderView subclasses 'PaintedWidget' and shows the whole 'cylinder'
  from the side, to scale, as large as fits in the widget, between its
  platens, turned about its axis by 'turn'; a drag across it turns it,
  the way the mouse goes. 'toScreen' maps millimetres in the cylinder,
  y up its axis, to pixels.

  Its paste is as opaque as 'pasteOpacity': how much of the light ten
  millimetres of it stops, solid at one, glass at nought. Through it the
  stones show, their faces lit from the top left, and, shown a 'test' on
  its 'lattice', the cracks: every face given more than a micrometre,
  opened or slid, coloured by how far, blue to red on the scale below
  the caption: the paste is laid over them in layers, deepest first,
  each as wide as the cylinder at its depth and as opaque as its depth
  of paste, so the deeper a thing, the fainter, as light would show it.
  Solid, the paste shows the cracks at its surface only.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_mortar_color__ = Color(88, 86, 82)
  __fallback_stone_color__ = Color(158, 152, 140)
  __fallback_platen_color__ = Color(176, 182, 194)
  __fallback_text_color__ = Color(140, 144, 152)
  __fallback_frame_margin__ = 16.0  # pixels around the cylinder's frame
  __fallback_platen_depth__ = 12.0  # pixels: how thick a platen is drawn
  __fallback_caption_room__ = 44.0  # pixels above: caption and scale
  __fallback_paste_layers__ = 12  # layers the paste is drawn in
  __fallback_paste_depth__ = 10.0  # mm of paste stopping the opacity
  __fallback_drag_turn__ = math.pi / 300  # radians a pixel's drag turns

  #  Private Variables
  __shown_cylinder__: Cylinder | None = None
  __shown_lattice__: Lattice3D | None = None
  __shown_test__: UniaxialTest | None = None
  __paste_opacity__: float = 1.0
  __view_turn__: float = 0.0
  __drag_start__: tuple[float, float] | None = None
  __stone_layers__: tuple | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  cylinderOp = PaintCylinder()
  font = AttriBox[WFont](
      GenericFamilyNum.MONO,
      FontWeightNum.NORMAL,
      10,
      Color(140, 144, 152),
  )

  #  Virtual Variables
  cylinder: Field[Cylinder] = Field()
  lattice: Field[Lattice3D] = Field()
  test: Field[UniaxialTest] = Field()
  pasteOpacity: Field[float] = Field()
  turn: Field[float] = Field()
  dragging: Field[bool] = Field()
  mortarColor: Field[Color] = Field()
  stoneColor: Field[Color] = Field()
  platenColor: Field[Color] = Field()
  textColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cylinder.GET
  def _getCylinder(self, ) -> Cylinder | None:
    """The 'cylinder' getter returns the cylinder shown, or 'None'."""
    return self.__shown_cylinder__

  @lattice.GET
  def _getLattice(self, ) -> Lattice3D | None:
    """The 'lattice' getter returns the lattice of the cylinder shown,
    or 'None'."""
    return self.__shown_lattice__

  @test.GET
  def _getTest(self, ) -> UniaxialTest | None:
    """The 'test' getter returns the test shown, or 'None'."""
    return self.__shown_test__

  @pasteOpacity.GET
  def _getPasteOpacity(self, ) -> float:
    """The 'pasteOpacity' getter returns how much of the light ten
    millimetres of paste stops."""
    return self.__paste_opacity__

  @turn.GET
  def _getTurn(self, ) -> float:
    """The 'turn' getter returns how far the cylinder is turned about its
    axis, in radians, its front going right."""
    return self.__view_turn__

  @dragging.GET
  def _getDragging(self, ) -> bool:
    """The 'dragging' getter tells whether a drag is turning the
    cylinder."""
    return False if self.__drag_start__ is None else True

  @mortarColor.GET
  def _getMortarColor(self, ) -> Color:
    return self.__fallback_mortar_color__

  @stoneColor.GET
  def _getStoneColor(self, ) -> Color:
    return self.__fallback_stone_color__

  @platenColor.GET
  def _getPlatenColor(self, ) -> Color:
    return self.__fallback_platen_color__

  @textColor.GET
  def _getTextColor(self, ) -> Color:
    return self.__fallback_text_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cylinder.SET
  def _setCylinder(self, cylinder: Cylinder) -> None:
    """The 'cylinder' setter shows 'cylinder'."""
    if not isinstance(cylinder, Cylinder):
      raise TypeException('cylinder', cylinder, Cylinder)
    self.__shown_cylinder__ = cylinder
    self.update()

  @lattice.SET
  def _setLattice(self, lattice: Lattice3D) -> None:
    """The 'lattice' setter shows 'lattice', untested."""
    if not isinstance(lattice, Lattice3D):
      raise TypeException('lattice', lattice, Lattice3D)
    self.__shown_lattice__ = lattice
    self.__shown_test__ = None
    self.update()

  @test.SET
  def _setTest(self, test: UniaxialTest) -> None:
    """The 'test' setter shows 'test', on its lattice."""
    if not isinstance(test, UniaxialTest):
      raise TypeException('test', test, UniaxialTest)
    self.__shown_lattice__ = test.lattice
    self.__shown_test__ = test
    self.update()

  @pasteOpacity.SET
  def _setPasteOpacity(self, opacity: float) -> None:
    """The 'pasteOpacity' setter makes the paste as opaque as 'opacity',
    kept from clear to solid."""
    self.__paste_opacity__ = min(max(float(opacity), 0.0), 1.0)
    self.update()

  @turn.SET
  def _setTurn(self, turn: float) -> None:
    """The 'turn' setter turns the cylinder about its axis."""
    self.__view_turn__ = float(turn) % (2 * math.pi)
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(380, 640)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(160, 280)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A press takes hold of the cylinder, to turn it."""
    if event.button() != Qt.MouseButton.LeftButton:
      return event.ignore()
    self.__drag_start__ = (event.position().x(), self.turn)
    self.setCursor(Qt.CursorShape.ClosedHandCursor)
    event.accept()

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """A drag turns the cylinder the way the mouse goes."""
    if self.__drag_start__ is None:
      return event.ignore()
    start, turn = self.__drag_start__
    rate = self.__fallback_drag_turn__
    self.turn = turn + (event.position().x() - start) * rate
    event.accept()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Letting go leaves the cylinder turned, drawn in full again."""
    if self.__drag_start__ is None:
      return event.ignore()
    self.mouseMoveEvent(event)
    self.__drag_start__ = None
    self.setCursor(Qt.CursorShape.OpenHandCursor)
    self.update()
    event.accept()

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
    self.setCursor(Qt.CursorShape.OpenHandCursor)
    self.setMouseTracking(True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def radius(self, ) -> float:
    """The 'radius' method returns the radius of the cylinder shown, in
    mm."""
    if self.lattice is not None:
      return self.lattice.radius
    return self.cylinder.radius if self.cylinder is not None else 1.0

  def tall(self, ) -> float:
    """The 'tall' method returns the height of the cylinder shown, in
    mm."""
    if self.lattice is not None:
      return self.lattice.height
    return self.cylinder.height if self.cylinder is not None else 1.0

  def shown(self, ) -> bool:
    """The 'shown' method tells whether there is a cylinder to show."""
    return False if self.lattice is None and self.cylinder is None else True

  def scale(self, ) -> float:
    """The 'scale' method returns the pixels to a millimetre."""
    margin = self.__fallback_frame_margin__
    depth = self.__fallback_platen_depth__
    room = self.__fallback_caption_room__
    width = max(self.width() - 2 * margin, 1.0)
    height = max(self.height() - 2 * margin - 2 * depth - room, 1.0)
    return min(width / (2 * self.radius()), height / self.tall())

  def viewRect(self, ) -> QRectF:
    """The 'viewRect' method returns the cylinder's outline as drawn,
    centred below the caption, between the platens."""
    scale = self.scale()
    width, height = 2 * self.radius() * scale, self.tall() * scale
    room = self.__fallback_caption_room__
    left = (self.width() - width) / 2
    top = room + (self.height() - room - height) / 2
    return QRectF(left, top, width, height)

  def turned(self, points: torch.Tensor) -> torch.Tensor:
    """The 'turned' method returns 'points' as the turned cylinder shows
    them: across, up, and how deep, the eye being in front."""
    across, deep = math.cos(self.turn), math.sin(self.turn)
    x, y, z = points[..., 0], points[..., 1], points[..., 2]
    return torch.stack(
        [
          x * across - z * deep, y,
          x * deep + z * across
        ], -1
        )

  def toScreen(self, x: float, y: float, z: float) -> QPointF:
    """The 'toScreen' method returns the pixel at 'x', 'y' and 'z' in the
    cylinder, in mm."""
    across = x * math.cos(self.turn) - z * math.sin(self.turn)
    box, scale = self.viewRect(), self.scale()
    left = box.left() + (across + self.radius()) * scale
    return QPointF(left, box.bottom() - y * scale)

  def platenRects(self, ) -> tuple[QRectF, QRectF]:
    """The 'platenRects' method returns where the bottom platen and the
    top platen are drawn, against the cylinder's ends."""
    box = self.viewRect()
    depth = self.__fallback_platen_depth__
    reach = 0.12 * box.width()
    bottom = QRectF(
      box.left() - reach, box.bottom(),
      box.width() + 2 * reach, depth
      )
    top = QRectF(
      box.left() - reach, box.top() - depth,
      box.width() + 2 * reach, depth
      )
    return bottom, top

  def caption(self, ) -> str:
    """The 'caption' method says what the cylinder is."""
    if not self.shown():
      return ''
    text = 'Ø%g × %g mm' % (2 * self.radius(), self.tall())
    if self.cylinder is not None:
      text += ', %d stones' % len(self.cylinder.stones)
    if self.lattice is not None:
      text += ', %d cells' % self.lattice.nodeCount
    return text

  def layerThickness(self, ) -> float:
    """The 'layerThickness' method returns how deep a layer of paste is,
    in mm."""
    return 2 * self.radius() / self.__fallback_paste_layers__

  def layerOf(self, depth: torch.Tensor) -> torch.Tensor:
    """The 'layerOf' method returns the layer each 'depth' is in, the
    deepest first."""
    count = self.__fallback_paste_layers__
    index = torch.floor((self.radius() - depth) / self.layerThickness())
    return torch.clamp(index, 0, count - 1).long()

  def pasteLayers(self, ) -> list[tuple[QRectF, float]]:
    """The 'pasteLayers' method returns the layers the paste is drawn in,
    the deepest first: where each is, as wide as the cylinder where it is
    widest, and how opaque, as its depth of paste is."""
    if not self.shown():
      return []
    count = self.__fallback_paste_layers__
    radius, thick = self.radius(), self.layerThickness()
    clear = 1.0 - self.pasteOpacity
    alpha = 1.0 - clear ** (thick / self.__fallback_paste_depth__)
    box, scale = self.viewRect(), self.scale()
    middle = box.center().x()
    out = []
    for index in range(count):
      far, near = radius - index * thick, radius - (index + 1) * thick
      nearest = 0.0 if near <= 0.0 <= far else min(abs(far), abs(near))
      half = math.sqrt(max(radius ** 2 - nearest ** 2, 0.0)) * scale
      rect = QRectF(middle - half, box.top(), 2 * half, box.height())
      out.append((rect, alpha))
    return out

  def crackScaleRect(self, ) -> QRectF:
    """The 'crackScaleRect' method returns where the cracks' colour
    scale is drawn, below the caption, while a test is shown."""
    if self.test is None:
      return QRectF()
    return QRectF(8.0, 22.0, min(280.0, self.width() - 16.0), 18.0)

  def crackPolygons(self, ) -> list[tuple[QPolygonF, float, int]]:
    """The 'crackPolygons' method returns the cracks to draw: each face
    given more than a micrometre, opened or slid, as drawn, how far it
    has given, in mm, and the layer of paste it is in."""
    test, lattice = self.test, self.lattice
    if test is None or lattice is None:
      return []
    widths = test.crackSizes
    shown = (widths > CRACK_LEAST)
    shown &= lattice.phases != _PLATEN
    if not bool(shown.any()):
      return []
    corners = self.turned(lattice.facetCorners[shown].double())
    layers = self.layerOf(self.turned(lattice.centres[shown])[:, 2])
    box, scale, radius = self.viewRect(), self.scale(), self.radius()
    xs = (box.left() + (corners[..., 0] + radius) * scale).tolist()
    ys = (box.bottom() - corners[..., 1] * scale).tolist()
    out = []
    for across, up, width, layer in zip(
        xs, ys, widths[shown].tolist(),
        layers.tolist()
        ):
      points = [QPointF(x, y) for x, y in zip(across, up)]
      out.append((QPolygonF(points), width, layer))
    return out

  def stoneLayers(self, ) -> list[QPixmap]:
    """The 'stoneLayers' method returns the stones drawn a layer of paste
    at a time, the deepest first, each layer the stones whose centres
    are in it; in full once for each cylinder, size and turn, and as
    plain rounds while a drag turns it."""
    count = self.__fallback_paste_layers__
    cylinder = self.cylinder
    if cylinder is None:
      return [self._blankPixmap() for _ in range(count)]
    quick = self.dragging
    key = (self.width(), self.height(), self.turn, quick)
    cache = self.__stone_layers__
    if cache is not None and cache[0] is cylinder and cache[1] == key:
      return cache[2]
    stones = cylinder.stones
    depths = torch.zeros(0).double()
    if stones:
      centres = torch.stack([stone.centre for stone in stones])
      depths = self.turned(centres)[:, 2]
    layers = self.layerOf(depths).tolist()
    order = torch.argsort(depths, 0, True).tolist()
    pictures = []
    painters = []
    for _ in range(count):
      picture = self._blankPixmap()
      painter = QPainter(picture)
      painter.setRenderHint(QPainter.RenderHint.Antialiasing)
      pictures.append(picture)
      painters.append(painter)
    for index in order:
      painter = painters[layers[index]]
      if quick:
        self._drawRound(painter, stones[index])
      else:
        self._drawStone(painter, stones[index])
    for painter in painters:
      painter.end()
    self.__stone_layers__ = (cylinder, key, pictures)
    return pictures

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _blankPixmap(self, ) -> QPixmap:
    """A clear pixmap the size of the widget, sharp on its screen."""
    ratio = self.devicePixelRatioF()
    pixmap = QPixmap(
      max(1, round(self.width() * ratio)),
      max(1, round(self.height() * ratio))
      )
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    return pixmap

  def _screen(self, points: torch.Tensor) -> tuple[list, list]:
    """Turned 'points' as pixels across and down."""
    box, scale, radius = self.viewRect(), self.scale(), self.radius()
    xs = (box.left() + (points[:, 0] + radius) * scale).tolist()
    ys = (box.bottom() - points[:, 1] * scale).tolist()
    return xs, ys

  def _drawStone(self, painter: QPainter, stone: Stone) -> None:
    """A stone: each face turned towards the eye, lit from the top left
    as much as it faces the light."""
    corners = self.turned(stone.corners)
    normals = self.turned(stone.normals)
    xs, ys = self._screen(corners)
    facing = normals[:, 2] < 0
    light = (normals[facing] @ _LIGHT).clamp(0.0).tolist()
    base = self.stoneColor.Q
    for face, lit in zip(stone.faces[facing].tolist(), light):
      shade = _AMBIENT + (1.0 - _AMBIENT) * lit
      color = QColor.fromRgbF(
        base.redF() * shade, base.greenF() * shade,
        base.blueF() * shade
        )
      painter.setPen(QPen(color, 0.6))
      painter.setBrush(color)
      painter.drawPolygon(QPolygonF([QPointF(xs[i], ys[i]) for i in face]))

  def _drawRound(self, painter: QPainter, stone: Stone) -> None:
    """A stone as a plain round as large as it, for a quick drawing."""
    centre = self.turned(stone.centre[None])[0]
    xs, ys = self._screen(centre[None])
    reach = stone.size / 2 * self.scale()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(self.stoneColor.Q)
    painter.drawEllipse(QPointF(xs[0], ys[0]), reach, reach)
