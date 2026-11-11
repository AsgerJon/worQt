"""
RunLabWindow covers 'LabApp' and its 'LabWindow', the lab: it opens on
the standard beam, set up and ready; 'Start test' runs the control
loop, the window stepping it, and the test stops by itself at its end,
saying why; 'Pause' and 'Resume' stop and go on; 'New beam' casts it
afresh; supports, actuators and transducers are added and removed
before a test; the panels' numbers shape the beam and the rig; and the
setup is saved to a '.beam' file and opened again.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile

from worQt.engineering.lab import BeamExperiment, BeamSetup, RCBeam, Rig
from worQt.engineering.lab.gui import LabApp, LabWindow

from . import LabWidgetTest, smallBeam, smallRig


class RunLabWindow(LabWidgetTest):
  """Tests for 'LabApp' and 'LabWindow'."""

  __application_type__ = LabApp
  __time_out__ = 1200.0

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)

  def openWindow(self) -> LabWindow:
    """The window, shown live."""
    window = LabWindow()
    self.showLive(window)
    return window

  def openSmall(self) -> LabWindow:
    """The window, shown live, the small beam on its rig set up in it,
    quick to test."""
    window = self.openWindow()
    window.setBeam(smallBeam())
    window.setRig(smallRig())
    return window

  def run_opens_ready(self) -> None:
    """It opens on the standard beam, ready to test, nothing to pause or
    remove."""
    window = self.openWindow()
    bar = window.toolBar
    self.assertEqual(window.windowTitle(), 'Beam lab')
    self.assertIsNone(window.experiment)
    self.assertTrue(bar.startButton.isEnabled())
    self.assertFalse(bar.pauseButton.isEnabled())
    self.assertTrue(bar.supportButton.isEnabled())
    self.assertFalse(bar.removeButton.isEnabled())
    self.assertEqual(window.status.mode, 'idle')
    self.assertEqual(window.status.text, 'Beam 1 ready')
    self.assertIn('T3 drives A1', window.status.details)
    self.assertEqual(window.controlPanel.rig, window.beamView.rig)
    window.close()

  def run_a_test_to_its_end(self) -> None:
    """'Start test' runs the control loop; run to its end, it stops,
    saying why, nothing left to pause and nothing to change."""
    window = self.openSmall()
    bar = window.toolBar
    self.click(bar.startButton)
    experiment = window.experiment
    self.assertIsInstance(experiment, BeamExperiment)
    self.assertTrue(window.running)
    for view in (window.beamView, window.curveView, window.controlView):
      self.assertIs(view.experiment, experiment)
    self.assertFalse(bar.startButton.isEnabled())
    self.assertTrue(bar.startButton.checked)
    self.assertFalse(window.beamPanel.lengthField.isEnabled())
    self.assertTrue(window.controlPanel.kpField.isEnabled())
    self.assertFalse(window.controlPanel.transducerField.isEnabled())
    while not experiment.finished:
      window.settle()
    self.assertFalse(window.running)
    self.assertFalse(bar.pauseButton.isEnabled())
    self.assertFalse(bar.actuatorButton.isEnabled())
    self.assertFalse(window.controlPanel.kpField.isEnabled())
    self.assertEqual(window.status.mode, 'finished')
    self.assertIn(experiment.ending, window.status.details)
    self.assertIn('Peak', window.curveView.peakText())
    self.assertIn('error', window.controlView.errorText())
    window.close()

  def run_retuned_under_test(self) -> None:
    """Under test, a gain typed retunes the control as it runs, and a
    limit of nought turns the ramp back, unloading the beam."""
    window = self.openSmall()
    panel = window.controlPanel
    self.click(window.toolBar.startButton)
    while window.experiment.latest.step < 10:
      window.settle()
    panel.kpField.value = 0.8
    panel.kpField.valueEdited.emit(0.8)
    self.assertEqual(window.experiment.rig.control.kp, 0.8)
    self.assertEqual(window.beamView.rig.control.kp, 0.8)
    panel.limitField.value = 0.0
    panel.limitField.valueEdited.emit(0.0)
    control = window.experiment.rig.control
    self.assertEqual((control.rate, control.limit), (0.1, 0.0))
    window.close()

  def run_pause_and_resume(self) -> None:
    """'Pause' stops the test and becomes 'Resume', which goes on."""
    window = self.openSmall()
    bar = window.toolBar
    self.click(bar.startButton)
    window.settle()
    self.click(bar.pauseButton)
    self.assertFalse(window.running)
    self.assertEqual(bar.pauseButton.text, 'Resume')
    self.assertEqual(window.status.mode, 'paused')
    step = window.experiment.latest.step
    self.click(bar.pauseButton)
    self.assertTrue(window.running)
    self.assertEqual(bar.pauseButton.text, 'Pause')
    window.settle()
    self.assertGreater(window.experiment.latest.step, step)
    window.close()

  def run_a_new_beam(self) -> None:
    """'New beam' casts the beam afresh, untested, to change it."""
    window = self.openSmall()
    self.click(window.toolBar.startButton)
    window.settle()
    self.click(window.toolBar.newButton)
    self.assertIsNone(window.experiment)
    self.assertFalse(window.running)
    self.assertEqual(window.cast, 2)
    self.assertIsNone(window.beamView.experiment)
    self.assertTrue(window.beamPanel.lengthField.isEnabled())
    self.assertEqual(window.status.text, 'Beam 2 ready')
    window.close()

  def run_add_and_remove(self) -> None:
    """'Add support', 'Add actuator' and 'Add transducer' put one in the
    widest gap, selected and shown in the panel; 'Remove' takes the one
    selected away."""
    window = self.openWindow()
    bar, view = window.toolBar, window.beamView
    self.click(bar.supportButton)
    self.assertEqual(len(view.rig.supports), 3)
    self.assertEqual(view.selected, ('support', 2))
    self.assertEqual(window.controlPanel.partTitle(), 'Support 3')
    self.click(bar.actuatorButton)
    self.assertEqual(len(view.rig.actuators), 3)
    self.assertEqual(view.rig.actuators[2].follows, 0)
    self.click(bar.transducerButton)
    self.assertEqual(len(view.rig.transducers), 4)
    self.assertTrue(bar.removeButton.isEnabled())
    self.click(bar.removeButton)
    self.assertEqual(len(view.rig.transducers), 3)
    self.assertIsNone(view.selected)
    self.assertEqual(window.controlPanel.rig, view.rig)
    window.close()

  def run_stirrup_gaps(self) -> None:
    """'Add stirrup gap' leaves the widest stretch between the supports
    and the actuators without stirrups, but 50 mm at either end,
    selected; 'Remove' fills it again."""
    window = self.openWindow()
    bar, view = window.toolBar, window.beamView
    self.click(bar.gapButton)
    self.assertEqual(view.beam.stirrups.gaps, ((2200.0, 3100.0),))
    self.assertEqual(view.selected, ('gap', 0))
    self.assertIn('Gap 1', window.controlPanel.partTitle())
    self.assertEqual(window.beamPanel.beam.stirrups, view.beam.stirrups)
    self.click(bar.removeButton)
    self.assertEqual(view.beam.stirrups.gaps, ())
    window.close()

  def run_the_panels_shape_the_rig(self) -> None:
    """A beam typed longer takes its rig along; a gain typed in the
    control panel sets the rig tested."""
    window = self.openWindow()
    window.beamPanel.lengthField.value = 6600.0
    window.beamPanel.lengthField.valueEdited.emit(6600.0)
    self.assertEqual(window.beamView.beam.length, 6600.0)
    self.assertEqual(window.beamView.rig.supports[1].at, 6300.0)
    window.controlPanel.kpField.value = 0.8
    window.controlPanel.kpField.valueEdited.emit(0.8)
    self.assertEqual(window.beamView.rig.control.kp, 0.8)
    self.click(window.toolBar.startButton)
    self.assertEqual(window.experiment.rig.control.kp, 0.8)
    self.assertEqual(window.experiment.beam.length, 6600.0)
    window.close()

  def run_save_and_open(self) -> None:
    """'Save…' writes the setup to a '.beam' file and 'Open…' sets it up
    again; a file holding no setup is refused, the status saying why,
    the setup as it was."""
    window = self.openSmall()
    bar = window.toolBar
    self.assertTrue(bar.openButton.isEnabled())
    self.assertTrue(bar.saveButton.isEnabled())
    expected = str(BeamSetup(smallBeam(), smallRig()))
    with tempfile.TemporaryDirectory() as folder:
      path = os.path.join(folder, 'small.beam')
      window.saveTo(path)
      with open(path, 'r', -1, 'utf-8') as file:
        self.assertEqual(file.read(), '%s\n' % expected)
      self.assertIn('saved to', window.status.details)
      window.setBeam(RCBeam())
      window.setRig(Rig.standard(RCBeam()))
      window.openFrom(path)
      self.assertEqual(str(window.setup), expected)
      self.assertEqual(window.beamPanel.beam.values(),
                       smallBeam().values())
      self.assertEqual(window.controlPanel.rig, window.beamView.rig)
      self.assertIn('opened', window.status.details)
      wrong = os.path.join(folder, 'wrong.beam')
      with open(wrong, 'w', -1, 'utf-8') as file:
        file.write('beam of light')
      window.openFrom(wrong)
      self.assertIn('could not open', window.status.details)
      self.assertIn('line 1', window.status.details)
      self.assertEqual(str(window.setup), expected)
    window.close()

  def run_saved_as_the_test_began(self) -> None:
    """Under test, the setup is as the test began, retuning not counted,
    and 'New beam' undoes the retuning; a setup opened ends the test, as
    'New beam' does."""
    window = self.openSmall()
    expected = str(BeamSetup(smallBeam(), smallRig()))
    self.click(window.toolBar.startButton)
    window.settle()
    panel = window.controlPanel
    panel.kpField.value = 0.8
    panel.kpField.valueEdited.emit(0.8)
    self.assertEqual(window.experiment.rig.control.kp, 0.8)
    self.assertEqual(str(window.setup), expected)
    self.click(window.toolBar.newButton)
    self.assertEqual(window.beamView.rig.control.kp, 0.5)
    self.assertEqual(window.controlPanel.rig, window.beamView.rig)
    self.click(window.toolBar.startButton)
    window.settle()
    with tempfile.TemporaryDirectory() as folder:
      path = os.path.join(folder, 'small.beam')
      window.saveTo(path)
      window.openFrom(path)
    self.assertIsNone(window.experiment)
    self.assertEqual(window.cast, 3)
    self.assertEqual(str(window.setup), expected)
    window.close()
