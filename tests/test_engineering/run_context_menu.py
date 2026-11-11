"""
RunContextMenu covers the menus a right click opens on a 'DiskWidget':
it selects what it is on, and offers what can be done with that, the
current choice checked: a support is a roller or a pin, or removed; a
load is reversed, spread over its edge or removed; on a free edge a
support or a load is added just there; elsewhere a support or a load is
added, and the last edit undone or redone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QAction, QContextMenuEvent
from PySide6.QtWidgets import QApplication, QMenu

from worQt.engineering import Disk, Load
from worQt.engineering.gui import DiskWidget, GripNum

from . import EngineeringWidgetTest, deepBeam


class RunContextMenu(EngineeringWidgetTest):
  """Tests for the context menus of a 'DiskWidget'."""

  def _liveWidget(self, disk: Disk = None) -> DiskWidget:
    widget = DiskWidget()
    widget.disk = deepBeam() if disk is None else disk
    widget.resize(800, 500)
    self.showLive(widget)
    widget.repaint()
    return widget

  def _texts(self, menu: QMenu) -> list[str]:
    return [a.text() for a in menu.actions() if not a.isSeparator()]

  def _action(self, menu: QMenu, text: str) -> QAction:
    for action in menu.actions():
      if action.text() == text:
        return action
    raise KeyError(text)

  def _choose(self, widget: DiskWidget, point: QPointF, text: str) -> None:
    """Right click at 'point' and choose 'text'."""
    self._action(widget.contextMenuAt(point), text).trigger()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SUPPORTS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_on_a_support(self) -> None:
    """On a support the menu selects it and offers a roller, a pin, the
    one it is checked, or to remove it."""
    widget = self._liveWidget()
    menu = widget.contextMenuAt(widget.plateRect(0).center())
    self.assertEqual(self._texts(menu), ['Roller', 'Pin', 'Remove support'])
    self.assertTrue(self._action(menu, 'Roller').isChecked())
    self.assertFalse(self._action(menu, 'Pin').isChecked())
    self.assertIs(widget.selection.kind, GripNum.SUPPORT)
    self.assertEqual(widget.selection.index, 0)

  def run_a_support_from_the_menu(self) -> None:
    """'Pin' makes the support a pin, 'Remove support' removes it."""
    widget = self._liveWidget()
    self._choose(widget, widget.plateRect(0).center(), 'Pin')
    self.assertEqual(str(widget.disk.supports[0]),
                     'support bottom 0 0.3 x y')
    self._choose(widget, widget.plateRect(0).center(), 'Remove support')
    self.assertEqual(len(widget.disk.supports), 1)
    self.assertIs(widget.selection.kind, GripNum.DISK)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LOADS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_on_a_load(self) -> None:
    """On a load the menu selects it and offers to reverse it, to spread
    it over its edge, unless it is already, or to remove it."""
    widget = self._liveWidget()
    menu = widget.contextMenuAt(widget.loadRect(0).center())
    self.assertEqual(self._texts(menu),
                     ['Reverse', 'Spread over the edge', 'Remove load'])
    self.assertFalse(self._action(menu, 'Spread over the edge').isEnabled())
    self.assertIs(widget.selection.kind, GripNum.LOAD)

  def run_a_load_from_the_menu(self) -> None:
    """'Reverse' turns the force round; 'Spread over the edge' spreads
    it along the whole edge, the same force; 'Remove load' removes it."""
    disk = Disk(6, 2.7, 0.3)
    disk.addLoad(Load('load top 2.85 3.15 F 0 -500'))
    widget = self._liveWidget(disk)
    self._choose(widget, widget.loadRect(0).center(), 'Reverse')
    self.assertEqual(str(widget.disk.loads[0]), 'load top 2.85 3.15 F 0 500')
    self._choose(widget, widget.loadRect(0).center(), 'Spread over the edge')
    self.assertEqual(str(widget.disk.loads[0]), 'load top 0 6 F 0 500')
    self._choose(widget, widget.loadRect(0).center(), 'Remove load')
    self.assertEqual(widget.disk.loads, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  EDGES AND THE DISK   # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_on_a_free_edge(self) -> None:
    """On a free edge the menu adds a support or a load just there, the
    load pressing on the edge, and selects it."""
    widget = self._liveWidget(Disk(6, 2.7, 0.3))
    point = widget.toScreen(3.0, 0.0)
    menu = widget.contextMenuAt(point)
    self.assertEqual(self._texts(menu),
                     ['Add support here', 'Add load here'])
    self._choose(widget, point, 'Add support here')
    self.assertEqual(str(widget.disk.supports[0]),
                     'support bottom 2.85 3.15 y')
    self.assertIs(widget.selection.kind, GripNum.SUPPORT)
    self._choose(widget, widget.toScreen(1.0, 2.7), 'Add load here')
    self.assertEqual(str(widget.disk.loads[0]),
                     'load top 0.85 1.15 F 0 -100')
    self.assertIs(widget.selection.kind, GripNum.LOAD)
    self._choose(widget, widget.toScreen(0.0, 1.35), 'Add load here')
    self.assertEqual(str(widget.disk.loads[1]), 'load left 1.2 1.5 F 100 0')

  def run_no_support_over_another(self) -> None:
    """Where a support would overlap one, adding one there is greyed
    out."""
    widget = self._liveWidget()
    menu = widget.contextMenuAt(widget.toScreen(0.35, 0.0))
    self.assertFalse(self._action(menu, 'Add support here').isEnabled())

  def run_on_the_disk(self) -> None:
    """On the disk, or beside it, the menu selects the disk and offers to
    add a support, a load or reinforcement, and to undo or redo, each
    greyed out with nothing to do."""
    widget = self._liveWidget()
    menu = widget.contextMenuAt(widget.diskRect().center())
    expected = ['Add support', 'Add load', 'Add reinforcement', 'Undo',
                'Redo']
    self.assertEqual(self._texts(menu), expected)
    self.assertFalse(self._action(menu, 'Undo').isEnabled())
    self._choose(widget, QPointF(4.0, 4.0), 'Add support')
    self.assertEqual(len(widget.disk.supports), 3)
    menu = widget.contextMenuAt(widget.diskRect().center())
    self.assertTrue(self._action(menu, 'Undo').isEnabled())
    self._action(menu, 'Undo').trigger()
    self.assertEqual(len(widget.disk.supports), 2)

  def run_a_right_click_shows_the_menu(self) -> None:
    """A right click shows the menu without waiting for it."""
    widget = self._liveWidget()
    point = widget.plateRect(0).center().toPoint()
    event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point,
                              widget.mapToGlobal(point))
    QApplication.sendEvent(widget, event)
    menu = widget.contextMenu
    self.assertTrue(menu.isVisible())
    self.assertIn('Remove support', self._texts(menu))
    menu.close()
