"""
TestDocking covers docking to the space station (user, 2026-11-17: "Get
the docking!"; "we include buttons so that a try-hard *could* manually
do the thing ... But where we also provide an automated system for the
rest of. Same with docking"): the reading of the nose to the port, the
latch (catching only slow, straight, turning with the station), riding
docked with the station, undocking pushed off; the automatic docking
flown by the flight (the CPU here) from 1.5 km off to the latch,
meeting the station's solids (never bumping them).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._dockingguidance import HOLD_OUT, HURRY, REACH
from worQt.gaming.space._dockingguidance import DockingGuidance
from worQt.gaming.space._dockingport import NOSE_PORT, PUSH_OFF
from worQt.gaming.space._dockingport import DockingPort
from worQt.gaming.space._station import SPIN, Station
from worQt.gaming.space._vessel import Vessel

from . import SpaceTest

#  The automatic docking's frame, s, and how long it may take at most.
STEP = 0.1
LONGEST = 1800.0


class TestDocking(SpaceTest):
  """Tests for docking to the space station."""

  __time_out__ = 900.0

  def _near(self, out: float, aside: float) -> tuple:
    """Returns a system, its station, a docking port and a vessel 'out'
    m from the port along the station's axis and 'aside' m off it,
    moving with the station, not turning."""
    system = self.systemOf()
    station = Station(system)
    port = DockingPort(station)
    vessel = Vessel()
    middle, velocity = station.stateAt(0.0)
    rows = station.turnAt(0.0)
    axis = tuple(row[2] for row in rows)
    side = tuple(row[0] for row in rows)
    place = tuple(m + (80.0 + out + NOSE_PORT[2]) * a + aside * s
                  for m, a, s in zip(middle, axis, side))
    vessel.placed(station.parent, place, velocity, (1.0, 0.0, 0.0, 0.0),
                  (0.0, 0.0, 0.0))
    return system, station, port, vessel

  def test_latch(self) -> None:
    """In the port, nose down the axis, turning with the station, the
    latch catches; turning still, or coming in fast, it does not;
    docked, the rocket rides with the station; undocked, it is pushed
    off along the axis."""
    system, station, port, vessel = self._near(0.0, 0.0)
    port.aligned(vessel, 0.0)
    turn = port.turnAt(0.0)
    vessel.placed(vessel.anchor, vessel.place, vessel.velocity, turn,
                  (0.0, 0.0, 0.0))
    port.heldOn(vessel, system, 0.0)
    reading = port.readingOf(vessel, system, 0.0)
    self.assertLess(reading['distance'], 1e-6)
    self.assertTrue(port.caught(reading))
    still = dict(reading, turning=SPIN)
    self.assertFalse(port.caught(still))
    fast = dict(reading, closing=2.0)
    self.assertFalse(port.caught(fast))
    port.latched(vessel, 0.0)
    self.assertTrue(vessel.docked)
    port.heldOn(vessel, system, 30.0)
    later = port.readingOf(vessel, system, 30.0)
    self.assertLess(later['distance'], 1e-6)
    self.assertLess(later['turning'], 1e-9)
    port.released(vessel, system, 30.0)
    self.assertFalse(vessel.docked)
    off = port.readingOf(vessel, system, 30.0)
    self.assertAlmostEqual(-off['closing'], PUSH_OFF, 6)

  def test_refused(self) -> None:
    """The automatic docking will not start far off."""
    system, station, port, vessel = self._near(REACH + 1000.0, 0.0)
    guidance = DockingGuidance()
    why = guidance.started(vessel, port, port.readingOf(
      vessel, system, 0.0), 0.0)
    self.assertIn('off', why)
    self.assertFalse(guidance.on)

  def test_hurried(self) -> None:
    """Far from where it heads it hurries time ('HURRY'); at the point
    out on the axis, and the last metres in, real time."""
    system, station, port, vessel = self._near(1500.0, 0.0)
    guidance = DockingGuidance()
    reading = port.readingOf(vessel, system, 0.0)
    guidance.started(vessel, port, reading, 0.0)
    self.assertEqual(guidance.hurried(reading), HURRY)
    there = tuple(HOLD_OUT * a for a in reading['axis'])
    self.assertEqual(guidance.hurried(dict(reading, offset=there)), 1)
    guidance.phase = 'final'
    self.assertEqual(guidance.hurried(dict(reading, along=50.0)), HURRY)
    self.assertEqual(guidance.hurried(dict(reading, along=5.0)), 1)

  def test_auto(self) -> None:
    """From 1.5 km off the port, off its axis and drifting, the
    automatic docking brings the rocket in until the latch catches,
    within half an hour, never closing fast."""
    system, station, port, vessel = self._near(300.0, 1500.0)
    vessel.placed(vessel.anchor, vessel.place, tuple(
      v + d for v, d in zip(vessel.velocity, (0.4, -0.3, 0.2))),
                  vessel.turn, vessel.spin)
    flight, guidance = self.flightOf(), DockingGuidance()
    self.assertEqual(guidance.started(vessel, port, port.readingOf(
      vessel, system, 0.0), 0.0), '')
    t, fastest = 0.0, 0.0
    while t < LONGEST:
      reading = port.readingOf(vessel, system, t)
      if port.caught(reading):
        break
      if reading['distance'] < 20.0:
        fastest = max(fastest, reading['closing'])
      guidance.acted(vessel, port, reading, t)
      flight.flown((vessel,), system, t, STEP, math.inf, station)
      self.assertEqual(vessel.bumped, 0.0)
      t += STEP
    self.assertLess(t, LONGEST, 'not docked: %r' % {
      k: v for k, v in reading.items() if isinstance(v, float)})
    self.assertLess(fastest, 1.0)
    self.assertEqual(guidance.phase, 'final')
