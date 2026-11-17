"""
TestApproach covers the closest approach to the space station, a
try-hard's aid for the rendezvous by hand (user, 2026-11-17: "we include
buttons so that a try-hard *could* manually do the thing"): out of the
station's plane by 5 km, moving as it does, the rocket crosses it a
quarter turn later, near; on its way after the rendezvous's burn it
passes near the station as it arrives; none round another body or
docked; the map marks it, its labels never covering each other.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._approach import closestApproach
from worQt.gaming.space._conic import Conic
from worQt.gaming.space._orrery import LETTER, LINE, Orrery, _uncrowded
from worQt.gaming.space._rendezvousguidance import RendezvousGuidance
from worQt.gaming.space._station import Station
from worQt.gaming.space._timekeeper import Timekeeper
from worQt.gaming.space._transfers import Transfers
from worQt.gaming.space._turns import cross, unit
from worQt.gaming.space._vessel import Vessel

from . import SpaceTest


class TestApproach(SpaceTest):
  """Tests for the closest approach."""

  def _beside(self, out: float) -> tuple:
    """Returns a system, its station and a vessel 'out' m from the
    station out of its path's plane, moving as it does."""
    system = self.systemOf()
    station = Station(system)
    middle, velocity = station.stateAt(0.0)
    axis = unit(cross(middle, velocity))
    vessel = Vessel()
    vessel.placed(station.parent, tuple(m + out * a for m, a in zip(
      middle, axis)), velocity, (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    return system, station, vessel

  def test_crossing(self) -> None:
    """5 km out of the station's path's plane, moving as it does, the
    rocket crosses the plane a quarter turn later within 20 m of the station,
    passing at 5 km times the turning rate."""
    system, station, vessel = self._beside(5000.0)
    wait, gap, speed, _, _ = closestApproach(vessel, system, station, 0.0)
    middle = station.stateAt(0.0)[0]
    turn = 2.0 * math.pi * math.sqrt(math.dist(middle, (0.0, 0.0, 0.0))
                                     ** 3 / system.bodies[
      station.parent].mu)
    self.assertAlmostEqual(wait, 0.25 * turn, delta=1.0)
    self.assertLess(gap, 20.0)
    self.assertAlmostEqual(speed, 5000.0 * 2.0 * math.pi / turn,
                           delta=0.05)

  def test_none(self) -> None:
    """None docked, none on the pad's ground without a path."""
    system, station, vessel = self._beside(5000.0)
    vessel.docked = True
    self.assertIsNone(closestApproach(vessel, system, station, 0.0))
    padded = self.padded(system)
    padded.placed(padded.anchor, padded.place, (0.0, 0.0, 0.0),
                  padded.turn, padded.spin)
    self.assertIsNone(closestApproach(padded, system, station, 0.0))

  def test_transfer(self) -> None:
    """After the rendezvous's burn from 200 km up, the closest approach
    comes as it arrives (within a minute), within 3 km."""
    system = self.systemOf()
    station = Station(system)
    vessel = self.orbiting(system, 200e3, 200e3, 'ahead')
    keeper = Timekeeper(system)
    guidance = RendezvousGuidance(station)
    guidance.transfers = Transfers('cpu')
    self.assertEqual(guidance.started(vessel, system, keeper), '')
    wait = guidance.depart - keeper.elapsed
    mu = system.bodies[vessel.anchor].mu
    place, velocity = Conic.fromState(mu, vessel.place,
                                      vessel.velocity).stateAt(wait)
    vessel.placed(vessel.anchor, place, tuple(
      v + w for v, w in zip(velocity, guidance.way)), vessel.turn,
                  vessel.spin)
    found = closestApproach(vessel, system, station, wait)
    self.assertIsNotNone(found)
    self.assertAlmostEqual(found[0], guidance.arrival - guidance.depart,
                           delta=60.0)
    self.assertLess(found[1], 3000.0)

  def test_marks(self) -> None:
    """The map marks the closest approach; its labels never cover each
    other, the closest's next to its own dot."""
    system, station, vessel = self._beside(5000.0)
    orrery = Orrery()
    orrery.opened(vessel, system)
    orrery.closest = closestApproach(vessel, system, station, 0.0)
    marks = orrery.marksOf(vessel, system, 0.0, 1280.0, 720.0)
    closest = [m for m in marks if m['text'].startswith('Closest')]
    self.assertEqual(len(closest), 1)
    crowd = _uncrowded([{'x': 100.0, 'y': 100.0, 'text': 'Ap 400 km'},
                        {'x': 101.0, 'y': 100.0, 'text': 'Closest 2 km'},
                        {'x': 102.0, 'y': 101.0, 'text': 'Station'}])
    self.assertEqual([m['line'] for m in crowd], [0, 1, -1])
    boxes = [(m['x'], m['y'] + LINE * m['line'],
              LETTER * len(m['text'])) for m in crowd]
    for k, (x, y, w) in enumerate(boxes):
      for x2, y2, w2 in boxes[:k]:
        self.assertFalse(abs(y - y2) < LINE - 2.0 and x < x2 + w2
                         and x2 < x + w)
