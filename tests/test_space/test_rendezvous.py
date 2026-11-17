"""
TestRendezvous covers the automatic rendezvous with the space station
(user, 2026-11-17: "we include buttons so that a try-hard *could*
manually do the thing. If he hates fun. But where we also provide an
automated system for the rest of. Same with docking"): Lambert's
transfers coast onto their ends; the plan from a low orbit is
Hohmann's; it will not start off orbit; from a low orbit, a tilted
one and the station's own height (phasing) it brings the rocket to
the station, slow, near enough for the automatic docking.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._conic import Conic
from worQt.gaming.space._dockingguidance import DockingGuidance
from worQt.gaming.space._dockingport import DockingPort
from worQt.gaming.space._rendezvousguidance import HOP_OVER, PLANE_SAME
from worQt.gaming.space._rendezvousguidance import RendezvousGuidance
from worQt.gaming.space._station import HIGH, Station
from worQt.gaming.space._timekeeper import Timekeeper
from worQt.gaming.space._transfers import Transfers
from worQt.gaming.space._turns import aboutAxis, norm, rotated, unit

from . import SpaceTest

#  The rendezvous's frame, s, and how many it may take at most.
STEP = 0.1
MOST = 20000
#  G M of Terra.
MU = 3.986004418e14
#  The rocket keeps this far from the station's middle, m.
CLEAR = 1500.0


class TestRendezvous(SpaceTest):
  """Tests for the automatic rendezvous."""

  __time_out__ = 900.0

  def _ready(self, low: float, tilt: float) -> tuple:
    """Returns a system, its station, a docking port, a vessel on a
    round orbit 'low' m up tilted 'tilt' rad off the equator, a
    timekeeper and the guidance."""
    system = self.systemOf()
    station = Station(system)
    vessel = self.orbiting(system, low, low, 'ahead')
    if tilt:
      turn = aboutAxis(unit(vessel.place), tilt)
      vessel.placed(vessel.anchor, vessel.place, rotated(
        turn, vessel.velocity), vessel.turn, vessel.spin)
    guidance = RendezvousGuidance(station)
    guidance.transfers = Transfers('cpu')
    return (system, station, DockingPort(station), vessel,
            Timekeeper(system), guidance)

  def _flown(self, system: object, vessel: object, keeper: Timekeeper,
             guidance: RendezvousGuidance) -> list:
    """Flies the guidance till it is done (or 'MOST' frames); returns
    the phases it went through. Never nearer the station's middle than
    'CLEAR' (its wheel and antennas reach 1.2 km)."""
    flight, phases = self.flightOf(), [guidance.phase]
    for _ in range(MOST):
      if not guidance.on:
        break
      guidance.acted(vessel, system, keeper)
      if guidance.phase != phases[-1]:
        phases.append(guidance.phase)
      middle = guidance.station.stateAt(keeper.now)[0]
      self.assertGreater(math.dist(middle, vessel.place), CLEAR)
      seconds = keeper.secondsOf(STEP)
      flight.flown((vessel,), system, keeper.now, seconds)
      keeper.ticked(seconds)
    return phases

  def _arrived(self, system: object, port: DockingPort, vessel: object,
               keeper: Timekeeper, guidance: RendezvousGuidance) -> None:
    """Fails unless the rendezvous is done near the station, slow, and
    the automatic docking will take it from there."""
    self.assertEqual(guidance.phase, 'done')
    reading = port.readingOf(vessel, system, keeper.now)
    self.assertLess(reading['distance'], HOP_OVER)
    self.assertLess(norm(reading['drift']), 5.0)
    self.assertEqual(DockingGuidance().started(vessel, port, reading,
                                               keeper.now), '')

  def test_transfers(self) -> None:
    """Each transfer coasts onto its end in its time (float32: within
    tens of m over thousands of km); none between places the same way
    or opposite."""
    transfers = Transfers('cpu')
    start = (6571e3, 0.0, 0.0)
    for degrees, seconds in ((40.0, 300.0), (120.0, 2000.0),
                             (170.0, 2600.0), (250.0, 4000.0)):
      angle = math.radians(degrees)
      end = (6771e3 * math.cos(angle), 6771e3 * math.sin(angle), 1000.0)
      leaving, arriving = transfers.solved(MU, [start], [end], [seconds],
                                           (0.0, 0.0, 1.0))
      place, velocity = Conic.fromState(MU, start, tuple(
        leaving[0])).stateAt(seconds)
      self.assertLess(math.dist(place, end), 60.0, degrees)
      self.assertLess(math.dist(velocity, arriving[0]), 0.1, degrees)
    for end in ((7000e3, 0.0, 0.0), (-7000e3, 0.0, 0.0)):
      leaving, _ = transfers.solved(MU, [start], [end], [2000.0],
                                    (0.0, 0.0, 1.0))
      self.assertTrue(math.isnan(leaving[0][0]))

  def test_plan(self) -> None:
    """From a round orbit 200 km up the plan is Hohmann's: the burn
    within 3 % of his, the flight within 5 % of half his ellipse's
    turn."""
    system, station, port, vessel, keeper, guidance = self._ready(200e3,
                                                                  0.0)
    self.assertEqual(guidance.started(vessel, system, keeper), '')
    self.assertEqual(guidance.phase, 'wait')
    radius = system.bodies[station.parent].radius
    low, high = radius + 200e3, radius + HIGH
    burn = math.sqrt(MU / low) * (math.sqrt(2.0 * high / (low + high))
                                  - 1.0)
    half = math.pi * math.sqrt((0.5 * (low + high)) ** 3 / MU)
    self.assertLess(abs(norm(guidance.way) - burn), 0.03 * burn)
    flight = guidance.arrival - guidance.depart
    self.assertLess(abs(flight - half), 0.05 * half)

  def test_refused(self) -> None:
    """On the pad it will not start (not in orbit), nor docked, nor
    before its sums are ready."""
    system, station, port, vessel, keeper, guidance = self._ready(200e3,
                                                                  0.0)
    padded = self.padded(system)
    self.assertIn('not', guidance.started(padded, system, keeper))
    self.assertFalse(guidance.on)
    vessel.docked = True
    self.assertIn('docked', guidance.started(vessel, system, keeper))
    vessel.docked = False
    guidance.transfers = None
    self.assertIn('ready', guidance.started(vessel, system, keeper))

  def test_low(self) -> None:
    """From 200 km up it waits, burns, coasts (its course checked),
    matches: done near the station."""
    system, station, port, vessel, keeper, guidance = self._ready(200e3,
                                                                  0.0)
    guidance.started(vessel, system, keeper)
    phases = self._flown(system, vessel, keeper, guidance)
    self.assertEqual(phases[:4], ['wait', 'burn', 'coast', 'burn'])
    self.assertEqual(phases[-2:], ['match', 'done'])
    self._arrived(system, port, vessel, keeper, guidance)

  def test_plane(self) -> None:
    """Tilted 2 degrees off the station's plane, it first turns the
    orbit into it, then goes on as from a low orbit."""
    system, station, port, vessel, keeper, guidance = self._ready(
      200e3, math.radians(2.0))
    self.assertEqual(guidance.started(vessel, system, keeper), '')
    self.assertEqual(guidance.phase, 'plane')
    self.assertAlmostEqual(norm(guidance.way), 2.0 * math.sin(
      math.radians(1.0)) * norm(vessel.velocity), -1)
    phases = self._flown(system, vessel, keeper, guidance)
    self.assertEqual(phases[1], 'wait')
    self._arrived(system, port, vessel, keeper, guidance)
    self.assertLess(guidance._tilt(vessel, keeper), PLANE_SAME)

  def test_phasing(self) -> None:
    """At the station's own height (it never comes round on its own) a
    phasing orbit brings the rocket back to where it burnt as the
    station's point gets there."""
    system, station, port, vessel, keeper, guidance = self._ready(HIGH,
                                                                  0.0)
    self.assertEqual(guidance.started(vessel, system, keeper), '')
    self.assertGreater(guidance.reach, 0.0)
    self._flown(system, vessel, keeper, guidance)
    self._arrived(system, port, vessel, keeper, guidance)
