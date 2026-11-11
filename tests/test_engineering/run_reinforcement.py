"""
RunReinforcement covers reinforcement and the strut-and-tie model on a
'DiskWidget' and in the 'DiskInspector': bars are added along the
bottom, selected, dragged, edited and removed like anything else; the
drawing says at all times how many times the loads the tied arch
carries, and what gives out first.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF

from worQt.engineering import Disk, Rebar
from worQt.engineering.gui import DiskWidget, DiskInspector, GripNum

from . import EngineeringWidgetTest, deepBeam

_NO_MOD = Qt.KeyboardModifier.NoModifier
_TIE = 'rebar 0.05 0.06 5.95 0.06 4 20'


class RunReinforcement(EngineeringWidgetTest):
  """Tests for reinforcement and the strut-and-tie model on screen."""

  def _liveWidget(self, disk: Disk = None) -> DiskWidget:
    widget = DiskWidget()
    widget.disk = deepBeam() if disk is None else disk
    widget.resize(800, 500)
    self.showLive(widget)
    widget.repaint()
    return widget

  def _tied(self, ) -> Disk:
    disk = deepBeam()
    disk.addRebar(Rebar(_TIE))
    return disk

  def run_adding_reinforcement(self) -> None:
    """Reinforcement is added as a tie along the bottom, 4 Ø20 at 60 mm,
    and selected."""
    widget = self._liveWidget()
    widget.addRebar()
    self.assertEqual(str(widget.disk.rebars[0]), _TIE)
    self.assertIs(widget.selection.kind, GripNum.REBAR)

  def run_selecting_and_dragging_bars(self) -> None:
    """A click on bars selects them; dragging them moves them, to the
    centimetre, inside the disk."""
    widget = self._liveWidget(self._tied())
    start = widget.rebarRect(0).center()
    self.click(widget, start)
    self.assertIs(widget.selection.kind, GripNum.REBAR)
    end = start - QPointF(0.0, widget.diskScale() * 0.1)
    self.press(widget, start)
    self.move(widget, (start + end) * 0.5)
    self.move(widget, end)
    self.release(widget, end)
    self.assertEqual(str(widget.disk.rebars[0]),
                     'rebar 0.05 0.16 5.95 0.16 4 20')

  def run_removing_bars(self) -> None:
    """Delete, or the menu, removes the selected bars."""
    widget = self._liveWidget(self._tied())
    menu = widget.contextMenuAt(widget.rebarRect(0).center())
    texts = [a.text() for a in menu.actions() if not a.isSeparator()]
    self.assertEqual(texts, ['Remove reinforcement'])
    self.key(widget, Qt.Key.Key_Delete)
    self.assertEqual(widget.disk.rebars, ())

  def run_the_verdict(self) -> None:
    """The drawing says what the tied arch carries: nothing without a
    tie, then how many times the loads, and what gives out first."""
    widget = self._liveWidget()
    self.assertIn('add reinforcement', widget.verdict())
    widget.addRebar()
    self.assertAlmostEqual(widget.strutTie.factor, 2.35, delta=0.01)
    self.assertIn('2.35', widget.verdict())
    self.assertIn('strut at the', widget.verdict())
    self.assertFalse(widget.grab().isNull())

  def run_bars_in_the_panel(self) -> None:
    """The panel shows the selected bars as their count, diameter and
    ends, and their area and force; a count typed changes them."""
    inspector = DiskInspector()
    inspector.resize(280, 520)
    self.showLive(inspector)
    widget = self._liveWidget(self._tied())
    self.click(widget, widget.rebarRect(0).center())
    inspector.inspect(widget.disk, widget.selection)
    self.assertEqual(inspector.title, 'Reinforcement')
    self.assertEqual(inspector.rowNames,
                     ('Bars', 'Ø', 'Start x', 'Start y', 'End x', 'End y'))
    values = [field.value for field in inspector.fields]
    self.assertEqual(values, [4.0, 20.0, 0.05, 0.06, 5.95, 0.06])
    self.assertEqual(inspector.note, 'As = 1257 mm², As fy = 1005 kN')
    spy = self.spy(inspector.edited)
    self.click(inspector.fields[0])
    self.typeText(inspector.fields[0], '6')
    self.key(inspector.fields[0], Qt.Key.Key_Return, _NO_MOD, '\r')
    self.assertEqual(spy.args[0].rebars[0].count, 6)
