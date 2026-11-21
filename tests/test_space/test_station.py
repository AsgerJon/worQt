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
from worQt.gaming.space._stationmeshes import TUBE_MIDDLE, beaconTips
from worQt.gaming.space._stationmeshes import DRUM_HALF, SOCKET, portTip
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
    self.assertIn(station, system.satellites)
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

  def test_glass(self) -> None:
    """The ring's glass lies in the hull's place where it is glazed (user,
    2026-11-21: "The glass roof on the ring renders with collisions when
    seen from the outside": laid a hair off the hull, they fought): no
    hull face there, the glass on the hull's own radius, its edges the
    hull's (no gap, no overlap), facing out."""
    from worQt.gaming.space._stationmeshes import GLAZED
    meshes = stationMeshes()
    hull, faces = meshes['hull'][0], meshes['hull'][1]
    middles = hull[faces[:len(faces) // 3 * 3]].reshape(-1, 3, 8)
    middles = middles[:, :, :3].mean(axis=1)
    ring = numpy.hypot(middles[:, 0], middles[:, 1]) > TUBE_MIDDLE - TUBE
    out = numpy.hypot(middles[ring, 0], middles[ring, 1]) - TUBE_MIDDLE
    round_ = numpy.arctan2(middles[ring, 2], out) % (2.0 * math.pi)
    glazed = (round_ > GLAZED + 1e-6) & (round_ < 2.0 * math.pi - GLAZED
                                         - 1e-6)
    self.assertFalse(glazed.any())
    glass = meshes['windows'][0]
    across = numpy.hypot(numpy.hypot(glass[:, 0], glass[:, 1])
                         - TUBE_MIDDLE, glass[:, 2])
    self.assertLess(numpy.abs(across - TUBE).max(), 1e-6)
    edge = glass[numpy.isclose(numpy.abs(numpy.arctan2(
      glass[:, 2], numpy.hypot(glass[:, 0], glass[:, 1]) - TUBE_MIDDLE)),
      GLAZED)][:, :3]
    shell = hull[:, :3]
    for point in edge[::37]:
      self.assertLess(numpy.linalg.norm(shell - point, axis=1).min(), 1e-6)

  def test_spoke_lamps(self) -> None:
    """The spokes are lit (user, 2026-11-19: "we need illuminated
    spokes"): a lamp on each corner of each girder's every frame, from
    inside the drum to the ring, shining of its own."""
    from worQt.gaming.space._spaceviewport import STATION_LOOKS
    from worQt.gaming.space._stationmeshes import BAY, CORNERS, GIRDER
    from worQt.gaming.space._stationmeshes import SPOKE_LAMP, SPOKES
    from worQt.gaming.space._stationmeshes import _girderSpan
    rows, faces = stationMeshes()['spoke lamps']
    start, end, bays = _girderSpan()
    lamps = SPOKES[0] * (bays + 1) * len(CORNERS)
    self.assertEqual(len(faces), 36 * lamps)
    middles = rows[:, :3].reshape(lamps, -1, 3).mean(axis=1)
    out = numpy.max(numpy.abs(middles[:, :2]), axis=1)
    self.assertAlmostEqual(float(out.min()), start, 6)
    self.assertGreater(float(out.max()), end - BAY - 1e-6)
    self.assertTrue(numpy.allclose(numpy.abs(middles[:, 2]), GIRDER))
    self.assertGreater(SPOKE_LAMP, 0.25)
    self.assertTrue(STATION_LOOKS['spoke lamps'][1])

  def test_shape(self) -> None:
    """1.8 km across; its antennas 300 m out of the ring, in its plane,
    none along its axis (user, 2026-11-18: "remove the antennas that are
    perpendicular to the plane of Terra Prime"), a beacon on each; the
    drum on its axis open through (user, 2026-11-19: "the head our
    rocket insert itself here"), a rocket's head in from either side
    ("docking ports on both sides"), its nose's tip past the plane;
    every face outward (but a ball's poles)."""
    meshes = stationMeshes()
    hull = meshes['hull'][0]
    across = numpy.hypot(hull[:, 0], hull[:, 1]).max()
    self.assertAlmostEqual(2.0 * across, 2.0 * (TUBE_MIDDLE + TUBE), 3)
    self.assertGreater(2.0 * across, 1790.0)
    reach = numpy.linalg.norm(meshes['antennas'][0][:, :3], axis=1).max()
    self.assertAlmostEqual(reach, FLOOR_RADIUS + HULL + ANTENNA[0], 0)
    self.assertEqual(portTip()[:2], (0.0, 0.0))
    self.assertLess(portTip()[2], 0.0)
    self.assertGreater(portTip()[2], -DRUM_HALF)
    self.assertEqual(portTip(-1.0), (0.0, 0.0, -portTip()[2]))
    self.assertAlmostEqual(hull[:, 2].max(), TUBE, 6)
    self.assertAlmostEqual(hull[:, 2].min(), -TUBE, 6)
    used = hull[numpy.unique(meshes['hull'][1])]
    flat = numpy.hypot(used[:, 0], used[:, 1])
    self.assertAlmostEqual(float(flat.min()), SOCKET, 6)
    self.assertLess(numpy.abs(meshes['antennas'][0][:, 2]).max(),
                    ANTENNA[1] + 1e-6)
    self.assertEqual(len(beaconTips()), 4)
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
    self.assertEqual(len(frame['lights']), 1 + len(beaconTips()))
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
