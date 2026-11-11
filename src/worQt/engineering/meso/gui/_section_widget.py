"""
SectionWidget subclasses 'PaintedWidget' and shows the section through a
cylinder's axis to scale, with its stones, its platens and its cracks.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

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
from .. import Cylinder, Lattice, PhaseNum, Stone, UniaxialTest
from . import PaintSection, CRACK_LEAST

_PLATEN = PhaseNum.PLATEN.index
_LIGHT = torch.tensor([-0.45, 0.55, -0.7]).double()
_LIGHT = _LIGHT / _LIGHT.norm()  # towards the light, from the top left
_AMBIENT = 0.35  # of the light a face turned away from it still has


class SectionWidget(PaintedWidget):
  """
  SectionWidget subclasses 'PaintedWidget' and shows the section through
  a cylinder's axis to scale, as large as fits in the widget and centred
  in it: the mortar, the stones in it, the steel platens above and
  below. 'toScreen' maps millimetres on the section, x from the axis and
  y up from the bottom, to pixels on the widget.

  Shown a 'test', it shows its cracks as they come: each face given more
  than a micrometre, opened or slid, drawn where it is, coloured by how
  far, blue to red on the scale below the caption.

  Shown the 'cylinder' too, its paste can be made clear: 'pasteOpacity'
  is how much of the light ten millimetres of paste stops, solid at one,
  glass at nought. The front half of the cylinder is cut away; through
  the cut, the stones behind it show, each drawn round where its front
  is, its faces lit from the top left, and the paste over them in
  layers, deepest first, each as wide as the round cylinder is at its
  depth and as opaque as its depth of paste, so the deeper a stone, the
  fainter, as light would show it.
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
  __fallback_frame_margin__ = 16.0  # pixels around the section's frame
  __fallback_platen_depth__ = 12.0  # pixels: how thick a platen is drawn
  __fallback_caption_room__ = 44.0  # pixels above: caption and scale
  __fallback_paste_layers__ = 12  # layers the paste behind is drawn in
  __fallback_paste_depth__ = 10.0  # mm of paste stopping the opacity

  #  Private Variables
  __shown_lattice__: Lattice | None = None
  __shown_test__: UniaxialTest | None = None
  __shown_cylinder__: Cylinder | None = None
  __paste_opacity__: float = 1.0
  __seen_through__: tuple | None = None
  __stone_layers__: tuple | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  sectionOp = PaintSection()
  font = AttriBox[WFont](
    GenericFamilyNum.MONO,
    FontWeightNum.NORMAL,
    10,
    Color(140, 144, 152),
  )

  #  Virtual Variables
  lattice: Field[Lattice] = Field()
  test: Field[UniaxialTest] = Field()
  cylinder: Field[Cylinder] = Field()
  pasteOpacity: Field[float] = Field()
  mortarColor: Field[Color] = Field()
  stoneColor: Field[Color] = Field()
  platenColor: Field[Color] = Field()
  textColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @lattice.GET
  def _getLattice(self, ) -> Lattice | None:
    """The 'lattice' getter returns the section shown, or 'None'."""
    return self.__shown_lattice__

  @test.GET
  def _getTest(self, ) -> UniaxialTest | None:
    """The 'test' getter returns the test shown, or 'None'."""
    return self.__shown_test__

  @cylinder.GET
  def _getCylinder(self, ) -> Cylinder | None:
    """The 'cylinder' getter returns the cylinder whose stones show
    through clear paste, or 'None'."""
    return self.__shown_cylinder__

  @pasteOpacity.GET
  def _getPasteOpacity(self, ) -> float:
    """The 'pasteOpacity' getter returns how much of the light ten
    millimetres of paste stops."""
    return self.__paste_opacity__

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

  @lattice.SET
  def _setLattice(self, lattice: Lattice) -> None:
    """The 'lattice' setter shows 'lattice', untested."""
    if not isinstance(lattice, Lattice):
      raise TypeException('lattice', lattice, Lattice)
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

  @cylinder.SET
  def _setCylinder(self, cylinder: Cylinder) -> None:
    """The 'cylinder' setter shows the stones of 'cylinder' through
    clear paste."""
    if not isinstance(cylinder, Cylinder):
      raise TypeException('cylinder', cylinder, Cylinder)
    self.__shown_cylinder__ = cylinder
    self.update()

  @pasteOpacity.SET
  def _setPasteOpacity(self, opacity: float) -> None:
    """The 'pasteOpacity' setter makes the paste as opaque as
    'opacity', kept from clear to solid."""
    self.__paste_opacity__ = min(max(float(opacity), 0.0), 1.0)
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(380, 640)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(160, 280)

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

  def scale(self, ) -> float:
    """The 'scale' method returns the pixels to a millimetre."""
    lattice = self.lattice
    if lattice is None:
      return 1.0
    margin = self.__fallback_frame_margin__
    depth = self.__fallback_platen_depth__
    room = self.__fallback_caption_room__
    width = max(self.width() - 2 * margin, 1.0)
    height = max(self.height() - 2 * margin - 2 * depth - room, 1.0)
    return min(width / lattice.width, height / lattice.height)

  def sectionRect(self, ) -> QRectF:
    """The 'sectionRect' method returns where the section is drawn,
    centred below the caption, between the platens."""
    lattice = self.lattice
    if lattice is None:
      return QRectF()
    scale = self.scale()
    width, height = lattice.width * scale, lattice.height * scale
    room = self.__fallback_caption_room__
    left = (self.width() - width) / 2
    top = room + (self.height() - room - height) / 2
    return QRectF(left, top, width, height)

  def toScreen(self, x: float, y: float) -> QPointF:
    """The 'toScreen' method returns the pixel at 'x' and 'y' on the
    section, in mm."""
    box = self.sectionRect()
    scale = self.scale()
    half = self.lattice.width / 2
    return QPointF(box.left() + (x + half) * scale, box.bottom() - y * scale)

  def platenRects(self, ) -> tuple[QRectF, QRectF]:
    """The 'platenRects' method returns where the bottom platen and the
    top platen are drawn, against the section's edges."""
    box = self.sectionRect()
    depth = self.__fallback_platen_depth__
    reach = 0.12 * box.width()
    bottom = QRectF(box.left() - reach, box.bottom(),
                    box.width() + 2 * reach, depth)
    top = QRectF(box.left() - reach, box.top() - depth,
                 box.width() + 2 * reach, depth)
    return bottom, top

  def caption(self, ) -> str:
    """The 'caption' method says what the section is of."""
    lattice = self.lattice
    if lattice is None:
      return ''
    return '%g × %g mm, %d stones, %d cells' % (
        lattice.width, lattice.height, len(lattice.stones),
        lattice.nodeCount)

  def crackScaleRect(self, ) -> QRectF:
    """The 'crackScaleRect' method returns where the cracks' colour
    scale is drawn, below the caption, while a test is shown."""
    if self.test is None:
      return QRectF()
    return QRectF(8.0, 22.0, min(280.0, self.width() - 16.0), 18.0)

  def crackSegments(self, ) -> list[tuple[QPointF, QPointF, float]]:
    """The 'crackSegments' method returns the cracks to draw: each face
    of the section given more than a micrometre, opened or slid, from
    end to end, and how far it has given, in mm."""
    test, lattice = self.test, self.lattice
    if test is None or lattice is None:
      return []
    widths = test.crackSizes
    shown = (widths > CRACK_LEAST)
    shown &= lattice.phases != _PLATEN
    ends = lattice.facetEnds[shown].tolist()
    out = []
    for (start, end), width in zip(ends, widths[shown].tolist()):
      out.append((self.toScreen(*start), self.toScreen(*end), width))
    return out

  def behindStones(self, ) -> list[tuple[Stone, float]]:
    """The 'behindStones' method returns the stones behind the cut, those
    with their centres behind it, each with the depth its front is at,
    in mm, the deepest first."""
    cylinder = self.cylinder
    if cylinder is None:
      return []
    stones = cylinder.stones
    depths = cylinder.centres[:, 2].tolist()
    ranked = []
    for index, (stone, depth) in enumerate(zip(stones, depths)):
      if depth > 0:
        front = max(depth + stone.vertices[:, 2].min().item(), 0.0)
        ranked.append((front, index))
    ranked.sort()
    return [(stones[index], front) for front, index in ranked[::-1]]

  def pasteDepth(self, ) -> float:
    """The 'pasteDepth' method returns how deep the paste behind the cut
    is: the radius."""
    return self.lattice.width / 2

  def pasteLayers(self, ) -> list[tuple[QRectF, float]]:
    """The 'pasteLayers' method returns the layers the paste behind the
    cut is drawn in, the deepest first: where each is, as wide as the
    cylinder at its near side, and how opaque, as its depth of paste
    is."""
    if self.lattice is None:
      return []
    count = self.__fallback_paste_layers__
    radius = self.pasteDepth()
    thick = radius / count
    clear = 1.0 - self.pasteOpacity
    alpha = 1.0 - clear ** (thick / self.__fallback_paste_depth__)
    box = self.sectionRect()
    scale = self.scale()
    out = []
    for index in reversed(range(count)):
      depth = index * thick
      half = math.sqrt(max(radius ** 2 - depth ** 2, 0.0)) * scale
      middle = box.center().x()
      rect = QRectF(middle - half, box.top(), 2 * half, box.height())
      out.append((rect, alpha))
    return out

  def seeThrough(self, ) -> QPixmap:
    """The 'seeThrough' method returns the stones behind the cut with the
    paste over them, as opaque as it is: the layers of stones drawn once
    for each cylinder and size, the paste laid between them, deepest
    first."""
    key = (self.width(), self.height(), self.pasteOpacity)
    cache = self.__seen_through__
    if cache is not None and cache[0] is self.cylinder and (
        cache[1] is self.lattice and cache[2] == key):
      return cache[3]
    pixmap = self._blankPixmap()
    painter = QPainter(pixmap)
    layers = zip(self.stoneLayers(), self.pasteLayers())
    for picture, (rect, alpha) in layers:
      painter.drawPixmap(QPointF(0.0, 0.0), picture)
      paste = QColor(self.mortarColor.Q)
      paste.setAlphaF(alpha)
      painter.fillRect(rect, paste)
    painter.end()
    self.__seen_through__ = (self.cylinder, self.lattice, key, pixmap)
    return pixmap

  def stoneLayers(self, ) -> list[QPixmap]:
    """The 'stoneLayers' method returns the stones behind the cut drawn
    a layer of paste at a time, the deepest first, each layer the stones
    whose fronts are in it, drawn once for each cylinder and size."""
    key = (self.width(), self.height())
    cache = self.__stone_layers__
    if cache is not None and cache[0] is self.cylinder and (
        cache[1] is self.lattice and cache[2] == key):
      return cache[3]
    count = self.__fallback_paste_layers__
    thick = self.pasteDepth() / count
    behind = self.behindStones()
    pictures, index = [], 0
    for layer in range(count):
      floor = (count - 1 - layer) * thick
      picture = self._blankPixmap()
      painter = QPainter(picture)
      painter.setRenderHint(QPainter.RenderHint.Antialiasing)
      while index < len(behind) and behind[index][1] >= floor:
        self._drawStone(painter, behind[index][0])
        index += 1
      painter.end()
      pictures.append(picture)
    self.__stone_layers__ = (self.cylinder, self.lattice, key, pictures)
    return pictures

  def _blankPixmap(self, ) -> QPixmap:
    """A clear pixmap the size of the widget, sharp on its screen."""
    ratio = self.devicePixelRatioF()
    pixmap = QPixmap(round(self.width() * ratio),
                     round(self.height() * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    return pixmap

  def _drawStone(self, painter: QPainter, stone: Stone) -> None:
    """A stone behind the cut: each face turned towards the eye, lit from
    the top left as much as it faces the light."""
    corners = stone.corners
    box, scale = self.sectionRect(), self.scale()
    half = self.lattice.width / 2
    xs = (box.left() + (corners[:, 0] + half) * scale).tolist()
    ys = (box.bottom() - corners[:, 1] * scale).tolist()
    facing = stone.normals[:, 2] < 0
    light = (stone.normals[facing] @ _LIGHT).clamp(0.0).tolist()
    base = self.stoneColor.Q
    for face, lit in zip(stone.faces[facing].tolist(), light):
      shade = _AMBIENT + (1.0 - _AMBIENT) * lit
      color = QColor.fromRgbF(base.redF() * shade, base.greenF() * shade,
                              base.blueF() * shade)
      painter.setPen(QPen(color, 0.6))
      painter.setBrush(color)
      painter.drawPolygon(QPolygonF([QPointF(xs[i], ys[i]) for i in face]))
