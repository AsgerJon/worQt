"""
RunInspector covers 'DiskInspector', the panel showing what is selected
as plain numbers to type over: the disk's dimensions and materials, a
support's stretch and whether it is a roller or a pin, a load's stretch
and force. Every number taken edits the disk, every button does what it
says.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worQt.engineering import EdgeNum
from worQt.engineering.gui import DiskInspector, DiskGrip, GripNum
from worQt.engineering.gui import NumberField

from . import EngineeringWidgetTest, deepBeam

_NO_MOD = Qt.KeyboardModifier.NoModifier
_DISK = DiskGrip(GripNum.DISK, -1, None)
_SUPPORT = DiskGrip(GripNum.SUPPORT, 0, EdgeNum.BOTTOM)
_LOAD = DiskGrip(GripNum.LOAD, 0, EdgeNum.TOP)


class RunInspector(EngineeringWidgetTest):
  """Tests for 'DiskInspector'."""

  def _liveInspector(self, grip: DiskGrip) -> DiskInspector:
    inspector = DiskInspector()
    inspector.resize(280, 480)
    self.showLive(inspector)
    inspector.inspect(deepBeam(), grip)
    return inspector

  def enter(self, field: NumberField, text: str) -> None:
    """Click 'field', type 'text' and press Enter."""
    self.click(field)
    self.typeText(field, text)
    self.key(field, Qt.Key.Key_Return, _NO_MOD, '\r')

  def _values(self, inspector: DiskInspector) -> list[float]:
    return [field.value for field in inspector.fields]

  def run_shows_the_disk(self) -> None:
    """With the disk selected the panel shows its dimensions and its
    materials, and no buttons."""
    inspector = self._liveInspector(_DISK)
    self.assertEqual(inspector.title, 'Disk')
    self.assertEqual(inspector.rowNames,
                     ('Length', 'Height', 'Thickness', 'fc', 'fy', 'E'))
    self.assertEqual(self._values(inspector),
                     [6.0, 2.7, 0.3, 30.0, 800.0, 200000.0])
    self.assertFalse(inspector.removeButton.isVisible())

  def run_editing_the_disk(self) -> None:
    """A dimension typed resizes the disk, a material typed changes it."""
    inspector = self._liveInspector(_DISK)
    spy = self.spy(inspector.edited)
    self.enter(inspector.fields[0], '7')
    disk = spy.args[0]
    self.assertEqual(disk.length, 7.0)
    self.assertAlmostEqual(disk.supports[1].end, 7.0)
    self.enter(inspector.fields[3], '35')
    self.assertEqual(spy.args[0].fc, 35.0)

  def run_limits_keep_the_disk_a_disk(self) -> None:
    """The length may be typed no less than four thicknesses, the
    thickness no more than a quarter of the lesser side."""
    inspector = self._liveInspector(_DISK)
    self.assertAlmostEqual(inspector.fields[0].minimum, 1.2)
    self.assertAlmostEqual(inspector.fields[2].maximum, 0.675)

  def run_shows_a_support(self) -> None:
    """With a support selected the panel shows its edge, its stretch and
    whether it is a roller or a pin, and offers to remove it."""
    inspector = self._liveInspector(_SUPPORT)
    self.assertEqual(inspector.title, 'Support')
    self.assertEqual(inspector.subtitle, 'on the bottom edge')
    self.assertEqual(inspector.rowNames, ('From', 'To'))
    self.assertEqual(self._values(inspector), [0.0, 0.3])
    self.assertTrue(inspector.rollerButton.checked)
    self.assertFalse(inspector.pinButton.checked)
    self.assertTrue(inspector.removeButton.isVisible())
    self.assertAlmostEqual(inspector.fields[1].maximum, 5.7)

  def run_turning_and_removing_a_support(self) -> None:
    """'Pin' makes the support a pin; 'Remove' asks for it to go."""
    inspector = self._liveInspector(_SUPPORT)
    edited = self.spy(inspector.edited)
    removed = self.spy(inspector.removeRequested)
    self.click(inspector.pinButton)
    support = edited.args[0].supports[0]
    self.assertTrue(support.setsX and support.setsY)
    self.click(inspector.removeButton)
    self.assertEqual(removed.count, 1)

  def run_moving_a_support(self) -> None:
    """A stretch typed moves the support."""
    inspector = self._liveInspector(_SUPPORT)
    spy = self.spy(inspector.edited)
    self.enter(inspector.fields[1], '0.5')
    self.assertEqual(str(spy.args[0].supports[0]), 'support bottom 0 0.5 y')

  def run_shows_a_load(self) -> None:
    """With a load selected the panel shows its stretch and its force,
    and the force per metre."""
    inspector = self._liveInspector(_LOAD)
    self.assertEqual(inspector.title, 'Load')
    self.assertEqual(inspector.subtitle, 'on the top edge')
    self.assertEqual(inspector.rowNames, ('From', 'To', 'Fx', 'Fy'))
    self.assertEqual(self._values(inspector), [0.0, 6.0, 0.0, -1200.0])
    self.assertEqual(inspector.note, 'q = 200 kN/m')

  def run_editing_a_load(self) -> None:
    """A force typed changes the load."""
    inspector = self._liveInspector(_LOAD)
    spy = self.spy(inspector.edited)
    self.enter(inspector.fields[3], '-1500')
    self.assertEqual(spy.args[0].loads[0].fy, -1500.0)
