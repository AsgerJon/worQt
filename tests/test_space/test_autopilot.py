"""
TestAutopilot covers the autopilot (user, 2026-11-16: "an autopilot
that can lock their orientation in place or locked to following a path
towards apogee, or the opposite point"): holding a turn against a
spin, pointing along the path and against it, over the ground in the
air, the keys taking over and the new turn held when let go, and at
time warp at once.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._turns import dot, rotated, unit

from . import FRAME, SpaceTest


def _degrees(one: tuple, two: tuple) -> float:
  """Returns the angle between the unit vectors 'one' and 'two', deg."""
  return math.degrees(math.acos(max(-1.0, min(1.0, dot(one, two)))))


class TestAutopilot(SpaceTest):
  """Tests for 'Autopilot' in the flight's kernel."""

  __time_out__ = 600.0

  def test_hold(self) -> None:
    """Spinning at 0.2 rad/s, held, the vessel is back on its turn within
    half a degree in 20 s, its spin gone."""
    system, flight = self.systemOf(), self.flightOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    turn = vessel.turn
    vessel.placed(vessel.anchor, vessel.place, vessel.velocity, turn,
                  (0.2, 0.0, 0.05))
    vessel.autopilot.engaged('hold', turn)
    self.flownFrames(flight, vessel, system, 20.0)
    for axis in ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)):
      self.assertLess(_degrees(rotated(vessel.turn, axis),
                               rotated(turn, axis)), 0.5)
    self.assertLess(math.dist(vessel.spin, (0, 0, 0)), 1e-3)

  def test_prograde(self) -> None:
    """Nose up, set to the path, the vessel points along its orbit
    within a degree in 30 s; set against it, against."""
    system, flight = self.systemOf(), self.flightOf()
    for mode, sign in (('prograde', 1.0), ('retrograde', -1.0)):
      vessel = self.orbiting(system, 300e3, 300e3)
      vessel.autopilot.engaged(mode, vessel.turn)
      self.flownFrames(flight, vessel, system, 30.0)
      aim = tuple(sign * x for x in unit(vessel.velocity))
      self.assertLess(_degrees(vessel.nose, aim), 1.0, mode)

  def test_surface(self) -> None:
    """In the air the path is the one over the ground (and the air): low
    over Terra going north the nose follows the ground velocity (three
    degrees west of the orbit's, Terra turning east under it), not the
    orbit."""
    system, flight = self.systemOf(), self.flightOf()
    vessel = self.orbiting(system, 40e3, 40e3)
    north = system.bodies[vessel.anchor].pole
    speed = math.dist(vessel.velocity, (0, 0, 0))
    vessel.placed(vessel.anchor, vessel.place, tuple(speed * x for x in
                                                     north), vessel.turn,
                  vessel.spin)
    vessel.autopilot.engaged('prograde', vessel.turn)
    self.flownFrames(flight, vessel, system, 30.0)
    ground = unit(vessel.groundVelocity(system))
    self.assertLess(_degrees(vessel.nose, ground), 1.0)
    self.assertGreater(_degrees(vessel.nose, unit(vessel.velocity)), 1.0)

  def test_steered(self) -> None:
    """The keys take over: held pitching for 2 s the vessel turns well
    over ten degrees; let go, it holds the turn it has then."""
    system, flight = self.systemOf(), self.flightOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    start = vessel.nose
    vessel.autopilot.engaged('hold', vessel.turn)
    vessel.steered(1.0, 0.0, 0.0)
    self.flownFrames(flight, vessel, system, 2.0)
    vessel.steered(0.0, 0.0, 0.0)
    self.assertGreater(_degrees(vessel.nose, start), 10.0)
    self.assertEqual(vessel.autopilot.held, vessel.turn)
    self.flownFrames(flight, vessel, system, 15.0)
    held = rotated(vessel.autopilot.held, (0.0, 0.0, 1.0))
    self.assertLess(_degrees(vessel.nose, held), 0.5)

  def test_warped(self) -> None:
    """At time warp the autopilot is on rails: after one long frame the
    nose points along the path exactly; held, the turn is the held
    one."""
    system, flight = self.systemOf(), self.flightOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    vessel.autopilot.engaged('prograde', vessel.turn)
    flight.flown((vessel,), system, 0.0, 1000.0)
    self.assertLess(_degrees(vessel.nose, unit(vessel.velocity)), 0.1)
    vessel.autopilot.engaged('hold', vessel.turn)
    turn = vessel.turn
    flight.flown((vessel,), system, 1000.0, 1000.0)
    self.assertLess(_degrees(vessel.nose, rotated(turn, (0.0, 0.0, 1.0))),
                    1e-3)
