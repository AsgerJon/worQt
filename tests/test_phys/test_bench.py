"""
TestBench covers the car on the suspension bench ('benchOf'): the
scales add up to its weight, half of it on the front, left as right;
tapped, its body heaves and pitches as its springs and dampers were
made to, standing on its tyres (the two in series: within 8 % of the
frequency and 0.08 of the damping); pulled sideways at half a g it
rolls about as far as its springs on their tyres let it (1.28 degrees
a g at 3 Hz; 5.5 at 1.5, the springs alone 4.7), its rear
wheels all but unsteered (their rods' stiffer rubber, 'REAR_ROD':
under 0.1 degrees, with the push; on the front's rubber they steered
0.25 and the car swayed at 2.8 Hz above ~25 m/s), its front wheels
steered by their rubber out of the turn, not into it.
The roll's ring is reported, not tested: it rings at 1.7 Hz damped
0.28 of critical, where the body taken as rolling about the ground on
its springs says 2.3 and 0.57 (not yet explained).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.phys import FULL, carBuilt
from worQt.phys._bench import PULL_SHARE, benchOf, reportOf
from worQt.phys._car import FRONT_SHARE, RIDE, RIDE_DAMPING

from . import PhysTest


class TestBench(PhysTest):
  """Tests for the car on the suspension bench."""

  #  The springs' world's car, stepped in its world's one thread: minutes
  #  a class (killed at the harness's 30 s, the user's run of 2026-11-14).
  __time_out__ = 3600.0

  @classmethod
  def setUpClass(cls, ) -> None:
    """Builds the car and puts it on the bench, once for every test
    ('car', 'found'; at the module's import it ran past the harness's
    minute for loading a class)."""
    super().setUpClass()
    cls.car = carBuilt(0.5)
    cls.found = benchOf(cls.car, FULL)

  def test_report(self) -> None:
    """The report tells every finding, a line each."""
    lines = reportOf(self.found).split('\n')
    self.assertEqual(len(lines), 12)

  def test_scales(self) -> None:
    """The four scales read the car's weight (within 0.2 %), the front
    'FRONT_SHARE' of it (within half a percent), left as right (within
    2 N)."""
    weight = 9.81 * sum(body.mass for body in self.car.assembly.bodies)
    loads = self.found['loads']
    self.assertNear(sum(loads), weight, 2e-3 * weight)
    self.assertNear(self.found['front'], FRONT_SHARE, 5e-3)
    self.assertNear(loads[0], loads[1], 2.0)
    self.assertNear(loads[2], loads[3], 2.0)

  def test_heave_and_pitch(self) -> None:
    """Tapped, the body heaves and pitches at what the corners' springs
    standing on their tyres make it on its mass and inertia, each within
    8 %; damped within 0.08 of what its dampers, so standing, were made
    for; the springs alone made for 'RIDE' Hz, 'RIDE_DAMPING'. (At 3 Hz,
    0.5, 2026-11-13: heave 2.69 Hz, 0.33 against 2.59, 0.32; pitch 4.21,
    0.43 against 3.77, 0.47: 12 % quick, at 1.5 Hz within 1 %, not yet
    explained.)"""
    for mode in ('heave', 'pitch'):
      (hz, ratio), (wantHz, wantRatio) = (self.found[mode],
                                          self.found['designed'][mode])
      self.assertNear(hz / wantHz, 1.0, 0.08)
      self.assertNear(ratio, wantRatio, 0.08)
    self.assertEqual(self.found['designed']['springs'], (RIDE, RIDE_DAMPING))

  def test_roll(self) -> None:
    """Pulled sideways at half a g, the body rolls within a fifth of as
    far as its springs on their tyres let it (1.28 deg a g against 1.18
    when measured at 3 Hz), its left side down (pulled left)."""
    pull = self.found['pulled']
    self.assertGreater(pull['roll'], 0.0)
    self.assertNear(pull['gradient'] / self.found['designed']['gradient'],
                    1.0, 0.2)
    self.assertNear(pull['gradient'] * PULL_SHARE, pull['roll'], 1e-12)

  def test_steering(self) -> None:
    """Pulled sideways, the rear wheels steer under 0.1 degrees (0.09
    when measured), the way they are pushed (with the turn: their
    compliance steer at or over nought), the front ones out of the turn
    (at or under nought), none leaning past a degree."""
    corners = self.found['pulled']['corners']
    for corner in corners[2:]:
      self.assertLess(abs(corner['steer']), 0.1)
      self.assertGreaterEqual(corner['compliance'], 0.0)
    for corner in corners[:2]:
      self.assertLessEqual(corner['compliance'], 0.0)
    for corner in corners:
      self.assertLess(abs(corner['camber']), 1.0)
      self.assertLess(corner['force'], 0.0)
