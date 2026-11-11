"""
RunControlPanel covers 'ControlPanel', the rig's control loop and the
part selected as numbers to type over: it shows the control; driving
another actuator has the one driven before follow it; a part selected
shows where it is, a support its kind and an actuator not driven what
it follows and its share; what the rig cannot take is given up, the
note saying why; and it locks while a test is on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worQt.engineering.lab import Rig
from worQt.engineering.lab.gui import ControlPanel

from . import LabWidgetTest, standardBeam


class RunControlPanel(LabWidgetTest):
  """Tests for 'ControlPanel'."""

  def openPanel(self, part: tuple[str, int] = None) -> ControlPanel:
    """The panel of the standard rig, 'part' of it selected, shown
    live."""
    panel = ControlPanel()
    panel.resize(270, 700)
    beam = standardBeam()
    panel.showRig(beam, Rig.standard(beam), part)
    self.showLive(panel)
    return panel

  def enter(self, panel: ControlPanel, field: str, text: str) -> None:
    """Types 'text' into the field named 'field' and takes it."""
    widget = getattr(panel, field)
    self.click(widget)
    self.typeText(widget, text)
    self.key(widget, Qt.Key.Key_Return)

  def run_shows_the_control(self) -> None:
    """It shows the control, the transducer and the actuator by their
    numbers, and nothing selected."""
    panel = self.openPanel()
    self.assertEqual(panel.transducerField.value, 3.0)
    self.assertEqual(panel.actuatorField.value, 1.0)
    self.assertEqual(panel.rateField.value, -0.1)
    self.assertEqual(panel.limitField.value, -150.0)
    self.assertEqual(panel.stepField.value, 0.001)
    self.assertEqual(panel.kpField.value, 0.5)
    self.assertEqual(panel.partTitle(), 'Nothing selected')
    self.assertFalse(panel.atField.isVisibleTo(panel))

  def run_limit_turns_the_rate(self) -> None:
    """A limit typed on the other side of nought turns the rate's sign to
    head for it; a rate typed heading away from the limit is given up,
    the note saying why."""
    panel = self.openPanel()
    self.enter(panel, 'limitField', '20')
    self.assertEqual(panel.rig.control.limit, 20.0)
    self.assertEqual(panel.rig.control.rate, 0.1)
    self.enter(panel, 'rateField', '-0.2')
    self.assertEqual(panel.rig.control.rate, 0.1)
    self.assertIn('never reaches', panel.note)

  def run_gains_typed(self) -> None:
    """A gain typed sets the control, emitting 'rigEdited'."""
    panel = self.openPanel()
    spy = self.spy(panel.rigEdited)
    self.enter(panel, 'kiField', '0.2')
    self.assertEqual(spy.count, 1)
    self.assertEqual(panel.rig.control.ki, 0.2)

  def run_drive_another(self) -> None:
    """Driving another actuator has the one driven before follow it."""
    panel = self.openPanel()
    self.enter(panel, 'actuatorField', '2')
    self.assertEqual(panel.rig.driven, 1)
    self.assertEqual(panel.rig.actuators[0].follows, 1)

  def run_read_none_there(self) -> None:
    """A transducer there is not is given up, the note saying why."""
    panel = self.openPanel()
    self.enter(panel, 'transducerField', '7')
    self.assertEqual(panel.rig.control.transducer, 2)
    self.assertIn('T7', panel.note)

  def run_a_support(self) -> None:
    """A support selected shows where it is and its kind, by its
    buttons; another kind makes it so."""
    panel = self.openPanel(('support', 1))
    self.assertEqual(panel.partTitle(), 'Support 2')
    self.assertEqual(panel.atField.value, 3150.0)
    self.assertTrue(panel.rollerButton.checked)
    self.assertFalse(panel.pinButton.checked)
    self.click(panel.fixedButton)
    self.assertEqual(panel.rig.supports[1].kind, 'fixed')
    self.assertTrue(panel.fixedButton.checked)

  def run_a_follower(self) -> None:
    """An actuator not driven shows what it follows and its share; a
    share typed sets it."""
    panel = self.openPanel(('actuator', 1))
    self.assertEqual(panel.partTitle(), 'Actuator A2')
    self.assertEqual(panel.followsField.value, 1.0)
    self.assertEqual(panel.shareField.value, 1.0)
    self.enter(panel, 'shareField', '0.5')
    self.assertEqual(panel.rig.shares, (1.0, 0.5))

  def run_the_driven(self) -> None:
    """The actuator driven shows only where it is, and says the control
    drives it."""
    panel = self.openPanel(('actuator', 0))
    self.assertFalse(panel.followsField.isVisibleTo(panel))
    self.assertIn('control drives it', panel.partWords())

  def run_moved_off(self) -> None:
    """A part typed off the beam is given up."""
    panel = self.openPanel(('transducer', 0))
    self.enter(panel, 'atField', '9000')
    self.assertEqual(panel.rig.transducers[0], 1150.0)
    self.assertIn('off the beam', panel.note)

  def run_a_gap(self) -> None:
    """A gap in the stirrups selected shows from and to where it is; a
    number typed moves its end, emitting 'beamEdited'; one off the beam
    is given up."""
    panel = ControlPanel()
    panel.resize(270, 700)
    beam = standardBeam()
    gapped = beam.withStirrups(beam.stirrups.withGap(200.0, 1000.0))
    panel.showRig(gapped, Rig.standard(gapped), ('gap', 0))
    self.showLive(panel)
    self.assertEqual(panel.partTitle(), 'Gap 1 in the stirrups')
    self.assertEqual(panel.gapFromField.value, 200.0)
    self.assertFalse(panel.atField.isVisibleTo(panel))
    edits = self.spy(panel.beamEdited)
    self.enter(panel, 'gapToField', '900')
    self.assertEqual(edits.count, 1)
    self.assertEqual(edits.emissions[0][0].stirrups.gaps,
                     ((200.0, 900.0),))
    self.enter(panel, 'gapToField', '9000')
    self.assertEqual(edits.count, 1)
    self.assertIn('gap', panel.note)

  def run_stages(self) -> None:
    """In setup everything may be changed; under test only the ramp, the
    gains and the top speed, each number emitting 'controlTuned'; once
    tested, nothing; the note says which."""
    panel = self.openPanel(('support', 0))
    panel.setStage('testing')
    self.assertTrue(panel.kpField.isEnabled())
    self.assertTrue(panel.limitField.isEnabled())
    self.assertFalse(panel.transducerField.isEnabled())
    self.assertFalse(panel.atField.isEnabled())
    self.assertFalse(panel.pinButton.isEnabled())
    self.assertIn('Under test', panel.note)
    tuned = self.spy(panel.controlTuned)
    edited = self.spy(panel.rigEdited)
    self.enter(panel, 'kpField', '0.9')
    self.assertEqual(tuned.count, 1)
    self.assertEqual(tuned.emissions[0][0].kp, 0.9)
    self.assertEqual(edited.count, 0)
    panel.setStage('tested')
    self.assertFalse(panel.kpField.isEnabled())
    self.assertIn('New beam', panel.note)
    panel.setStage('setup')
    self.assertTrue(panel.atField.isEnabled())
    self.assertEqual(panel.note, '')
