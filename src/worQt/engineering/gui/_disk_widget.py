"""
DiskWidget subclasses 'PaintedWidget' and shows a disk to scale, with
its supports and loads, edited the way any drawing program edits.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtWidgets import QMenu, QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.waitaminute import MissingVariable, TypeException

from ...paint_ops import PaintBoxModel
from ...utils import WFont, Color
from ...utils.font_nums import GenericFamilyNum, FontWeightNum
from ...utils.geom import InSets, Size
from ...widgets import PaintedWidget
from .. import Disk, EdgeNum, Support, Load, Rebar, StrutTie
from .._numbers import snapTo
from . import PaintDisk, GripNum, DiskGrip
from ._glyphs import PLATE, TRIANGLE, HALF_BASE, ROLLER, HATCH, unit, dot

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Callable

  from PySide6.QtGui import QAction, QContextMenuEvent, QKeyEvent
  from PySide6.QtGui import QMouseEvent
  from PySide6.QtCore import QEvent

_SHAPE = Qt.CursorShape
_LEFT = Qt.MouseButton.LeftButton
_HANDLES = (GripNum.CORNER, GripNum.LENGTH, GripNum.HEIGHT)
_ENDS = (GripNum.SUPPORT_START, GripNum.SUPPORT_END)
_DISK = DiskGrip(GripNum.DISK, -1, None)
_PARTS = (GripNum.SUPPORT, GripNum.LOAD, GripNum.REBAR)
_LOAD_REACH = 56.0  # pixels out of the disk a load's arrows and label take
_REBAR_REACH = 6.0  # pixels around bars


class DiskWidget(PaintedWidget):
  """
  DiskWidget subclasses 'PaintedWidget' and shows a 'Disk' to scale: as
  large as fits in its 'frameRect', centred in it, with its supports
  below or beside its edges, its loads as arrows onto them, and its
  dimensions. 'toScreen' and 'toModel' map between metres on the disk,
  with y upwards, and pixels on the widget, with y downwards.

  It edits the disk the way any drawing program edits, with nothing to
  learn: a click selects the disk, a support or a load, and a click
  beside the disk selects the disk again; the 'selection' is drawn in
  the accent colour. The selected disk has handles on its right edge, on
  its top edge and at its top right corner, which resize it to 5 cm; the
  drawing holds still while a handle is dragged and fits the frame again
  when it is let go, and the disk is never made less than four
  thicknesses. A support is dragged anywhere round the edges, up to its
  neighbours, and the selected one has a handle at each end of its plate
  that widens it. A load is dragged along its edge. Delete removes the
  selected support or load. 'addSupport' and 'addLoad' add one where
  there is room and select it.

  A right click selects what it is on and opens the menu of what can be
  done with it, the current choice checked and what cannot be done
  greyed out: a support is made a roller or a pin, or removed; a load
  is reversed, spread over its edge or removed; on a free edge a support
  or a load is added just there; elsewhere a support, a load or
  reinforcement is added, and the last edit undone or redone.

  Reinforcement is added as a tie along the bottom, selected, dragged to
  the centimetre and removed like the rest. 'strutTie' is the tied arch
  of the disk shown, which the drawing shows over the disk, and
  'verdict' says what it carries and what gives out first.

  Each edit is told of by 'diskEdited' once it is done, and can be undone
  and redone by 'undo' and 'redo'; 'edit' shows a disk as an edit too.
  Setting 'disk' starts afresh.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_disk_color__ = Color(72, 76, 83)
  __fallback_edge_color__ = Color(150, 155, 165)
  __fallback_support_color__ = Color(200, 204, 212)
  __fallback_load_color__ = Color(224, 108, 117)
  __fallback_text_color__ = Color(140, 144, 152)
  __fallback_accent_color__ = Color(229, 192, 123)
  __fallback_hover_color__ = Color(240, 240, 240)
  __fallback_steel_color__ = Color(176, 182, 194)
  __fallback_strut_color__ = Color(97, 175, 239)
  __fallback_tie_color__ = Color(152, 195, 121)
  __fallback_frame_margin__ = 72  # pixels around the disk for its glyphs
  __fallback_snap_step__ = 0.05  # metres: sizes and positions snap to it
  __fallback_support_width__ = 0.3  # metres: how wide a new support is
  __fallback_load_force__ = -100.0  # kN: the force of a new load
  __fallback_grip_reach__ = 8.0  # pixels: around a handle
  __fallback_edge_reach__ = 10.0  # pixels: around an edge
  __fallback_edge_stick__ = 16.0  # pixels: how much nearer another edge
  __fallback_click_slack__ = 4.0  # pixels a click may move
  __fallback_rebar_snap__ = 0.01  # metres: bars move to the centimetre
  __fallback_cover__ = 0.05  # metres: from the edges to a new tie
  __fallback_bar_count__ = 4  # bars in a new tie
  __fallback_bar_diameter__ = 20.0  # mm: of the bars in a new tie

  #  Private Variables
  __shown_disk__: Disk | None = None
  __selected_part__: DiskGrip | None = None
  __hover_grip__: DiskGrip | None = None
  __drag_grip__: DiskGrip | None = None
  __drag_start__: tuple[Disk, QPointF] | None = None
  __frozen_mapping__: tuple[float, QPointF] | None = None
  __undo_disks__: list[Disk] | None = None
  __redo_disks__: list[Disk] | None = None
  __context_menu__: QMenu | None = None
  __model_cache__: tuple[Disk, StrutTie] | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  diskOp = PaintDisk()
  font = AttriBox[WFont](
      GenericFamilyNum.MONO,
      FontWeightNum.NORMAL,
      10,
      Color(140, 144, 152),
  )
  disk: Field[Disk] = Field()
  selection: Field[DiskGrip] = Field()
  dragMoved = AttriBox[bool](False)
  atWall = AttriBox[bool](False)

  #  Virtual Variables
  hoverGrip: Field[DiskGrip] = Field()
  dragGrip: Field[DiskGrip] = Field()
  canUndo: Field[bool] = Field()
  canRedo: Field[bool] = Field()
  contextMenu: Field[QMenu] = Field()
  strutTie: Field[StrutTie] = Field()
  diskColor: Field[Color] = Field()
  edgeColor: Field[Color] = Field()
  supportColor: Field[Color] = Field()
  loadColor: Field[Color] = Field()
  textColor: Field[Color] = Field()
  accentColor: Field[Color] = Field()
  hoverColor: Field[Color] = Field()
  steelColor: Field[Color] = Field()
  strutColor: Field[Color] = Field()
  tieColor: Field[Color] = Field()

  #  Signals
  diskEdited = Signal()
  selectionChanged = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @disk.GET
  def _getDisk(self, ) -> Disk | None:
    """The 'disk' getter returns the disk shown, or 'None' before one
    is."""
    return self.__shown_disk__

  @selection.GET
  def _getSelection(self, ) -> DiskGrip:
    """The 'selection' getter returns what is selected: the disk, a
    support or a load."""
    if self.__selected_part__ is None:
      return _DISK
    return self.__selected_part__

  @hoverGrip.GET
  def _getHoverGrip(self, ) -> DiskGrip | None:
    """The 'hoverGrip' getter returns what the mouse is over, if it can
    be selected or taken hold of."""
    return self.__hover_grip__

  @dragGrip.GET
  def _getDragGrip(self, ) -> DiskGrip | None:
    """The 'dragGrip' getter returns what the mouse has hold of, while a
    button is down."""
    return self.__drag_grip__

  @canUndo.GET
  def _getCanUndo(self, ) -> bool:
    """The 'canUndo' getter tells whether there is an edit to undo."""
    return True if self._undoList() else False

  @canRedo.GET
  def _getCanRedo(self, ) -> bool:
    """The 'canRedo' getter tells whether there is an undo to redo."""
    return True if self._redoList() else False

  @strutTie.GET
  def _getStrutTie(self, ) -> StrutTie | None:
    """The 'strutTie' getter returns the tied arch of the disk shown,
    worked out once for each disk, or 'None' with no disk shown."""
    if self.disk is None:
      return None
    cache = self.__model_cache__
    if cache is None or cache[0] is not self.disk:
      cache = self.__model_cache__ = (self.disk, StrutTie(self.disk))
    return cache[1]

  @contextMenu.GET
  def _getContextMenu(self, ) -> QMenu | None:
    """The 'contextMenu' getter returns the menu the last right click
    opened, or 'None'."""
    return self.__context_menu__

  @diskColor.GET
  def _getDiskColor(self, ) -> Color:
    return self.__fallback_disk_color__

  @edgeColor.GET
  def _getEdgeColor(self, ) -> Color:
    return self.__fallback_edge_color__

  @supportColor.GET
  def _getSupportColor(self, ) -> Color:
    return self.__fallback_support_color__

  @loadColor.GET
  def _getLoadColor(self, ) -> Color:
    return self.__fallback_load_color__

  @textColor.GET
  def _getTextColor(self, ) -> Color:
    return self.__fallback_text_color__

  @accentColor.GET
  def _getAccentColor(self, ) -> Color:
    return self.__fallback_accent_color__

  @hoverColor.GET
  def _getHoverColor(self, ) -> Color:
    return self.__fallback_hover_color__

  @steelColor.GET
  def _getSteelColor(self, ) -> Color:
    return self.__fallback_steel_color__

  @strutColor.GET
  def _getStrutColor(self, ) -> Color:
    return self.__fallback_strut_color__

  @tieColor.GET
  def _getTieColor(self, ) -> Color:
    return self.__fallback_tie_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  def _undoList(self, ) -> list[Disk]:
    if self.__undo_disks__ is None:
      self.__undo_disks__ = []
    return self.__undo_disks__

  def _redoList(self, ) -> list[Disk]:
    if self.__redo_disks__ is None:
      self.__redo_disks__ = []
    return self.__redo_disks__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @disk.SET
  def _setDisk(self, disk: Disk) -> None:
    """The 'disk' setter shows 'disk' afresh, the disk selected and
    nothing to undo, refusing what is no disk."""
    if not isinstance(disk, Disk):
      raise TypeException('disk', disk, Disk)
    self.__shown_disk__ = disk
    self.__undo_disks__, self.__redo_disks__ = [], []
    self.select(_DISK)
    self.update()

  @selection.SET
  def _setSelection(self, grip: DiskGrip) -> None:
    """The 'selection' setter selects 'grip', telling of it if it
    differs from what was selected."""
    self.select(grip)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(640, 400)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(240, 160)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A press selects what is under the mouse, the disk where nothing
    is, and takes hold of it."""
    if event.button() != _LEFT or self.disk is None:
      return event.ignore()
    self.setFocus()
    point = event.position()
    grip = self.gripAt(point)
    if grip is None or grip.kind is GripNum.DISK:
      self.select(_DISK)
      return event.accept()
    if grip.kind in _PARTS:
      self.select(grip)
    self.__frozen_mapping__ = self._fittedMapping()
    self.__drag_grip__ = grip
    self.__drag_start__ = (self.disk, point)
    self.dragMoved, self.atWall = False, False
    self.setCursor(self._cursorFor(grip))
    event.accept()

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """A move drags what is held, or shows what is under the mouse."""
    if self.__drag_grip__ is None:
      return self._hover(event.position())
    self._dragTo(event.position())
    event.accept()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Letting go ends the drag, which is then told of."""
    if self.__drag_grip__ is None or event.button() != _LEFT:
      return event.ignore()
    start = self.__drag_start__[0]
    self._endDrag()
    if str(self.disk) != str(start):
      self._remember(start)
      self.diskEdited.emit()
    self._hover(event.position())
    event.accept()

  def leaveEvent(self, event: QEvent) -> None:
    """Leaving the widget shows nothing more under the mouse."""
    self.__hover_grip__ = None
    self.update()
    PaintedWidget.leaveEvent(self, event)

  def contextMenuEvent(self, event: QContextMenuEvent) -> None:
    """A right click shows the menu of what can be done with what it is
    on, without waiting for it."""
    if self.disk is None:
      return event.ignore()
    menu = self.contextMenuAt(QPointF(event.pos()))
    menu.popup(event.globalPos())
    event.accept()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Delete removes what is selected; Escape selects the disk."""
    if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
      self.removeSelected()
      return event.accept()
    if event.key() == Qt.Key.Key_Escape:
      self.select(_DISK)
      return event.accept()
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
    #  Hovering shows what can be taken hold of, so the widget follows
    #  the mouse with no button down too.
    self.setMouseTracking(True)
    self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # \_____________________
  #  Mapping and areas  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def frameRect(self, ) -> QRectF:
    """The 'frameRect' method returns the area the disk is fitted in: the
    widget less a margin all round, and never less than a pixel."""
    outer, margin = QRectF(self.rect()), self.__fallback_frame_margin__
    width = max(outer.width() - 2 * margin, 1.0)
    height = max(outer.height() - 2 * margin, 1.0)
    frame = QRectF(0.0, 0.0, width, height)
    frame.moveCenter(outer.center())
    return frame

  def diskScale(self, ) -> float:
    """The 'diskScale' method returns how many pixels a metre of the disk
    takes, or zero with no disk shown."""
    return 0.0 if self.disk is None else self._mapping()[0]

  def diskRect(self, ) -> QRectF:
    """The 'diskRect' method returns where the disk is on the widget, or
    an empty rect with no disk shown."""
    if self.disk is None:
      return QRectF()
    scale, origin = self._mapping()
    width, height = self.disk.length * scale, self.disk.height * scale
    return QRectF(origin.x(), origin.y() - height, width, height)

  def toScreen(self, x: float, y: float) -> QPointF:
    """The 'toScreen' method returns where the point '(x, y)' of the
    disk, in metres, is on the widget."""
    scale, origin = self._liveMapping()
    return QPointF(origin.x() + x * scale, origin.y() - y * scale)

  def toModel(self, point: QPointF) -> tuple[float, float]:
    """The 'toModel' method returns which point of the disk, in metres,
    is at 'point' on the widget."""
    scale, origin = self._liveMapping()
    return (
      (point.x() - origin.x()) / scale,
      (origin.y() - point.y()) / scale
    )

  def stretchOnScreen(self, stretch) -> tuple[QPointF, QPointF, QPointF]:
    """The 'stretchOnScreen' method returns where a support's or a
    load's stretch starts and ends on the widget, and the unit vector out
    of the disk across its edge, on the widget."""
    disk = self.disk
    start = self.toScreen(*disk.pointAt(stretch.edge, stretch.start))
    end = self.toScreen(*disk.pointAt(stretch.edge, stretch.end))
    ox, oy = stretch.edge.outward
    return start, end, QPointF(ox, -oy)

  def handlePoint(self, kind: GripNum) -> QPointF:
    """The 'handlePoint' method returns where the disk's handle 'kind'
    is: the middle of the right edge, the middle of the top edge or the
    top right corner."""
    box = self.diskRect()
    if kind is GripNum.LENGTH:
      return QPointF(box.right(), box.center().y())
    if kind is GripNum.HEIGHT:
      return QPointF(box.center().x(), box.top())
    if kind is GripNum.CORNER:
      return QPointF(box.right(), box.top())
    raise ValueError("""the disk has no '%s' handle""" % kind.value)

  def supportEndPoint(self, kind: GripNum) -> QPointF:
    """The 'supportEndPoint' method returns where the handle 'kind' at an
    end of the selected support's plate is."""
    support = self.disk.supports[self.selection.index]
    start, end, out = self.stretchOnScreen(support)
    point = start if kind is GripNum.SUPPORT_START else end
    return point + out * (PLATE / 2)

  def plateRect(self, index: int) -> QRectF:
    """The 'plateRect' method returns where the plate of support 'index'
    is."""
    return self.supportPlate(self.disk.supports[index])

  def rebarRect(self, index: int) -> QRectF:
    """The 'rebarRect' method returns where the bars 'index' are, give or
    take a few pixels."""
    return self.rebarArea(self.disk.rebars[index])

  def rebarArea(self, rebar: Rebar) -> QRectF:
    """The 'rebarArea' method returns where 'rebar' is drawn, give or
    take a few pixels."""
    start, end = self.toScreen(*rebar.start), self.toScreen(*rebar.end)
    box = QRectF(start, end).normalized()
    return box.adjusted(
      -_REBAR_REACH, -_REBAR_REACH, _REBAR_REACH,
      _REBAR_REACH
      )

  def loadRect(self, index: int) -> QRectF:
    """The 'loadRect' method returns where the arrows of load 'index' and
    their label are."""
    return self.loadArea(self.disk.loads[index])

  def supportPlate(self, support: Support) -> QRectF:
    """The 'supportPlate' method returns where the plate of 'support'
    is."""
    start, end, out = self.stretchOnScreen(support)
    return QRectF(start, end + out * PLATE).normalized()

  def supportArea(self, support: Support) -> QRectF:
    """The 'supportArea' method returns where 'support' is drawn: its
    plate, its triangle and what it stands on."""
    start, end, out = self.stretchOnScreen(support)
    side = unit(end - start)
    reach = side * (HALF_BASE + 4.0)
    depth = out * (PLATE + TRIANGLE + 2 * ROLLER + HATCH)
    plate = QRectF(start - side * 2.0, end + side * 2.0 + out * PLATE)
    middle = (start + end) * 0.5
    glyph = QRectF(middle - reach, middle + reach + depth)
    return plate.normalized().united(glyph.normalized())

  def loadArea(self, load: Load) -> QRectF:
    """The 'loadArea' method returns where the arrows of 'load' and their
    label are drawn."""
    start, end, out = self.stretchOnScreen(load)
    side = unit(end - start)
    first, last = start - side * 8.0, end + side * 8.0
    return QRectF(first, last + out * _LOAD_REACH).normalized()

  def gripAt(self, point: QPointF) -> DiskGrip | None:
    """The 'gripAt' method returns what can be selected or taken hold of
    at 'point', or 'None': the handles of what is selected first, then
    the supports, then the loads, then the disk."""
    if self.disk is None:
      return None
    grip = self._handleAt(point)
    if grip is not None:
      return grip
    for index, support in enumerate(self.disk.supports):
      if self.supportArea(support).contains(point):
        return DiskGrip(GripNum.SUPPORT, index, support.edge)
    for index, rebar in enumerate(self.disk.rebars):
      if self.rebarArea(rebar).contains(point):
        return DiskGrip(GripNum.REBAR, index, None)
    for index, load in enumerate(self.disk.loads):
      if self.loadArea(load).contains(point):
        return DiskGrip(GripNum.LOAD, index, load.edge)
    if self.diskRect().contains(point):
      return _DISK
    return None

  # \__________________________
  #  Selecting, adding, undo  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def select(self, grip: DiskGrip) -> None:
    """The 'select' method selects 'grip': the disk, a support or a
    load, telling of it if it differs from what was selected."""
    if not isinstance(grip, DiskGrip):
      raise TypeException('grip', grip, DiskGrip)
    if grip == self.selection:
      return
    self.__selected_part__ = grip
    self.update()
    self.selectionChanged.emit()

  def addSupport(self, ) -> None:
    """The 'addSupport' method adds a roller where there is room, trying
    the bottom, the top, the left and the right edge in turn, and
    selects it."""
    disk, width = self.disk, self.__fallback_support_width__
    for edge in (EdgeNum.BOTTOM, EdgeNum.TOP, EdgeNum.LEFT, EdgeNum.RIGHT):
      start = disk.freeStretch(edge, width)
      if start is None:
        continue
      across = False if edge.horizontal else True
      added = Disk(disk)
      added.addSupport(
        Support(
          edge, start, round(start + width, 9),
          across, not across
          )
        )
      self.edit(added)
      grip = DiskGrip(GripNum.SUPPORT, len(added.supports) - 1, edge)
      return self.select(grip)

  def addLoad(self, ) -> None:
    """The 'addLoad' method adds a load pressing down on the middle of
    the top edge, as wide as a support, and selects it."""
    disk = self.disk
    width = min(self.__fallback_support_width__, disk.length)
    start = round(disk.length / 2 - width / 2, 9)
    added = Disk(disk)
    added.addLoad(
      Load(
        EdgeNum.TOP, start, round(start + width, 9), 0.0,
        self.__fallback_load_force__
        )
      )
    self.edit(added)
    self.select(DiskGrip(GripNum.LOAD, len(added.loads) - 1, EdgeNum.TOP))

  def addRebar(self, ) -> None:
    """The 'addRebar' method adds a tie along the bottom, 4 Ø20 a cover
    in from the ends and the bottom edge, and selects it."""
    disk, cover = self.disk, self.__fallback_cover__
    diameter = self.__fallback_bar_diameter__
    height = round(cover + diameter / 2000, 9)
    rebar = Rebar(
      cover, height, round(disk.length - cover, 9), height,
      self.__fallback_bar_count__, diameter
      )
    added = Disk(disk)
    added.addRebar(rebar)
    self.edit(added)
    self.select(DiskGrip(GripNum.REBAR, len(added.rebars) - 1, None))

  def verdict(self, ) -> str:
    """The 'verdict' method says what the tied arch carries, and what
    gives out first; or why there is none."""
    model = self.strutTie
    if model is None:
      return ''
    if not model.applicable:
      return 'Strut and tie: %s' % model.reason
    if model.factor <= 0:
      return 'Strut and tie: nothing ties the supports: add reinforcement'
    if model.factor < 1:
      infoSpec = 'Strut and tie: carries only %.2f × the loads; the %s fails'
    else:
      infoSpec = 'Strut and tie: carries %.2f × the loads; the %s governs'
    return infoSpec % (model.factor, model.governing)

  def removeSelected(self, ) -> None:
    """The 'removeSelected' method removes the selected support, load or
    reinforcement, and selects the disk; with the disk selected it
    removes nothing."""
    grip = self.selection
    if grip.kind not in _PARTS:
      return
    removed = Disk(self.disk)
    if grip.kind is GripNum.SUPPORT:
      removed.removeSupport(grip.index)
    elif grip.kind is GripNum.LOAD:
      removed.removeLoad(grip.index)
    else:
      removed.removeRebar(grip.index)
    self.select(_DISK)
    self.edit(removed)

  def turnSelected(self, pin: bool) -> None:
    """The 'turnSelected' method makes the selected support a pin, or a
    roller holding the disk across its edge."""
    grip = self.selection
    if grip.kind is not GripNum.SUPPORT:
      return
    support = self.disk.supports[grip.index]
    across = False if support.edge.horizontal else True
    setsX, setsY = (True, True) if pin else (across, not across)
    turned = Disk(self.disk)
    turned.replaceSupport(
      grip.index, Support(
        support.edge, support.start,
        support.end, setsX, setsY
        )
      )
    self.edit(turned)

  def reverseSelected(self, ) -> None:
    """The 'reverseSelected' method turns the force of the selected load
    round."""
    self._replaceSelectedLoad(
      lambda load: Load(
          load.edge, load.start, load.end, -load.fx, -load.fy
      )
      )

  def spreadSelected(self, ) -> None:
    """The 'spreadSelected' method spreads the selected load over the
    whole of its edge, the same force."""
    length = self.disk.edgeLength
    self._replaceSelectedLoad(
      lambda load: Load(
          load.edge, 0.0, length(load.edge), load.fx, load.fy
      )
      )

  def edgeAt(self, point: QPointF) -> EdgeNum | None:
    """The 'edgeAt' method returns the edge 'point' is on, give or take a
    few pixels, or 'None'."""
    disk, reach = self.disk, self.__fallback_edge_reach__
    for edge in EdgeNum:
      first = self.toScreen(*disk.pointAt(edge, 0.0))
      last = self.toScreen(*disk.pointAt(edge, disk.edgeLength(edge)))
      span = last - first
      along = dot(point - first, span) / dot(span, span)
      off = point - (first + span * along)
      if 0.0 <= along <= 1.0 and dot(off, off) <= reach * reach:
        return edge
    return None

  def contextMenuAt(self, point: QPointF) -> QMenu:
    """The 'contextMenuAt' method selects what is at 'point', the disk
    where nothing else is, and returns the menu of what can be done with
    it."""
    if self.__context_menu__ is not None:
      self.__context_menu__.deleteLater()
    menu = self.__context_menu__ = QMenu(self)
    grip = self.gripAt(point)
    kind = None if grip is None else grip.kind
    if kind in (GripNum.SUPPORT, *_ENDS):
      self.select(DiskGrip(GripNum.SUPPORT, grip.index, grip.edge))
      self._supportMenu(menu, grip.index)
    elif kind is GripNum.LOAD:
      self.select(grip)
      self._loadMenu(menu, grip.index)
    elif kind is GripNum.REBAR:
      self.select(grip)
      self._offer(menu, 'Remove reinforcement', self.removeSelected)
    else:
      edge = self.edgeAt(point)
      self.select(_DISK)
      if edge is None:
        self._diskMenu(menu)
      else:
        self._edgeMenu(menu, edge, point)
    return menu

  def edit(self, disk: Disk) -> None:
    """The 'edit' method shows 'disk' as an edit, which can be undone,
    and tells of it."""
    if not isinstance(disk, Disk):
      raise TypeException('disk', disk, Disk)
    if self.disk is not None:
      self._remember(self.disk)
    self._show(disk)

  def undo(self, ) -> None:
    """The 'undo' method goes back to the disk before the last edit."""
    if self._undoList():
      self._redoList().append(self.disk)
      self._show(self._undoList().pop())

  def redo(self, ) -> None:
    """The 'redo' method goes forward to the disk the last undo left."""
    if self._redoList():
      self._undoList().append(self.disk)
      self._show(self._redoList().pop())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # \__________
  #  Mapping  ]
  # /¨¨¨¨¨¨¨¨¨¨

  def _fittedMapping(self, ) -> tuple[float, QPointF]:
    """The scale, and where the disk's origin is, fitting the disk in
    the frame and centring it."""
    frame, disk = self.frameRect(), self.disk
    scale = min(frame.width() / disk.length, frame.height() / disk.height)
    center = frame.center()
    left = center.x() - disk.length * scale / 2
    bottom = center.y() + disk.height * scale / 2
    return scale, QPointF(left, bottom)

  def _mapping(self, ) -> tuple[float, QPointF]:
    """The mapping held still during a drag, else the fitted one."""
    if self.__frozen_mapping__ is not None:
      return self.__frozen_mapping__
    return self._fittedMapping()

  def _liveMapping(self, ) -> tuple[float, QPointF]:
    """The mapping, which needs a disk shown."""
    if self.disk is None:
      raise MissingVariable(self, '__shown_disk__', Disk)
    return self._mapping()

  # \_________________________
  #  What the mouse is over  ]
  # /¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨

  def _handleAt(self, point: QPointF) -> DiskGrip | None:
    """The handle of what is selected at 'point', if any."""
    selection, reach = self.selection, self.__fallback_grip_reach__
    if selection.kind is GripNum.DISK:
      kinds, places = _HANDLES, self.handlePoint
    elif selection.kind is GripNum.SUPPORT:
      kinds, places = _ENDS, self.supportEndPoint
    else:
      return None
    for kind in kinds:
      offset = places(kind) - point
      if max(abs(offset.x()), abs(offset.y())) <= reach:
        return DiskGrip(kind, selection.index, selection.edge)
    return None

  def _cursorFor(self, grip: DiskGrip | None) -> Qt.CursorShape:
    """The cursor telling what 'grip' does."""
    if grip is None or grip.kind is GripNum.DISK:
      return _SHAPE.ArrowCursor
    kind = grip.kind
    if kind is GripNum.LENGTH:
      return _SHAPE.SizeHorCursor
    if kind is GripNum.HEIGHT:
      return _SHAPE.SizeVerCursor
    if kind is GripNum.CORNER:
      return _SHAPE.SizeBDiagCursor
    if kind in _ENDS:
      horizontal = grip.edge.horizontal
      return _SHAPE.SizeHorCursor if horizontal else _SHAPE.SizeVerCursor
    held = self.__drag_grip__ is not None
    return _SHAPE.ClosedHandCursor if held else _SHAPE.OpenHandCursor

  def _hover(self, point: QPointF) -> None:
    """Shows what is under the mouse."""
    grip = None if self.disk is None else self.gripAt(point)
    self.__hover_grip__ = grip
    self.setCursor(self._cursorFor(grip))
    self.update()

  # \___________
  #  Dragging  ]
  # /¨¨¨¨¨¨¨¨¨¨¨

  def _dragTo(self, point: QPointF) -> None:
    """Shows the disk as the drag to 'point' leaves it."""
    start, origin = self.__drag_start__
    delta = point - origin
    if abs(delta.x()) + abs(delta.y()) > self.__fallback_click_slack__:
      self.dragMoved = True
    if not self.dragMoved:
      return
    grip = self.__drag_grip__
    if grip.kind in _HANDLES:
      self.__shown_disk__ = self._resizedBy(start, delta, grip.kind)
    elif grip.kind is GripNum.SUPPORT:
      self.__shown_disk__ = self._supportTo(start, point, grip.index)
    elif grip.kind is GripNum.LOAD:
      self.__shown_disk__ = self._loadBy(start, delta, grip.index)
    elif grip.kind is GripNum.REBAR:
      self.__shown_disk__ = self._rebarBy(start, delta, grip.index)
    elif grip.kind in _ENDS:
      self.__shown_disk__ = self._widenedBy(start, delta, grip)
    self.update()

  def _along(self, delta: QPointF, edge: EdgeNum) -> float:
    """How far, in metres, 'delta' runs along 'edge'."""
    scale = self.__frozen_mapping__[0]
    return (delta.x() if edge.horizontal else -delta.y()) / scale

  def _resizedBy(self, start: Disk, delta: QPointF, kind: GripNum) -> Disk:
    """The disk 'start' with a handle dragged by 'delta'."""
    scale, step = self.__frozen_mapping__[0], self.__fallback_snap_step__
    length, height = start.length, start.height
    if kind is not GripNum.HEIGHT:
      length = snapTo(length + delta.x() / scale, step)
    if kind is not GripNum.LENGTH:
      height = snapTo(height - delta.y() / scale, step)
    least = start.leastSide
    self.atWall = True if min(length, height) < least else False
    return start.resized(
      max(length, least), max(height, least),
      start.thickness
      )

  def _nearestEdge(self, point: QPointF, current: EdgeNum) -> EdgeNum:
    """The edge nearest 'point' on the screen; the current one unless
    another is clearly nearer."""
    disk, distances, nearest = self.disk, {}, current
    for edge in EdgeNum:
      first = self.toScreen(*disk.pointAt(edge, 0.0))
      last = self.toScreen(*disk.pointAt(edge, disk.edgeLength(edge)))
      span = last - first
      along = min(max(dot(point - first, span) / dot(span, span), 0.0), 1.0)
      off = point - (first + span * along)
      distances[edge] = dot(off, off) ** 0.5
      if distances[edge] < distances.get(nearest, float('inf')):
        nearest = edge
    stick = self.__fallback_edge_stick__
    if distances[nearest] + stick < distances[current]:
      return nearest
    return current

  def _supportTo(self, start: Disk, point: QPointF, index: int) -> Disk:
    """The disk 'start' with support 'index' following the mouse to
    'point' round the edges, up to its neighbours; on another edge a
    roller holds the disk across that edge."""
    support = start.supports[index]
    edge = self._nearestEdge(point, self.disk.supports[index].edge)
    x, y = self.toModel(point)
    width = min(support.width, start.edgeLength(edge))
    wanted = snapTo(
      (x if edge.horizontal else y) - width / 2,
      self.__fallback_snap_step__
      )
    if edge is support.edge:
      low, high = start.supportRoom(index)
    else:
      low, high = 0.0, start.edgeLength(edge)
    position = round(min(max(wanted, low), high - width), 9)
    end = round(position + width, 9)
    if not start.isFree(edge, position, end, index):
      return self.disk
    setsX, setsY = support.setsX, support.setsY
    if edge is not support.edge and not (setsX and setsY):
      setsX = False if edge.horizontal else True
      setsY = not setsX
    disk = Disk(start)
    disk.replaceSupport(index, Support(edge, position, end, setsX, setsY))
    return disk

  def _loadBy(self, start: Disk, delta: QPointF, index: int) -> Disk:
    """The disk 'start' with load 'index' slid by 'delta' along its edge,
    within the edge."""
    load = start.loads[index]
    length, width = start.edgeLength(load.edge), load.width
    position = snapTo(
      load.start + self._along(delta, load.edge),
      self.__fallback_snap_step__
      )
    position = round(min(max(position, 0.0), length - width), 9)
    moved = Load(
      load.edge, position, round(position + width, 9), load.fx,
      load.fy
      )
    disk = Disk(start)
    disk.replaceLoad(index, moved)
    return disk

  def _rebarBy(self, start: Disk, delta: QPointF, index: int) -> Disk:
    """The disk 'start' with the bars 'index' moved by 'delta', to the
    centimetre, inside the disk."""
    rebar, step = start.rebars[index], self.__fallback_rebar_snap__
    scale = self.__frozen_mapping__[0]
    xs, ys = (rebar.start[0], rebar.end[0]), (rebar.start[1], rebar.end[1])
    dx = snapTo(delta.x() / scale, step)
    dy = snapTo(-delta.y() / scale, step)
    dx = min(max(dx, -min(xs)), start.length - max(xs))
    dy = min(max(dy, -min(ys)), start.height - max(ys))
    points = [round(value, 9) for value in (
      xs[0] + dx, ys[0] + dy,
      xs[1] + dx, ys[1] + dy
    )]
    moved = Disk(start)
    moved.replaceRebar(index, Rebar(*points, rebar.count, rebar.diameter))
    return moved

  def _widenedBy(self, start: Disk, delta: QPointF, grip: DiskGrip) -> Disk:
    """The disk 'start' with an end of a support's plate dragged by
    'delta', between its neighbours and never narrower than a snap."""
    support, step = start.supports[grip.index], self.__fallback_snap_step__
    low, high = start.supportRoom(grip.index)
    along = self._along(delta, support.edge)
    first, last = support.start, support.end
    if grip.kind is GripNum.SUPPORT_END:
      last = min(max(snapTo(last + along, step), first + step), high)
    else:
      first = max(min(snapTo(first + along, step), last - step), low)
    widened = Support(
      support.edge, round(first, 9), round(last, 9),
      support.setsX, support.setsY
      )
    disk = Disk(start)
    disk.replaceSupport(grip.index, widened)
    return disk

  def _endDrag(self, ) -> None:
    """Lets go: the drawing fits the frame again."""
    self.__drag_grip__, self.__drag_start__ = None, None
    self.__frozen_mapping__ = None
    self.dragMoved, self.atWall = False, False

  # \________
  #  Menus  ]
  # /¨¨¨¨¨¨¨¨

  def _offer(
      self, menu: QMenu, text: str, method: Callable,
      *args
      ) -> QAction:
    """Adds 'text' to 'menu', doing 'method' with 'args' when chosen."""
    action = menu.addAction(text)
    action.triggered.connect(partial(self._chosen, method, args))
    return action

  @staticmethod
  def _chosen(method: Callable, args: tuple, *_) -> None:
    """Does what a menu entry offers, whatever the menu tells beside."""
    method(*args)

  def _supportMenu(self, menu: QMenu, index: int) -> None:
    support = self.disk.supports[index]
    pin = True if support.setsX and support.setsY else False
    for text, choice in (('Roller', False), ('Pin', True)):
      action = self._offer(menu, text, self.turnSelected, choice)
      action.setCheckable(True)
      action.setChecked(True if choice is pin else False)
    menu.addSeparator()
    self._offer(menu, 'Remove support', self.removeSelected)

  def _loadMenu(self, menu: QMenu, index: int) -> None:
    load = self.disk.loads[index]
    whole = self.disk.edgeLength(load.edge) - load.width < 1e-9
    self._offer(menu, 'Reverse', self.reverseSelected)
    spread = self._offer(menu, 'Spread over the edge', self.spreadSelected)
    spread.setEnabled(not whole)
    menu.addSeparator()
    self._offer(menu, 'Remove load', self.removeSelected)

  def _edgeMenu(self, menu: QMenu, edge: EdgeNum, point: QPointF) -> None:
    support = self._supportHere(edge, point)
    action = self._offer(menu, 'Add support here', self._addHere, support)
    action.setEnabled(support is not None)
    self._offer(
      menu, 'Add load here', self._addHere,
      self._loadHere(edge, point)
      )

  def _diskMenu(self, menu: QMenu) -> None:
    self._offer(menu, 'Add support', self.addSupport)
    self._offer(menu, 'Add load', self.addLoad)
    self._offer(menu, 'Add reinforcement', self.addRebar)
    menu.addSeparator()
    self._offer(menu, 'Undo', self.undo).setEnabled(self.canUndo)
    self._offer(menu, 'Redo', self.redo).setEnabled(self.canRedo)

  def _stretchHere(
      self, edge: EdgeNum,
      point: QPointF
      ) -> tuple[float, float]:
    """A stretch as wide as a new support, centred where 'point' is on
    'edge', snapped and kept on the edge."""
    x, y = self.toModel(point)
    length = self.disk.edgeLength(edge)
    width = min(self.__fallback_support_width__, length)
    start = snapTo(
      (x if edge.horizontal else y) - width / 2,
      self.__fallback_snap_step__
      )
    start = round(min(max(start, 0.0), length - width), 9)
    return start, round(start + width, 9)

  def _supportHere(self, edge: EdgeNum, point: QPointF) -> Support | None:
    """A roller where 'point' is on 'edge', or 'None' where it would
    overlap a support."""
    start, end = self._stretchHere(edge, point)
    if not self.disk.isFree(edge, start, end):
      return None
    across = False if edge.horizontal else True
    return Support(edge, start, end, across, not across)

  def _loadHere(self, edge: EdgeNum, point: QPointF) -> Load:
    """A load where 'point' is on 'edge', pressing on the edge."""
    start, end = self._stretchHere(edge, point)
    ox, oy = edge.outward
    force = -self.__fallback_load_force__
    return Load(edge, start, end, -ox * force + 0.0, -oy * force + 0.0)

  def _addHere(self, part: Support | Load | None) -> None:
    """Adds 'part', a support or a load, and selects it."""
    if part is None:
      return
    added = Disk(self.disk)
    if isinstance(part, Support):
      added.addSupport(part)
      grip = DiskGrip(GripNum.SUPPORT, len(added.supports) - 1, part.edge)
    else:
      added.addLoad(part)
      grip = DiskGrip(GripNum.LOAD, len(added.loads) - 1, part.edge)
    self.edit(added)
    self.select(grip)

  def _replaceSelectedLoad(self, change: Callable) -> None:
    """Puts the selected load changed by 'change' in its place."""
    grip = self.selection
    if grip.kind is not GripNum.LOAD:
      return
    changed = Disk(self.disk)
    changed.replaceLoad(grip.index, change(self.disk.loads[grip.index]))
    self.edit(changed)

  # \__________
  #  History  ]
  # /¨¨¨¨¨¨¨¨¨¨

  def _remember(self, disk: Disk) -> None:
    """Keeps 'disk' to go back to; what was undone is gone."""
    self._undoList().append(disk)
    self._redoList().clear()

  def _show(self, disk: Disk) -> None:
    """Shows 'disk' as an edit, keeps the selection where it still is,
    and tells of it."""
    self.__shown_disk__ = disk
    grip = self.selection
    parts = {
      GripNum.SUPPORT: disk.supports, GripNum.LOAD: disk.loads,
      GripNum.REBAR  : disk.rebars
    }.get(grip.kind, ())
    if grip.kind is not GripNum.DISK and not grip.index < len(parts):
      self.select(_DISK)
    self.update()
    self.diskEdited.emit()
