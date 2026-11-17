"""
TestStation covers the space station (user, 2026-11-17: "a space station
in orbit. One that needs no fucking magic for its gravity. Think 2001";
"1800m"; "300m antennas ... RGB lighting ... visible from the gorund"):
its turning pulls one g on its deck, once a minute; it goes round
Terra in a circle 400 km up over the equator, over the pad as the game
opens, kept by the system's leaps; its shape (1.8 km across, the
antennas 300 m, the port on its axis, every face outward); seen from
the ground its lights are points, hidden behind Terra; in Terra's
shadow the sun's light is gone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._planets import PAD
from worQt.gaming.space._scenery import Scenery
from worQt.gaming.space._station import FLOOR_RADIUS, HIGH, SPIN, Station
from worQt.gaming.space._stationmeshes import ANTENNA, HULL, TUBE
from worQt.gaming.space._stationmeshes import TUBE_MIDDLE, portTip
from worQt.gaming.space._stationmeshes import stationMeshes
from worQt.gaming.space._turns import norm
from worQt.gaming.space._vessel import Vessel

from . import SpaceTest

#  A look from the rocket's middle (no offset), along x, z up.
SEEN = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


class TestStation(SpaceTest):
  """Tests for the space station."""

  def test_gravity(self) -> None:
    """It turns once a minute, its deck pulled one g by it alone."""
    self.assertAlmostEqual(2.0 * math.pi / SPIN, 60.0, 9)
    self.assertAlmostEqual(SPIN ** 2 * FLOOR_RADIUS, G0, 9)
    self.assertAlmostEqual(HULL, 8.0, 9)

  def test_orbit(self) -> None:
    """A circle 400 km over the equator, overhead the pad at time
    nought; one of the system's satellites, kept across a leap."""
    system = self.systemOf()
    station = Station(system)
    terra = system.bodies[station.parent]
    self.assertIn(station.body, system.satellites)
    for t in (0.0, 1000.0, 3000.0):
      place, velocity = station.stateAt(t)
      self.assertAlmostEqual(norm(place) - terra.radius, HIGH, 0)
      self.assertAlmostEqual(sum(p * q for p, q in zip(place,
                                                       terra.pole)), 0.0, 0)
      self.assertAlmostEqual(norm(velocity), math.sqrt(
        terra.mu / norm(place)), 3)
    vessel = Vessel()
    vessel.stood(system, station.parent, PAD[0], PAD[1], 0.0)
    over = station.stateAt(0.0)[0]
    up = tuple(x / norm(vessel.place) for x in vessel.place)
    self.assertAlmostEqual(sum(o * u for o, u in zip(over, up)),
                           norm(over), 0)
    before = station.stateAt(700.0)[0]
    system.fold(700.0)
    self.assertClose(station.stateAt(0.0)[0], before, 1e-3)

  def test_shape(self) -> None:
    """1.8 km across; its antennas 300 m out of the ring; its port on its
    axis; every face outward (but a ball's poles)."""
    meshes = stationMeshes()
    hull = meshes['hull'][0]
    across = numpy.hypot(hull[:, 0], hull[:, 1]).max()
    self.assertAlmostEqual(2.0 * across, 2.0 * (TUBE_MIDDLE + TUBE), 3)
    self.assertGreater(2.0 * across, 1790.0)
    reach = numpy.linalg.norm(meshes['antennas'][0][:, :3], axis=1).max()
    self.assertAlmostEqual(reach, FLOOR_RADIUS + HULL + ANTENNA[0], 0)
    self.assertEqual(portTip()[:2], (0.0, 0.0))
    self.assertGreater(portTip()[2], 0.0)
    for name, (rows, faces) in meshes.items():
      a, b, c = (rows[faces[k::3], :3] for k in range(3))
      normal = numpy.cross(b - a, c - a)
      way = sum(rows[faces[k::3], 3:6] for k in range(3))
      along = numpy.einsum('ij,ij->i', normal, way)
      flat = numpy.linalg.norm(normal, axis=1) < 1e-9
      self.assertTrue(((along > 0.0) | flat).all(), name)

  def test_seen(self) -> None:
    """From the pad as it passes over, its lights are points (it is far);
    once it is below the horizon, hidden by Terra."""
    system = self.systemOf()
    Station(system)
    vessel = Vessel()
    terra = system.named('Terra')
    vessel.stood(system, terra, PAD[0], PAD[1], 60.0)
    frame = Scenery().flightOf(system, vessel, SEEN, 60.0)
    self.assertEqual(len(frame['satellites']), 1)
    self.assertEqual(len(frame['lights']), 6)
    vessel.stood(system, terra, PAD[0], PAD[1], 1500.0)
    frame = Scenery().flightOf(system, vessel, SEEN, 1500.0)
    self.assertEqual(frame['lights'], [])

  def test_shadow(self) -> None:
    """In Terra's shadow no sunlight reaches the eye; on its day side,
    all of it, and the ground's light thrown back up."""
    system = self.systemOf()
    terra = system.named('Terra')
    body = system.bodies[terra]
    sol = system.relative(0, terra, 0.0)[0]
    toward = tuple(s / norm(sol) for s in sol)
    scenery = Scenery()
    away = tuple(-x for x in toward)
    for side, lit in ((toward, 1.0), (away, 0.0)):
      eye = tuple((body.radius + 400e3) * x for x in side)
      shine, earth = scenery._litOf(body, eye, away)
      self.assertAlmostEqual(shine, lit, 6, side)
      if lit:
        self.assertGreater(earth[1], 0.2)
      else:
        self.assertLess(earth[1], 0.01)
