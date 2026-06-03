"""
CADWindow composes the drawing app from a central 'CADWidget' canvas and a
left tool panel holding three grouped sections: 'Selection' (the list of
existing items and 'Clear all'), 'New item' (the vertex fields) and 'Viewer'
(grid, snap and zoom). The panel and canvas sit in a 'QSplitter', so the
layout is fully under the app's control - no separate top-level windows for
the compositor to misplace. The window owns the wiring between the tools and
the canvas and reports the hovered world coordinate on the status bar.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
  QMainWindow,
  QMessageBox,
  QFileDialog,
  QSplitter,
  QWidget,
  QGroupBox,
  QVBoxLayout,
  QSizePolicy,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..mixin import MixinBase
from ._cad_widget import CADWidget
from ._selection_tool import SelectionToolPanel
from ._new_item_tool import NewItemToolPanel
from ._view_tool import ViewToolPanel
from ._tool_icons import (
  navigateIcon,
  selectIcon,
  anchorIcon,
  moduleIcon,
  memberIcon,
  supportIcon,
  loadIcon,
  dimensionIcon,
  angleIcon,
)
from .draw import (
  AnchorPoint,
  Member,
  buildItem,
  describeItem,
  saveScene,
  loadScene,
  sceneToData,
  sceneFromData,
)

if TYPE_CHECKING:  # pragma: no cover
  pass


class CADWindow(QMainWindow, MixinBase):
  """Main window: a central canvas beside a left panel of grouped tools."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __undo_limit__ = 100  # cap on how many edits the history keeps

  #  Private Variables
  __show_selection_action__ = None  # checkable QAction toggling the group
  __show_new_item_action__ = None
  __show_view_action__ = None
  __tool_group__ = None  # exclusive QActionGroup for the tool palette
  __tool_actions__ = None  # data ('navigate'/kind) -> checkable QAction
  __splitter__ = None  # central panel|canvas splitter
  __tool_boxes__ = None  # key -> QGroupBox wrapping each tool
  __edit_index__ = None  # scene index being edited, or None when creating
  # new
  __undo_stack__ = None  # scene snapshots preceding each edit (list)
  __redo_stack__ = None  # snapshots undone, available to redo (list)
  __undo_action__ = None  # the Edit > Undo QAction
  __redo_action__ = None  # the Edit > Redo QAction
  __saved_state__ = None  # sceneToData of the scene as last saved/loaded
  __file_path__ = None  # the model's file on disk, or None while untitled

  #  Public Variables
  canvas = AttriBox[CADWidget](THIS)
  selectionTool = AttriBox[SelectionToolPanel](THIS)
  newItemTool = AttriBox[NewItemToolPanel](THIS)
  viewTool = AttriBox[ViewToolPanel](THIS)
  dirty = AttriBox[bool](False)  # scene differs from the last saved file

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """Build menus, toolbar, the split canvas/panel and the status bar."""
    self._updateTitle()
    self.resize(900, 600)
    self._buildMenus()
    self._buildToolBar()
    self._buildCentral()
    self._connectSignals()
    self._markSaved()  # the empty startup scene is the clean baseline
    self.statusBar().showMessage(
        'Pick a tool: Navigate pans, the shape tools draw on the canvas'
    )

  def _buildMenus(self, ) -> None:
    """Populate the menubar."""
    fileMenu = self.menuBar().addMenu('&File')
    fileMenu.addAction(self._action('&Open...', 'Ctrl+O', self._onOpen))
    fileMenu.addAction(self._action('&Save', 'Ctrl+S', self._onSave))
    fileMenu.addAction(self._action('&Rename...', 'Ctrl+R', self._onRename))
    fileMenu.addSeparator()
    fileMenu.addAction(self._action('&Quit', 'Ctrl+Q', self.close))
    editMenu = self.menuBar().addMenu('&Edit')
    self.__undo_action__ = self._action('&Undo', 'Ctrl+Z', self._onUndo)
    self.__redo_action__ = self._action(
        '&Redo', 'Ctrl+Shift+Z', self._onRedo
    )
    editMenu.addAction(self.__undo_action__)
    editMenu.addAction(self.__redo_action__)
    self._updateUndoActions()  # start disabled until the first edit
    viewMenu = self.menuBar().addMenu('&View')
    viewMenu.addAction(self._action('&Reset view', 'Ctrl+0', self._onReset))
    viewMenu.addAction(
        self._action('&Delete selected (Del)', '', self._deleteSelected)
    )
    viewMenu.addAction(self._action('&Clear', 'Ctrl+L', self._onClear))
    viewMenu.addSeparator()
    self.__show_selection_action__ = self._toggle(
        'Show &selection tool', self._onShowSelection
    )
    self.__show_new_item_action__ = self._toggle(
        'Show &new-item tool', self._onShowNewItem
    )
    self.__show_view_action__ = self._toggle(
        'Show &viewer tool', self._onShowView
    )
    viewMenu.addAction(self.__show_selection_action__)
    viewMenu.addAction(self.__show_new_item_action__)
    viewMenu.addAction(self.__show_view_action__)

  def _buildToolBar(self, ) -> None:
    """Build the icon palette: Navigate, Select, Anchor, Module, dims."""
    bar = self.addToolBar('Tools')
    bar.setMovable(False)
    bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    group = QActionGroup(self)
    group.setExclusive(True)
    self.__tool_actions__ = dict()
    specs = (
      ('navigate', 'Navigate (pan / zoom)', navigateIcon()),
      ('select', 'Select (pick an item)', selectIcon()),
      ('Anchor', 'Anchor point (double-click to place)', anchorIcon()),
      (
        'support', 'Support (click an anchor to cycle its support)',
        supportIcon()
      ),
      (
        'load', 'Load (drag a force out of an anchor; click it to clear)',
        loadIcon()
      ),
      (
        'Module', 'Module line (drag from origin toward its angle)',
        moduleIcon()
      ),
      (
        'Member', 'Structural member (drag between two anchor nodes)',
        memberIcon()
      ),
      ('Dimension', 'Dimension', dimensionIcon()),
      (
        'Angle', 'Angular dimension (click vertex, then two arms)',
        angleIcon()
      ),
    )
    for data, tip, icon in specs:
      action = QAction(icon, tip, self)
      action.setCheckable(True)
      action.setToolTip(tip)
      action.setData(data)
      group.addAction(action)
      bar.addAction(action)
      self.__tool_actions__[data] = action
    self.__tool_actions__['navigate'].setChecked(True)
    group.triggered.connect(self._onToolSelected)
    self.__tool_group__ = group

  def _buildCentral(self, ) -> None:
    """
    Build a splitter with a left panel of grouped tools and the canvas on
    the right. The 'New item' and 'Viewer' groups take exactly their natural
    height; only the 'Selection' list absorbs spare space (and scrolls
    internally if long) - the panel itself never scrolls.
    """
    self.selectionTool.build()
    self.newItemTool.build()
    self.viewTool.build()
    column = QWidget(self)
    column.setMinimumWidth(270)
    columnLayout = QVBoxLayout(column)
    columnLayout.setContentsMargins(4, 4, 4, 4)
    self.__tool_boxes__ = dict()
    specs = (
      ('selection', 'Selection', self.selectionTool, 1),
      ('newItem', 'New item', self.newItemTool, 0),
      ('view', 'Viewer', self.viewTool, 0),
    )
    for key, title, panel, stretch in specs:
      box = QGroupBox(title, column)
      boxLayout = QVBoxLayout(box)
      boxLayout.setContentsMargins(6, 6, 6, 6)
      boxLayout.addWidget(panel)
      if not stretch:  # fix New-item / Viewer to their natural height
        box.setSizePolicy(
          QSizePolicy.Policy.Preferred,
          QSizePolicy.Policy.Fixed
          )
      columnLayout.addWidget(box, stretch)
      self.__tool_boxes__[key] = box
    self.canvas.setFocusPolicy(
      Qt.FocusPolicy.StrongFocus
      )  # for the Delete key
    splitter = QSplitter(Qt.Orientation.Horizontal, self)
    splitter.addWidget(column)
    splitter.addWidget(self.canvas)
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    splitter.setSizes([280, 620])
    self.setCentralWidget(splitter)
    self.__splitter__ = splitter

  def _connectSignals(self, ) -> None:
    """Wire the tool controls and the canvas hover readout."""
    self.newItemTool.addButton.clicked.connect(self._onAdd)
    self.newItemTool.deleteButton.clicked.connect(self._deleteSelected)
    self.selectionTool.clearButton.clicked.connect(self._onClear)
    self.selectionTool.itemList.currentRowChanged.connect(self._onSelectRow)
    self.canvas.setHoverCallback(self._onHover)
    self.canvas.setAddCallback(self._onCanvasAdd)
    self.canvas.setDragCallback(self._onDrag)
    self.canvas.setPickCallback(self._pickItem)
    self.canvas.setDeleteCallback(self._deleteSelected)
    self.canvas.setSupportCallback(self._onCycleSupport)
    self.canvas.setLoadCallback(self._onSetLoad)
    self.canvas.setDisplaceCallback(self._onSetDisplace)
    self.canvas.setMemberCallback(self._onAddMember)
    #  Default: navigate mode, but a kind is ready so the Add button works.
    self.canvas.setActiveKind('Anchor')
    self.newItemTool.configureFor('Anchor')
    self.canvas.setMode('navigate')
    self.viewTool.showGridCheck.toggled.connect(self.canvas.setShowGrid)
    self.viewTool.snapCheck.toggled.connect(self.canvas.setSnap)
    self.viewTool.gridSlider.valueChanged.connect(self._onGridSpacingSlider)
    self.viewTool.gridEdit.editingFinished.connect(self._onGridSpacingEdit)
    self.viewTool.resetButton.clicked.connect(self._onReset)
    self.canvas.setViewChangedCallback(self._onViewChanged)
    self._onViewChanged()  # seed the millimetre readout

  def _action(self, text: str, shortcut: str, slot) -> QAction:
    """Build a 'QAction' with text, shortcut and triggered handler."""
    action = QAction(text, self)
    action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(slot)
    return action

  def _toggle(self, text: str, slot) -> QAction:
    """Build a checkable 'QAction' whose toggled state drives 'slot'."""
    action = QAction(text, self)
    action.setCheckable(True)
    action.toggled.connect(slot)
    return action

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HANDLERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addItem(self, item: object) -> None:
    """
    Add 'item' to the scene and the selection list, keeping the two
    index-aligned, zooming out if it falls outside the view. This is the
    single path for adding items; the Add button and any programmatic
    seeding both use it.
    """
    self._pushUndo()  # record the pre-edit scene so this add can be undone
    self.canvas.scene.addItem(item)
    self._refreshDirty()  # now differs from the saved baseline
    self.canvas.ensureContains(item)  # zoom out if the item is off-view
    self.canvas.update()
    self.selectionTool.itemList.addItem(str(item))
    self.statusBar().showMessage('Added %s' % (item,), 2000)

  def _onAdd(self, *_) -> None:
    """Add a new item, or update the selected item when in edit mode."""
    kind = self.canvas.activeKind()
    #  Editing an anchor changes its coordinates IN PLACE, so members that
    #  reference it keep their connection (a new object would orphan them).
    if self.__edit_index__ is not None:
      items = self.canvas.scene.items
      if 0 <= self.__edit_index__ < len(items):
        target = items[self.__edit_index__]
        if isinstance(target, AnchorPoint):
          self._updateAnchor(target)
          return
    try:
      vertices = self.newItemTool.vertexEditor.vertices()
      item = buildItem(kind, vertices)
    except ValueError as error:
      self.statusBar().showMessage(str(error), 4000)
      return
    if self.__edit_index__ is not None:
      self._replaceItem(self.__edit_index__, item)
      return
    self.addItem(item)
    #  Keep the just-used coordinates as the running default for this kind.
    self.newItemTool.rememberLast(kind, vertices)

  def _updateAnchor(self, anchor: object) -> None:
    """
    Apply the edited coordinates, load components and (when supported)
    settlement to 'anchor' in place, so members referencing it follow.
    """
    try:
      x, y, loadX, loadY, dispX, dispY = self.newItemTool.anchorValues()
    except (ValueError, IndexError):
      self.statusBar().showMessage('Each value must be a number', 4000)
      return
    self._pushUndo()
    anchor.x = float(x)
    anchor.y = float(y)
    anchor.loadX = loadX
    anchor.loadY = loadY
    if anchor.supportKind() == 'free':  # a settlement needs a support
      dispX = dispY = 0.0
    anchor.dispX = dispX
    anchor.dispY = dispY
    self._refreshDirty()
    items = self.canvas.scene.items
    row = self.selectionTool.itemList.item(items.index(anchor))
    row.setText(str(anchor))
    self.canvas.update()
    self.statusBar().showMessage('Updated %s' % (anchor,), 2000)

  def _onAddMember(self, anchorA: object, anchorB: object) -> None:
    """Add a structural member between two anchor nodes (a canvas drag)."""
    self.addItem(Member(anchorA, anchorB))

  def _deleteSelected(self, *_) -> None:
    """
    Remove the edited item. Deleting an anchor cascades: every member that
    references it is removed too (a node and its members go together), as one
    undoable step.
    """
    index = self.__edit_index__
    items = self.canvas.scene.items
    if index is None or not (0 <= index < len(items)):
      return
    self._pushUndo()
    target = items[index]
    doomed = {id(target)}
    if isinstance(target, AnchorPoint):
      for item in items:
        if isinstance(item, Member):
          if item.nodeA is target or item.nodeB is target:
            doomed.add(id(item))
    items[:] = [item for item in items if id(item) not in doomed]
    self._refreshDirty()
    self._syncListToScene()  # indices shifted: rebuild the list to match
    self._enterNewMode()  # clears the selection and the row, back to New
    self.canvas.update()
    self.statusBar().showMessage('Deleted %d item(s)' % (len(doomed),), 2000)

  def _replaceItem(self, index: int, item: object) -> None:
    """Replace the item at 'index' in place (edit), refreshing its row."""
    items = self.canvas.scene.items
    if not (0 <= index < len(items)):
      return
    self._pushUndo()
    items[index] = item
    self._refreshDirty()
    self.canvas.setSelected(item)
    self.canvas.ensureContains(item)
    self.canvas.update()
    self.selectionTool.itemList.item(index).setText(str(item))
    self.statusBar().showMessage('Updated %s' % (item,), 2000)

  def clearScene(self, ) -> None:
    """Remove every item from the scene, the list and the selection."""
    self._pushUndo()
    self.canvas.scene.clear()
    self._refreshDirty()
    self.canvas.setSelected(None)
    self.canvas.update()
    self.selectionTool.itemList.clear()
    self._enterNewMode()  # nothing left to edit
    self.statusBar().showMessage('Cleared', 2000)

  def _confirmClear(self, ) -> bool:
    """Ask before discarding the whole scene. True means go ahead."""
    yes = QMessageBox.StandardButton.Yes
    no = QMessageBox.StandardButton.No
    question = 'Remove all %d item(s)?' % (len(self.canvas.scene),)
    answer = QMessageBox.question(self, 'Clear all', question, yes | no)
    return True if answer == yes else False

  def _onClear(self, *_) -> None:
    """Clear the scene, confirming first when it holds any items."""
    if len(self.canvas.scene) and not self._confirmClear():
      return
    self.clearScene()

  def _onReset(self, *_) -> None:
    """Restore the default zoom and centre on the origin."""
    self.canvas.resetView()
    self.statusBar().showMessage('View reset', 2000)

  def _setBoxVisible(self, key: str, visible: bool) -> None:
    """Show or hide one grouped tool section in the left panel."""
    boxes = self.__tool_boxes__ or dict()
    if key in boxes:
      boxes[key].setVisible(visible)

  def _onShowSelection(self, visible: bool) -> None:
    """Show or hide the selection group."""
    self._setBoxVisible('selection', visible)

  def _onShowNewItem(self, visible: bool) -> None:
    """Show or hide the new-item group."""
    self._setBoxVisible('newItem', visible)

  def _onShowView(self, visible: bool) -> None:
    """Show or hide the viewer group."""
    self._setBoxVisible('view', visible)

  def _applyGridSpacing(self, pixels: float) -> None:
    """Clamp 'pixels' to the allowed range, apply it, and sync the
    widgets."""
    low, high = self.viewTool.spacingRange()
    pixels = max(low, min(high, int(round(pixels))))
    self.canvas.setGridTargetPx(float(pixels))
    self.viewTool.setSpacing(pixels)

  def _onGridSpacingSlider(self, pixels: int) -> None:
    """Apply the grid spacing chosen with the slider."""
    self._applyGridSpacing(pixels)

  def _onGridSpacingEdit(self, ) -> None:
    """Apply a precise grid spacing typed into the line edit."""
    text = self.viewTool.gridEdit.text()
    try:
      pixels = int(round(float(text)))
    except ValueError:
      self.viewTool.setSpacing(int(self.canvas.gridTargetPx))
      return
    self._applyGridSpacing(pixels)

  def _applyTool(self, data: str) -> None:
    """
    Apply a tool-palette choice: 'navigate' pans, 'select'/'support' switch
    to those modes, a kind name switches to draw mode for that kind.
    """
    if data in ('navigate', 'select', 'support', 'load'):
      self.canvas.setMode(data)
      return
    self.canvas.setMode('draw')
    self.canvas.setActiveKind(data)
    self.newItemTool.configureFor(data)

  def _onToolSelected(self, action: QAction) -> None:
    """Handle a click on a tool-palette icon."""
    data = action.data()
    if data not in ('navigate', 'select', 'support', 'load'):
      self._enterNewMode()  # choosing a shape tool means 'create new'
    self._applyTool(data)

  def _selectTool(self, data: str) -> None:
    """Check a tool icon programmatically and apply it."""
    action = (self.__tool_actions__ or dict()).get(data)
    if action is not None:
      action.setChecked(True)
    self._applyTool(data)

  def _enterEditMode(self, index: int) -> None:
    """Re-title the New-item tool to edit the selected item in place, and
    reveal the Delete button so the edited item can be removed."""
    self.__edit_index__ = index
    if self.__tool_boxes__ is not None:
      self.__tool_boxes__['newItem'].setTitle('Edit item')
    self.newItemTool.addButton.setText('Update item')
    self.newItemTool.deleteButton.setVisible(True)

  def _enterNewMode(self, ) -> None:
    """Return the New-item tool to creating new items, and deselect."""
    self.__edit_index__ = None
    if self.__tool_boxes__ is not None:
      self.__tool_boxes__['newItem'].setTitle('New item')
    self.newItemTool.addButton.setText('Add item')
    self.newItemTool.deleteButton.setVisible(False)
    self.canvas.setSelected(None)
    itemList = self.selectionTool.itemList
    blocked = itemList.blockSignals(True)
    itemList.setCurrentRow(-1)
    itemList.blockSignals(blocked)

  def _selectItem(self, index: int) -> None:
    """Select scene item 'index' for editing in the bespoke Edit tool."""
    items = self.canvas.scene.items
    if not (0 <= index < len(items)):
      self.canvas.setSelected(None)
      self._enterNewMode()
      return
    item = items[index]
    self.canvas.setSelected(item)
    if isinstance(item, AnchorPoint):
      self.newItemTool.editAnchor(item, self._membersOf(item))
      self.canvas.setActiveKind('Anchor')
    elif isinstance(item, Member):
      self.newItemTool.editMember(self._memberInfo(item))
      self.canvas.setActiveKind('Member')
    else:
      kind, vertices = describeItem(item)
      self.canvas.setActiveKind(kind)
      self.newItemTool.loadItem(kind, vertices)
    self._selectTool('select')
    self._enterEditMode(index)

  def _membersOf(self, anchor: object) -> list:
    """The label of every member attached to 'anchor'."""
    return [str(item) for item in self.canvas.scene
            if isinstance(item, Member)
            and (item.nodeA is anchor or item.nodeB is anchor)]

  @staticmethod
  def _memberInfo(member: object) -> str:
    """A summary naming a member's two end nodes."""
    return 'Node A: %s\nNode B: %s' % (member.nodeA, member.nodeB)

  def _onCanvasAdd(self, kind: str, vertices: list) -> None:
    """Add an item drawn with the mouse, reusing the keyboard add path."""
    try:
      item = buildItem(kind, vertices)
    except ValueError as error:
      self.statusBar().showMessage(str(error), 4000)
      return
    self.addItem(item)
    self.newItemTool.rememberLast(kind, vertices)

  def _onSelectRow(self, row: int) -> None:
    """Select the item for the chosen list row (for editing)."""
    self._selectItem(row)

  def _pickItem(self, index: int) -> None:
    """Select an item clicked on the canvas with the Select tool."""
    self._selectItem(index)
    itemList = self.selectionTool.itemList
    blocked = itemList.blockSignals(True)  # reflect without re-entering
    itemList.setCurrentRow(index)
    itemList.blockSignals(blocked)

  def _onCycleSupport(self, anchor: object) -> None:
    """Cycle the boundary condition on the anchor clicked in support mode."""
    self._pushUndo()
    kind = anchor.cycleSupport()
    self._refreshDirty()
    items = self.canvas.scene.items
    if anchor in items:  # refresh the list row to show the new support
      self.selectionTool.itemList.item(items.index(anchor)).setText(
          str(anchor)
      )
    self.canvas.update()
    self.statusBar().showMessage('Support: %s' % (kind,), 2000)

  def _onSetLoad(self, anchor: object, fx: float, fy: float) -> None:
    """Set the nodal load on an anchor dragged in load mode (a near-zero
    drag clears it). Skips the edit when the load is unchanged."""
    if (anchor.loadX, anchor.loadY) == (fx, fy):
      return
    self._pushUndo()
    anchor.loadX = fx
    anchor.loadY = fy
    self._refreshDirty()
    items = self.canvas.scene.items
    if anchor in items:  # refresh the list row to show the new load
      self.selectionTool.itemList.item(items.index(anchor)).setText(
          str(anchor)
      )
    self.canvas.update()
    self.statusBar().showMessage('Load: (%.2f, %.2f) N' % (fx, fy), 2000)

  def _onSetDisplace(self, anchor: object, dx: float, dy: float) -> None:
    """Set the prescribed support displacement on an anchor (a settlement
    that forces the node off equilibrium). Skips an unchanged edit."""
    if (anchor.dispX, anchor.dispY) == (dx, dy):
      return
    self._pushUndo()
    anchor.dispX = dx
    anchor.dispY = dy
    self._refreshDirty()
    items = self.canvas.scene.items
    if anchor in items:  # refresh the list row to show the displacement
      self.selectionTool.itemList.item(items.index(anchor)).setText(
          str(anchor)
      )
    self.canvas.update()
    self.statusBar().showMessage(
        'Prescribed displacement: (%.2f, %.2f)' % (dx, dy), 2000
    )

  def _onViewChanged(self, ) -> None:
    """
    Refresh the viewer's factor readout. Zoomed out (scale <= 1) it reads in
    millimetres per pixel; zoomed in it swaps to pixels per millimetre.
    """
    if self.canvas.scale <= 1.0:
      self.viewTool.setFactor(self.canvas.viewFactor(), True)
    else:
      self.viewTool.setFactor(self.canvas.scale, False)

  def _onHover(self, wx: float, wy: float) -> None:
    """Show the world coordinate (mm) currently under the pointer."""
    self.statusBar().showMessage('x = %.3f mm,  y = %.3f mm' % (wx, wy))

  def _onDrag(self, kind: str, start: tuple, end: tuple) -> None:
    """Show the live geometry of an in-progress press-drag gesture."""
    (sx, sy), (ex, ey) = start, end
    span = '(%.2f, %.2f) -> (%.2f, %.2f)' % (sx, sy, ex, ey)
    if kind == 'Module':
      angle = math.degrees(math.atan2(ey - sy, ex - sx))
      message = ('Module  origin (%.2f, %.2f)   %.1f deg from horizontal'
                 % (sx, sy, angle))
    elif kind == 'Member':
      length = math.hypot(ex - sx, ey - sy)
      angle = math.degrees(math.atan2(ey - sy, ex - sx))
      message = ('Member  %s   len %.2f mm   %.1f deg'
                 % (span, length, angle))
    elif kind == 'Dimension':
      dx, dy = ex - sx, ey - sy
      length = math.hypot(dx, dy)
      fromHorizontal = math.degrees(math.atan2(dy, dx))
      fromVertical = math.degrees(math.atan2(dx, dy))
      message = ('Dimension  %s   len %.2f mm   %.1f deg from horizontal,  '
                 '%.1f deg from vertical'
                 % (span, length, fromHorizontal, fromVertical))
    else:
      message = 'x = %.2f mm,  y = %.2f mm' % (ex, ey)
    self.statusBar().showMessage(message)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  UNDO / REDO   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _snapshot(self, ) -> dict:
    """A JSON-native snapshot of the current scene for the history stacks."""
    return sceneToData(self.canvas.scene)

  def _pushUndo(self, ) -> None:
    """
    Record the current scene before an edit so it can be undone. A new edit
    invalidates the redo trail, and the history is capped at '__undo_limit__'
    entries (the oldest is dropped).
    """
    if self.__undo_stack__ is None:
      self.__undo_stack__ = []
    if self.__redo_stack__ is None:
      self.__redo_stack__ = []
    self.__undo_stack__.append(self._snapshot())
    while len(self.__undo_stack__) > self.__undo_limit__:
      del self.__undo_stack__[0]
    self.__redo_stack__.clear()
    self._updateUndoActions()

  def _clearHistory(self, ) -> None:
    """Drop all undo/redo history (e.g. after opening another drawing)."""
    self.__undo_stack__ = []
    self.__redo_stack__ = []
    self._updateUndoActions()

  def _restoreSnapshot(self, snapshot: dict) -> None:
    """Replace the scene with 'snapshot' and refresh the dependent UI."""
    sceneFromData(snapshot, self.canvas.scene)
    self._syncListToScene()
    self._enterNewMode()  # the restored scene starts with nothing selected
    self.canvas.update()

  def _updateUndoActions(self, ) -> None:
    """Enable each of Undo and Redo only while its stack has entries."""
    if self.__undo_action__ is not None:
      self.__undo_action__.setEnabled(bool(self.__undo_stack__))
    if self.__redo_action__ is not None:
      self.__redo_action__.setEnabled(bool(self.__redo_stack__))

  def _onUndo(self, *_) -> None:
    """Revert the most recent edit, if there is one to revert."""
    stack = self.__undo_stack__ or []
    if not stack:
      return
    if self.__redo_stack__ is None:
      self.__redo_stack__ = []
    self.__redo_stack__.append(self._snapshot())  # so it can be redone
    self._restoreSnapshot(stack.pop())
    self._refreshDirty()  # clean again if this returns to the saved state
    self._updateUndoActions()
    self.statusBar().showMessage('Undo', 2000)

  def _onRedo(self, *_) -> None:
    """Reapply the most recently undone edit, if there is one."""
    stack = self.__redo_stack__ or []
    if not stack:
      return
    if self.__undo_stack__ is None:
      self.__undo_stack__ = []
    self.__undo_stack__.append(self._snapshot())
    self._restoreSnapshot(stack.pop())
    self._refreshDirty()  # clean again if this returns to the saved state
    self._updateUndoActions()
    self.statusBar().showMessage('Redo', 2000)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  FILE PERSISTENCE   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _syncListToScene(self, ) -> None:
    """Rebuild the selection list so it mirrors the scene row-for-row."""
    itemList = self.selectionTool.itemList
    blocked = itemList.blockSignals(True)
    itemList.clear()
    for item in self.canvas.scene:
      itemList.addItem(str(item))
    itemList.setCurrentRow(-1)
    itemList.blockSignals(blocked)

  def _sceneState(self, ) -> dict:
    """The current scene as plain data, for comparison with the baseline."""
    return sceneToData(self.canvas.scene)

  def _markSaved(self, ) -> None:
    """Adopt the current scene as the clean baseline (saved or loaded)."""
    self.__saved_state__ = self._sceneState()
    self.dirty = False
    self._updateTitle()

  def _refreshDirty(self, ) -> None:
    """
    Recompute the unsaved-changes flag by comparing the scene to the saved
    baseline, so returning to the saved state (e.g. by undo) reads as clean.
    """
    changed = self._sceneState() != self.__saved_state__
    self.dirty = True if changed else False
    self._updateTitle()

  def _updateTitle(self, ) -> None:
    """Reflect the model name and unsaved-changes state in the title bar.
    An unsaved model reads as 'untitled'; a star marks unsaved changes."""
    name = self.__file_path__ if self.__file_path__ else 'untitled'
    star = '*' if self.dirty else ''
    self.setWindowTitle('worQt CAD - %s%s' % (name, star))

  def _confirmDiscard(self, ) -> bool:
    """
    Guard against losing unsaved work. With no unsaved changes, return True
    at once (no dialog). Otherwise ask whether to save, discard or cancel:
    'Save' runs the save and proceeds only if it succeeds, 'Discard' proceeds
    and loses the edits, 'Cancel' aborts. True means it is safe to proceed.
    """
    if not self.dirty:
      return True
    save = QMessageBox.StandardButton.Save
    discard = QMessageBox.StandardButton.Discard
    cancel = QMessageBox.StandardButton.Cancel
    answer = QMessageBox.question(
        self, 'Unsaved changes',
        'The drawing has unsaved changes. Save them before continuing?',
        save | discard | cancel
    )
    if answer == save:
      return self._onSave()
    return True if answer == discard else False

  def _onSave(self, *_) -> bool:
    """
    Save the drawing to its own file on disk, with no dialog. An untitled
    model (never saved, so it has no file) cannot be saved to that name, so
    saving it runs Rename to name it first. Returns True when the drawing was
    written (clearing the unsaved-changes flag), False when it was not.
    """
    if not self.__file_path__:  # untitled: name it before any save
      return self._onRename()
    try:
      saveScene(self.canvas.scene, self.__file_path__)
    except OSError as error:
      self.statusBar().showMessage('Save failed: %s' % (error,), 4000)
      return False
    self._markSaved()  # this scene is now the clean baseline
    self.statusBar().showMessage(
        'Saved %d item(s) to %s'
        % (len(self.canvas.scene), self.__file_path__), 3000
    )
    return True

  def _onRename(self, *_) -> bool:
    """
    Give the model a (new) name and save it there. The user picks the
    destination; the current scene is written to it, and if the model already
    had a file the old one is removed once the new write succeeds,
    so a rename
    moves the model rather than leaving a copy behind (there is no 'Save
    As').
    Returns True when the drawing was written, False when it was not.
    """
    path, _filter = QFileDialog.getSaveFileName(
        self, 'Rename drawing', self.__file_path__ or '',
        'worQt drawing (*.json)'
    )
    if not path:
      return False
    if not path.endswith('.json'):
      path = '%s.json' % (path,)
    try:
      saveScene(self.canvas.scene, path)
    except OSError as error:
      self.statusBar().showMessage('Save failed: %s' % (error,), 4000)
      return False
    previous = self.__file_path__  # the file the model moves away from
    self.__file_path__ = path
    if previous and os.path.normpath(previous) != os.path.normpath(path):
      try:  # the save already succeeded; a stale old file is non-fatal
        os.remove(previous)
      except OSError:
        pass
    self._markSaved()  # the named scene is now the clean baseline
    self.statusBar().showMessage(
        'Saved %d item(s) to %s' % (len(self.canvas.scene), path), 3000
    )
    return True

  def _onOpen(self, *_) -> None:
    """Load a drawing from a JSON file, replacing the current scene."""
    if not self._confirmDiscard():  # keep unsaved work if the user cancels
      return
    path, _filter = QFileDialog.getOpenFileName(
        self, 'Open drawing', '', 'worQt drawing (*.json)'
    )
    if not path:
      return
    try:
      loadScene(path, self.canvas.scene)
    except (OSError, ValueError, KeyError) as error:
      self.statusBar().showMessage('Open failed: %s' % (error,), 4000)
      return
    self.__file_path__ = path  # Save now writes back to this file, no dialog
    self._syncListToScene()
    self._enterNewMode()  # nothing is selected after a fresh load
    self.canvas.fitAll()  # zoom-to-extents on the loaded drawing
    self.canvas.update()
    self._clearHistory()  # a freshly opened drawing starts a fresh history
    self._markSaved()  # the loaded scene matches its file: clean baseline
    self.statusBar().showMessage(
        'Loaded %d item(s) from %s' % (len(self.canvas.scene), path), 3000
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GEOMETRY PERSISTENCE   # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _settings() -> QSettings:
    """The 'QSettings' store for this app's window geometry."""
    return QSettings(
      QSettings.Format.IniFormat,
      QSettings.Scope.UserScope, 'worQt', 'draw'
      )

  def _saveGeometry(self, ) -> None:
    """Persist the main window size/position and the splitter sizes."""
    settings = self._settings()
    settings.setValue('main/geometry', self.saveGeometry())
    if self.__splitter__ is not None:
      settings.setValue('splitter/state', self.__splitter__.saveState())
    settings.sync()

  def _restoreGeometry(self, ) -> None:
    """Restore the saved main window geometry and splitter sizes, if any."""
    settings = self._settings()
    geometry = settings.value('main/geometry')
    if geometry is not None:
      self.restoreGeometry(geometry)
    state = settings.value('splitter/state')
    if state is not None and self.__splitter__ is not None:
      self.__splitter__.restoreState(state)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def closeEvent(self, event) -> None:
    """Guard unsaved changes, then save window geometry before closing."""
    if not self._confirmDiscard():
      event.ignore()  # the user cancelled: keep the window open
      return
    self._saveGeometry()
    super().closeEvent(event)

  def show(self, ) -> None:
    self.initUi()
    self._restoreGeometry()
    #  All tool groups start visible (the View toggles can hide them).
    self.__show_selection_action__.setChecked(True)
    self.__show_new_item_action__.setChecked(True)
    self.__show_view_action__.setChecked(True)
    super().show()
