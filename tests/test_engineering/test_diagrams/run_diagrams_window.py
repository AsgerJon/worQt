"""
RunDiagramsWindow covers 'DiagramsApp' and its 'DiagramsWindow': it
opens on the portal, saying how indeterminate it is; members are run
from a node or join two, supports pin a node, loads go on the member
selected; the panel's numbers and buttons set the parts, hinges making
the portal determinate and a roller leaving it not held; the diagram
shown is chosen by its button.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.diagrams import LineLoad, Node, PointLoad
from worQt.engineering.diagrams.gui import DiagramsApp, DiagramsWindow

from . import DiagramsWidgetTest


class RunDiagramsWindow(DiagramsWidgetTest):
  """Tests for 'DiagramsApp' and 'DiagramsWindow'."""

  __application_type__ = DiagramsApp

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)

  def openWindow(self) -> DiagramsWindow:
    """The window, shown live."""
    window = DiagramsWindow()
    self.showLive(window)
    return window

  def run_opens(self) -> None:
    """It opens on the portal, indeterminate twice, showing M."""
    window = self.openWindow()
    self.assertEqual(window.windowTitle(), 'Section forces')
    self.assertEqual(window.status.text, 'Indeterminate 2×')
    self.assertIn('max |M|', window.status.details)
    self.assertEqual(window.frameView.kind, 'M')
    self.assertTrue(window.toolBar.bendingButton.checked)
    self.assertIn('indeterminate 2 times', window.panel.words())
    window.close()

  def run_members_and_supports(self) -> None:
    """'Add member' runs a member 3 m right of the node selected, to a
    new node, selected; 'Add support' pins it; with two nodes selected,
    'Add member' joins them."""
    window = self.openWindow()
    bar, view = window.toolBar, window.frameView
    view.select(('node', 2))
    self.click(bar.memberButton)
    frame = window.frame
    self.assertEqual(frame.nodes[-1], Node(9.0, 4.0))
    self.assertEqual(frame.members[-1][:2], (2, 4))
    self.assertEqual(view.selected, ('node', 4))
    self.click(bar.supportButton)
    self.assertEqual(window.frame.supports[-1][:], (4, 'pin'))
    view.select(('node', 0))
    view.toggle(('node', 2))
    self.click(bar.memberButton)
    self.assertEqual(window.frame.members[-1][:2], (0, 2))
    window.close()

  def run_loads(self) -> None:
    """Loads go on the member selected, or the one of the load selected,
    and the panel's numbers set them."""
    window = self.openWindow()
    bar, view, panel = window.toolBar, window.frameView, window.panel
    view.select(('member', 1))
    self.click(bar.pointButton)
    load = window.frame.loads[-1]
    self.assertEqual(load, PointLoad(1, 3.0, 10.0, 0.0))
    self.assertEqual(panel.kind, 'point')
    panel.downField.value = 25.0
    panel.downField.valueEdited.emit(25.0)
    self.assertEqual(window.frame.loads[-1].down, 25.0)
    self.click(bar.lineButton)
    self.assertIsInstance(window.frame.loads[-1], LineLoad)
    self.assertEqual(window.frame.loads[-1].member, 1)
    self.click(panel.rightButton)
    self.assertEqual(window.frame.loads[-1].direction, 'right')
    window.close()

  def run_hinges_and_supports(self) -> None:
    """Hinging the beam at both ends makes the portal determinate; a
    roller for its fixed foot leaves it not held."""
    window = self.openWindow()
    view, panel = window.frameView, window.panel
    view.select(('member', 1))
    self.click(panel.startButton)
    self.click(panel.endButton)
    self.assertEqual(window.status.text, 'Determinate')
    view.select(('support', 0))
    self.click(panel.rollerButton)
    self.assertEqual(window.status.text, 'Not held')
    window.close()

  def run_diagram_buttons(self) -> None:
    """A diagram's button shows it, lit, the others not."""
    window = self.openWindow()
    bar = window.toolBar
    self.click(bar.shearButton)
    self.assertEqual(window.frameView.kind, 'V')
    self.assertTrue(bar.shearButton.checked)
    self.assertFalse(bar.bendingButton.checked)
    self.click(bar.shapeButton)
    self.assertEqual(window.frameView.kind, 'shape')
    window.close()
