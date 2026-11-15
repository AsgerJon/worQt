"""
TestGround covers 'Ground', the flat ground bodies fall onto, and
'World' stepping them on it: the push grows from nought as a point
touches, more while it sinks, never pulling; a box dropped flat bounces
lower each time and rests flat, sunk as its weight on four corners
says; boxes and an L tossed tumbling come to rest square on a face;
energy never rises more than a hair; a box slid along stops as Coulomb
says, and on a slope below its grip it stands, above it slides at g
(sin - grip cos); a run in pieces is the run whole; a body without a
shape falls through.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import AXES, IDENTITY, ORIGIN, UNTURNED, Body, Ground
from worQt.phys import State, World, boxShape, norm, normalised, rotated

from . import PhysTest, lShape

GROUND = Ground()
WORLD = World((0.0, 0.0, -9.81), 1e-3, GROUND)
BOX = Body.of(boxShape(0.4, 0.3, 0.2), 1000.0)
TOSSES = (State((0.0, 0.0, 1.0), normalised((0.9, 0.2, -0.3, 0.4)),
                (1.0, 0.5, 2.0), (3.0, -6.0, 2.0)),
          State((0.0, 0.0, 0.8), normalised((0.3, 0.8, 0.1, -0.4)),
                (-0.5, 1.0, 0.0), (-8.0, 2.0, 5.0)),
          State((0.0, 0.0, 1.5), normalised((0.5, -0.5, 0.5, 0.5)),
                (0.0, 0.0, -1.0), (0.0, 10.0, 0.0)))


def tiltOf(state: State) -> float:
  """The 'tiltOf' function returns how far, in degrees, the body's own
  axis nearest upright is from it."""
  upright = max(abs(rotated(state.turn, axis)[2]) for axis in AXES)
  return math.degrees(math.acos(min(1.0, upright)))


def onSlope(degrees: float) -> World:
  """The 'onSlope' function returns the world tilted 'degrees' about y,
  so the ground is a slope falling along x."""
  slope = math.radians(degrees)
  return World((9.81 * math.sin(slope), 0.0, -9.81 * math.cos(slope)),
               1e-3, GROUND)


class TestGround(PhysTest):
  """Tests for 'Ground' and 'World' on it."""

  def test_push(self) -> None:
    """Above the ground nothing; pressed in and still, the stiffness
    times the depth; more while sinking, less while rising, and never
    pulling."""
    self.assertEqual(GROUND.pushOf(-0.001, 1.0), 0.0)
    self.assertEqual(GROUND.pushOf(0.0, 1.0), 0.0)
    self.assertAlmostEqual(GROUND.pushOf(0.001, 0.0), 100.0, 12)
    self.assertGreater(GROUND.pushOf(0.001, 0.5), 100.0)
    self.assertLess(GROUND.pushOf(0.001, -0.5), 100.0)
    self.assertEqual(GROUND.pushOf(0.001, -5.0), 0.0)

  def test_steps(self) -> None:
    """On the ground a body is stepped in whole parts of the world's
    step; with no ground, in the world's step."""
    step = WORLD.stepFor(BOX)
    self.assertLess(step, 1e-3)
    self.assertAlmostEqual(1e-3 / step, round(1e-3 / step), 9)
    self.assertEqual(World().stepFor(BOX), 1e-3)

  def test_dropped_flat(self) -> None:
    """A box dropped flat from half a metre bounces lower each time,
    then rests flat on its four corners, sunk its weight over four
    times the stiffness."""
    state = State((0.0, 0.0, 0.6), UNTURNED, ORIGIN, ORIGIN)
    heights = []
    for _ in range(400):
      state = WORLD.advanced(BOX, state, 0.01)
      heights.append(state.place[2])
    tops = [heights[i] for i in range(1, 399)
            if heights[i - 1] < heights[i] >= heights[i + 1]
            and heights[i] > 0.1001]
    self.assertGreaterEqual(len(tops), 3)
    for higher, lower in zip(tops, tops[1:]):
      self.assertLess(lower, higher)
    sunk = BOX.mass * 9.81 / (4.0 * GROUND.stiffness)
    self.assertAlmostEqual(state.place[2], 0.1 - sunk, 5)
    self.assertLess(norm(state.velocity), 1e-6)
    self.assertLess(norm(state.spin), 1e-6)
    self.assertLess(tiltOf(state), 1e-6)
    self.assertEqual(len(state.bristles), 4)

  def test_tossed(self) -> None:
    """A box and an L tossed tumbling three ways each come to rest
    square on a face, the box at half a side less its sink."""
    shape = lShape()
    for body in (BOX, Body.of(shape, 1000.0)):
      for toss in TOSSES:
        state = WORLD.advanced(body, toss, 6.0)
        self.assertLess(norm(state.velocity), 1e-6)
        self.assertLess(norm(state.spin), 1e-6)
        self.assertLess(tiltOf(state), 0.1)
        if body is BOX:
          sides = [abs(state.place[2] - half) for half in (0.1, 0.15, 0.2)]
          self.assertLess(min(sides), 1e-3)

  def test_energy(self) -> None:
    """A box tossed never gains more than a hair of energy in any
    millisecond, the ground's and the bristles' counted; it loses most
    of it."""
    state = TOSSES[0]
    start = energy = WORLD.energyOf(BOX, state)
    for _ in range(2000):
      state = WORLD.advanced(BOX, state, 0.001)
      now = WORLD.energyOf(BOX, state)
      self.assertLess(now - energy, 1e-3)
      energy = now
    self.assertLess(energy, 0.1 * start)

  def test_slid(self) -> None:
    """A box resting flat, slid along at 2 m/s, stops after v²/(2 grip
    g), staying flat."""
    rest = WORLD.advanced(BOX, State((0.0, 0.0, 0.1)), 1.0)
    slid = State(rest.place, rest.turn, (2.0, 0.0, 0.0), ORIGIN,
                 rest.bristles)
    slid = WORLD.advanced(BOX, slid, 1.0)
    self.assertAlmostEqual(slid.place[0] / (4.0 / (2.0 * 0.5 * 9.81)),
                           1.0, 2)
    self.assertLess(abs(slid.velocity[0]), 0.01)
    self.assertLess(tiltOf(slid), 0.01)

  def test_slope(self) -> None:
    """On a slope gentler than its grip (26.6 degrees at 0.5) a box
    stands, not creeping; steeper, it slides at g (sin - grip cos)."""
    for degrees in (20.0, 25.0, 30.0, 35.0):
      world = onSlope(degrees)
      settled = world.advanced(BOX, State((0.0, 0.0, 0.1)), 0.5)
      later = world.advanced(BOX, settled, 1.0)
      moved = later.place[0] - settled.place[0]
      if degrees < 26.0:
        self.assertLess(abs(moved), 1e-4)
        self.assertLess(norm(later.velocity), 1e-2)
      else:
        slope = math.radians(degrees)
        sliding = 9.81 * (math.sin(slope) - 0.5 * math.cos(slope))
        gained = later.velocity[0] - settled.velocity[0]
        self.assertLess(abs(gained / sliding - 1.0), 0.01)

  def test_pieces(self) -> None:
    """A run on the ground in pieces of whole steps is the run whole,
    bristles and all."""
    toss = State((0.0, 0.0, 0.4), normalised((0.9, 0.2, -0.3, 0.4)),
                 (1.0, 0.0, 0.0), (3.0, -6.0, 2.0))
    whole = WORLD.advanced(BOX, toss, 1.0)
    pieces = WORLD.advanced(BOX, WORLD.advanced(BOX, toss, 0.4), 0.6)
    self.assertTrue(whole.bristles)
    self.assertNear(pieces, whole, 1e-11)

  def test_no_shape(self) -> None:
    """A body known only by its mass and inertia has nothing to touch
    the ground with: it falls through."""
    body = Body(1.0, ORIGIN, IDENTITY)
    state = WORLD.advanced(body, State((0.0, 0.0, 1.0)), 1.0)
    self.assertAlmostEqual(state.place[2], 1.0 - 0.5 * 9.81, 12)
