"""
TestEgg covers the gravity egg (user, 2026-11-18: "A glass egg with a
ball rolling around inside, a ball that emits light. On the ground the
ball is on the ground, but without gravity i just floats"; "place the
egg on a pedetal centrally in the room"): its marble lies at the bottom
on the pad, is pressed down under thrust, floats on as it was going
weightless, settles slowly outward docked to the turning station, and
never leaves the glass; the pedestal stands clear of the hatch's way
up, the floor's bolts, the furniture and his chair; the glass and the
marble are drawn.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cockpit import FLOOR, SEAT_AT
from worQt.gaming.space._egg import BALL, EGG_HALF, PEDESTAL, Egg
from worQt.gaming.space._egg import eggMiddle, eggRows, marbleRows
from worQt.gaming.space._egg import pedestalSolids
from worQt.gaming.space._furnishings import obstacles
from worQt.gaming.space._station import SPIN

from . import FRAME, SpaceTest


class TestEgg(SpaceTest):
  """Tests for the gravity egg."""

  def _meter(self, felt: tuple, turning: tuple = (0.0, 0.0, 0.0)
             ) -> Accelerometer:
    """Returns an accelerometer reading 'felt' (m/s², the vessel's own
    axes) and turning 'turning' (rad/s)."""
    meter = Accelerometer()
    meter.felt, meter.turning = felt, turning
    meter.speeding = (0.0, 0.0, 0.0)
    return meter

  def _flown(self, egg: Egg, meter: Accelerometer, seconds: float,
             inside: list = None) -> None:
    """Steps 'egg' 'seconds' s a frame at a time; keeps how far inside
    the glass its marble was each frame in 'inside'."""
    for _ in range(int(round(seconds / FRAME))):
      egg.stepped(FRAME, meter)
      if inside is not None:
        inside.append(egg.inside(egg.ball))

  def test_ground(self) -> None:
    """On the pad (one g up) the marble, let go off its middle moving,
    bounces and rolls round the glass (glass on glass: its bounces and
    its sliding take its speed) and within a minute lies at the egg's
    bottom, still."""
    egg = Egg()
    egg.ball, egg.moving = (0.01, -0.005, 0.02), (0.3, 0.1, 0.0)
    inside = []
    self._flown(egg, self._meter((0.0, 0.0, G0)), 60.0, inside)
    self.assertLess(egg.ball[2], -0.03)
    self.assertLess(math.hypot(egg.ball[0], egg.ball[1]), 0.002)
    self.assertLess(math.hypot(*egg.moving), 0.005)
    self.assertGreater(min(inside), -1e-9)

  def test_thrust(self) -> None:
    """Under four g of thrust (up its nose) it is pressed to the bottom
    as on the pad."""
    egg = Egg()
    egg.ball = (0.0, 0.0, 0.03)
    self._flown(egg, self._meter((0.0, 0.0, 4.0 * G0)), 3.0)
    self.assertLess(egg.ball[2], -0.03)

  def test_floats(self) -> None:
    """Weightless and not turning it floats on as it was going: let go
    still in the middle it stays there; moving, it goes straight on at
    its speed (but the air's) until it meets the glass, off which it
    bounces, staying inside."""
    egg = Egg()
    egg.ball = (0.0, 0.0, 0.0)
    meter = self._meter((0.0, 0.0, 0.0))
    self._flown(egg, meter, 5.0)
    self.assertLess(math.hypot(*egg.ball), 1e-9)
    egg.moving = (0.01, 0.0, 0.0)
    self._flown(egg, meter, 1.0)
    self.assertAlmostEqual(egg.ball[0], 0.01, 3)
    self.assertLess(abs(egg.ball[2]), 1e-9)
    inside = []
    egg.moving = (0.2, 0.15, 0.1)
    self._flown(egg, meter, 10.0, inside)
    self.assertGreater(min(inside), -1e-9)
    self.assertGreater(math.hypot(*egg.moving), 0.01)

  def test_docked(self) -> None:
    """Docked to the station, the rocket on its axis turning with it,
    the marble settles slowly to the side away from the axis (the egg
    is 1.6 m off it: the turn's pull there is a few thousandths of a
    g)."""
    egg = Egg()
    egg.ball = (0.0, 0.0, 0.0)
    self._flown(egg, self._meter((0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)), 20.0)
    out = tuple(m / math.hypot(*eggMiddle()[:2]) for m in eggMiddle()[:2])
    self.assertGreater(egg.ball[0] * out[0] + egg.ball[1] * out[1],
                       EGG_HALF - BALL - 0.01)

  def test_pedestal(self) -> None:
    """The pedestal stands in the room's middle, clear of the hatch's way
    up (a metre and more off its axis: the ladder's there), of his chair,
    and of every other solid; the egg sits on it at about chest
    height."""
    self.assertGreater(math.hypot(*PEDESTAL), 1.0)
    self.assertLess(math.hypot(*PEDESTAL), 2.0)
    self.assertGreater(math.dist(PEDESTAL, SEAT_AT), 2.0)
    own = pedestalSolids()
    for middle, half, _ in obstacles():
      if any(middle == m for m, _, _ in own):
        continue
      apart = math.dist(middle[:2], PEDESTAL) - math.hypot(*half[:2])
      self.assertGreater(apart, 0.5, middle)
    self.assertGreater(eggMiddle()[2] - FLOOR, 0.9)
    self.assertLess(eggMiddle()[2] - FLOOR, 1.4)

  def test_drawn(self) -> None:
    """The glass is an egg round its middle, wider low than high; the
    marble a ball of its radius."""
    rows, faces = eggRows()
    self.assertGreater(len(faces), 0)
    middle = eggMiddle()
    across = max(math.hypot(r[0] - middle[0], r[1] - middle[1])
                 for r in rows)
    self.assertAlmostEqual(across, EGG_HALF, 3)
    marble, _ = marbleRows()
    self.assertAlmostEqual(max(math.hypot(*r[:3]) for r in marble), BALL,
                           6)
