"""
TestDocking covers docking to the space station (user, 2026-11-17: "Get
the docking!"; "we include buttons so that a try-hard *could* manually
do the thing ... But where we also provide an automated system for the
rest of. Same with docking"): the reading of the nose to the port, the
latch (catching only slow, straight, turning with the station), riding
docked with the station, undocking pushed off; the automatic docking
flown by the flight (the CPU here) from 1.5 km off to the latch,
meeting the station's solids (never bumping them); from behind the
station (the user's let's play, 2026-11-18: straight in, it backed into
the hub's foot at 18.5 m/s) it goes round, every corner of its way
clear of all the station sweeps, and latches never bumping.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._dockingguidance import HOLD_OUT, PORT_TOP, REACH
from worQt.gaming.space._dockingguidance import ROCKET_UP, ROCKET_WIDE
from worQt.gaming.space._dockingguidance import DockingGuidance, routeOf
from worQt.gaming.space._stationsolids import stationSolids, sweptDistance
from worQt.gaming.space._dockingport import NOSE_PORT, PUSH_OFF
from worQt.gaming.space._dockingport import DockingPort
from worQt.gaming.space._station import SPIN, Station
from worQt.gaming.space._vessel import Vessel

from . import SpaceTest

#  The automatic docking's frame, s, and how long it may take at most
#  (user, 2026-11-17: "adjust the autodocking thing to use a high speed
#  when closing in"; "DOCK: FINAL is moving so slooooooooow").
STEP = 0.1
LONGEST = 600.0


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
    port.latched(vessel, system, 0.0)
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

  def test_auto(self) -> None:
    """From 1.5 km off the port, off its axis and drifting, the
    automatic docking brings the rocket in until the latch catches,
    within ten minutes, never bumping, slow enough as it is caught."""
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
        fastest = reading['closing']
        break
      guidance.acted(vessel, port, reading, t)
      flight.flown((vessel,), system, t, STEP, math.inf, station)
      self.assertEqual(vessel.bumped, 0.0)
      t += STEP
    self.assertLess(t, LONGEST, 'not docked: %r' % {
      k: v for k, v in reading.items() if isinstance(v, float)})
    self.assertLess(fastest, 1.0)
    self.assertEqual(guidance.phase, 'final')

  def _docked(self, out: float, aside: float) -> tuple:
    """Flies the automatic docking from 'out' m along the station's axis
    from its port and 'aside' m off it; returns the time it latched (or
    'LONGEST'), the phases it went through, the hardest bump."""
    system, station, port, vessel = self._near(out, aside)
    flight, guidance = self.flightOf(), DockingGuidance()
    self.assertEqual(guidance.started(vessel, port, port.readingOf(
      vessel, system, 0.0), 0.0), '')
    t, phases, bump = 0.0, [guidance.phase], 0.0
    while t < LONGEST:
      reading = port.readingOf(vessel, system, t)
      if port.caught(reading):
        return t, phases, bump
      guidance.acted(vessel, port, reading, t)
      if guidance.phase != phases[-1]:
        phases.append(guidance.phase)
      flight.flown((vessel,), system, t, STEP, math.inf, station)
      bump = max(bump, vessel.bumped)
      t += STEP
    return t, phases, bump

  def test_behind(self) -> None:
    """From 2 km behind the station (the side of its other port: user,
    2026-11-18, "Terra Prime should have docking ports on both sides"),
    110 m off its axis, the automatic docking takes that port, straight
    in, and latches, never bumping; from beside it, out past its wheel,
    it goes round to the nearer port's front first."""
    t, phases, bump = self._docked(-2160.0, 110.0)
    self.assertLess(t, LONGEST)
    self.assertEqual(phases, ['closing', 'final'])
    self.assertEqual(bump, 0.0)
    t, phases, bump = self._docked(-80.0, 1500.0)
    self.assertLess(t, LONGEST)
    self.assertEqual(phases, ['round', 'closing', 'final'])
    self.assertEqual(bump, 0.0)

  def test_route(self) -> None:
    """Every way round, from in front, beside and behind the station (and
    under and over its wheel), keeps the rocket (its nose down the axis,
    its body above it) clear of all the station sweeps as it turns, the
    last leg in to the point out on the axis too; from the front there is
    no way round."""
    solids = stationSolids()

    def clear(out: float, along: float) -> float:
      least = math.inf
      for k in range(0, int(ROCKET_UP) + 1, 4):
        point = (out, 0.0, PORT_TOP + along + k)
        least = min(least, min(sweptDistance(s, point) for s in solids))
      return least - ROCKET_WIDE

    self.assertEqual(routeOf(300.0, 300.0), ())
    for start in ((115.0, -1976.0), (2000.0, -80.0), (1500.0, -600.0),
                  (300.0, -400.0), (800.0, -2500.0), (600.0, 30.0)):
      corners = (start,) + routeOf(*start) + ((0.0, HOLD_OUT),)
      for (a, b), (c, d) in zip(corners, corners[1:]):
        for k in range(41):
          s = k / 40.0
          self.assertGreater(clear(a + s * (c - a), b + s * (d - b)), 10.0,
                             'from %r by %r' % (start, corners))
