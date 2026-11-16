"""
TestAccelerometer covers what the vessel feels (user, 2026-11-17: Asger
floating round, "FAFO rules"): on the pad one g up; coasting nothing;
the pull on what is loose in the cabin: the vessel's push the other
way, the enchantment's toward the floor, its turning's outward.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._turns import norm

from . import FRAME, SpaceTest


class TestAccelerometer(SpaceTest):
  """Tests for the vessel's accelerometer."""

  def test_pad(self) -> None:
    """Standing on the pad it feels the ground hold it up: about one g
    along its nose."""
    system = self.systemOf()
    vessel = self.padded(system)
    meter = Accelerometer()
    for _ in range(120):
      meter.measured(vessel, system, FRAME, False)
    self.assertAlmostEqual(meter.felt[2], 9.82, 1)
    self.assertLess(abs(meter.felt[0]) + abs(meter.felt[1]), 0.05)

  def test_coasting(self) -> None:
    """Falling freely round Terra it feels nothing."""
    system = self.systemOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    body = system.bodies[vessel.anchor]
    meter = Accelerometer()
    for _ in range(120):
      far = norm(vessel.place)
      pull = tuple(-body.mu * x / far ** 3 for x in vessel.place)
      velocity = tuple(v + FRAME * g for v, g in zip(vessel.velocity,
                                                     pull))
      place = tuple(p + FRAME * v for p, v in zip(vessel.place, velocity))
      vessel.placed(vessel.anchor, place, velocity, vessel.turn,
                    vessel.spin)
      meter.measured(vessel, system, FRAME, False)
    self.assertLess(norm(meter.felt), 0.01)

  def test_pull(self) -> None:
    """The pull on what is loose: the push the other way and the
    enchantment toward the floor; turning, outward from its axis."""
    meter = Accelerometer()
    meter.felt = (0.0, 0.0, 2.0 * G0)
    self.assertClose(meter.pullAt((0.0, 1.0, 0.0), (0.0, 0.0, 0.0), 1.0),
                     (0.0, 0.0, -3.0 * G0), 1e-9)
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, 0.5)
    self.assertClose(meter.pullAt((0.0, 2.0, 0.0), (0.0, 0.0, 0.0), 0.0),
                     (0.0, 0.5, 0.0), 1e-9)
