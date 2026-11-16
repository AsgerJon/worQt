"""
TestFlight covers the vessel's flight on the device (the CPU here):
standing on the pad it turns with Terra, at rest on its legs; at full
throttle it lifts off; coasting it keeps its orbit, a frame at a time
(about 320 000 small steps an orbit, float32: the place and velocity
in two parts) and at the fastest warp alike, Terra pulling alone; the air drags it as
reckoned; near Luna it is handed to Luna.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._turns import dot, norm, unit
from worQt.gaming.space._vessel import CENTRE, DRAG, MASS, SAG

from . import FRAME, SpaceTest


class TestFlight(SpaceTest):
  """Tests for 'Flight' and its kernel (a minute or so on the CPU)."""

  __time_out__ = 900.0

  def test_rests(self) -> None:
    """On the pad the vessel stands on its four legs, turning with
    Terra: its height and its speed over the ground still, upright."""
    system, flight = self.systemOf(), self.flightOf()
    vessel = self.padded(system)
    self.flownFrames(flight, vessel, system, 3.0)
    self.assertEqual(vessel.touching, 4)
    height = vessel.heightOver(system)
    self.assertAlmostEqual(height, CENTRE - SAG, delta=0.01)
    self.assertLess(norm(vessel.groundVelocity(system)), 0.01)
    self.assertGreater(dot(vessel.nose, unit(vessel.place)), 0.99999)

  def test_lifts(self) -> None:
    """At full throttle (1.5 g) the vessel leaves the pad, held upright
    by its autopilot: some 200 m up after 10 s, still climbing."""
    system, flight = self.systemOf(), self.flightOf()
    vessel = self.padded(system)
    vessel.autopilot.engaged('hold', vessel.turn)
    vessel.engine.throttled(1.0)
    self.flownFrames(flight, vessel, system, 10.0)
    height = vessel.heightOver(system) - CENTRE
    self.assertGreater(height, 180.0)
    self.assertLess(height, 260.0)
    self.assertEqual(vessel.touching, 0)
    climb = dot(vessel.groundVelocity(system), unit(vessel.place))
    self.assertGreater(climb, 30.0)
    self.assertGreater(dot(vessel.nose, unit(vessel.place)), 0.999)

  def test_coasts(self) -> None:
    """On a 200 by 300 km orbit the vessel keeps its apoapsis and
    periapsis within 10 m (Terra pulling alone: every other body made
    weightless, the kernel's steps tried by themselves): once round a
    frame at a time (322 000 float32 steps), and twenty times round at
    100 000 times real time (some thirty Kepler arcs an orbit)."""
    system, flight = self.systemOf(), self.flightOf()
    for body in system.bodies:
      if body.name != 'Terra':
        body.mu = 1e-3
    terra = system.bodies[system.named('Terra')]
    for longest, rounds, frame in ((FRAME, 1, None), (math.inf, 20,
                                                      100000 * FRAME)):
      vessel = self.orbiting(system, 200e3, 300e3)
      before = vessel.conicOf(system)
      seconds = rounds * before.period
      if frame is None:
        flight.flown((vessel,), system, 0.0, seconds, longest)
      else:
        t = 0.0
        while t < seconds - 1e-6:
          step = min(frame, seconds - t)
          flight.flown((vessel,), system, t, step)
          t += step
      after = vessel.conicOf(system)
      self.assertEqual(vessel.anchor, system.named('Terra'))
      self.assertAlmostEqual(after.periapsis - terra.radius, 200e3,
                             delta=10.0)
      self.assertAlmostEqual(after.apoapsis - terra.radius, 300e3,
                             delta=10.0)

  def test_drag(self) -> None:
    """At 30 km going 1 km/s over the ground nose first, the air slows
    the vessel as half rho v² CdA over its mass says, within a tenth."""
    system, flight = self.systemOf(), self.flightOf()
    terra = system.named('Terra')
    body = system.bodies[terra]
    vessel = self.orbiting(system, 30e3, 30e3, 'ahead')
    ground = vessel.groundVelocity(system)
    lead = unit(ground)
    slower = tuple(1000.0 * x for x in lead)
    spin = body.spinVector
    moving = tuple(a + b for a, b in zip(slower, (
      spin[1] * vessel.place[2] - spin[2] * vessel.place[1],
      spin[2] * vessel.place[0] - spin[0] * vessel.place[2],
      spin[0] * vessel.place[1] - spin[1] * vessel.place[0])))
    vessel.placed(terra, vessel.place, moving, vessel.turn, vessel.spin)
    before = vessel.groundVelocity(system)
    pull = system.pullOn(terra, vessel.place, 0.0)
    flight.flown((vessel,), system, 0.0, 0.1, FRAME)
    after = vessel.groundVelocity(system)
    lost = dot(tuple(a - b for a, b in zip(before, after)), lead) / 0.1
    lost += dot(pull, lead)
    rho = body.air.densityAt(30e3 - 0.0)
    wanted = 0.5 * rho * 1000.0 ** 2 * DRAG[0] / MASS
    self.assertAlmostEqual(lost / wanted, 1.0, delta=0.1)

  def test_handed(self) -> None:
    """A vessel 30 000 km short of Luna is handed to Luna, its place and
    velocity then from Luna's middle."""
    system, flight = self.systemOf(), self.flightOf()
    terra, luna = system.named('Terra'), system.named('Luna')
    there, moving = system.relative(luna, terra, 0.0)
    back = unit(there)
    place = tuple(a - 3e7 * b for a, b in zip(there, back))
    vessel = self.orbiting(system, 200e3, 200e3)
    vessel.placed(terra, place, moving, vessel.turn, vessel.spin)
    flight.flown((vessel,), system, 0.0, 1.0)
    self.assertEqual(vessel.anchor, luna)
    self.assertAlmostEqual(norm(vessel.place) / 3e7, 1.0, delta=1e-4)
    self.assertLess(norm(vessel.velocity), 1.0)
