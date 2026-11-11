"""
TestRig covers 'Rig' and its parts, 'Support', 'Actuator' and
'Control': any number of supports, actuators and transducers; one
actuator driven by the control, which reads one transducer, every other
following one, in a chain, by a share of its force; the rig refusing to
be anything but whole, and to fit a beam its supports do not hold.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.lab import Actuator, Control, Rig, Support

from . import LabTest, standardBeam

_CONTROL = Control(0, 0, 0.1, 150.0, 0.001, 0.5, 0.05, 0.0, 1.0)
_SUPPORTS = (Support(150.0, 'pin'), Support(3150.0, 'roller'))


class TestRig(LabTest):
  """Tests for 'Rig' and its parts."""

  def test_standard(self) -> None:
    """Four point bending: a pin and a roller 150 mm in, two actuators
    at the thirds, the second as hard as the first, a transducer under
    each and one at midspan, which the control reads, ramping it down,
    below nought as a transducer under the beam reads."""
    rig = Rig.standard(standardBeam())
    self.assertEqual(rig.supports, _SUPPORTS)
    self.assertEqual(rig.actuators, (Actuator(1150.0, -1, 1.0),
                                     Actuator(2150.0, 0, 1.0)))
    self.assertEqual(rig.transducers, (1150.0, 2150.0, 1650.0))
    self.assertEqual(rig.control.transducer, 2)
    self.assertEqual((rig.control.rate, rig.control.limit), (-0.1, -150.0))
    self.assertEqual(rig.driven, 0)
    self.assertEqual(rig.shares, (1.0, 1.0))
    self.assertEqual(rig.control.step, 0.001)
    self.assertAlmostEqual(rig.cycle, 1.5)
    self.assertEqual(rig.stroke, 150.0)

  def test_supports(self) -> None:
    """A pin holds along and across, a roller across, a clamp turning
    too."""
    self.assertEqual(Support(0.0, 'pin').holds, (1, 1, 0))
    self.assertEqual(Support(0.0, 'roller').holds, (0, 1, 0))
    self.assertEqual(Support(0.0, 'fixed').holds, (1, 1, 1))
    with self.assertRaises(ValueError):
      Rig((Support(0.0, 'glue'),), (Actuator(500.0, -1, 1.0),), (500.0,),
          _CONTROL)

  def test_chain(self) -> None:
    """Each actuator pushes the product of the shares along its chain
    of the force of the one driven."""
    actuators = (Actuator(500.0, -1, 1.0), Actuator(1000.0, 0, 0.5),
                 Actuator(1500.0, 1, 0.5), Actuator(2000.0, 0, -1.0))
    rig = Rig(_SUPPORTS, actuators, (500.0,), _CONTROL)
    self.assertEqual(rig.shares, (1.0, 0.5, 0.25, -1.0))

  def test_whole(self) -> None:
    """A rig is whole: the control drives an actuator and reads a
    transducer there are, its ramp moves, its step is a share of it,
    and every chain leads to the one driven."""
    one = (Actuator(500.0, -1, 1.0),)
    with self.assertRaises(ValueError):
      Rig(_SUPPORTS, (), (500.0,), _CONTROL)
    with self.assertRaises(ValueError):
      Rig(_SUPPORTS, one, (), _CONTROL)
    with self.assertRaises(ValueError):
      Rig(_SUPPORTS, one, (500.0,), _CONTROL.changed('actuator', 1))
    circle = (Actuator(500.0, -1, 1.0), Actuator(900.0, 2, 1.0),
             Actuator(1300.0, 1, 1.0))
    with self.assertRaises(ValueError):
      Rig(_SUPPORTS, circle, (500.0,), _CONTROL)
    with self.assertRaises(ValueError):
      Rig(_SUPPORTS, (*one, Actuator(900.0, 5, 1.0)), (500.0,), _CONTROL)
    with self.assertRaises(ValueError):
      Rig(_SUPPORTS, one, (500.0,), _CONTROL.changed('rate', 0.0))
    for share in (0.0, 1.5):
      with self.assertRaises(ValueError):
        Rig(_SUPPORTS, one, (500.0,), _CONTROL.changed('step', share))

  def test_held(self) -> None:
    """A beam is held along by a pin or a clamp, and from turning by two
    supports or a clamp; the rig's parts are on it."""
    beam = standardBeam()
    rig = Rig.standard(beam)
    rig.check(beam)
    rollers = rig.withSupports(Support(150.0, 'roller'),
                               Support(3150.0, 'roller'))
    self.assertIn('along', rollers.unheld())
    one = rig.withSupports(Support(150.0, 'pin'))
    self.assertIn('turn', one.unheld())
    clamped = rig.withSupports(Support(0.0, 'fixed'))
    self.assertEqual(clamped.unheld(), '')
    for unfit in (rollers, one, rig.withTransducers(1150.0, 2150.0,
                                                    3500.0)):
      with self.assertRaises(ValueError):
        unfit.check(beam)

  def test_ramp_reaches(self) -> None:
    """A rig fits a beam only if its ramp reaches its limit from nought;
    'towards' turns a rate's sign to head for its limit."""
    beam = standardBeam()
    rig = Rig.standard(beam)
    away = rig.withControl(rig.control.changed('rate', 0.1))
    with self.assertRaises(ValueError):
      away.check(beam)
    self.assertEqual(away.control.towards(0.0).rate, -0.1)
    self.assertEqual(rig.control.towards(0.0), rig.control)
    back = rig.control.changed('limit', 0.0).towards(-20.0)
    self.assertEqual(back.rate, 0.1)

  def test_without(self) -> None:
    """A part is taken away, the indices after it moving down; not the
    actuator driven, one another follows, or the transducer read."""
    rig = Rig.standard(standardBeam())
    with self.assertRaises(ValueError):
      rig.withoutActuator(0)
    with self.assertRaises(ValueError):
      rig.withoutTransducer(2)
    fewer = rig.withoutTransducer(0)
    self.assertEqual(fewer.transducers, (2150.0, 1650.0))
    self.assertEqual(fewer.control.transducer, 1)
    third = rig.withActuators(*rig.actuators, Actuator(1650.0, 1, 0.5))
    with self.assertRaises(ValueError):
      third.withoutActuator(1)
    self.assertEqual(len(third.withoutActuator(2).actuators), 2)
    self.assertEqual(len(rig.withoutSupport(1).supports), 1)

  def test_driving(self) -> None:
    """Driving another actuator has the one driven before follow it,
    as hard."""
    rig = Rig.standard(standardBeam()).driving(1)
    self.assertEqual(rig.driven, 1)
    self.assertEqual(rig.actuators[0], Actuator(1150.0, 1, 1.0))
    self.assertEqual(rig.actuators[1].follows, -1)
    self.assertEqual(rig.shares, (1.0, 1.0))
    with self.assertRaises(ValueError):
      rig.driving(5)

  def test_stretched(self) -> None:
    """A rig stretched for a longer beam takes its parts along, to the
    centimetre."""
    rig = Rig.standard(standardBeam()).stretched(2.0)
    self.assertEqual(rig.supports[1], Support(6300.0, 'roller'))
    self.assertEqual(rig.actuators[0].at, 2300.0)
    self.assertEqual(rig.transducers[2], 3300.0)
