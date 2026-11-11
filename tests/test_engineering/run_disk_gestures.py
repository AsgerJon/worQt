"""
RunDiskGestures covers editing a disk on a 'DiskWidget' with the mouse,
the way any drawing program does: a click selects the disk, a support
or a load; the selected disk shows handles that resize it; a support is
dragged anywhere round the edges, and the selected one shows handles
that widen it; a load is dragged along its edge; Delete removes what is
selected; supports and loads are added at once where there is room;
every edit can be undone and redone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF

from worQt.engineering import Disk, Load
from worQt.engineering.gui import DiskWidget, GripNum

from . import EngineeringWidgetTest, deepBeam


class RunDiskGestures(EngineeringWidgetTest):
  """Tests for editing a disk on a 'DiskWidget' with the mouse."""

  def _liveWidget(self, disk: Disk = None) -> DiskWidget:
    widget = DiskWidget()
    widget.disk = deepBeam() if disk is None else disk
    widget.resize(800, 500)
    self.showLive(widget)
    widget.repaint()
    return widget

  def drag(self, widget: DiskWidget, start: QPointF, end: QPointF) -> None:
    """Press at 'start', move through the middle to 'end', release."""
    self.press(widget, start)
    self.move(widget, (start + end) * 0.5)
    self.move(widget, end)
    self.release(widget, end)

  def _kind(self, widget: DiskWidget) -> GripNum:
    return widget.selection.kind

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SELECTING  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_a_click_selects(self) -> None:
    """The disk is selected at first; a click on a support, a load or
    the disk selects that, and a click beside the disk selects the disk
    again. Each change of selection is told of."""
    widget = self._liveWidget()
    self.assertIs(self._kind(widget), GripNum.DISK)
    spy = self.spy(widget.selectionChanged)
    self.click(widget, widget.plateRect(1).center())
    self.assertIs(self._kind(widget), GripNum.SUPPORT)
    self.assertEqual(widget.selection.index, 1)
    self.click(widget, widget.loadRect(0).center())
    self.assertIs(self._kind(widget), GripNum.LOAD)
    self.click(widget, widget.diskRect().center())
    self.assertIs(self._kind(widget), GripNum.DISK)
    self.click(widget, widget.loadRect(0).center())
    self.click(widget, QPointF(4.0, 4.0))
    self.assertIs(self._kind(widget), GripNum.DISK)
    self.assertEqual(spy.count, 5)

  def run_handles_belong_to_the_selected_disk(self) -> None:
    """The handles that resize the disk are there while the disk is
    selected, and not while a support is."""
    widget = self._liveWidget()
    point = widget.handlePoint(GripNum.LENGTH)
    self.assertIs(widget.gripAt(point).kind, GripNum.LENGTH)
    self.click(widget, widget.plateRect(1).center())
    grip = widget.gripAt(point)
    self.assertIsNot(None if grip is None else grip.kind, GripNum.LENGTH)

  def run_the_cursor_tells(self) -> None:
    """Over a handle the cursor shows the way it resizes; over what can
    be dragged, a hand; elsewhere, the arrow."""
    widget = self._liveWidget()
    shape = Qt.CursorShape
    cases = (
      (widget.handlePoint(GripNum.LENGTH), shape.SizeHorCursor),
      (widget.handlePoint(GripNum.HEIGHT), shape.SizeVerCursor),
      (widget.handlePoint(GripNum.CORNER), shape.SizeBDiagCursor),
      (widget.plateRect(0).center(), shape.OpenHandCursor),
      (widget.loadRect(0).center(), shape.OpenHandCursor),
      (widget.diskRect().center(), shape.ArrowCursor),
    )
    for point, expected in cases:
      self.move(widget, point)
      self.assertEqual(widget.cursor().shape(), expected)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  RESIZING   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_dragging_the_length(self) -> None:
    """Dragging the handle on the right edge sets the length, to 5 cm;
    the far bearing rides along. The edit is told of once."""
    widget = self._liveWidget()
    spy = self.spy(widget.diskEdited)
    start = widget.handlePoint(GripNum.LENGTH)
    end = start + QPointF(widget.diskScale() * 1.01, 0.0)
    self.drag(widget, start, end)
    self.assertAlmostEqual(widget.disk.length, 7.0)
    self.assertAlmostEqual(widget.disk.supports[1].end, 7.0)
    self.assertEqual(spy.count, 1)

  def run_dragging_the_height_and_the_corner(self) -> None:
    """The handle on the top edge sets the height, the one at the top
    right corner both."""
    widget = self._liveWidget()
    start = widget.handlePoint(GripNum.HEIGHT)
    self.drag(widget, start, start - QPointF(0.0, widget.diskScale() * 0.3))
    self.assertAlmostEqual(widget.disk.height, 3.0)
    scale = widget.diskScale()
    start = widget.handlePoint(GripNum.CORNER)
    self.drag(widget, start, start + QPointF(scale * -1.0, scale * 1.0))
    self.assertAlmostEqual(widget.disk.length, 5.0)
    self.assertAlmostEqual(widget.disk.height, 2.0)

  def run_four_thicknesses_are_a_wall(self) -> None:
    """The length stops at four thicknesses, however far it is
    dragged."""
    widget = self._liveWidget()
    start = widget.handlePoint(GripNum.LENGTH)
    self.drag(widget, start, start - QPointF(5000.0, 0.0))
    self.assertAlmostEqual(widget.disk.length, 1.2)

  def run_the_view_holds_still_while_dragging(self) -> None:
    """While a handle is dragged the drawing keeps its scale, so the
    disk follows the mouse; let go, and it fits the frame again."""
    widget = self._liveWidget()
    origin = widget.toScreen(0.0, 0.0)
    start = widget.handlePoint(GripNum.LENGTH)
    self.press(widget, start)
    self.move(widget, start + QPointF(200.0, 0.0))
    self.assertEqual(widget.toScreen(0.0, 0.0), origin)
    self.release(widget, start + QPointF(200.0, 0.0))
    frame, box = widget.frameRect(), widget.diskRect()
    self.assertTrue(frame.adjusted(-1e-6, -1e-6, 1e-6, 1e-6).contains(box))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SUPPORTS AND LOADS   # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_sliding_a_support(self) -> None:
    """A support dragged along its edge slides there, and stops at its
    neighbour."""
    widget = self._liveWidget()
    start = widget.plateRect(0).center()
    self.drag(widget, start, start + QPointF(widget.diskScale(), 0.0))
    self.assertEqual(str(widget.disk.supports[0]), 'support bottom 1 1.3 y')
    start = widget.plateRect(0).center()
    self.drag(widget, start, start + QPointF(5000.0, 0.0))
    self.assertEqual(str(widget.disk.supports[0]),
                     'support bottom 5.4 5.7 y')

  def run_a_support_goes_round_the_corner(self) -> None:
    """A support dragged to another edge goes onto that edge, a roller
    holding the disk across it."""
    widget = self._liveWidget()
    start = widget.plateRect(0).center()
    self.drag(widget, start, widget.toScreen(-0.1, 1.35))
    self.assertEqual(str(widget.disk.supports[0]), 'support left 1.2 1.5 x')

  def run_widening_the_selected_support(self) -> None:
    """The selected support shows a handle at each end of its plate,
    which widens it."""
    widget = self._liveWidget()
    self.click(widget, widget.plateRect(0).center())
    start = widget.supportEndPoint(GripNum.SUPPORT_END)
    end = start + QPointF(widget.diskScale() * 0.2, 0.0)
    self.drag(widget, start, end)
    self.assertEqual(str(widget.disk.supports[0]), 'support bottom 0 0.5 y')

  def run_sliding_a_load(self) -> None:
    """A load dragged along its edge slides there, within the edge."""
    disk = Disk(6, 2.7, 0.3)
    disk.addLoad(Load('load top 2.85 3.15 F 0 -500'))
    widget = self._liveWidget(disk)
    start = widget.loadRect(0).center()
    self.drag(widget, start, start + QPointF(widget.diskScale(), 0.0))
    self.assertEqual(str(widget.disk.loads[0]),
                     'load top 3.85 4.15 F 0 -500')
    start = widget.loadRect(0).center()
    self.drag(widget, start, start + QPointF(5000.0, 0.0))
    self.assertEqual(str(widget.disk.loads[0]), 'load top 5.7 6 F 0 -500')

  def run_delete_removes_the_selected(self) -> None:
    """Delete removes the selected support or load, and the disk is
    selected again; with the disk selected it removes nothing."""
    widget = self._liveWidget()
    self.click(widget, widget.plateRect(0).center())
    self.key(widget, Qt.Key.Key_Delete)
    self.assertEqual(len(widget.disk.supports), 1)
    self.assertIs(self._kind(widget), GripNum.DISK)
    self.key(widget, Qt.Key.Key_Delete)
    self.assertEqual(len(widget.disk.supports), 1)
    self.assertEqual(len(widget.disk.loads), 1)

  def run_adding_selects_what_is_added(self) -> None:
    """A support is added at the first room on the bottom edge, a load
    in the middle of the top edge, each selected as it comes."""
    widget = self._liveWidget()
    widget.addSupport()
    self.assertEqual(str(widget.disk.supports[-1]),
                     'support bottom 0.3 0.6 y')
    self.assertIs(self._kind(widget), GripNum.SUPPORT)
    self.assertEqual(widget.selection.index, 2)
    widget.addLoad()
    self.assertEqual(str(widget.disk.loads[-1]),
                     'load top 2.85 3.15 F 0 -100')
    self.assertIs(self._kind(widget), GripNum.LOAD)
    self.assertEqual(widget.selection.index, 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  UNDO   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_undo_and_redo(self) -> None:
    """Every edit can be undone and redone, each told of; what was
    selected and is gone leaves the disk selected."""
    widget = self._liveWidget()
    spy = self.spy(widget.diskEdited)
    self.assertFalse(widget.canUndo)
    before = str(widget.disk)
    widget.addSupport()
    after = str(widget.disk)
    self.assertTrue(widget.canUndo)
    widget.undo()
    self.assertEqual(str(widget.disk), before)
    self.assertIs(self._kind(widget), GripNum.DISK)
    self.assertTrue(widget.canRedo)
    widget.redo()
    self.assertEqual(str(widget.disk), after)
    self.assertFalse(widget.canRedo)
    self.assertEqual(spy.count, 3)
