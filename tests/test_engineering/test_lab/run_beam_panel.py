"""
RunBeamPanel covers 'BeamPanel', the beam as numbers to type over: it
shows the standard beam and its section; a number typed edits the beam;
one it cannot take is given up, the note saying why; and the numbers
lock while a test is on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worQt.engineering.lab.gui import BeamPanel

from . import LabWidgetTest


class RunBeamPanel(LabWidgetTest):
  """Tests for 'BeamPanel'."""

  def openPanel(self) -> BeamPanel:
    """The panel, shown live."""
    panel = BeamPanel()
    panel.resize(270, 720)
    self.showLive(panel)
    return panel

  def enter(self, panel: BeamPanel, field: str, text: str) -> None:
    """Types 'text' into the field named 'field' and takes it."""
    widget = getattr(panel, field)
    self.click(widget)
    self.typeText(widget, text)
    self.key(widget, Qt.Key.Key_Return)

  def run_shows_the_standard_beam(self) -> None:
    """It shows the standard beam, and says what its section is."""
    panel = self.openPanel()
    self.assertEqual(panel.lengthField.value, 3300.0)
    self.assertEqual(panel.bottomCountField.value, 3.0)
    self.assertEqual(panel.bottomDiameterField.value, 16.0)
    self.assertEqual(panel.topCountField.value, 2.0)
    self.assertEqual(panel.note, '')
    words = panel.sectionWords()
    self.assertEqual(words[1], 'bottom 3 Ø16, cover 30')
    self.assertIn('ρ 1.15 %', words[3])

  def run_a_number_typed(self) -> None:
    """A number typed edits the beam, emitting 'edited'."""
    panel = self.openPanel()
    spy = self.spy(panel.edited)
    self.enter(panel, 'heightField', '350')
    self.assertEqual(spy.count, 1)
    self.assertEqual(spy.emissions[0][0].height, 350.0)
    self.assertEqual(panel.beam.height, 350.0)

  def run_a_number_given_up(self) -> None:
    """Bars that do not fit are given up, the note saying why."""
    panel = self.openPanel()
    spy = self.spy(panel.edited)
    self.enter(panel, 'bottomCountField', '9')
    self.assertEqual(spy.count, 0)
    self.assertEqual(panel.bottomCountField.value, 3.0)
    self.assertIn('Ø16', panel.note)

  def run_locked(self) -> None:
    """While a test is on, the numbers are locked, the note saying so;
    freed, they are not."""
    panel = self.openPanel()
    panel.setLocked(True)
    self.assertFalse(panel.lengthField.isEnabled())
    self.assertIn('tested as it is', panel.note)
    panel.setLocked(False)
    self.assertTrue(panel.lengthField.isEnabled())
    self.assertEqual(panel.note, '')
