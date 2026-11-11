"""
RunSceneView covers 'SceneView', a system of springs in space: it shows
the whole system; a click selects a part, Ctrl and a click more, a click
on nothing nothing; a point dragged, set up, goes where it is dragged,
to the centimetre; a drag across the space turns it; Delete removes
what is selected; moving, a point dragged is held by the hand and let
go.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from worQt.engineering.springs import Motion
from worQt.engineering.springs.gui import SceneView

from . import SpringsWidgetTest


class RunSceneView(SpringsWidgetTest):
  """Tests for 'SceneView'."""

  def openView(self) -> SceneView:
    """The view of the standard system, shown live."""
    view = SceneView()
    view.resize(900, 620)
    self.showLive(view)
    view.fit()
    return view

  def pixelOf(self, view: SceneView, index: int) -> QPointF:
    """Where the point of 'index' is seen."""
    return view.project(view.positions()[index])[0]

  def ctrlClick(self, view: SceneView, pixel: QPointF) -> None:
    """A click at 'pixel' with Ctrl held."""
    for kind in (QEvent.Type.MouseButtonPress,
                 QEvent.Type.MouseButtonRelease):
      button = Qt.MouseButton.LeftButton
      buttons = button if kind == QEvent.Type.MouseButtonPress else (
        Qt.MouseButton.NoButton)
      event = QMouseEvent(kind, pixel, view.mapToGlobal(pixel), button,
                          buttons, Qt.KeyboardModifier.ControlModifier)
      QApplication.sendEvent(view, event)

  def run_shows_all(self) -> None:
    """Fitted, every point is seen inside the view."""
    view = self.openView()
    self.assertTrue(view.showsAll())
    self.assertEqual(len(view.positions()), 3)

  def run_click_selects(self) -> None:
    """A click selects the point under it, Ctrl and a click selects
    another besides, a click on nothing selects nothing."""
    view = self.openView()
    spy = self.spy(view.selectionChanged)
    self.click(view, self.pixelOf(view, 1))
    self.assertEqual(view.selected, ('point', 1))
    self.ctrlClick(view, self.pixelOf(view, 2))
    self.assertEqual(view.selection, (('point', 1), ('point', 2)))
    self.assertEqual(view.selectedPoints(), (1, 2))
    self.click(view, QPointF(20.0, 20.0))
    self.assertEqual(view.selection, ())
    self.assertGreaterEqual(spy.count, 3)

  def run_drag_a_point(self) -> None:
    """Set up, a point dragged goes where it is dragged, square to the
    view, to the centimetre, emitting 'systemEdited'."""
    view = self.openView()
    spy = self.spy(view.systemEdited)
    start = self.pixelOf(view, 2)
    target = QPointF(start.x() + 60.0, start.y() - 40.0)
    self.press(view, start)
    self.move(view, target)
    self.release(view, target)
    moved = view.system.points[2].at
    self.assertNotEqual(moved, (0.25, 0.1, 0.7))
    for value in moved:
      self.assertAlmostEqual(value * 100, round(value * 100))
    self.assertLess(abs(self.pixelOf(view, 2).x() - target.x()), 6.0)
    self.assertGreaterEqual(spy.count, 1)

  def run_drag_the_space(self) -> None:
    """A drag across nothing turns the view, and selects nothing."""
    view = self.openView()
    yaw, pitch = view.yaw, view.pitch
    self.press(view, QPointF(20.0, 300.0))
    self.move(view, QPointF(120.0, 340.0))
    self.release(view, QPointF(120.0, 340.0))
    self.assertNotAlmostEqual(view.yaw, yaw)
    self.assertNotAlmostEqual(view.pitch, pitch)

  def run_delete(self) -> None:
    """Delete removes what is selected, the springs on a point with
    it."""
    view = self.openView()
    view.select(('point', 2))
    self.key(view, Qt.Key.Key_Delete)
    self.assertEqual(len(view.system.points), 2)
    self.assertEqual(len(view.system.springs), 1)
    self.assertEqual(view.selection, ())

  def run_held_while_moving(self) -> None:
    """Moving, a point dragged is held by the hand, and let go."""
    view = self.openView()
    motion = Motion(view.system)
    view.motion = motion
    view.live = True
    start = self.pixelOf(view, 2)
    self.press(view, start)
    self.move(view, QPointF(start.x() + 50.0, start.y()))
    self.assertEqual(motion.held, (2,))
    self.release(view, QPointF(start.x() + 50.0, start.y()))
    self.assertEqual(motion.held, ())
    self.assertEqual(view.system.points[2].at, (0.25, 0.1, 0.7))
