"""
TestBeamExperiment covers 'BeamExperiment', a test of a beam on its rig
reckoned by OpenSees on the beam as a solid of bricks, its bars and
stirrups through it, the control moving one actuator and the others
following its force, every reading up positive as the transducers under
the beam read. The small beam without stirrups fails in shear, a
diagonal crack opening in a shear span before its bars yield; with
its stirrups it bends until its bars yield; with a gap in its stirrups
over a shear span, it fails in shear there. The reading keeps to the
command; the actuators push their shares of the force; a command held
at its limit ends the test; retuned under test, a ramp turned back
unloads the beam; the concrete's scatter repeats by its seed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.lab import Actuator, BarLayer, BeamExperiment
from worQt.engineering.lab import RCBeam, Rig, Stirrups

from . import LabTest, smallBeam, smallRig

_NONE = Stirrups(0.0, 100.0, ())


class TestBeamExperiment(LabTest):
  """Tests for 'BeamExperiment'."""

  __time_out__ = 1200.0

  bare: BeamExperiment
  linked: BeamExperiment

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.bare = BeamExperiment(smallBeam(_NONE), smallRig(), 1, cls.worker)
    cls.bare.run()
    cls.linked = BeamExperiment(smallBeam(), smallRig(), 1, cls.worker)
    cls.linked.run()

  def experimentOn(self, beam: RCBeam, rig: Rig,
                   cycles: int = None) -> BeamExperiment:
    """'beam' tested on 'rig', 'cycles' cycles or to its end."""
    experiment = BeamExperiment(beam, rig, 1, self.worker)
    if cycles is None:
      experiment.run()
    else:
      experiment.advance(cycles)
    return experiment

  def test_shear_without_stirrups(self) -> None:
    """Without stirrups, a diagonal crack opens in a shear span and the
    beam fails in shear, its bars not yielding."""
    experiment = self.bare
    self.assertTrue(experiment.finished)
    self.assertIn('failed in shear', experiment.ending)
    self.assertIsNone(experiment.happened('bars yield'))
    _, where, _, _ = experiment.widest(experiment.latest)
    self.assertTrue(100.0 < where < 600.0 or 1000.0 < where < 1500.0)

  def test_bending_with_stirrups(self) -> None:
    """With its stirrups, the beam carries more, its bars yielding, and
    does not fail in shear."""
    linked, bare = self.linked, self.bare
    self.assertNotIn('shear', linked.ending)
    self.assertIsNotNone(linked.happened('bars yield'))
    self.assertGreater(abs(linked.peak.force), abs(bare.peak.force))

  def test_gap_over_a_shear_span(self) -> None:
    """Stirrups left out over a shear span fail the beam in shear
    there."""
    gapped = smallBeam(Stirrups(6.0, 100.0, ((150.0, 550.0),)))
    experiment = self.experimentOn(gapped, smallRig())
    self.assertIn('failed in shear', experiment.ending)
    self.assertIn('no stirrups there', experiment.ending)
    _, where, _, _ = experiment.widest(experiment.latest)
    self.assertTrue(100.0 < where < 600.0)

  def test_reading_keeps_to_the_command(self) -> None:
    """The control ramps the transducer at midspan down 0.1 mm a second,
    the transducer under the beam reading less than nought: the feedback
    keeps to the command, the actuator moving at most its top speed a
    cycle."""
    experiment = self.linked
    readings = experiment.readings
    for reading in readings[5:30]:
      self.assertAlmostEqual(reading.command, -0.1 * reading.time)
      self.assertLess(reading.feedback, 0.0)
      self.assertLess(reading.force, 0.0)
      self.assertLess(abs(reading.command - reading.feedback), 0.15)
      self.assertEqual(reading.feedback, reading.transducers[2])
    most = experiment.rig.control.speed * experiment.cycle + 1e-9
    for before, after in zip(readings, readings[1:]):
      self.assertLessEqual(abs(after.stroke - before.stroke), most)

  def test_shares_of_force(self) -> None:
    """The actuators push their shares of the force of the one driven;
    the force is their total."""
    for reading in self.linked.readings[::10]:
      first, second = reading.forces
      self.assertAlmostEqual(first, second)
      self.assertAlmostEqual(reading.force, first + second)
    rig = smallRig()
    half = rig.withActuators(rig.actuators[0], Actuator(1000.0, 0, 0.5))
    experiment = self.experimentOn(smallBeam(), half, 8)
    for reading in experiment.readings[2:]:
      first, second = reading.forces
      self.assertAlmostEqual(second, 0.5 * first)

  def test_cracks_and_stirrups_read(self) -> None:
    """The cells of the face crack as the beam bends; the bars and the
    stirrups are read stretch by stretch and stirrup by stirrup."""
    experiment = self.linked
    peak = experiment.peak
    mesh = experiment.mesh
    self.assertEqual(len(peak.cells),
                     (len(mesh.xs) - 1) * (len(mesh.ys) - 1))
    self.assertEqual(len(peak.stirrups), len(mesh.stirrupPlaces))
    self.assertGreater(max(peak.bottomBars), experiment.yieldStrain)
    self.assertIsNotNone(experiment.happened('first crack'))

  def test_held_at_the_limit(self) -> None:
    """A command held at its limit, the reading kept to it, ends the
    test."""
    rig = smallRig()
    lower = rig.control.changed('limit', -1.0).changed('step', 0.05)
    held = self.experimentOn(smallBeam(), rig.withControl(lower))
    self.assertEqual(held.ending, 'the control held its command at its '
                                  'limit')
    self.assertLess(abs(held.latest.feedback + 1.0), 0.011)

  def test_retuned(self) -> None:
    """Under test the control is retuned, and a ramp turned back to
    nought brings the beam back, cracked, the actuator holding it there;
    it reads and drives what it began with."""
    rig = smallRig()
    experiment = self.experimentOn(smallBeam(), rig, 6)
    command = experiment.command
    self.assertAlmostEqual(command, -1.2)
    back = rig.control.changed('rate', 0.1).changed('limit', 0.0)
    experiment.retune(back.changed('step', 0.1))
    first = experiment.advance(1)[0]
    self.assertAlmostEqual(first.command, command + 0.12)
    experiment.run()
    self.assertIn('held its command', experiment.ending)
    self.assertLess(abs(experiment.latest.feedback), 0.011)
    with self.assertRaises(ValueError):
      experiment.retune(rig.control.changed('transducer', 0))

  def test_no_bars(self) -> None:
    """With no bars, it breaks at its first crack."""
    values = [*smallBeam(_NONE).values()]
    values[6] = BarLayer(0, 12.0, 25.0)
    values[7] = BarLayer(0, 8.0, 25.0)
    experiment = self.experimentOn(RCBeam(*values), smallRig())
    self.assertIn('first crack', experiment.ending)

  def test_seeded(self) -> None:
    """The concrete's scatter is drawn from the seed: the same seed, the
    same strengths, another seed, others."""
    beam, rig = smallBeam(), smallRig()
    first = BeamExperiment(beam, rig, 1).mesh.strengths
    again = BeamExperiment(beam, rig, 1).mesh.strengths
    other = BeamExperiment(beam, rig, 2).mesh.strengths
    self.assertEqual(first, again)
    self.assertNotEqual(first, other)

  def test_finished(self) -> None:
    """A finished test runs no further."""
    count = len(self.bare.readings)
    self.assertEqual(self.bare.advance(10), ())
    self.assertEqual(len(self.bare.readings), count)
