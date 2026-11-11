"""
RunDiskApp covers 'DiskApp' and its 'DiskWindow': the window opens on
the example deep beam with the disk selected and nothing to undo; the
buttons add, undo and redo; a click on the drawing shows its selection
in the panel, and what the panel edits shows in the drawing.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.gui import DiskApp, DiskWindow

from . import EngineeringWidgetTest, DEEP_BEAM


class RunDiskApp(EngineeringWidgetTest):
  """Tests for 'DiskApp' and 'DiskWindow'."""

  __application_type__ = DiskApp

  def setUp(self) -> None:
    """Every test gets a fresh window. Closing it must not quit the
    application the tests run in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)
    self.app.__main_window__ = None

  def openWindow(self) -> DiskWindow:
    """The application's window, shown live, so its UI is built."""
    window = self.app.window
    self.showLive(window)
    return window

  def run_opens_on_the_example(self) -> None:
    """The window opens on the wall over the entrance, the disk
    selected and shown in the panel, with nothing to undo or redo."""
    window = self.openWindow()
    self.assertEqual(str(window.diskView.disk), DEEP_BEAM)
    self.assertEqual(window.inspector.title, 'Disk')
    self.assertFalse(window.toolBar.undoButton.isEnabled())
    self.assertFalse(window.toolBar.redoButton.isEnabled())

  def run_adding_shows_what_is_added(self) -> None:
    """'Add support' adds one and shows it in the panel; 'Add load' and
    'Add reinforcement' likewise; then there is something to undo."""
    window = self.openWindow()
    self.click(window.toolBar.addSupportButton)
    self.assertEqual(len(window.diskView.disk.supports), 3)
    self.assertEqual(window.inspector.title, 'Support')
    self.click(window.toolBar.addLoadButton)
    self.assertEqual(len(window.diskView.disk.loads), 2)
    self.assertEqual(window.inspector.title, 'Load')
    self.click(window.toolBar.addRebarButton)
    self.assertEqual(len(window.diskView.disk.rebars), 1)
    self.assertEqual(window.inspector.title, 'Reinforcement')
    self.assertTrue(window.toolBar.undoButton.isEnabled())

  def run_the_panel_follows_the_drawing(self) -> None:
    """A click on a support shows it in the panel; a click beside the
    disk shows the disk again."""
    window = self.openWindow()
    view = window.diskView
    self.click(view, view.plateRect(1).center())
    self.assertEqual(window.inspector.title, 'Support')
    self.assertEqual([field.value for field in window.inspector.fields],
                     [5.7, 6.0])
    self.click(view, view.diskRect().center())
    self.assertEqual(window.inspector.title, 'Disk')

  def run_the_drawing_follows_the_panel(self) -> None:
    """What the panel edits shows in the drawing, and its 'Remove'
    removes."""
    window = self.openWindow()
    view = window.diskView
    self.click(view, view.plateRect(0).center())
    self.click(window.inspector.pinButton)
    support = view.disk.supports[0]
    self.assertTrue(support.setsX and support.setsY)
    self.assertTrue(window.inspector.pinButton.checked)
    self.click(window.inspector.removeButton)
    self.assertEqual(len(view.disk.supports), 1)
    self.assertEqual(window.inspector.title, 'Disk')

  def run_undo_and_redo_buttons(self) -> None:
    """'Undo' steps back an edit and 'Redo' forward again, each greyed
    out when there is nothing for it."""
    window = self.openWindow()
    bar, view = window.toolBar, window.diskView
    self.click(bar.addSupportButton)
    self.click(bar.undoButton)
    self.assertEqual(str(view.disk), DEEP_BEAM)
    self.assertFalse(bar.undoButton.isEnabled())
    self.assertTrue(bar.redoButton.isEnabled())
    self.click(bar.redoButton)
    self.assertEqual(len(view.disk.supports), 3)
    self.assertFalse(bar.redoButton.isEnabled())
