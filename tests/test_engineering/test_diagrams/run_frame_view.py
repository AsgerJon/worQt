"""
RunFrameView covers 'FrameView', a plane frame drawn with its section
force diagrams: it fits the frame; a click selects a node, a member, a
support or a load, Ctrl and a click more, a click on nothing nothing; a
node dragged goes where it is dragged, to the decimetre, carrying the
loads on its members; a load dragged slides along its member; Delete
removes what is selected and what is on it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPointF, Qt

from worQt.engineering.diagrams.gui import FrameView

from . import DiagramsWidgetTest


class RunFrameView(DiagramsWidgetTest):
  """Tests for 'FrameView'."""

  def openView(self) -> FrameView:
    """The view of the standard portal, shown live."""
    view = FrameView()
    view.resize(1000, 700)
    self.showLive(view)
    return view

  def nodePixel(self, view: FrameView, index: int) -> QPointF:
    """Where the node of 'index' is drawn."""
    return view.toScreen(*view.frame.nodes[index])

  def drag(self, view: FrameView, start: QPointF, end: QPointF) -> None:
    """A drag from 'start' to 'end'."""
    self.press(view, start)
    self.move(view, end)
    self.release(view, end)

  def run_fits(self) -> None:
    """Every node is drawn inside the view."""
    view = self.openView()
    for index in range(len(view.frame.nodes)):
      pixel = self.nodePixel(view, index)
      self.assertTrue(0 < pixel.x() < view.width())
      self.assertTrue(0 < pixel.y() < view.height())

  def run_click_selects(self) -> None:
    """A click selects the node, the member or the load under it; on
    nothing, nothing."""
    view = self.openView()
    self.click(view, self.nodePixel(view, 2))
    self.assertEqual(view.selected, ('node', 2))
    start, end = view.memberEnds(1)
    middle = QPointF((start.x() + end.x()) / 2, start.y())
    self.click(view, middle)
    self.assertEqual(view.selected, ('member', 1))
    self.click(view, QPointF(middle.x(), middle.y() - 20.0))
    self.assertEqual(view.selected, ('load', 0))
    view.toggle(('node', 0))
    self.assertEqual(view.selection, (('load', 0), ('node', 0)))
    self.click(view, QPointF(5.0, view.height() - 5.0))
    self.assertEqual(view.selection, ())

  def run_drag_a_node(self) -> None:
    """A node dragged goes where it is dragged, to the decimetre, the
    line load on its member stretched along, emitting 'frameEdited'."""
    view = self.openView()
    spy = self.spy(view.frameEdited)
    start = self.nodePixel(view, 2)
    scale = view.place()[0]
    self.drag(view, start, QPointF(start.x() + 2.04 * scale, start.y()))
    node = view.frame.nodes[2]
    self.assertAlmostEqual(node.x, 8.0)
    self.assertAlmostEqual(node.y, 4.0)
    self.assertAlmostEqual(view.frame.loads[0].end, 8.0)
    self.assertGreaterEqual(spy.count, 1)

  def run_drag_a_load(self) -> None:
    """A point load dragged slides along its member, to the half
    decimetre."""
    view = self.openView()
    tail, head = view.arrowOf(view.frame.loads[1])
    grip = QPointF((tail.x() + head.x()) / 2, (tail.y() + head.y()) / 2)
    scale = view.place()[0]
    self.drag(view, grip, QPointF(grip.x(), grip.y() + 1.0 * scale))
    self.assertAlmostEqual(view.frame.loads[1].at, 3.0)

  def run_delete(self) -> None:
    """Delete removes the node selected, its members and support with
    it."""
    view = self.openView()
    view.select(('node', 3))
    self.key(view, Qt.Key.Key_Delete)
    frame = view.frame
    self.assertEqual(len(frame.nodes), 3)
    self.assertEqual(len(frame.members), 2)
    self.assertEqual(len(frame.supports), 1)
    self.assertEqual(view.selection, ())
