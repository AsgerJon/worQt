"""
TestGridWall covers walls laid on a grid from how tall things stand
along a road ('_gridwall'; user, 2026-11-15, uncannyball's town: "What
counts as a wall for the car comes from the standing heights"): a
straight road written here, a row of houses beyond its right edge, a
tree over its middle; the houses walled (their face where they begin,
within a cell; the way out of them toward the road; their height), the
road and the tree over it open; the ground's law pushing a point in
the wall back out toward the road, nothing over its top; in the small
steps a box and a ball thrown at the houses stopped at their face, a
ball thrown over their roofs going on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.phys import Assembly, Body, Ground, SmallSteps, Sphere, State
from worQt.phys import boxShape
from worQt.phys._crg import CrgTrack
from worQt.phys._gridwall import standingWall

from . import PhysTest

#  The road: its rows' spacing and count (along x from nought), its
#  columns' (across, right to left, about y nought), m; its edges
#  either side; how tall the houses beyond its right edge stand and
#  where they begin (y), the tree over its middle (its height, the
#  rows it stands over), m; the walls' threshold and corridor, m.
STEP, ROWS = 0.4, 101
ACROSS = numpy.round(numpy.arange(-12.0, 12.0001, 0.4), 6)
EDGE, HOUSE, HOUSE_AT = 4.0, 4.0, -6.0
TREE, TREE_ROWS = 8.0, (40, 50)
LEAST, CORRIDOR = 3.5, 3.0
GRAVITY = (0.0, 0.0, -9.81)


def _road() -> tuple:
  """Returns the road (a 'CrgTrack' on level ground) and how tall
  things stand along it (the same rows)."""
  count = len(ACROSS)
  x = STEP * numpy.arange(ROWS)
  zeros = numpy.zeros(ROWS)
  ones = numpy.ones(ROWS)
  ground = numpy.zeros((ROWS, count), numpy.float32)
  standing = numpy.zeros((ROWS, count), numpy.float32)
  standing[:, ACROSS <= HOUSE_AT + 1e-9] = HOUSE
  standing[TREE_ROWS[0]:TREE_ROWS[1], numpy.abs(ACROSS) <= 2.0] = TREE
  heading = zeros[:-1]
  track = CrgTrack(STEP, x, zeros, zeros, ones, ACROSS, ground, heading)
  tall = CrgTrack(STEP, x, zeros, zeros, ones, ACROSS, standing, heading)
  return track, tall


def _wall() -> object:
  """Returns the walls by the road, on a grid of 0.5 m cells about it."""
  track, tall = _road()
  edges = (numpy.full(ROWS, EDGE), numpy.full(ROWS, EDGE))
  return standingWall(track, tall, edges, ((-5.0, -15.0), 0.5, (101, 61)),
                      LEAST, CORRIDOR, 0.5)


class TestGridWall(PhysTest):
  """Tests for walls on a grid (a few seconds)."""

  def test_walled(self) -> None:
    """The houses are walled from where they begin (within a cell), the
    way out of them toward the road, as tall as they stand; the road,
    and the tree over its middle, open."""
    wall = _wall()
    for x in (8.0, 18.0, 30.0):
      self.assertLess(wall.beyond(x, 0.0)[0], -2.5)
      self.assertLess(wall.beyond(x, HOUSE_AT + 1.0)[0], 0.0)
      depth, nx, ny = wall.beyond(x, HOUSE_AT - 2.0)
      self.assertGreater(depth, 1.0)
      self.assertLess(ny, -0.95)
      self.assertNear(wall.heightAt(x, HOUSE_AT - 2.0), HOUSE, 1e-3)
      self.assertEqual(wall.heightAt(x, 0.0), 0.0)
      face = [y for y in numpy.arange(-4.0, -8.0, -0.01)
              if wall.beyond(x, float(y))[0] > 0.0][0]
      self.assertNear(face, HOUSE_AT, 0.6)
    self.assertLess(wall.beyond(-30.0, 0.0)[0], -1.0)

  def test_ground(self) -> None:
    """The ground's law: a point 2 m into the houses, under their top,
    is pushed back toward the road; over their top, not at all."""
    ground = Ground(1e5, 1.0, 0.5, 1e5, 100.0, 0.0, None, _wall())
    depth, normal = ground.wallOf((20.0, HOUSE_AT - 0.5, 1.0))
    self.assertGreater(depth, 0.0)
    self.assertLess(normal[1], -0.95)
    push = ground.wallPush((20.0, HOUSE_AT - 0.5, 1.0), (0.0, 0.0, 0.0))
    self.assertGreater(push[1], 0.0)
    self.assertEqual(ground.wallOf((20.0, HOUSE_AT - 0.5, HOUSE + 0.5)),
                     (0.0, (0.0, 0.0, 0.0)))
    self.assertNear(ground.topOf(), HOUSE, 1e-3)

  def test_small_steps(self) -> None:
    """Thrown at the houses at 6 m/s from 1.5 m off, a 30 cm box and a
    30 cm ball stop at their face, neither through it by more than a cell's smoothing
    (10 cm); a ball thrown at them 7 m up (over their 4 m roofs, staying
    over them) goes on past where they begin."""
    world = SmallSteps(GRAVITY, Ground(1e5, 1.0, 0.5, 1e5, 100.0, 0.0,
                                       None, _wall()),
                       2.5e-4, 1, 0.0, 'cpu')
    wall = world.ground.wall
    face = [y for y in numpy.arange(-4.0, -8.0, -0.01)
            if wall.beyond(20.0, float(y))[0] > 0.0][0]
    box = Body.of(boxShape(0.3, 0.3, 0.3), 2000.0)
    ball = Body.of(Sphere(0.15), 2000.0)
    for body, lift, through in ((box, 0.16, False), (ball, 0.16, False),
                                (ball, 7.0, True)):
      start = State((20.0, face + 1.5, lift), (1.0, 0.0, 0.0, 0.0),
                    (0.0, -6.0, 0.0))
      after = world.advancedAll(Assembly((body,), ()), (start,), 0.6)
      reach = after[0].place[1] - 0.15
      with self.subTest(lift=lift, ball=body is ball):
        if through:
          self.assertLess(reach, face - 0.5)
        else:
          self.assertGreater(reach, face - 0.1)
          self.assertGreater(after[0].velocity[1], -0.5)
