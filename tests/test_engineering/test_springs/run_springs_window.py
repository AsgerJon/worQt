"""
RunSpringsWindow covers 'SpringsApp' and its 'SpringsWindow': it opens
set up; 'Play' sets it moving, 'Pause' stops it, 'Reset' takes it back;
masses, anchors, springs, dampers and components are added and
removed; the panel's numbers and buttons set the parts: a point's axes,
a component's turning; a mode clicked sets it swinging in it; the
curves plot the energies, the total kept, and the place of the point
selected.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.springs import Damper, Motion
from worQt.engineering.springs.gui import SpringsApp, SpringsWindow

from . import SpringsWidgetTest


class RunSpringsWindow(SpringsWidgetTest):
  """Tests for 'SpringsApp' and 'SpringsWindow'."""

  __application_type__ = SpringsApp

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)

  def openWindow(self) -> SpringsWindow:
    """The window, shown live."""
    window = SpringsWindow()
    self.showLive(window)
    return window

  def run_opens_set_up(self) -> None:
    """It opens on the standard system, set up: it may be played or
    changed, not reset, and joins nothing with no two points
    selected."""
    window = self.openWindow()
    bar = window.toolBar
    self.assertEqual(window.windowTitle(), 'Springs')
    self.assertIsNone(window.motion)
    self.assertTrue(bar.playButton.isEnabled())
    self.assertFalse(bar.resetButton.isEnabled())
    self.assertTrue(bar.massButton.isEnabled())
    self.assertFalse(bar.springButton.isEnabled())
    self.assertEqual(window.status.text, 'Set up')
    self.assertEqual(window.status.details,
                     '3 points, 2 springs, 0 dampers, 0 components')
    window.close()

  def run_play_pause_reset(self) -> None:
    """'Play' sets it moving and says 'Pause'; paused, it stops; 'Reset'
    takes it back to how it was set up."""
    window = self.openWindow()
    bar = window.toolBar
    self.click(bar.playButton)
    self.assertTrue(window.running)
    self.assertIsInstance(window.motion, Motion)
    self.assertEqual(bar.playButton.text, 'Pause')
    self.assertFalse(bar.massButton.isEnabled())
    window.advance(1.0)
    self.assertAlmostEqual(window.motion.time, 1.0)
    self.click(bar.playButton)
    self.assertFalse(window.running)
    self.assertEqual(window.status.mode, 'paused')
    self.click(bar.resetButton)
    self.assertIsNone(window.motion)
    self.assertTrue(bar.massButton.isEnabled())
    window.close()

  def run_add_and_remove(self) -> None:
    """'Add mass' hangs a mass under the point selected; with two points
    selected, 'Add damper' joins them; 'Add anchor' adds a pinned point;
    'Remove' takes away what is selected."""
    window = self.openWindow()
    bar, view = window.toolBar, window.sceneView
    view.select(('point', 2))
    self.click(bar.massButton)
    system = window.system
    self.assertEqual(len(system.points), 4)
    self.assertEqual(system.springs[-1][:2], (2, 3))
    self.assertEqual(system.points[3].at[2], system.points[2].at[2] - 0.5)
    self.assertEqual(view.selected, ('point', 3))
    view.select(('point', 0))
    view.toggle(('point', 3))
    window.refresh()
    self.assertTrue(bar.damperButton.isEnabled())
    self.click(bar.damperButton)
    self.assertEqual(window.system.dampers, (Damper(0, 3, 2.0),))
    self.click(bar.anchorButton)
    self.assertTrue(window.system.points[-1].pinned)
    self.click(bar.removeButton)
    self.assertEqual(len(window.system.points), 4)
    window.close()

  def run_panel_sets_parts(self) -> None:
    """A spring selected shows its stiffness, and a number typed sets
    it; with nothing selected, the gravity."""
    window = self.openWindow()
    panel = window.panel
    window.sceneView.select(('spring', 0))
    self.assertEqual(panel.title(), 'Spring S1')
    self.assertEqual(panel.stiffnessField.value, 80.0)
    panel.stiffnessField.value = 120.0
    panel.stiffnessField.valueEdited.emit(120.0)
    self.assertEqual(window.system.springs[0].stiffness, 120.0)
    window.sceneView.select(None)
    panel.gravityField.value = 1.62
    panel.gravityField.valueEdited.emit(1.62)
    self.assertEqual(window.system.gravity, 1.62)
    window.close()

  def run_pluck_a_mode(self) -> None:
    """A mode clicked sets the system swinging in it alone, from rest,
    the point moving most in it moved a tenth of a metre."""
    window = self.openWindow()
    buttons = [b for b in window.panel.modeButtons() if b.isVisible()]
    self.assertEqual(len(buttons), 6)
    self.assertIn('Hz', buttons[0].text)
    self.click(buttons[2])
    self.assertTrue(window.running)
    rest = window.system.rest()
    moved = (window.motion.positions - rest).norm(2, -1)
    self.assertAlmostEqual(float(moved.max()), 0.1)
    window.close()

  def run_curves(self) -> None:
    """Moving, the energies are plotted, their total kept, and the place
    of the point selected."""
    window = self.openWindow()
    window.sceneView.select(('point', 2))
    window.togglePlay()
    for _ in range(120):
      window.advance(1 / 60)
    energy = window.energyCurve.series
    self.assertEqual([name for name, *_ in energy],
                     ['moving', 'springs', 'height', 'heat', 'total'])
    totals = [value for _, value in energy[-1][2]]
    self.assertLess(max(totals) - min(totals), 1e-3)
    trace = window.traceCurve.series
    self.assertEqual([name for name, *_ in trace], ['x', 'y', 'z'])
    self.assertEqual(window.traceCurve.title, 'Where P3 is')
    window.close()

  def run_components(self) -> None:
    """'Add component' hangs a spring-mass-damper under the point
    selected, fixed in direction; its buttons turn it on a hinge, about
    another axis, or free; a point's buttons choose the axes it moves
    along."""
    window = self.openWindow()
    bar, panel, view = window.toolBar, window.panel, window.sceneView
    view.select(('point', 2))
    self.click(bar.componentButton)
    system = window.system
    self.assertEqual(len(system.components), 1)
    rod = system.components[0]
    self.assertEqual((rod.base, rod.tip, rod.turning), (2, 3, 'fixed'))
    self.assertEqual(view.selected, ('component', 0))
    self.assertEqual(panel.title(), 'Component C1')
    self.assertFalse(panel.aboutXButton.isVisible())
    self.click(panel.hingeButton)
    self.assertEqual(window.system.components[0].turning, 'hinge')
    self.assertTrue(panel.aboutXButton.isVisible())
    self.click(panel.aboutXButton)
    self.assertEqual(window.system.components[0].axis, (1.0, 0.0, 0.0))
    self.click(panel.aboutZButton)
    self.assertEqual(window.system.components[0].axis, (1.0, 0.0, 0.0))
    self.assertIn('along the rod', panel.note)
    self.click(panel.freeButton)
    self.assertEqual(window.system.components[0].turning, 'free')
    view.select(('point', 1))
    self.assertTrue(panel.moveXButton.checked)
    self.click(panel.moveXButton)
    self.assertEqual(window.system.points[1].moves, 'yz')
    self.click(panel.moveYButton)
    self.click(panel.moveZButton)
    self.assertEqual(panel.title(), 'Anchor P2')
    window.close()
