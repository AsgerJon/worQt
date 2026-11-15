"""
TestTerrain covers the ground shaped by a terrain ('Terrain'): its
heights are bilinear between the grid's and its normal is the slope's;
a ball let go on a 10 degree slope rolls down at five sevenths of
gravity's share along it (within 1 %: the bristles hold it along the
level), the kernel as the plain Python; and the car ('trackWorld')
drives over the track's three speed humps (past the last, its far
side at x 28.6), its chassis riding between a quarter and a half metre
over the ground, no wheel leaning past 5 degrees; the oval is a mile,
banked as built, its height smooth all the way round (no step where the
lap starts over), its surfaces drawn following its curves, the flat
ground about it leaving out its grid exactly, and the car stands on its
bank.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys import Assembly, Body, Ground, Sphere, State, World
from worQt.phys import camberOf, carBuilt, drive, plus, scaled, steer
from worQt.phys._car import carPlaced, ovalWorld, speedOf, trackWorld
from worQt.phys._terrain import OVAL_RADIUS, OVAL_STRAIGHT, Terrain, oval
from worQt.phys._terrain import ASPHALT, OVAL_RUNOFF, PAVED, ovalAcross
from worQt.phys._terrain import ovalAt

from . import PhysTest

SLOPE = math.radians(10.0)


def plane(index: int) -> float:
  """The 'plane' function returns the slope's height at grid line
  'index' (falling along x at 'SLOPE')."""
  return 3.0 - (-20.0 + 0.5 * index) * math.tan(SLOPE)


TILTED = Terrain((-20.0, -20.0), 0.5,
                 tuple(tuple(plane(i) for _ in range(81))
                       for i in range(81)))


class TestTerrain(PhysTest):
  """Tests for the terrain and the car on its track."""

  #  The springs' world's car, stepped in its world's one thread: minutes
  #  a class (killed at the harness's 30 s, the user's run of 2026-11-14).
  __time_out__ = 3600.0

  def test_heights(self) -> None:
    """Between the grid's heights the ground is bilinear, its normal
    the slope's; off the grid it is flat at nought."""
    x = 0.3
    self.assertNear(TILTED.heightAt(x, 0.7), 3.0 - x * math.tan(SLOPE),
                    1e-12)
    self.assertNear(TILTED.normalAt(x, 0.7),
                    (math.sin(SLOPE), 0.0, math.cos(SLOPE)), 1e-12)
    self.assertEqual(TILTED.heightAt(30.0, 0.0), 0.0)

  def test_ball_rolls_down(self) -> None:
    """A ball let go on the slope rolls down it at five sevenths of
    gravity's share along it, within 1 %, the kernel as the plain
    Python."""
    ball = Body.of(Sphere(0.1), 1000.0)
    ground = Ground(1e5, 1.0, 0.8, 1e5, 100.0, 0.0, TILTED)
    normal = TILTED.normalAt(0.0, 0.0)
    sunk = ball.mass * 9.81 * normal[2] / ground.stiffness
    start = State(plus((0.0, 0.0, TILTED.heightAt(0.0, 0.0)),
                       scaled(normal, 0.1 - sunk)))
    rolled = []
    for compiled in (False, True):
      world = World((0.0, 0.0, -9.81), 1e-3, ground, None, compiled)
      rolled.append(world.advancedAll(Assembly((ball,), ()), (start,),
                                      1.0)[0])
    speed = math.hypot(rolled[0].velocity[0], rolled[0].velocity[2])
    wanted = 5.0 / 7.0 * 9.81 * math.sin(SLOPE)
    self.assertNear(speed, wanted, 0.01 * wanted)
    self.assertNear((rolled[0].place, rolled[0].velocity),
                    (rolled[1].place, rolled[1].velocity), 1e-12)

  def test_car_over_humps(self) -> None:
    """At 10 m/s the car goes over the track's three speed humps, its
    chassis riding between 0.25 and 0.5 m over the ground, no wheel
    leaning past 5 degrees (driven at 480 N m: 0.4 of the rear wheel
    drive's 1200, as 0.3 of the four wheel drive's 1600 was)."""
    car = carBuilt(0.5)
    world = trackWorld()
    terrain = world.ground.terrain
    states = []
    for index, state in enumerate(car.states):
      spin = (0.0, 10.0 / 0.316, 0.0) if index in car.wheels else (
        state.spin)
      states.append(State(state.place, state.turn, (10.0, 0.0, 0.0),
                          spin))
    states = tuple(states)
    frame = 1.0 / 60.0
    for _ in range(150):
      steer(car, 0.0)
      drive(car, states, 0.4, frame)
      states = world.advancedAll(car.assembly, states, frame)
      chassis = states[car.chassis].place
      over = chassis[2] - terrain.heightAt(chassis[0], chassis[1])
      self.assertGreater(over, 0.25)
      self.assertLess(over, 0.5)
      for corner in range(4):
        self.assertLess(abs(math.degrees(camberOf(car, states, corner))),
                        5.0)
    self.assertGreater(states[car.chassis].place[0], 28.65)

  def test_oval(self) -> None:
    """The oval is a mile round its middle line; at the middle of each
    straight its ground leans 9 degrees and at each turn's apex 24, its
    normal leaning in toward the infield; its racing surface is
    concrete, the apron below it asphalt, its infield not paved."""
    self.assertNear(2.0 * OVAL_STRAIGHT + 2.0 * math.pi * OVAL_RADIUS,
                    1609.3, 0.1)
    ground = oval(1.0)
    half, radius = 0.5 * OVAL_STRAIGHT, OVAL_RADIUS
    for (x, y), bank, inward in (((0.0, 0.0), 9.0, (0.0, 1.0)),
                                 ((half + radius, radius), 24.0,
                                  (-1.0, 0.0)),
                                 ((0.0, 2.0 * radius), 9.0, (0.0, -1.0)),
                                 ((-half - radius, radius), 24.0,
                                  (1.0, 0.0))):
      normal = ground.normalAt(x, y)
      self.assertNear(math.degrees(math.acos(normal[2])), bank, 0.05)
      self.assertGreater(normal[0] * inward[0] + normal[1] * inward[1],
                         0.0)
    for (x, y), paved in (((0.0, 0.0), PAVED), ((0.0, 8.8), ASPHALT),
                          ((0.0, radius), 0)):
      i = round((x - ground.origin[0]) / ground.cell)
      j = round((y - ground.origin[1]) / ground.cell)
      self.assertEqual(ground.paved[i][j], paved)

  def test_oval_smooth(self) -> None:
    """Round the oval's middle line, a tenth of a metre at a time, its
    height never steps more than a centimetre: the banking eases out of
    the last turn into the front straight past where the lap starts
    over (user: "the end of turn four has a crazy sharp drop": it fell
    1.4 m within a metre there)."""
    ground = oval(1.0)
    before = None
    for step in range(int(10.0 * 1609.3) + 1):
      x, y, _ = ovalAt(0.1 * step, 0.0)
      height = ground.heightAt(x, y)
      if before is not None:
        self.assertLess(abs(height - before), 0.01)
      before = height

  def test_track_mesh(self) -> None:
    """The oval's surfaces drawn as their own mesh ('ovalTrackMesh'),
    following its curves: every triangle faces up; the asphalt's lie
    between the apron's inner edge and the banking's foot, the
    concrete's between that and the run-off's outer edge (to a tenth of
    a millimetre, single precision: their edges are curves, not a
    metre's steps); the
    terrain's grid squares under it are left out of the terrain's mesh
    ('terrainMesh''s 'dropped')."""
    from worQt.phys.gui._meshes import SCALE, ovalTrackMesh, terrainMesh
    ground = oval(1.0)
    vertices, margins, paved, asphalt, covered = ovalTrackMesh(ground,
                                                               2.0)
    places = numpy.array(vertices[:, :3], numpy.float64) / SCALE
    for indices in (margins, paved, asphalt):
      corners = places[indices.reshape(-1, 3)]
      facing = numpy.cross(corners[:, 1] - corners[:, 0],
                           corners[:, 2] - corners[:, 0])
      self.assertTrue(bool((facing[:, 1] > 0.0).all()))
    for indices, low, high in ((asphalt, 'apron', 0.0),
                               (paved, 0.0, 'top')):
      at = places[numpy.unique(indices)]
      inner, width, apron, _ = ovalAcross(at[:, 0], -at[:, 2])
      lowest = -apron if low == 'apron' else low
      highest = width + OVAL_RUNOFF if high == 'top' else high
      self.assertTrue(bool((inner >= lowest - 1e-4).all()))
      self.assertTrue(bool((inner <= highest + 1e-4).all()))
    whole = terrainMesh(ground._replace(paved=None), 2.0)[1]
    kept = terrainMesh(ground._replace(paved=None), 2.0, covered)[1]
    self.assertLess(len(kept), len(whole))

  def test_flat_ground(self) -> None:
    """The flat ground about a terrain ('groundMesh') leaves out its
    grid exactly, the oval's (not square about the origin) too: every
    triangle faces up, none lies over the grid, and they cover all the
    rest (its area); with no grid, all of it."""
    from worQt.phys.gui._meshes import SCALE, groundMesh
    ground, outer = oval(1.0), 2000.0
    (x0, y0), cell = ground.origin, ground.cell
    hole = (x0, y0, x0 + cell * (len(ground.heights) - 1),
            y0 + cell * (len(ground.heights[0]) - 1))
    for gap in (hole, None):
      vertices, indices = groundMesh(gap, outer, 2.0)
      corners = (numpy.array(vertices[:, :3], numpy.float64)
                 / SCALE)[indices.reshape(-1, 3)]
      facing = numpy.cross(corners[:, 1] - corners[:, 0],
                           corners[:, 2] - corners[:, 0])
      self.assertTrue(bool((facing[:, 1] > 0.0).all()))
      left = (2.0 * outer) ** 2
      if gap is not None:
        left -= (gap[2] - gap[0]) * (gap[3] - gap[1])
        middle = corners.mean(axis=1)
        inside = ((middle[:, 0] > gap[0]) & (middle[:, 0] < gap[2])
                  & (-middle[:, 2] > gap[1]) & (-middle[:, 2] < gap[3]))
        self.assertFalse(bool(inside.any()))
      self.assertNear(0.5 * facing[:, 1].sum(), left, 1.0)

  def test_car_on_the_bank(self) -> None:
    """Set down on the oval's start line, on its straight's 9 degree
    bank, the car stands: a second later it has moved under 2 cm and is
    all but still."""
    car = carBuilt(0.5)
    world = ovalWorld()
    terrain = world.ground.terrain
    start = (0.0, 0.0, terrain.heightAt(0.0, 0.0))
    states = carPlaced(car.states, start, terrain.normalAt(0.0, 0.0))
    before = states[car.chassis].place
    for _ in range(60):
      steer(car, 0.0)
      drive(car, states, 0.0, 1.0 / 60.0)
      states = world.advancedAll(car.assembly, states, 1.0 / 60.0)
    after = states[car.chassis]
    self.assertNear(after.place[:2], before[:2], 0.02)
    self.assertLess(abs(speedOf(car, states)), 0.05)
    self.assertLess(math.hypot(*after.velocity), 0.05)
