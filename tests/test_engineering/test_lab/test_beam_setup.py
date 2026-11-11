"""
TestBeamSetup covers 'BeamSetup', a beam on its rig as a '.beam' file
holds it: its text, a line a part, reads back as it was written; the
materials, the control's numbers, the stroke and the 'Ø' may be left
out, the lines in any order; a text that is no setup, or a rig that
does not fit its beam, is refused, saying the line and why.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.lab import Actuator, BarLayer, BeamSetup, Control
from worQt.engineering.lab import RCBeam, Rig, Stirrups, Support

from . import LabTest, smallBeam, smallRig

_GAPPED = Stirrups(6.0, 100.0, ((150.0, 550.0),))
_TEXT = """beam 1600 x 200 x 120 fcm 38 fy 550 Es 200000
bottom 2 Ø12 cover 25
top 2 Ø8 cover 25
stirrups Ø6 c/c 100 gap 150 550
support 100 pin
support 1500 roller
actuator 600 driven
actuator 1000 follows A1 share 1
transducer 600
transducer 1000
transducer 800
control T3 A1 rate -0.1 limit -50 step 0.004 kp 0.5 ki 0.05 kd 0 speed 1
stroke 150"""
_LEFT_OUT = """control T1 A1 limit -20
transducer 800

support 100 pin
beam 1600 x 200 x 120
stirrups 0 c/c 100
top 0 8 cover 25
bottom 2 12 cover 25
support 1500 roller
actuator 800 driven"""


class TestBeamSetup(LabTest):
  """Tests for 'BeamSetup'."""

  def test_text(self) -> None:
    """The text is a line a part: the beam, its bars and stirrups, the
    supports, the actuators, the transducers, the control and the
    stroke."""
    setup = BeamSetup(smallBeam(_GAPPED), smallRig())
    self.assertEqual(str(setup), _TEXT)

  def test_read_back(self) -> None:
    """The text reads back as the setup it was written from: the beam,
    and the rig's parts in their order, its chain and its stroke."""
    setup = BeamSetup(_TEXT)
    self.assertEqual(setup.beam.values(), smallBeam(_GAPPED).values())
    rig = smallRig()
    self.assertEqual(setup.rig.supports, rig.supports)
    self.assertEqual(setup.rig.actuators, rig.actuators)
    self.assertEqual(setup.rig.transducers, rig.transducers)
    self.assertEqual(setup.rig.control, rig.control)
    self.assertEqual(setup.rig.stroke, rig.stroke)
    beam = RCBeam()
    standard = Rig.standard(beam).driving(1)
    actuators = (*standard.actuators, Actuator(1650.0, 0, 0.5))
    chained = Rig((Support(150.0, 'fixed'),), actuators,
                  standard.transducers, standard.control, 100.0)
    written = BeamSetup(beam, chained)
    again = BeamSetup(str(written))
    self.assertEqual(str(again), str(written))
    self.assertEqual(again.rig.driven, 1)
    self.assertEqual(again.rig.shares, (1.0, 1.0, 0.5))
    self.assertEqual(again.rig.stroke, 100.0)

  def test_left_out(self) -> None:
    """The materials, the control's numbers, the stroke and the 'Ø' left
    out are the lab's own; the lines come in any order, blank lines
    skipped."""
    setup = BeamSetup(_LEFT_OUT)
    beam, rig = setup.beam, setup.rig
    self.assertEqual((beam.fcm, beam.fy, beam.Es), (38.0, 550.0, 2e5))
    self.assertEqual(beam.bottom, BarLayer(2, 12.0, 25.0))
    self.assertEqual(beam.top.count, 0)
    self.assertEqual(beam.stirrups, Stirrups(0.0, 100.0, ()))
    self.assertEqual(rig.supports, (Support(100.0, 'pin'),
                                    Support(1500.0, 'roller')))
    self.assertEqual(rig.control, Control(0, 0, -0.1, -20.0, 0.001, 0.5,
                                          0.05, 0.0, 1.0))
    self.assertEqual(rig.stroke, 150.0)

  def test_refused(self) -> None:
    """A text that is no setup is refused, saying the line and why; so
    is a rig that does not fit its beam."""
    cases = (
      ('stroke 150', 'stroke 150\nwhatever 3', 'line 14: expected beam'),
      ('stroke 150', 'beam 1600 x 200 x 120',
       "line 13: a setup has one 'beam' line"),
      ('fy 550', 'fy strong', 'line 1: the fy must be a number'),
      ('A1 rate', 'B1 rate', 'line 12: expected A1, A2'),
      ('1500 roller', '1500 hinge', 'line 6: a support is a pin'),
      ('gap 150 550', 'gap 150', "line 4: expected 'stirrups"),
      ('bottom 2 Ø12', 'bottom 2.5 Ø12',
       'line 2: a layer has a whole number'),
      ('600 driven', '600 follows A2 share 1',
       'A1, which the control drives, is the one'),
      ('support 1500 roller', 'support 1700 roller', 'off the beam'),
      ('support 1500 roller\n', '', 'the beam can turn'),
      ('bottom 2 Ø12', 'bottom 9 Ø12', 'need'),
    )
    for old, new, words in cases:
      with self.assertRaises(ValueError) as context:
        BeamSetup(str.replace(_TEXT, old, new))
      self.assertIn(words, str(context.exception))
    lines = [line for line in str.splitlines(_TEXT)
             if not str.startswith(line, 'control')]
    with self.assertRaises(ValueError) as context:
      BeamSetup('\n'.join(lines))
    self.assertIn("a setup has a 'control' line", str(context.exception))
