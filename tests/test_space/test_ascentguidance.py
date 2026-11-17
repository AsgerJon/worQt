"""
TestAscentGuidance covers the ascent guidance (user, 2026-11-16: "go
ahead and get that mechjeb in here"): from the pad to a round 200 km
orbit through its phases (climb, turn, coast warped above the air, the
round burn), its target moved by its keys, and letting go.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._ascentguidance import TARGETS, TOP_UP
from worQt.gaming.space._ascentguidance import AscentGuidance
from worQt.gaming.space._timekeeper import Timekeeper
from worQt.gaming.space._vessel import MASS

from . import FRAME, SpaceTest


class TestAscentGuidance(SpaceTest):
  """Tests for 'AscentGuidance' (some 15 s on the CPU)."""

  __time_out__ = 600.0

  def test_to_orbit(self) -> None:
    """From the pad the guidance flies a round orbit 200 km up: its
    periapsis and apoapsis within 5 km of it, every phase gone through
    in order, the coast warped by hand (never by it), the engine shut at
    the end."""
    system, flight = self.systemOf(), self.flightOf()
    keeper = Timekeeper(system)
    vessel = self.padded(system)
    guidance = AscentGuidance()
    guidance.started(vessel, system)
    phases, warped, frames = [guidance.phase], False, 0
    while guidance.on and frames < 300000:
      self.warpedByHand(keeper, vessel, system)
      guidance.acted(vessel, system, keeper)
      warped = warped or keeper.factor > 1
      seconds = keeper.secondsOf(FRAME)
      flight.flown((vessel,), system, keeper.now, seconds)
      keeper.ticked(seconds)
      if guidance.phase != phases[-1]:
        phases.append(guidance.phase)
      frames += 1
    self.assertEqual(phases, ['climb', 'turn', 'coast', 'round', 'done'])
    self.assertTrue(warped)
    self.assertEqual(vessel.engine.throttle, 0.0)
    conic = vessel.conicOf(system)
    radius = system.bodies[vessel.anchor].radius
    self.assertAlmostEqual(conic.periapsis - radius, 200e3, delta=5e3)
    self.assertAlmostEqual(conic.apoapsis - radius, 200e3, delta=5e3)

  def test_target(self) -> None:
    """Its target steps through its marked heights, kept within them;
    its notch says which."""
    guidance = AscentGuidance()
    self.assertEqual(guidance.notch(), TARGETS.index(200e3))
    guidance.targeted(3)
    self.assertEqual(guidance.target, 400e3)
    guidance.targeted(1000)
    self.assertEqual(guidance.target, TARGETS[-1])
    guidance.targeted(-1000)
    self.assertEqual(guidance.target, TARGETS[0])

  def test_stopped(self) -> None:
    """Let go in the climb, the engine is shut and the autopilot holds
    the vessel as it is."""
    system, flight = self.systemOf(), self.flightOf()
    keeper = Timekeeper(system)
    vessel = self.padded(system)
    guidance = AscentGuidance()
    guidance.started(vessel, system)
    for _ in range(60):
      guidance.acted(vessel, system, keeper)
      flight.flown((vessel,), system, keeper.now, FRAME)
      keeper.ticked(FRAME)
    self.assertEqual(vessel.engine.throttle, 1.0)
    guidance.stopped(vessel)
    self.assertFalse(guidance.on)
    self.assertEqual(vessel.engine.throttle, 0.0)
    self.assertEqual(vessel.autopilot.mode, 'hold')

  def test_top_up(self) -> None:
    """Coasting in the air, the apoapsis under the target and falling
    fast, it tops up at no more than one g, only with Asger seated; not
    falling fast, it coasts on (user, 2026-11-17: "the auto pilot should
    not give tiny engine bursts to keep the AP at an exact value";
    "'top up' bursts ... should be limited to 1g AND require Asger to be
    seated")."""
    system = self.systemOf()
    keeper = Timekeeper(system)
    vessel = self.orbiting(system, 80e3, 150e3, 'ahead')
    guidance = AscentGuidance()
    guidance.started(vessel, system)
    self.assertEqual(guidance.phase, 'turn')
    guidance.phase = 'coast'
    guidance.acted(vessel, system, keeper, True)
    self.assertEqual(vessel.engine.throttle, 0.0)
    guidance._fall = 1e4
    guidance._last = None
    guidance.acted(vessel, system, keeper, False)
    self.assertEqual(vessel.engine.throttle, 0.0)
    guidance.acted(vessel, system, keeper, True)
    push = vessel.engine.push / (MASS * G0)
    self.assertAlmostEqual(push, TOP_UP, 6)

  def test_rounded_low(self) -> None:
    """Rounding, the orbit is rounded at the apoapsis reached (the air
    took some of it coasting), not at the target."""
    system, flight = self.systemOf(), self.flightOf()
    keeper = Timekeeper(system)
    vessel = self.orbiting(system, 120e3, 190e3, 'ahead')
    guidance = AscentGuidance()
    guidance.started(vessel, system)
    self.assertEqual(guidance.phase, 'turn')
    guidance.phase = 'coast'
    frames = 0
    while guidance.on and frames < 300000:
      self.warpedByHand(keeper, vessel, system)
      guidance.acted(vessel, system, keeper)
      seconds = keeper.secondsOf(FRAME)
      flight.flown((vessel,), system, keeper.now, seconds)
      keeper.ticked(seconds)
      frames += 1
    self.assertEqual(guidance.phase, 'done')
    self.assertAlmostEqual(guidance.rounding, 190e3, delta=1e3)
    conic = vessel.conicOf(system)
    radius = system.bodies[vessel.anchor].radius
    self.assertAlmostEqual(conic.periapsis - radius, 190e3, delta=2e3)
    self.assertAlmostEqual(conic.apoapsis - radius, 190e3, delta=2e3)
