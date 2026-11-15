"""
TestWall covers the oval's safety barrier ('OvalWall', the ground's
'wall'): a place's depth through its face and the face's outward
normal on the straights and round the turns; a box slid into it on
flat ground stops at its face, the kernel as the plain Python (to
1e-12), the books balanced (the heat the energy lost, within 0.1 %);
over its top it holds nothing; the car steered into the oval's
barrier at 20 m/s stays inside it, scraping along it; and drawn
('wallMesh'), its face's foot is a blue stripe meeting the white above
on one edge.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys import LIVE, Assembly, Body, Books, Ground, State, World
from worQt.phys import boxShape, carBuilt, drive, ovalWorld, steer
from worQt.phys._car import carPlaced
from worQt.phys._terrain import OVAL_WALL_OUT, OvalWall, oval, ovalAt
from worQt.phys._terrain import ovalPlaceOf, ovalWall

from . import PhysTest

WALL = OvalWall(10.0, 10.0, 2.0, 1.0, 0.5)
GROUND = Ground(1e5, 1.0, 0.5, 1e5, 100.0, 0.0, None, WALL)
BOX = Body.of(boxShape(1.0, 1.0, 1.0), 100.0)
SUNK = 100.0 * 9.81 / (4 * 1e5)


class TestWall(PhysTest):
  """Tests for the oval's safety barrier."""

  def test_beyond(self) -> None:
    """On the front straight the face stands 'out' m to the right of
    the middle line (-y), on the back straight to the left of it (+y,
    past twice the radius), round the turns 'out' m past their radius;
    the normal points out of the oval."""
    for (x, y), depth, normal in (
            ((0.0, -2.5), 0.5, (0.0, -1.0)),
            ((0.0, 23.0), 1.0, (0.0, 1.0)),
            ((10.0 + 12.0, 10.0), 0.0, (1.0, 0.0)),
            ((-10.0, 10.0 - 13.0), 1.0, (0.0, -1.0))):
      found = WALL.beyond(x, y)
      self.assertNear(found, (depth, *normal), 1e-12)

  def test_box(self) -> None:
    """A 100 kg box slid at 5 m/s at the wall on flat ground stops at
    it (bounced back off its face a little and held by the ground: its
    side within 10 cm of it, 7.3 when measured, all but still 1.5 s
    later); the kernel as the plain Python; the heat booked the energy
    lost, within 0.1 % (0.02)."""
    start = (State((0.0, 0.0, 0.5 - SUNK), (1.0, 0.0, 0.0, 0.0),
                   (2.0, -5.0, 0.0)),)
    alone = Assembly((BOX,), ())
    ran = []
    for compiled in (False, True):
      world = World((0.0, 0.0, -9.81), 1e-3, GROUND, None, compiled)
      ran.append(world.booked(alone, start, 1.5, 0.0, Books()))
    (python, books), (kernel, _) = ran
    self.assertNear(kernel[0].place, python[0].place, 1e-12)
    self.assertNear(kernel[0].velocity, python[0].velocity, 1e-12)
    self.assertNear(python[0].place[1] - 0.5, -2.0, 0.1)
    self.assertLess(math.hypot(*python[0].velocity), 0.05)
    world = World((0.0, 0.0, -9.81), 1e-3, GROUND)
    lost = sum(world.storedOf(alone, start)) - sum(
      world.storedOf(alone, python))
    self.assertNear(books.ground, lost, 1e-3 * lost)

  def test_over(self) -> None:
    """Over the wall's top, or inside its face, the ground holds a
    point by the ground alone."""
    for place in ((0.0, -2.5, 1.5), (0.0, -1.5, -0.1)):
      self.assertEqual(GROUND.wallPush(place, (0.0, -1.0, 0.0)),
                       (0.0, 0.0, 0.0))
    push = GROUND.wallPush((0.0, -2.1, 0.5), (0.0, 0.0, 0.0))
    self.assertNear(push, (0.0, 1e4, 0.0), 1e-9)

  def test_car(self) -> None:
    """The car set down on the oval's front straight 3 m inside its
    barrier, going 20 m/s along it and steered right into it for three
    seconds (at 'LIVE' fidelity), hits it and scrapes along it, no
    wheel's middle ever more than 5 cm past its face, slowing."""
    car, world = carBuilt(0.5, LIVE), ovalWorld(LIVE)
    terrain = world.ground.terrain
    x, y, _ = ovalAt(200.0, OVAL_WALL_OUT - 3.0)
    states = carPlaced(car.states, (x, y, terrain.heightAt(x, y)),
                       terrain.normalAt(x, y))
    states = tuple(State(s.place, s.turn, (20.0, 0.0, 0.0),
                         (0.0, 20.0 / 0.316, 0.0) if index in car.wheels
                         else s.spin, s.bristles, s.holds, s.rest)
                   for index, s in enumerate(states))
    frame, most = 1.0 / 60.0, -math.inf
    for count in range(180):
      steer(car, -0.25)
      drive(car, states, 0.0, frame)
      states = world.advancedAll(car.assembly, states, frame,
                                 count * frame)
      most = max(most, max(ovalPlaceOf(states[w].place[0],
                                       states[w].place[1])[0]
                           for w in car.wheels))
    steer(car, 0.0)
    self.assertGreater(most, OVAL_WALL_OUT - 0.15)
    self.assertLess(most, OVAL_WALL_OUT + 0.05)
    self.assertLess(math.hypot(*states[car.chassis].velocity[:2]), 10.0)

  def test_drawn(self) -> None:
    """The oval's barrier drawn ('wallMesh'): every triangle wound to
    face out of it; the blue stripe's corners on its face, from its foot
    up 'WALL_STRIPE' m; the white's on the face no lower than that (the
    two meet on one edge, neither covering the other)."""
    from worQt.phys.gui._meshes import SCALE, WALL_STRIPE, wallMesh
    terrain, wall = oval(1.0), ovalWall()
    rows, white, blue = wallMesh(terrain, wall)
    scene = numpy.array(rows[:, :3], numpy.float64) / SCALE
    normals = numpy.array(rows[:, 3:6], numpy.float64)
    for indices in (white, blue):
      corners = indices.reshape(-1, 3)
      at = scene[corners]
      facing = numpy.cross(at[:, 1] - at[:, 0], at[:, 2] - at[:, 0])
      self.assertTrue(bool((numpy.einsum(
        'ij,ij->i', facing, normals[corners[:, 0]]) > 0.0).all()))
    x, y, z = scene[:, 0], -scene[:, 2], scene[:, 1]
    rise = z - numpy.array([terrain.heightAt(a, b) for a, b in zip(x, y)])
    depth = numpy.array([wall.beyond(a, b)[0] for a, b in zip(x, y)])
    stripe = numpy.unique(blue)
    self.assertLess(float(numpy.abs(depth[stripe]).max()), 1e-4)
    self.assertGreater(float(rise[stripe].min()), -1e-4)
    self.assertLess(float(rise[stripe].max()), WALL_STRIPE + 1e-4)
    corners = white.reshape(-1, 3)
    level = normals[corners[:, 0], 1] == 0.0
    onFace = (numpy.abs(depth[corners]).max(axis=1) < 1e-3) & level
    toward = numpy.array([
      normals[k, 0] * wall.beyond(x[k], y[k])[1]
      - normals[k, 2] * wall.beyond(x[k], y[k])[2] < 0.0
      for k in corners[:, 0]])
    face = corners[onFace & toward]
    self.assertEqual(len(face), len(blue) // 3)
    self.assertGreater(float(rise[face].min()), WALL_STRIPE - 1e-4)
