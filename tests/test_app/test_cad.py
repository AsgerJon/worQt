"""
Exercises the drawing app: the coordinate-defined geometry model and the
zoomable canvas. Model assertions need no Qt; canvas assertions run against
a live 'QApplication' and force a real paint with 'grab()'. No event loop
pumping or modal dialog is involved.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QPointF

from worQt.qtest import AppTest
from worQt.cad.draw import (
  AnchorPoint,
  ModuleLine,
  Member,
  Dimension,
  AngularDimension,
  CADScene,
  KINDS,
  itemFromCoords,
  buildItem,
  describeItem,
  sceneToData,
  sceneToJson,
  sceneFromJson,
  saveScene,
  loadScene,
)
from worQt.widgets import CADWidget, VertexEditor
from worQt.window import CADWindow


class _MouseEvent:
  """A minimal stand-in for 'QMouseEvent' for driving the canvas handlers."""

  def __init__(self, x, y, button=Qt.MouseButton.LeftButton) -> None:
    self._pos = QPointF(x, y)
    self._button = button

  def button(self): return self._button

  def position(self): return self._pos

  def accept(self): pass


class _WheelEvent:
  """A minimal stand-in for 'QWheelEvent' for driving 'wheelEvent'."""

  def __init__(self, dy, x, y) -> None:
    self._dy = dy
    self._pos = QPointF(x, y)

  def angleDelta(self): return QPoint(0, self._dy)

  def position(self): return self._pos

  def accept(self): pass


class TestCAD(AppTest):
  """Covers the geometry model, the factory and the canvas transform."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MODEL (no Qt required)   # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_items_hold_coordinates(self, ) -> None:
    """Each item stores exactly the coordinates it was built with."""
    self.assertEqual((AnchorPoint(3.0, 4.0).x, AnchorPoint(3.0, 4.0).y),
                     (3.0, 4.0))
    module = ModuleLine(1.0, 2.0, 90.0)
    self.assertEqual((module.x, module.y, module.angle), (1.0, 2.0, 90.0))
    dimension = Dimension(0.0, 1.0, 2.0, 3.0)
    got = (dimension.x1, dimension.y1, dimension.x2, dimension.y2)
    self.assertEqual(got, (0.0, 1.0, 2.0, 3.0))

  def test_module_line_direction(self, ) -> None:
    """A module line yields a unit direction from its angle."""
    dx, dy = ModuleLine(0.0, 0.0, 0.0).direction()
    self.assertAlmostEqual(dx, 1.0)
    self.assertAlmostEqual(dy, 0.0)
    dx, dy = ModuleLine(0.0, 0.0, 90.0).direction()
    self.assertAlmostEqual(dx, 0.0)
    self.assertAlmostEqual(dy, 1.0)

  def test_scene_collects_items(self, ) -> None:
    """The scene appends, iterates and clears its items."""
    scene = CADScene()
    scene.addItem(AnchorPoint(1.0, 1.0))
    scene.addItem(ModuleLine(0.0, 0.0, 45.0))
    self.assertEqual(len(scene), 2)
    scene.clear()
    self.assertEqual(len(scene), 0)

  def test_factory_builds_each_kind(self, ) -> None:
    """'itemFromCoords' parses coordinates into the right item type."""
    self.assertIsInstance(itemFromCoords('Anchor', '1, 2'), AnchorPoint)
    self.assertIsInstance(itemFromCoords('Module', '0, 0, 30'), ModuleLine)
    self.assertIsInstance(itemFromCoords('Dimension', '1 2 3 4'), Dimension)

  def test_factory_rejects_bad_arity(self, ) -> None:
    """Wrong coordinate counts raise 'ValueError'."""
    with self.assertRaises(ValueError):
      itemFromCoords('Anchor', '1 2 3')
    with self.assertRaises(ValueError):
      itemFromCoords('Module', '0 0')  # missing the angle

  def test_anchor_and_module_round_trip(self, ) -> None:
    """Anchor and module describe/build round-trip through the factory."""
    anchor = buildItem('Anchor', [(1.0, 2.0)])
    self.assertIsInstance(anchor, AnchorPoint)
    self.assertEqual(describeItem(anchor), ('Anchor', [(1.0, 2.0)]))
    #  A module is built from origin + a through-point; the angle is derived.
    module = buildItem('Module', [(0.0, 0.0), (0.0, 5.0)])  # straight up
    self.assertIsInstance(module, ModuleLine)
    self.assertAlmostEqual(module.angle, 90.0)
    kind, vertices = describeItem(ModuleLine(2.0, 3.0, 30.0))
    self.assertEqual(kind, 'Module')
    self.assertAlmostEqual(buildItem(kind, vertices).angle, 30.0)
    with self.assertRaises(ValueError):
      buildItem('Module', [(0.0, 0.0)])  # needs origin + through-point

  def test_member_references_anchors_and_follows(self, ) -> None:
    """A member references two anchors; coords read through and follow."""
    a, b = AnchorPoint(0.0, 0.0), AnchorPoint(3.0, 4.0)
    member = Member(a, b)
    self.assertIs(member.nodeA, a)
    self.assertIs(member.nodeB, b)
    self.assertEqual((member.x1, member.y1, member.x2, member.y2),
                     (0.0, 0.0, 3.0, 4.0))
    self.assertAlmostEqual(member.length(), 5.0)
    self.assertEqual(describeItem(member),
                     ('Member', [(0.0, 0.0), (3.0, 4.0)]))
    a.x, a.y = 0.0, 10.0  # move the anchor -> the member tracks it
    self.assertEqual((member.x1, member.y1), (0.0, 10.0))
    self.assertIn('Member', KINDS)

  def test_member_not_built_from_coordinates(self, ) -> None:
    """Members cannot be built from raw coordinates (they need anchors)."""
    with self.assertRaises(ValueError):
      buildItem('Member', [(0.0, 0.0), (3.0, 4.0)])
    with self.assertRaises(ValueError):
      itemFromCoords('Member', '0 0 3 4')

  def test_dimension_built_from_coordinates(self, ) -> None:
    """A Dimension is built from two points and reports its length."""
    dimension = buildItem('Dimension', [(0.0, 0.0), (3.0, 4.0)])
    self.assertIsInstance(dimension, Dimension)
    self.assertAlmostEqual(dimension.length(), 5.0)
    self.assertEqual(describeItem(dimension),
                     ('Dimension', [(0.0, 0.0), (3.0, 4.0)]))
    self.assertIsInstance(itemFromCoords('Dimension', '0 0 3 4'), Dimension)

  def test_angular_dimension_from_coordinates(self, ) -> None:
    """An Angle is built from three points and reports its included angle."""
    angle = buildItem('Angle', [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)])
    self.assertIsInstance(angle, AngularDimension)
    self.assertAlmostEqual(angle.angle(), 90.0)
    self.assertEqual(describeItem(angle),
                     ('Angle', [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)]))
    self.assertIsInstance(itemFromCoords('Angle', '0 0 5 0 0 5'),
                          AngularDimension)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CANVAS (live QApplication)   # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_transform_round_trip(self, ) -> None:
    """'screenToWorld' is the inverse of 'worldToScreen'."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    wx, wy = canvas.screenToWorld(123.0, 77.0)
    back = canvas.worldToScreen(wx, wy)
    self.assertAlmostEqual(back.x(), 123.0, places=6)
    self.assertAlmostEqual(back.y(), 77.0, places=6)

  def test_zoom_anchors_cursor(self, ) -> None:
    """Zooming keeps the world point under the cursor fixed."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    before = canvas.screenToWorld(123.0, 77.0)
    canvas.zoomAt(2.0, 123.0, 77.0)
    after = canvas.screenToWorld(123.0, 77.0)
    self.assertAlmostEqual(before[0], after[0], places=6)
    self.assertAlmostEqual(before[1], after[1], places=6)
    self.assertEqual(canvas.scale, 2.0)  # default 1 px/mm, doubled

  def test_wheel_zoom_lands_on_integer_factors(self, ) -> None:
    """Each wheel notch steps one rung of the integer-factor ladder."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    canvas.scale = 1.0
    canvas.wheelEvent(_WheelEvent(120, 200.0, 150.0))  # one notch in
    self.assertEqual(canvas.scale, 2.0)  # 2 px/mm
    canvas.wheelEvent(_WheelEvent(120, 200.0, 150.0))
    self.assertEqual(canvas.scale, 3.0)  # 3 px/mm
    canvas.wheelEvent(_WheelEvent(-120, 200.0, 150.0))
    self.assertEqual(canvas.scale, 2.0)
    canvas.scale = 1.0
    canvas.wheelEvent(_WheelEvent(-120, 200.0, 150.0))  # one notch out
    self.assertAlmostEqual(canvas.scale, 0.5)  # 2 mm/px
    canvas.wheelEvent(_WheelEvent(-120, 200.0, 150.0))
    self.assertAlmostEqual(canvas.scale, 1 / 3)  # 3 mm/px

  def test_zoom_is_clamped(self, ) -> None:
    """The zoom never exceeds its configured bounds."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    for _ in range(50):
      canvas.zoomAt(2.0, 200.0, 150.0)
    self.assertLessEqual(canvas.scale, canvas.__max_scale__)
    for _ in range(50):
      canvas.zoomAt(0.5, 200.0, 150.0)
    self.assertGreaterEqual(canvas.scale, canvas.__min_scale__)

  def test_canvas_paints_every_kind(self, ) -> None:
    """A scene with every element kind renders without error."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    canvas.scene.addItem(AnchorPoint(0.0, 0.0))
    canvas.scene.addItem(ModuleLine(0.0, 0.0, 30.0))
    canvas.scene.addItem(Dimension(-2.0, -1.0, 3.0, 2.0))
    canvas.scene.addItem(AngularDimension(0.0, 0.0, 5.0, 0.0, 0.0, 5.0))
    pixmap = canvas.grab()
    self.assertFalse(pixmap.isNull())
    self.assertEqual(pixmap.width(), 400)

  def test_grid_step_is_pixel_invariant(self, ) -> None:
    """Grid cell = targetPx / scale (mm); the pixel spacing stays constant."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    canvas.gridTargetPx = 64.0
    canvas.scale = 32.0
    self.assertEqual(canvas.gridStep(), 2.0)  # 64 px / 32 px-per-mm
    canvas.scale = 8.0
    self.assertEqual(canvas.gridStep(), 8.0)  # mm-per-cell grew on zoom-out
    #  but the on-screen pixel spacing is invariant across zoom
    for scale in (5.0, 40.0, 200.0):
      canvas.scale = scale
      self.assertAlmostEqual(canvas.gridStep() * canvas.scale,
                             canvas.gridTargetPx, places=6)

  def test_grid_color_is_greenish_near_black(self, ) -> None:
    """The gridline colour stays near black but is greener and less blue."""
    from PySide6.QtGui import QColor
    colour = QColor(getattr(CADWidget, '__grid_color__'))
    self.assertLess(colour.red() + colour.green() + colour.blue(), 180)
    self.assertGreater(colour.green(), colour.blue())  # more green
    self.assertLess(colour.blue(), 55)  # less blue than the old #2a2e37

  def test_hover_highlights_snapped_gridlines(self, ) -> None:
    """Hovering tracks the snapped grid node so its gridlines highlight."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    canvas.mouseMoveEvent(_MouseEvent(207.0, 143.0))
    node = getattr(canvas, '__hover_world__')
    self.assertIsNotNone(node)
    step = canvas.gridStep()
    self.assertAlmostEqual(node[0], round(node[0] / step) * step, places=9)
    self.assertAlmostEqual(node[1], round(node[1] / step) * step, places=9)
    self.assertFalse(canvas.grab().isNull())  # highlight paints
    canvas.setSnap(False)  # no snapping -> no highlight
    self.assertIsNone(getattr(canvas, '__hover_world__'))

  def test_snap_rounds_to_grid_when_enabled(self, ) -> None:
    """Snapping rounds to the nearest grid node; disabling it is exact."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    canvas.gridTargetPx = 64.0
    canvas.scale = 32.0  # grid step 2.0 mm
    self.assertEqual(canvas.snap(2.7, 3.1), (2.0, 4.0))
    canvas.setSnap(False)
    self.assertEqual(canvas.snap(2.7, 3.1), (2.7, 3.1))

  def test_auto_zoom_contains_offview_item(self, ) -> None:
    """Adding an off-view item zooms out until it is visible, with margin."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    canvas.scale = 100.0  # zoomed in near the origin
    far = AnchorPoint(50.0, 50.0)
    minX, minY, maxX, maxY = canvas.visibleWorldRect()
    self.assertFalse(minX <= 50.0 <= maxX and minY <= 50.0 <= maxY)
    canvas.ensureContains(far)
    minX, minY, maxX, maxY = canvas.visibleWorldRect()
    self.assertTrue(minX <= 50.0 <= maxX)
    self.assertTrue(minY <= 50.0 <= maxY)
    self.assertTrue(minX <= 0.0 <= maxX)  # origin still visible (union)
    self.assertLess(canvas.scale, 100.0)  # zoomed out, never in

  def test_auto_zoom_noop_when_visible(self, ) -> None:
    """An item already inside the view leaves the zoom untouched."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    scale = canvas.scale
    canvas.ensureContains(AnchorPoint(0.0, 0.0))
    self.assertEqual(canvas.scale, scale)

  def test_selection_emphasis_paints(self, ) -> None:
    """A selected item paints (glow + halo) without error; None clears it."""
    canvas = CADWidget()
    canvas.resize(400, 300)
    point = AnchorPoint(0.0, 0.0)
    canvas.scene.addItem(point)
    canvas.setSelected(point)
    self.assertIs(getattr(canvas, '__selected__'), point)
    self.assertFalse(canvas.grab().isNull())
    canvas.setSelected(None)
    self.assertIsNone(getattr(canvas, '__selected__'))

  def test_list_row_selects_scene_item(self, ) -> None:
    """Selecting a list row emphasises the matching scene item."""
    window = CADWindow()
    window.show()
    window._selectTool('Anchor')
    window._onAdd()
    window._selectTool('Dimension')
    window._onAdd()
    window.selectionTool.itemList.setCurrentRow(1)
    self.assertIs(getattr(window.canvas, '__selected__'),
                  window.canvas.scene.items[1])
    window.clearScene()
    self.assertIsNone(getattr(window.canvas, '__selected__'))

  def test_clear_scene_empties_everything(self, ) -> None:
    """'clearScene' drops items, list rows and the selection."""
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))
    window.addItem(Dimension(-1.0, -1.0, 2.0, 2.0))
    window.selectionTool.itemList.setCurrentRow(0)
    window.clearScene()
    self.assertEqual(len(window.canvas.scene), 0)
    self.assertEqual(window.selectionTool.itemList.count(), 0)
    self.assertIsNone(getattr(window.canvas, '__selected__'))

  def test_clear_empty_scene_needs_no_confirmation(self, ) -> None:
    """Clearing an already-empty scene runs without a confirmation dialog."""
    window = CADWindow()
    window.show()
    window._onClear()  # no items -> no modal, just a no-op clear
    self.assertEqual(len(window.canvas.scene), 0)

  def test_tools_live_in_left_panel(self, ) -> None:
    """The tools are grouped in the left panel beside the canvas splitter."""
    from PySide6.QtWidgets import QSplitter
    window = CADWindow()
    window.show()
    self.assertIsInstance(window.centralWidget(), QSplitter)
    boxes = getattr(window, '__tool_boxes__')
    self.assertEqual(set(boxes), {'selection', 'newItem', 'view'})
    #  each tool panel is parented into its group box (not a top-level window)
    self.assertFalse(window.selectionTool.isWindow())
    self.assertTrue(boxes['selection'].isAncestorOf(window.selectionTool))
    self.assertTrue(hasattr(window.selectionTool, 'itemList'))
    self.assertTrue(hasattr(window.newItemTool, 'vertexEditor'))
    self.assertIn('Anchor', getattr(window, '__tool_actions__'))

  def test_window_geometry_persists(self, ) -> None:
    """Saved window geometry is restored on the next launch."""
    import tempfile
    from PySide6.QtCore import QSettings
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                      tempfile.mkdtemp())
    first = CADWindow()
    first.show()
    first.resize(760, 760)  # request a size; the actual one may be clamped
    #  Capture the size the window actually took (panel minimums can clamp
    #  the request); persistence means the next launch restores that size.
    expected = (first.size().width(), first.size().height())
    self.assertNotEqual(expected, (900, 600))  # it did change from default
    first._saveGeometry()
    second = CADWindow()
    second.show()  # show() restores geometry from settings
    self.assertEqual((second.size().width(), second.size().height()),
                     expected)

  def test_view_menu_shows_tools(self, ) -> None:
    """The View toggles show and hide the grouped tool sections."""
    window = CADWindow()
    window.show()
    action = getattr(window, '__show_selection_action__')
    self.assertTrue(action.isChecked())  # shown on launch
    self.assertTrue(window.selectionTool.isVisible())
    action.setChecked(False)
    self.assertFalse(window.selectionTool.isVisible())
    action.setChecked(True)
    self.assertTrue(window.selectionTool.isVisible())

  def test_add_item_keeps_list_aligned(self, ) -> None:
    """Items added via 'addItem' stay index-aligned with the list rows."""
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))
    window.addItem(Dimension(-3.0, -2.0, 4.0, 3.0))
    self.assertEqual(window.selectionTool.itemList.count(), 2)
    self.assertEqual(len(window.canvas.scene), 2)
    window.selectionTool.itemList.setCurrentRow(1)  # the line
    self.assertEqual(window.canvas.activeKind(), 'Dimension')
    self.assertIs(getattr(window.canvas, '__selected__'),
                  window.canvas.scene.items[1])

  def test_add_keeps_values_as_running_default(self, ) -> None:
    """After adding, fields keep the used values and become the default."""
    window = CADWindow()
    window.show()
    tool = window.newItemTool
    window._selectTool('Anchor')
    rows = getattr(tool.vertexEditor, '__rows__')
    rows[0][2].setText('7')
    rows[0][3].setText('8')
    tool.addButton.click()
    #  fields are not reset to the original default
    self.assertEqual(tool.vertexEditor.vertices(), [(7.0, 8.0)])
    #  switching away and back restores the most recently used values
    window._selectTool('Dimension')
    window._selectTool('Anchor')
    self.assertEqual(tool.vertexEditor.vertices(), [(7.0, 8.0)])

  def test_select_loads_item_into_panel(self, ) -> None:
    """Selecting an item sets the tool kind and vertex rows to match it."""
    window = CADWindow()
    window.show()
    tool = window.newItemTool
    editor = tool.vertexEditor

    #  a dimension with custom coordinates
    window._selectTool('Dimension')
    rows = getattr(editor, '__rows__')
    rows[0][2].setText('1')
    rows[0][3].setText('2')
    rows[1][2].setText('8')
    rows[1][3].setText('9')
    window._onAdd()

    #  an anchor point
    window._selectTool('Anchor')
    rows = getattr(editor, '__rows__')
    rows[0][2].setText('4')
    rows[0][3].setText('5')
    window._onAdd()

    #  selecting the dimension restores its kind and coordinates
    window.selectionTool.itemList.setCurrentRow(0)
    self.assertEqual(window.canvas.activeKind(), 'Dimension')
    self.assertEqual(editor.vertices(), [(1.0, 2.0), (8.0, 9.0)])

    #  selecting the anchor restores a single active row and its coordinate
    window.selectionTool.itemList.setCurrentRow(1)
    self.assertEqual(window.canvas.activeKind(), 'Anchor')
    self.assertEqual(editor.vertices(), [(4.0, 5.0)])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MOUSE GESTURES (live QApplication)   # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_default_mode_is_navigation(self, ) -> None:
    """The canvas starts in navigate mode, with the Navigate tool active."""
    window = CADWindow()
    window.show()
    self.assertEqual(getattr(window.canvas, '__mode__'), 'navigate')
    self.assertTrue(getattr(window, '__tool_actions__')['navigate'].isChecked())

  def test_navigate_drag_pans_without_adding(self, ) -> None:
    """In navigate mode a left drag pans the view and adds no item."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    before = (canvas.panX, canvas.panY)
    canvas.mousePressEvent(_MouseEvent(100.0, 100.0))
    canvas.mouseMoveEvent(_MouseEvent(160.0, 140.0))
    canvas.mouseReleaseEvent(_MouseEvent(160.0, 140.0))
    self.assertNotEqual((canvas.panX, canvas.panY), before)
    self.assertEqual(len(canvas.scene), 0)

  def test_tool_icons_select_mode_and_kind(self, ) -> None:
    """Triggering a tool icon sets the mode/kind; Navigate returns to pan."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    actions = getattr(window, '__tool_actions__')
    actions['Anchor'].trigger()  # as if the Anchor icon were clicked
    self.assertEqual(getattr(canvas, '__mode__'), 'draw')
    self.assertEqual(canvas.activeKind(), 'Anchor')
    canvas.mouseDoubleClickEvent(_MouseEvent(120.0, 80.0))
    self.assertEqual(len(canvas.scene), 1)
    actions['navigate'].trigger()
    self.assertEqual(getattr(canvas, '__mode__'), 'navigate')

  def test_mouse_double_click_adds_anchor(self, ) -> None:
    """A left double-click adds an anchor at that world coordinate."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    canvas.snapToGrid = False  # land exactly where clicked
    window._selectTool('Anchor')
    expect = canvas.screenToWorld(120.0, 80.0)
    canvas.mouseDoubleClickEvent(_MouseEvent(120.0, 80.0))
    self.assertEqual(len(canvas.scene), 1)
    anchor = canvas.scene.items[0]
    self.assertIsInstance(anchor, AnchorPoint)
    self.assertAlmostEqual(anchor.x, expect[0], places=6)
    self.assertAlmostEqual(anchor.y, expect[1], places=6)
    self.assertEqual(window.selectionTool.itemList.count(), 1)

  def test_mouse_drag_adds_module_line(self, ) -> None:
    """A press-drag adds a module line: press is origin, drag sets angle."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    canvas.snapToGrid = False
    window._selectTool('Module')
    start = canvas.screenToWorld(100.0, 100.0)
    end = canvas.screenToWorld(260.0, 180.0)
    canvas.mousePressEvent(_MouseEvent(100.0, 100.0))
    canvas.mouseMoveEvent(_MouseEvent(260.0, 180.0))
    canvas.mouseReleaseEvent(_MouseEvent(260.0, 180.0))
    module = canvas.scene.items[-1]
    self.assertIsInstance(module, ModuleLine)
    self.assertAlmostEqual(module.x, start[0], places=6)  # origin=press
    self.assertAlmostEqual(module.y, start[1], places=6)
    import math
    expectAngle = math.degrees(math.atan2(end[1] - start[1],
                                          end[0] - start[0]))
    self.assertAlmostEqual(module.angle, expectAngle, places=4)

  def test_drag_reports_live_geometry_in_status_bar(self, ) -> None:
    """Mid-drag, the status bar shows the gesture's live geometry."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window._selectTool('Dimension')
    canvas.mousePressEvent(_MouseEvent(100.0, 100.0))
    canvas.mouseMoveEvent(_MouseEvent(260.0, 180.0))
    message = window.statusBar().currentMessage()
    self.assertIn('Dimension', message)
    self.assertEqual(message.count('('), 2)  # both endpoints in parentheses
    self.assertIn('->', message)
    self.assertIn('len', message)
    self.assertIn('from horizontal', message)
    self.assertIn('from vertical', message)
    canvas.mouseReleaseEvent(_MouseEvent(260.0, 180.0))

    window._selectTool('Module')
    canvas.mousePressEvent(_MouseEvent(150.0, 120.0))
    canvas.mouseMoveEvent(_MouseEvent(300.0, 60.0))
    message = window.statusBar().currentMessage()
    self.assertIn('Module', message)
    self.assertIn('origin', message)
    self.assertIn('from horizontal', message)
    canvas.mouseReleaseEvent(_MouseEvent(300.0, 60.0))

  def test_drag_marks_start_and_current_snaplines(self, ) -> None:
    """While dragging, both the start and current snapped nodes are tracked."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window._selectTool('Dimension')
    canvas.mousePressEvent(_MouseEvent(120.0, 220.0))
    canvas.mouseMoveEvent(_MouseEvent(300.0, 110.0))
    self.assertIsNotNone(getattr(canvas, '__drag_start__'))
    self.assertIsNotNone(getattr(canvas, '__hover_world__'))
    self.assertFalse(canvas.grab().isNull())  # both crosshairs paint
    canvas.mouseReleaseEvent(_MouseEvent(300.0, 110.0))

  def test_angle_tool_three_clicks_adds_angle(self, ) -> None:
    """The Angle tool collects three clicks into an angular dimension."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window._selectTool('Angle')

    def click(x, y):
      canvas.mousePressEvent(_MouseEvent(x, y))
      canvas.mouseReleaseEvent(_MouseEvent(x, y))

    click(200.0, 160.0)  # vertex
    self.assertEqual(len(canvas.scene), 0)
    click(280.0, 160.0)  # arm A
    self.assertEqual(len(canvas.scene), 0)
    click(200.0, 90.0)  # arm B -> commits
    self.assertEqual(len(canvas.scene), 1)
    self.assertIsInstance(canvas.scene.items[0], AngularDimension)

  def test_selecting_item_enters_edit_mode(self, ) -> None:
    """Selecting an item retitles the tool to Edit and updates in place."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    box = getattr(window, '__tool_boxes__')['newItem']
    actions = getattr(window, '__tool_actions__')
    actions['Anchor'].trigger()
    window.newItemTool.addButton.click()
    actions['Dimension'].trigger()
    window.newItemTool.addButton.click()
    self.assertEqual(box.title(), 'New item')

    window.selectionTool.itemList.setCurrentRow(1)  # select the line
    self.assertEqual(box.title(), 'Edit item')
    self.assertEqual(window.newItemTool.addButton.text(), 'Update item')
    self.assertEqual(getattr(window, '__edit_index__'), 1)

    rows = getattr(window.newItemTool.vertexEditor, '__rows__')
    rows[0][2].setText('1')
    rows[0][3].setText('1')
    rows[1][2].setText('9')
    rows[1][3].setText('9')
    count = len(canvas.scene)
    window.newItemTool.addButton.click()  # Update, not Add
    self.assertEqual(len(canvas.scene), count)  # replaced in place
    self.assertEqual(canvas.scene.items[1].x2, 9.0)
    self.assertEqual(window.selectionTool.itemList.item(1).text(),
                     str(canvas.scene.items[1]))

    actions['Anchor'].trigger()  # back to creating new
    self.assertEqual(box.title(), 'New item')
    self.assertEqual(window.newItemTool.addButton.text(), 'Add item')
    self.assertIsNone(getattr(window, '__edit_index__'))

  def test_delete_button_appears_in_edit_and_removes(self, ) -> None:
    """The Edit panel's Delete button shows only while editing and removes
    the edited item, returning to New mode."""
    window = CADWindow()
    window.show()
    button = window.newItemTool.deleteButton
    self.assertFalse(button.isVisible())  # New mode: no delete button
    window.addItem(AnchorPoint(1.0, 2.0))
    window.addItem(AnchorPoint(3.0, 4.0))
    window.selectionTool.itemList.setCurrentRow(0)  # edit the first item
    self.assertTrue(button.isVisible())
    count = len(window.canvas.scene)
    button.click()
    self.assertEqual(len(window.canvas.scene), count - 1)
    self.assertFalse(button.isVisible())  # back to New mode

  def test_anchor_edit_panel_updates_in_place(self, ) -> None:
    """Editing an anchor shows its support/load/members and updates in place
    so attached members keep their reference and follow it."""
    window = CADWindow()
    window.show()
    panel = window.newItemTool
    a = AnchorPoint(10.0, 10.0)
    a.fixX, a.fixY, a.loadY = True, True, -20.0
    b = AnchorPoint(90.0, 60.0)
    window.addItem(a)
    window.addItem(b)
    window.addItem(Member(a, b))
    window.selectionTool.itemList.setCurrentRow(0)  # edit anchor 'a'
    self.assertTrue(panel.vertexEditor.isVisible())  # coordinates editable
    self.assertIn('pinned', panel.supportLabel.text())
    self.assertTrue(panel.loadHost.isVisible())  # load Fx/Fy fields
    self.assertEqual(panel.loadYEdit.text(), '-20')  # prefilled with its load
    self.assertTrue(panel.membersList.isVisible())
    self.assertEqual(panel.membersList.count(), 1)  # one attached member
    #  edit the coordinates and update -> the same anchor object moves
    rows = getattr(panel.vertexEditor, '__rows__')
    rows[0][2].setText('25')
    rows[0][3].setText('15')
    window._onAdd()
    self.assertIs(window.canvas.scene.items[0], a)  # identity preserved
    self.assertEqual((a.x, a.y), (25.0, 15.0))
    member = [i for i in window.canvas.scene if isinstance(i, Member)][0]
    self.assertEqual((member.x1, member.y1), (25.0, 15.0))  # member follows

  def test_anchor_panel_edits_load_and_settlement(self, ) -> None:
    """The anchor panel edits load by component, and settlement when it has a
    support; a free anchor hides the settlement and keeps none."""
    window = CADWindow()
    window.show()
    panel = window.newItemTool
    a = AnchorPoint(0.0, 0.0)
    a.fixX, a.fixY = True, True  # pinned -> settlement fields available
    b = AnchorPoint(80.0, 0.0)
    window.addItem(a)
    window.addItem(b)
    window.selectionTool.itemList.setCurrentRow(0)  # edit the pinned anchor
    self.assertTrue(panel.loadHost.isVisible())
    self.assertTrue(panel.dispHost.isVisible())  # has a support
    panel.loadXEdit.setText('12')
    panel.loadYEdit.setText('-30')
    panel.dispYEdit.setText('-5')
    window._onAdd()
    self.assertIs(window.canvas.scene.items[0], a)  # applied in place
    self.assertEqual((a.loadX, a.loadY), (12.0, -30.0))
    self.assertEqual((a.dispX, a.dispY), (0.0, -5.0))
    #  a free anchor: settlement fields hidden and never applied
    window.selectionTool.itemList.setCurrentRow(1)
    self.assertFalse(panel.dispHost.isVisible())
    panel.loadXEdit.setText('5')
    panel.dispYEdit.setText('99')  # typed but ignored: no support
    window._onAdd()
    self.assertEqual(b.loadX, 5.0)
    self.assertEqual((b.dispX, b.dispY), (0.0, 0.0))

  def test_member_edit_panel_shows_nodes_only(self, ) -> None:
    """Editing a member shows its two anchors; no coordinate edit."""
    window = CADWindow()
    window.show()
    panel = window.newItemTool
    a = AnchorPoint(0.0, 0.0)
    b = AnchorPoint(80.0, 0.0)
    window.addItem(a)
    window.addItem(b)
    window.addItem(Member(a, b))
    window.selectionTool.itemList.setCurrentRow(2)  # the member
    self.assertFalse(panel.vertexEditor.isVisible())  # no vertex fields
    self.assertTrue(panel.infoLabel.isVisible())
    self.assertIn('Node A', panel.infoLabel.text())
    self.assertIn('Node B', panel.infoLabel.text())
    self.assertFalse(panel.addButton.isVisible())  # no 'Update' for a member
    self.assertTrue(panel.deleteButton.isVisible())

  def test_select_tool_picks_item(self, ) -> None:
    """The Select tool picks the clicked item and stays in select mode."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window.addItem(AnchorPoint(0.0, 0.0))
    window._selectTool('select')
    self.assertEqual(getattr(canvas, '__mode__'), 'select')
    screen = canvas.worldToScreen(0.0, 0.0)  # current screen pos of the point
    canvas.mousePressEvent(_MouseEvent(screen.x(), screen.y()))
    self.assertIs(getattr(canvas, '__selected__'), canvas.scene.items[0])
    self.assertEqual(getattr(canvas, '__mode__'), 'select')

  def test_select_click_toggles_and_empty_deselects(self, ) -> None:
    """Clicking the selected item again, or empty space, deselects it."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window.addItem(AnchorPoint(0.0, 0.0))
    window._selectTool('select')
    spot = canvas.worldToScreen(0.0, 0.0)
    canvas.mousePressEvent(_MouseEvent(spot.x(), spot.y()))
    self.assertIsNotNone(getattr(canvas, '__selected__'))
    canvas.mousePressEvent(_MouseEvent(spot.x(), spot.y()))  # same -> deselect
    self.assertIsNone(getattr(canvas, '__selected__'))
    self.assertIsNone(getattr(window, '__edit_index__'))
    canvas.mousePressEvent(_MouseEvent(spot.x(), spot.y()))  # reselect
    self.assertIsNotNone(getattr(canvas, '__selected__'))
    canvas.mousePressEvent(  # empty space -> deselect
        _MouseEvent(spot.x() + 140.0, spot.y() + 90.0))
    self.assertIsNone(getattr(canvas, '__selected__'))

  def test_dimension_tool_adds_dimension(self, ) -> None:
    """The Dimension tool drags out a persistent linear dimension."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window._selectTool('Dimension')
    self.assertEqual(canvas.activeKind(), 'Dimension')
    canvas.mousePressEvent(_MouseEvent(100.0, 220.0))
    canvas.mouseMoveEvent(_MouseEvent(280.0, 120.0))
    canvas.mouseReleaseEvent(_MouseEvent(280.0, 120.0))
    self.assertEqual(len(canvas.scene), 1)
    self.assertIsInstance(canvas.scene.items[0], Dimension)
    self.assertFalse(canvas.grab().isNull())  # committed dimension renders

  def test_member_drag_snaps_endpoints_to_anchors(self, ) -> None:
    """A member dragged between two anchors latches onto them as nodes."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(520, 420)
    window.addItem(AnchorPoint(20.0, 20.0))
    window.addItem(AnchorPoint(120.0, 80.0))
    window._selectTool('Member')
    self.assertEqual(canvas.activeKind(), 'Member')
    start = canvas.worldToScreen(20.0, 20.0)
    end = canvas.worldToScreen(120.0, 80.0)
    canvas.mousePressEvent(_MouseEvent(start.x() + 3.0, start.y() - 3.0))
    canvas.mouseMoveEvent(_MouseEvent(end.x() - 2.0, end.y() + 2.0))
    canvas.mouseReleaseEvent(_MouseEvent(end.x() - 2.0, end.y() + 2.0))
    members = [item for item in canvas.scene if isinstance(item, Member)]
    self.assertEqual(len(members), 1)
    member = members[0]
    #  the member references the two anchor nodes, its coords read through
    self.assertIs(member.nodeA, canvas.scene.items[0])
    self.assertIs(member.nodeB, canvas.scene.items[1])
    self.assertEqual((member.x1, member.y1), (20.0, 20.0))
    self.assertEqual((member.x2, member.y2), (120.0, 80.0))
    self.assertFalse(canvas.grab().isNull())  # the member renders

  def test_member_drag_to_empty_adds_nothing(self, ) -> None:
    """A member drag that does not end on a second anchor adds no member."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(520, 420)
    window.addItem(AnchorPoint(20.0, 20.0))
    window._selectTool('Member')
    start = canvas.worldToScreen(20.0, 20.0)
    canvas.mousePressEvent(_MouseEvent(start.x(), start.y()))
    canvas.mouseReleaseEvent(_MouseEvent(300.0, 300.0))  # empty space
    self.assertEqual([i for i in canvas.scene if isinstance(i, Member)], [])

  def test_deleting_anchor_cascades_to_members(self, ) -> None:
    """Deleting an anchor removes every member that used it, undoably."""
    window = CADWindow()
    window.show()
    a = AnchorPoint(0.0, 0.0)
    b = AnchorPoint(80.0, 0.0)
    c = AnchorPoint(40.0, 50.0)
    for node in (a, b, c):
      window.addItem(node)
    window.addItem(Member(a, c))
    window.addItem(Member(b, c))  # both members touch 'c'
    total = len(window.canvas.scene)
    window.selectionTool.itemList.setCurrentRow(2)  # the anchor 'c'
    window._deleteSelected()
    members = [i for i in window.canvas.scene if isinstance(i, Member)]
    self.assertEqual(members, [])  # both members went with 'c'
    self.assertEqual(len(window.canvas.scene), 2)  # only a and b remain
    window._onUndo()  # the cascade is one undo step
    self.assertEqual(len(window.canvas.scene), total)

  def test_member_serialization_round_trip(self, ) -> None:
    """Members survive a JSON round-trip by node index, references intact."""
    scene = CADScene()
    a = AnchorPoint(0.0, 0.0)
    b = AnchorPoint(80.0, 60.0)
    scene.addItem(a)
    scene.addItem(b)
    scene.addItem(Member(a, b))
    restored = sceneFromJson(sceneToJson(scene))
    anchors = [i for i in restored if isinstance(i, AnchorPoint)]
    member = [i for i in restored if isinstance(i, Member)][0]
    self.assertIs(member.nodeA, anchors[0])  # rebuilt-anchor identity
    self.assertIs(member.nodeB, anchors[1])
    anchors[0].x = 5.0  # the restored member tracks the restored anchor
    self.assertEqual(member.x1, 5.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  BOUNDARY CONDITIONS (supports)   # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_anchor_support_cycle(self, ) -> None:
    """An anchor cycles free -> pinned -> rollerH -> rollerV -> free."""
    anchor = AnchorPoint(0.0, 0.0)
    self.assertEqual(anchor.supportKind(), 'free')
    self.assertEqual(anchor.cycleSupport(), 'pinned')
    self.assertTrue(anchor.fixX and anchor.fixY)
    self.assertEqual(anchor.cycleSupport(), 'rollerH')  # fixed Y only
    self.assertTrue(anchor.fixY)
    self.assertFalse(anchor.fixX)
    self.assertEqual(anchor.cycleSupport(), 'rollerV')  # fixed X only
    self.assertTrue(anchor.fixX)
    self.assertFalse(anchor.fixY)
    self.assertEqual(anchor.cycleSupport(), 'free')
    pinned = AnchorPoint(1.0, 2.0)
    pinned.cycleSupport()
    self.assertIn('pinned', str(pinned))  # the support shows in the label

  def test_support_persists_through_json(self, ) -> None:
    """An anchor's support survives JSON; a free anchor stores nothing."""
    scene = CADScene()
    supported = AnchorPoint(5.0, 0.0)
    supported.cycleSupport()  # pinned
    scene.addItem(supported)
    scene.addItem(AnchorPoint(9.0, 0.0))  # left free
    data = sceneToData(scene)
    self.assertEqual(data['items'][0]['attrs'], {'fixX': True, 'fixY': True})
    self.assertNotIn('attrs', data['items'][1])  # free anchor stays minimal
    restored = sceneFromJson(sceneToJson(scene))
    self.assertEqual(restored.items[0].supportKind(), 'pinned')
    self.assertEqual(restored.items[1].supportKind(), 'free')

  def test_support_tool_cycles_on_click(self, ) -> None:
    """The Support tool cycles the clicked anchor's boundary condition."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(520, 420)
    anchor = AnchorPoint(30.0, 30.0)
    window.addItem(anchor)
    window._selectTool('support')
    self.assertEqual(getattr(canvas, '__mode__'), 'support')
    spot = canvas.worldToScreen(30.0, 30.0)
    #  a click is a press and release with no drag (the cycle fires on
    #  release; a drag would instead set a prescribed displacement).
    canvas.mousePressEvent(_MouseEvent(spot.x() + 2.0, spot.y() - 2.0))
    canvas.mouseReleaseEvent(_MouseEvent(spot.x() + 2.0, spot.y() - 2.0))
    self.assertEqual(anchor.supportKind(), 'pinned')
    self.assertTrue(window.dirty)
    #  the list row reflects the new support
    self.assertIn('pinned', window.selectionTool.itemList.item(0).text())
    window._onUndo()  # cycling is undoable
    self.assertEqual(canvas.scene.items[0].supportKind(), 'free')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NODAL LOADS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_anchor_load_and_label(self, ) -> None:
    """An anchor carries a nodal force that shows in its label."""
    anchor = AnchorPoint(0.0, 0.0)
    self.assertEqual((anchor.loadX, anchor.loadY), (0.0, 0.0))
    self.assertNotIn('F(', str(anchor))  # no load -> no force in the label
    anchor.loadX = 10.0
    anchor.loadY = -25.0
    self.assertIn('F(10, -25)', str(anchor))

  def test_load_persists_through_json(self, ) -> None:
    """A nodal load survives a JSON round-trip; zero loads store nothing."""
    scene = CADScene()
    loaded = AnchorPoint(5.0, 0.0)
    loaded.loadY = -30.0
    scene.addItem(loaded)
    scene.addItem(AnchorPoint(9.0, 0.0))  # no load
    data = sceneToData(scene)
    self.assertEqual(data['items'][0]['attrs'], {'loadY': -30.0})
    self.assertNotIn('attrs', data['items'][1])  # zero load stays minimal
    restored = sceneFromJson(sceneToJson(scene))
    self.assertAlmostEqual(restored.items[0].loadY, -30.0)
    self.assertEqual((restored.items[1].loadX, restored.items[1].loadY),
                     (0.0, 0.0))

  def test_load_tool_drag_sets_and_click_clears(self, ) -> None:
    """The Load tool drags a force from an anchor; a click clears it."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(520, 420)
    anchor = AnchorPoint(50.0, 50.0)
    window.addItem(anchor)
    window._selectTool('load')
    self.assertEqual(getattr(canvas, '__mode__'), 'load')
    origin = canvas.worldToScreen(50.0, 50.0)
    end = canvas.worldToScreen(50.0, 20.0)  # drag 30 mm down -> Fy = -30 N
    canvas.mousePressEvent(_MouseEvent(origin.x() + 2.0, origin.y() - 2.0))
    canvas.mouseMoveEvent(_MouseEvent(end.x(), end.y()))
    canvas.mouseReleaseEvent(_MouseEvent(end.x(), end.y()))
    self.assertAlmostEqual(anchor.loadX, 0.0, 3)
    self.assertAlmostEqual(anchor.loadY, -30.0, 3)
    self.assertTrue(window.dirty)
    self.assertIn('F(', window.selectionTool.itemList.item(0).text())
    window._onUndo()  # setting a load is undoable
    self.assertEqual(canvas.scene.items[0].loadY, 0.0)
    window._onRedo()  # undo/redo rebuild the scene; re-fetch the live anchor
    #  a click with no appreciable drag clears the load
    spot = canvas.worldToScreen(50.0, 50.0)
    canvas.mousePressEvent(_MouseEvent(spot.x(), spot.y()))
    canvas.mouseReleaseEvent(_MouseEvent(spot.x(), spot.y()))
    cleared = canvas.scene.items[0]
    self.assertEqual((cleared.loadX, cleared.loadY), (0.0, 0.0))

  def test_load_drag_snaps_to_axis(self, ) -> None:
    """With snapping on, a force drag snaps to the dominant axis (H or V)."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(520, 420)
    canvas.snapToGrid = True
    anchor = AnchorPoint(50.0, 50.0)
    window.addItem(anchor)
    window._selectTool('load')
    origin = canvas.worldToScreen(50.0, 50.0)
    #  drag down 30 with a small 8 sideways -> the vertical axis wins
    end = canvas.worldToScreen(58.0, 20.0)
    canvas.mousePressEvent(_MouseEvent(origin.x(), origin.y()))
    canvas.mouseMoveEvent(_MouseEvent(end.x(), end.y()))
    canvas.mouseReleaseEvent(_MouseEvent(end.x(), end.y()))
    self.assertAlmostEqual(anchor.loadX, 0.0, 6)  # snapped to pure vertical
    self.assertAlmostEqual(anchor.loadY, -30.0, 3)

  def test_support_click_cycles_drag_displaces(self, ) -> None:
    """In support mode a click cycles support; a drag sets a settlement."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(520, 420)
    canvas.snapToGrid = True
    anchor = AnchorPoint(50.0, 50.0)
    window.addItem(anchor)
    window._selectTool('support')
    spot = canvas.worldToScreen(50.0, 50.0)
    #  a click (press-release, no move) cycles the support kind
    canvas.mousePressEvent(_MouseEvent(spot.x(), spot.y()))
    canvas.mouseReleaseEvent(_MouseEvent(spot.x(), spot.y()))
    self.assertEqual(anchor.supportKind(), 'pinned')
    #  a drag sets a prescribed displacement, leaving the support kind alone
    down = canvas.worldToScreen(50.0, 30.0)  # 20 mm down -> dispY = -20
    canvas.mousePressEvent(_MouseEvent(spot.x(), spot.y()))
    canvas.mouseMoveEvent(_MouseEvent(down.x(), down.y()))
    canvas.mouseReleaseEvent(_MouseEvent(down.x(), down.y()))
    self.assertAlmostEqual(anchor.dispX, 0.0, 6)
    self.assertAlmostEqual(anchor.dispY, -20.0, 3)
    self.assertEqual(anchor.supportKind(), 'pinned')  # drag did not cycle
    self.assertIn('d(', window.selectionTool.itemList.item(0).text())

  def test_displacement_persists_through_json(self, ) -> None:
    """A prescribed displacement survives a JSON round-trip."""
    scene = CADScene()
    settled = AnchorPoint(0.0, 0.0)
    settled.dispY = -8.0
    scene.addItem(settled)
    data = sceneToData(scene)
    self.assertEqual(data['items'][0]['attrs'], {'dispY': -8.0})
    restored = sceneFromJson(sceneToJson(scene))
    self.assertAlmostEqual(restored.items[0].dispY, -8.0)

  def test_dimension_overlay_paints(self, ) -> None:
    """The technical-dimension overlay paints mid-drag without error."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window._selectTool('Dimension')
    canvas.mousePressEvent(_MouseEvent(100.0, 100.0))
    canvas.mouseMoveEvent(_MouseEvent(260.0, 180.0))
    self.assertFalse(canvas.grab().isNull())  # dimensions render
    canvas.mouseReleaseEvent(_MouseEvent(260.0, 180.0))

  def test_mouse_point_snaps_to_grid(self, ) -> None:
    """A double-clicked point lands on a grid node while snapping is on."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window._selectTool('Anchor')
    canvas.mouseDoubleClickEvent(_MouseEvent(207.0, 143.0))
    point = canvas.scene.items[-1]
    step = canvas.gridStep()
    self.assertAlmostEqual(point.x, round(point.x / step) * step, places=9)
    self.assertAlmostEqual(point.y, round(point.y / step) * step, places=9)

  def test_viewer_tool_controls_grid_and_snap(self, ) -> None:
    """The viewer tool's controls drive the canvas grid, snap and fineness."""
    window = CADWindow()
    window.show()
    self.assertTrue(window.canvas.showGrid)
    self.assertTrue(window.canvas.snapToGrid)
    window.viewTool.showGridCheck.setChecked(False)
    self.assertFalse(window.canvas.showGrid)
    window.viewTool.snapCheck.setChecked(False)
    self.assertFalse(window.canvas.snapToGrid)
    window.viewTool.gridSlider.setValue(120)
    self.assertEqual(window.canvas.gridTargetPx, 120.0)
    self.assertEqual(window.viewTool.gridEdit.text(), '120')

  def test_viewer_tool_grid_spacing_typed(self, ) -> None:
    """Typing a precise spacing applies it; values clamp to >= 8 px."""
    window = CADWindow()
    window.show()
    #  a precise typed value flows to the canvas and the slider
    window.viewTool.gridEdit.setText('8')
    window._onGridSpacingEdit()
    self.assertEqual(window.canvas.gridTargetPx, 8.0)
    self.assertEqual(window.viewTool.gridSlider.value(), 8)
    #  values below the 8 px minimum are clamped
    window.viewTool.gridEdit.setText('3')
    window._onGridSpacingEdit()
    self.assertEqual(window.canvas.gridTargetPx, 8.0)
    self.assertEqual(window.viewTool.spacingRange()[0], 8)

  def test_factor_readout_swaps_units(self, ) -> None:
    """The factor reads integer mm/px when zoomed out, px/mm when zoomed in."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    canvas.scale = 1.0  # default view: 1 px = 1 mm
    window._onViewChanged()
    self.assertIn('1 mm/px', window.viewTool.factorLabel.text())
    canvas.scale = 4.0  # zoomed in
    window._onViewChanged()
    self.assertIn('4 px/mm', window.viewTool.factorLabel.text())
    canvas.scale = 0.25  # zoomed out
    window._onViewChanged()
    self.assertIn('4 mm/px', window.viewTool.factorLabel.text())

  def test_mouse_click_without_drag_adds_nothing(self, ) -> None:
    """A bare click (no appreciable drag) adds no item."""
    window = CADWindow()
    window.show()
    canvas = window.canvas
    canvas.resize(400, 300)
    window._selectTool('Dimension')
    canvas.mousePressEvent(_MouseEvent(200.0, 150.0))
    canvas.mouseReleaseEvent(_MouseEvent(201.0, 150.0))  # ~1px, below threshold
    self.assertEqual(len(canvas.scene), 0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  VERTEX EDITOR (live QApplication)   # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_vertex_editor_reads_active_rows(self, ) -> None:
    """Only the active leading rows are read back as float pairs."""
    editor = VertexEditor()
    editor.configure(2, False)  # 2 active, plus a greyed surplus row
    rows = getattr(editor, '__rows__')
    self.assertEqual(len(rows), 3)  # baseline kept for stable height
    rows[0][2].setText('1')  # row tuple: (host, indexLabel, xEdit, yEdit)
    rows[0][3].setText('2')
    rows[1][2].setText('3')
    rows[1][3].setText('4')
    self.assertEqual(editor.vertices(), [(1.0, 2.0), (3.0, 4.0)])

  def test_vertex_editor_greys_surplus_rows(self, ) -> None:
    """Fewer-input kinds keep the surplus rows present but disabled."""
    editor = VertexEditor()
    editor.configure(1, False, [(0.0, 0.0)])  # Anchor: 1 active of 3
    rows = getattr(editor, '__rows__')
    self.assertEqual(len(rows), 3)  # height unchanged
    self.assertTrue(rows[0][0].isEnabled())  # active row
    self.assertFalse(rows[1][0].isEnabled())  # greyed
    self.assertFalse(rows[2][0].isEnabled())
    self.assertEqual(len(editor.vertices()), 1)

  def test_vertex_editor_defaults_prefilled(self, ) -> None:
    """Active rows are prefilled with the configured default coordinates."""
    editor = VertexEditor()
    editor.configure(2, False, [(-2.0, -1.0), (3.0, 2.0)])
    self.assertEqual(editor.vertices(), [(-2.0, -1.0), (3.0, 2.0)])
    rows = getattr(editor, '__rows__')
    self.assertEqual(rows[0][1].text(), 'v1')  # per-vertex index label
    self.assertEqual(rows[1][1].text(), 'v2')

  def test_vertex_editor_clear_restores_defaults(self, ) -> None:
    """'clear' resets the active rows to their defaults, not to empty."""
    editor = VertexEditor()
    editor.configure(1, False, [(5.0, 7.0)])
    rows = getattr(editor, '__rows__')
    rows[0][2].setText('99')
    editor.clear()
    self.assertEqual(editor.vertices(), [(5.0, 7.0)])

  def test_vertex_editor_add_remove(self, ) -> None:
    """Variable mode adds vertices and never drops below the baseline."""
    editor = VertexEditor()
    editor.configure(3, True, [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)])
    editor._onAddVertex()
    self.assertEqual(len(getattr(editor, '__rows__')), 4)
    for _ in range(10):
      editor._onRemoveVertex()
    self.assertEqual(len(getattr(editor, '__rows__')), 3)

  def test_vertex_editor_rejects_empty(self, ) -> None:
    """Cleared-to-empty coordinate fields raise 'ValueError'."""
    editor = VertexEditor()
    editor.configure(1, False, [(0.0, 0.0)])
    rows = getattr(editor, '__rows__')
    rows[0][2].setText('')
    rows[0][3].setText('')
    with self.assertRaises(ValueError):
      editor.vertices()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  JSON SAVE / LOAD (no Qt required)   # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _populatedScene() -> CADScene:
    """A scene holding one of every kind, for serialisation tests."""
    scene = CADScene()
    scene.addItem(AnchorPoint(1.0, 2.0))
    scene.addItem(ModuleLine(0.0, 0.0, 30.0))
    scene.addItem(Dimension(-3.0, -2.0, 4.0, 3.0))
    scene.addItem(Dimension(0.0, 0.0, 3.0, 4.0))
    scene.addItem(AngularDimension(0.0, 0.0, 10.0, 0.0, 0.0, 10.0))
    return scene

  def test_scene_to_data_is_json_native(self, ) -> None:
    """'sceneToData' yields only plain dicts, lists, str and float."""
    data = sceneToData(self._populatedScene())
    self.assertEqual(data['version'], 1)
    self.assertEqual(len(data['items']), 5)
    first = data['items'][0]
    self.assertEqual(first['kind'], 'Anchor')
    self.assertEqual(first['vertices'], [[1.0, 2.0]])
    for entry in data['items']:
      self.assertIsInstance(entry['kind'], str)
      for x, y in entry['vertices']:
        self.assertIsInstance(x, float)
        self.assertIsInstance(y, float)

  def test_json_round_trip_recreates_every_kind(self, ) -> None:
    """A scene survives a JSON round-trip, kind and value identical."""
    scene = self._populatedScene()
    restored = sceneFromJson(sceneToJson(scene))
    self.assertEqual(len(restored), len(scene))
    for before, after in zip(scene, restored):
      self.assertIs(type(before), type(after))
      self.assertEqual(describeItem(before), describeItem(after))

  def test_save_then_load_from_disk(self, ) -> None:
    """'saveScene'/'loadScene' round-trip a drawing through a real file."""
    import os
    import tempfile
    scene = self._populatedScene()
    path = os.path.join(tempfile.mkdtemp(), 'drawing.json')
    saveScene(scene, path)
    self.assertTrue(os.path.exists(path))
    loaded = loadScene(path)
    self.assertEqual(len(loaded), 5)
    self.assertEqual([describeItem(i) for i in loaded],
                     [describeItem(i) for i in scene])

  def test_saved_file_is_plain_text_json_not_pickle(self, ) -> None:
    """The saved file is legible JSON text naming each kind."""
    import os
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'drawing.json')
    saveScene(self._populatedScene(), path)
    with open(path, 'r') as handle:
      text = handle.read()
    self.assertIn('"kind"', text)
    self.assertIn('Module', text)
    self.assertEqual(text, sceneToJson(self._populatedScene()))

  def test_load_into_existing_scene_keeps_identity(self, ) -> None:
    """Loading into a given scene refills it in place, not replacing it."""
    scene = CADScene()
    scene.addItem(AnchorPoint(9.0, 9.0))
    same = loadScene  # alias to keep the line short
    import os
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'd.json')
    saveScene(self._populatedScene(), path)
    returned = same(path, scene)
    self.assertIs(returned, scene)
    self.assertEqual(len(scene), 5)

  def test_malformed_entry_leaves_scene_untouched(self, ) -> None:
    """A bad item aborts the load without disturbing the target scene."""
    scene = self._populatedScene()
    bad = '{"version":1,"items":[{"kind":"Module","vertices":[[0,0]]}]}'
    with self.assertRaises(ValueError):
      sceneFromJson(bad, scene)
    self.assertEqual(len(scene), 5)  # untouched: built before committing

  def test_open_rebuilds_list_and_fits_view(self, ) -> None:
    """The window's Open path mirrors the list and zooms to the drawing."""
    import os
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'drawing.json')
    saveScene(self._populatedScene(), path)
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))  # something to be replaced
    loaded = loadScene(path, window.canvas.scene)
    window._syncListToScene()
    window._enterNewMode()
    window.canvas.fitAll()
    self.assertEqual(len(loaded), 5)
    self.assertEqual(window.selectionTool.itemList.count(), 5)
    self.assertIsNone(getattr(window.canvas, '__selected__'))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OBJECT SNAP (snap to straight segments)   # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _snapCanvas(item) -> CADWidget:
    """A sized canvas holding 'item', with snapping on, for snap tests."""
    canvas = CADWidget()
    canvas.resize(520, 420)
    canvas.scene.addItem(item)
    canvas.snapToGrid = True
    return canvas

  def _nearSegment(self, canvas: CADWidget, a: tuple, b: tuple,
                   off: float) -> QPointF:
    """A screen point 'off' pixels below the midpoint of segment a-b."""
    mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    screen = canvas.worldToScreen(mid[0], mid[1])
    return QPointF(screen.x(), screen.y() + off)

  def test_pointer_snaps_onto_existing_line(self, ) -> None:
    """With snapping on, a pointer near a line is pulled onto it."""
    canvas = CADWidget()
    canvas.resize(520, 420)
    canvas.scene.addItem(Dimension(0.0, 0.0, 100.0, 0.0))  # at y = 0
    canvas.snapToGrid = True
    onLine = canvas.worldToScreen(50.0, 0.0)
    near = QPointF(onLine.x() + 1.0, onLine.y() + 4.0)  # 4 px off the line
    wx, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wy, 0.0, 6)  # pulled exactly onto the line
    #  Object snap wins over the grid node (which would be x = 48 here).
    self.assertAlmostEqual(wx, 51.0, 3)

  def test_object_snap_obeys_snap_toggle(self, ) -> None:
    """With snapping off, the pointer is not pulled onto a line."""
    canvas = CADWidget()
    canvas.resize(520, 420)
    canvas.scene.addItem(Dimension(0.0, 0.0, 100.0, 0.0))
    canvas.snapToGrid = False
    onLine = canvas.worldToScreen(50.0, 0.0)
    near = QPointF(onLine.x() + 1.0, onLine.y() + 4.0)
    _, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wy, -4.0, 3)  # raw world y, no pull onto y = 0

  def test_drawn_line_endpoint_snaps_to_existing_line(self, ) -> None:
    """A gesture ending near an existing line snaps its endpoint onto it."""
    canvas = CADWidget()
    canvas.resize(520, 420)
    canvas.scene.addItem(Dimension(0.0, 0.0, 100.0, 0.0))
    canvas.snapToGrid = True
    canvas.setMode('draw')
    canvas.setActiveKind('Dimension')
    captured = []
    canvas.setAddCallback(lambda kind, verts: captured.append((kind, verts)))
    start = canvas.worldToScreen(20.0, 60.0)
    endOff = canvas.worldToScreen(70.0, 0.0)
    end = QPointF(endOff.x(), endOff.y() + 5.0)  # 5 px past the line
    canvas.mousePressEvent(_MouseEvent(start.x(), start.y()))
    canvas.mouseMoveEvent(_MouseEvent(end.x(), end.y()))
    canvas.mouseReleaseEvent(_MouseEvent(end.x(), end.y()))
    self.assertTrue(captured)
    kind, vertices = captured[0]
    self.assertEqual(kind, 'Dimension')
    self.assertAlmostEqual(vertices[1][1], 0.0, 6)  # endpoint on the line

  def test_pointer_snaps_onto_module_line(self, ) -> None:
    """The pointer snaps onto an infinite module line past its origin."""
    canvas = self._snapCanvas(ModuleLine(0.0, 0.0, 0.0))  # horizontal y = 0
    far = canvas.worldToScreen(200.0, 0.0)  # well beyond the origin
    near = QPointF(far.x(), far.y() + 4.0)  # 4 px off the line
    wx, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wy, 0.0, 6)  # the infinite line snaps anywhere
    self.assertAlmostEqual(wx, 200.0, 3)

  def test_pointer_snaps_to_module_intersection(self, ) -> None:
    """The crossing of two module lines is a snap node."""
    canvas = self._snapCanvas(ModuleLine(0.0, 0.0, 0.0))  # horizontal y = 0
    canvas.scene.addItem(ModuleLine(30.0, 0.0, 90.0))  # vertical x = 30
    cross = canvas.worldToScreen(30.0, 0.0)  # their intersection
    near = QPointF(cross.x() + 3.0, cross.y() + 3.0)
    wx, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wx, 30.0, 6)  # snapped to the exact crossing
    self.assertAlmostEqual(wy, 0.0, 6)

  def _dragDimension(self, window: CADWindow, startWorld: tuple,
                     endWorld: tuple) -> tuple:
    """Drag a dimension between two world points; return its vertices."""
    canvas = window.canvas
    captured = []
    canvas.setAddCallback(lambda kind, verts: captured.append(verts))
    window._selectTool('Dimension')
    start = canvas.worldToScreen(startWorld[0], startWorld[1])
    end = canvas.worldToScreen(endWorld[0], endWorld[1])
    canvas.mousePressEvent(_MouseEvent(start.x(), start.y()))
    canvas.mouseMoveEvent(_MouseEvent(end.x(), end.y()))
    canvas.mouseReleaseEvent(_MouseEvent(end.x(), end.y()))
    return captured[0]

  def test_dimension_locks_perpendicular_to_module(self, ) -> None:
    """A dimension begun on a module line measures perpendicular to it."""
    window = CADWindow()
    window.show()
    window.canvas.resize(520, 420)
    window.canvas.scene.addItem(ModuleLine(0.0, 0.0, 0.0))  # datum
    (x1, y1), (x2, y2) = self._dragDimension(
        window, (20.0, 0.0), (45.0, 30.0))  # start on datum, drag diagonally
    self.assertAlmostEqual(y1, 0.0, 6)  # start sits on the datum
    self.assertAlmostEqual(x2, x1, 6)  # locked vertical: perpendicular

  def test_dimension_off_module_is_unconstrained(self, ) -> None:
    """A dimension not begun on a module line is free, not perpendicular."""
    window = CADWindow()
    window.show()
    window.canvas.resize(520, 420)
    window.canvas.scene.addItem(ModuleLine(0.0, 0.0, 0.0))
    (x1, y1), (x2, y2) = self._dragDimension(
        window, (10.0, 50.0), (60.0, 80.0))  # well clear of the module line
    self.assertNotAlmostEqual(x2, x1, 3)  # free: both coordinates move

  def test_dimension_at_intersection_picks_axis_by_drag(self, ) -> None:
    """At a module crossing the dimension locks to the drag-aligned axis."""
    window = CADWindow()
    window.show()
    window.canvas.resize(520, 420)
    window.canvas.scene.addItem(ModuleLine(0.0, 0.0, 0.0))  # horizontal
    window.canvas.scene.addItem(ModuleLine(30.0, 0.0, 90.0))  # vertical
    (x1, y1), (x2, y2) = self._dragDimension(
        window, (30.0, 0.0), (70.0, 8.0))  # at crossing, drag mostly right
    self.assertAlmostEqual(y2, y1, 6)  # locked horizontal

  def test_pointer_snaps_onto_dimension_body(self, ) -> None:
    """The pointer snaps onto the body of an existing linear dimension."""
    canvas = self._snapCanvas(Dimension(10.0, 10.0, 90.0, 10.0))
    near = self._nearSegment(canvas, (10.0, 10.0), (90.0, 10.0), 5.0)
    _, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wy, 10.0, 6)

  def test_pointer_snaps_onto_angle_arm(self, ) -> None:
    """The pointer snaps onto an arm of an existing angular dimension."""
    canvas = self._snapCanvas(
        AngularDimension(0.0, 0.0, 60.0, 0.0, 0.0, 60.0))
    near = self._nearSegment(canvas, (0.0, 0.0), (60.0, 0.0), 3.0)
    wx, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wy, 0.0, 6)  # onto the horizontal arm
    self.assertAlmostEqual(wx, 30.0, 3)

  def test_pointer_snaps_onto_point_node(self, ) -> None:
    """The pointer snaps exactly onto a nearby standalone point node."""
    canvas = self._snapCanvas(AnchorPoint(40.0, 40.0))
    screen = canvas.worldToScreen(40.0, 40.0)
    near = QPointF(screen.x() + 3.0, screen.y() - 3.0)
    wx, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wx, 40.0, 6)  # exact node, not a grid round
    self.assertAlmostEqual(wy, 40.0, 6)

  def test_point_snap_takes_priority_over_segment(self, ) -> None:
    """A point node near a line wins the snap over the line beneath it."""
    canvas = self._snapCanvas(Dimension(0.0, 0.0, 100.0, 0.0))  # along y = 0
    canvas.scene.addItem(AnchorPoint(50.0, 3.0))  # 3 mm above the line
    screen = canvas.worldToScreen(50.0, 3.0)
    near = QPointF(screen.x() + 1.0, screen.y() + 1.0)
    wx, wy = canvas._worldAt(near)
    self.assertAlmostEqual(wx, 50.0, 6)
    self.assertAlmostEqual(wy, 3.0, 6)  # the node, not (≈50, 0) on the line

  def test_snap_segments_cover_dimension_kinds(self, ) -> None:
    """'_snapSegments' yields a segment per dimension body and angle arm."""
    canvas = CADWidget()
    canvas.scene.addItem(Dimension(0.0, 0.0, 1.0, 0.0))  # 1 segment
    canvas.scene.addItem(AngularDimension(0.0, 0.0, 1.0, 0.0, 0.0, 1.0))  # 2
    canvas.scene.addItem(ModuleLine(0.0, 0.0, 45.0))  # infinite, no seg
    canvas.scene.addItem(AnchorPoint(5.0, 5.0))  # a node, not a segment
    self.assertEqual(len(canvas._snapSegments()), 1 + 2)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  UNSAVED-CHANGES GUARD   # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _patchDiscardAnswer(answer) -> tuple:
    """
    Replace the window module's 'QMessageBox' so the unsaved-changes prompt
    returns 'answer' with no real dialog. Returns '(module, original)' so the
    caller restores it in a 'finally'.
    """
    import worQt.window._cad_window as windowModule
    from PySide6.QtWidgets import QMessageBox

    class _FakeMessageBox:
      StandardButton = QMessageBox.StandardButton

      @staticmethod
      def question(*_a) -> object:
        return answer

    original = windowModule.QMessageBox
    windowModule.QMessageBox = _FakeMessageBox
    return windowModule, original

  def test_edits_mark_document_dirty(self, ) -> None:
    """A fresh document is clean; editing the scene marks it unsaved."""
    window = CADWindow()
    window.show()
    self.assertFalse(window.dirty)
    window.addItem(AnchorPoint(1.0, 2.0))
    self.assertTrue(window.dirty)
    window._onUndo()  # back to the empty startup baseline
    self.assertFalse(window.dirty)  # matches the original document again

  def test_undo_redo_track_saved_state(self, ) -> None:
    """Dirty clears when undo/redo returns the scene to the saved state."""
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(1.0, 1.0))
    window._markSaved()  # stand in for a successful save of this state
    self.assertFalse(window.dirty)
    window.addItem(AnchorPoint(2.0, 2.0))  # diverge from the saved state
    self.assertTrue(window.dirty)
    window._onUndo()  # back to exactly the saved state
    self.assertFalse(window.dirty)
    window._onRedo()  # diverge again
    self.assertTrue(window.dirty)

  def test_clean_document_needs_no_discard_prompt(self, ) -> None:
    """With nothing unsaved, the discard guard passes without a dialog."""
    window = CADWindow()
    window.show()
    self.assertTrue(window._confirmDiscard())  # clean -> True, no modal
    window.addItem(AnchorPoint(0.0, 0.0))
    window.dirty = False  # as if it had just been saved
    self.assertTrue(window._confirmDiscard())

  def test_unsaved_changes_cancel_blocks_close(self, ) -> None:
    """Cancelling the unsaved-changes prompt keeps the window open."""
    from PySide6.QtGui import QCloseEvent
    from PySide6.QtWidgets import QMessageBox
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))  # make it dirty
    module, original = self._patchDiscardAnswer(
        QMessageBox.StandardButton.Cancel)
    try:
      event = QCloseEvent()
      window.closeEvent(event)
      self.assertFalse(event.isAccepted())  # cancelled: not closing
    finally:
      module.QMessageBox = original

  def test_unsaved_changes_discard_allows_close(self, ) -> None:
    """Discarding unsaved changes lets the window close."""
    import tempfile
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QCloseEvent
    from PySide6.QtWidgets import QMessageBox
    #  redirect QSettings so _saveGeometry never touches real config
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                      tempfile.mkdtemp())
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))
    module, original = self._patchDiscardAnswer(
        QMessageBox.StandardButton.Discard)
    try:
      event = QCloseEvent()
      window.closeEvent(event)
      self.assertTrue(event.isAccepted())  # discarded: free to close
    finally:
      module.QMessageBox = original

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  UNDO / REDO   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_undo_reverts_add_and_redo_restores_it(self, ) -> None:
    """Undo removes the last added item; redo brings it back identically."""
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(1.0, 2.0))
    window.addItem(Dimension(0.0, 0.0, 5.0, 5.0))
    window._onUndo()
    self.assertEqual(len(window.canvas.scene), 1)
    self.assertEqual(window.selectionTool.itemList.count(), 1)
    self.assertEqual(describeItem(window.canvas.scene.items[0]),
                     ('Anchor', [(1.0, 2.0)]))
    window._onRedo()
    self.assertEqual(len(window.canvas.scene), 2)
    self.assertEqual(describeItem(window.canvas.scene.items[1]),
                     ('Dimension', [(0.0, 0.0), (5.0, 5.0)]))

  def test_undo_redo_actions_track_history(self, ) -> None:
    """Undo/Redo menu actions enable only when their stack has entries."""
    window = CADWindow()
    window.show()
    undo = getattr(window, '__undo_action__')
    redo = getattr(window, '__redo_action__')
    self.assertFalse(undo.isEnabled())  # nothing to undo on a fresh document
    self.assertFalse(redo.isEnabled())
    window.addItem(AnchorPoint(0.0, 0.0))
    self.assertTrue(undo.isEnabled())
    self.assertFalse(redo.isEnabled())
    window._onUndo()
    self.assertFalse(undo.isEnabled())
    self.assertTrue(redo.isEnabled())

  def test_new_edit_invalidates_redo(self, ) -> None:
    """A fresh edit after an undo clears the redo trail."""
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))
    window.addItem(AnchorPoint(1.0, 1.0))
    window._onUndo()  # redo now holds one entry
    self.assertTrue(getattr(window, '__redo_action__').isEnabled())
    window.addItem(AnchorPoint(2.0, 2.0))  # a new edit
    self.assertFalse(getattr(window, '__redo_action__').isEnabled())

  def test_delete_is_undoable(self, ) -> None:
    """Undo restores an item removed with the delete action."""
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(3.0, 4.0))
    window.addItem(Dimension(0.0, 0.0, 1.0, 1.0))
    window.selectionTool.itemList.setCurrentRow(0)  # enter edit mode
    window._deleteSelected()
    self.assertEqual(len(window.canvas.scene), 1)
    window._onUndo()
    self.assertEqual(len(window.canvas.scene), 2)
    self.assertEqual(describeItem(window.canvas.scene.items[0]),
                     ('Anchor', [(3.0, 4.0)]))

  def test_open_clears_undo_history(self, ) -> None:
    """Opening a drawing starts a fresh history with nothing to undo."""
    import os
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'drawing.json')
    saveScene(self._populatedScene(), path)
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))  # gives the history an entry
    loadScene(path, window.canvas.scene)
    window._syncListToScene()
    window._clearHistory()
    self.assertFalse(getattr(window, '__undo_action__').isEnabled())
    self.assertFalse(getattr(window, '__redo_action__').isEnabled())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SAVE / RENAME (file naming)   # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _patchFileDialog(path: str) -> tuple:
    """
    Replace the window module's 'QFileDialog' so the Save/Open dialogs
    return 'path' (an empty string stands in for a cancelled dialog) with
    no real modal. Returns '(module, original)' for the caller to restore
    in a 'finally'.
    """
    import worQt.window._cad_window as windowModule

    class _FakeFileDialog:
      @staticmethod
      def getSaveFileName(*_a) -> tuple:
        return (path, '')

      @staticmethod
      def getOpenFileName(*_a) -> tuple:
        return (path, '')

    original = windowModule.QFileDialog
    windowModule.QFileDialog = _FakeFileDialog
    return windowModule, original

  def test_untitled_model_has_untitled_title(self, ) -> None:
    """A never-saved model is 'untitled', and a star marks unsaved edits."""
    window = CADWindow()
    window.show()
    self.assertIsNone(getattr(window, '__file_path__'))
    self.assertEqual(window.windowTitle(), 'worQt CAD - untitled')
    window.addItem(AnchorPoint(1.0, 2.0))  # an edit -> dirty
    self.assertEqual(window.windowTitle(), 'worQt CAD - untitled*')

  def test_save_while_untitled_runs_rename(self, ) -> None:
    """Saving an untitled model routes through Rename to name it first."""
    import os
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'model.json')
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(1.0, 2.0))
    module, original = self._patchFileDialog(path)
    try:
      self.assertTrue(window._onSave())  # untitled -> rename dialog
    finally:
      module.QFileDialog = original
    self.assertEqual(getattr(window, '__file_path__'), path)
    self.assertTrue(os.path.exists(path))
    self.assertFalse(window.dirty)
    self.assertEqual(window.windowTitle(), 'worQt CAD - %s' % path)

  def test_named_save_writes_without_a_dialog(self, ) -> None:
    """Once named, Save writes straight to the file, opening no dialog."""
    import os
    import json
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'model.json')
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(1.0, 2.0))
    module, original = self._patchFileDialog(path)
    try:
      window._onSave()  # the first save names the model
    finally:
      module.QFileDialog = original
    window.addItem(AnchorPoint(3.0, 4.0))  # a further edit to save

    import worQt.window._cad_window as windowModule

    class _NoDialog:
      @staticmethod
      def getSaveFileName(*_a) -> tuple:
        raise AssertionError('a named Save must not open a dialog')

    guard = windowModule.QFileDialog
    windowModule.QFileDialog = _NoDialog
    try:
      self.assertTrue(window._onSave())  # silent write, no dialog
    finally:
      windowModule.QFileDialog = guard
    self.assertFalse(window.dirty)
    with open(path) as handle:
      self.assertEqual(len(json.load(handle)['items']), 2)

  def test_rename_moves_the_file(self, ) -> None:
    """Rename writes the new file and removes the old: a move, not a copy."""
    import os
    import tempfile
    folder = tempfile.mkdtemp()
    pathA = os.path.join(folder, 'a.json')
    pathB = os.path.join(folder, 'b.json')
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))
    module, original = self._patchFileDialog(pathA)
    try:
      window._onSave()  # named a.json
    finally:
      module.QFileDialog = original
    self.assertTrue(os.path.exists(pathA))
    module, original = self._patchFileDialog(pathB)
    try:
      self.assertTrue(window._onRename())
    finally:
      module.QFileDialog = original
    self.assertEqual(getattr(window, '__file_path__'), pathB)
    self.assertTrue(os.path.exists(pathB))
    self.assertFalse(os.path.exists(pathA))  # the old file is gone

  def test_rename_appends_json_extension(self, ) -> None:
    """A rename target with no extension gets '.json' appended."""
    import os
    import tempfile
    base = os.path.join(tempfile.mkdtemp(), 'noext')
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))
    module, original = self._patchFileDialog(base)  # no '.json'
    try:
      window._onRename()
    finally:
      module.QFileDialog = original
    self.assertEqual(getattr(window, '__file_path__'), base + '.json')

  def test_rename_cancel_keeps_state(self, ) -> None:
    """Cancelling the Rename dialog leaves the model untitled and dirty."""
    window = CADWindow()
    window.show()
    window.addItem(AnchorPoint(0.0, 0.0))
    module, original = self._patchFileDialog('')  # cancelled
    try:
      self.assertFalse(window._onRename())
    finally:
      module.QFileDialog = original
    self.assertIsNone(getattr(window, '__file_path__'))
    self.assertTrue(window.dirty)

  def test_open_tracks_path_for_silent_save(self, ) -> None:
    """Opening a file records its path, so a later Save needs no dialog."""
    import os
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'doc.json')
    saveScene(self._populatedScene(), path)
    window = CADWindow()
    window.show()
    module, original = self._patchFileDialog(path)
    try:
      window._onOpen()  # clean scene -> no discard prompt
    finally:
      module.QFileDialog = original
    self.assertEqual(getattr(window, '__file_path__'), path)
    self.assertEqual(window.windowTitle(), 'worQt CAD - %s' % path)
    self.assertFalse(window.dirty)
