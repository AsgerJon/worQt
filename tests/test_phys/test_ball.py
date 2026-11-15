"""
TestBall covers 'Sphere', a ball exactly round, on the ground: its mass
and moments are a solid ball's (2/5 m r²); dropped, it bounces and
comes to rest sunk as its weight says; slid without spin it slides,
spinning up, and rolls on at 5/7 of its speed, having lost m v²/7 to
the ground; rolling it rolls on, losing nothing; with enough backspin
it comes back at (5 v + 2 r w)/7; on a gentle slope it rolls down at
5/7 g sin, on a steep one it slides at g (sin - grip cos); a run in
pieces is the run whole, and compiled it runs as in plain Python. The
ball touches the ground at its lowest point, whatever turns under it:
rolling stretches no bristle, only slipping does.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Books, Ground, Sphere, State
from worQt.phys import World, norm

from . import PhysTest

GROUND = Ground()
R = 0.05
BALL = Body.of(Sphere(R), 7850.0)
G = 9.81
GRIP = GROUND.grip
SUNK = BALL.mass * G / GROUND.stiffness


def worldOn(degrees: float, compiled: bool) -> World:
  """The 'worldOn' function returns the world tilted 'degrees' about y,
  so the ground is a slope falling along x."""
  slope = math.radians(degrees)
  return World((G * math.sin(slope), 0.0, -G * math.cos(slope)), 1e-3,
               GROUND, None, compiled)


FLAT = worldOn(0.0, False)


def resting(velocity: tuple, spin: tuple) -> State:
  """The 'resting' function returns the ball on the ground, sunk as its
  weight says, moving at 'velocity' and spinning at 'spin'."""
  return State((0.0, 0.0, R - SUNK), (1.0, 0.0, 0.0, 0.0), velocity, spin)


class TestBall(PhysTest):
  """Tests for 'Sphere' and a ball on the ground."""

  def test_mass(self) -> None:
    """A solid ball: 4/3 pi r³ of the stuff, its centre in its middle,
    turning as easily about any axis, 2/5 m r²."""
    mass = 7850.0 * 4.0 / 3.0 * math.pi * R ** 3
    self.assertAlmostEqual(BALL.mass / mass, 1.0, 12)
    self.assertNear(BALL.centre, (0.0, 0.0, 0.0), 1e-15)
    moment = 0.4 * mass * R * R
    self.assertNear(BALL.inertia, ((moment, 0.0, 0.0), (0.0, moment, 0.0),
                                   (0.0, 0.0, moment)), 1e-15)

  def test_rests(self) -> None:
    """Dropped 10 cm, it bounces lower and lower and comes to rest sunk
    as its weight on one point says, still (within a hundredth of a
    millimetre: the ground's damping is light at so shallow a sink, a
    last bob of a micrometre dies slowly)."""
    state = State((0.0, 0.0, R + 0.1))
    state = FLAT.advanced(BALL, state, 3.0)
    self.assertAlmostEqual(state.place[2], R - SUNK, 5)
    self.assertLess(norm(state.velocity), 1e-4)
    self.assertLess(norm(state.spin), 1e-3)

  def test_slides_into_rolling(self) -> None:
    """Slid at 2 m/s without spin, it slides, spinning up, until it
    rolls at 5/7 of that after 2 v / (7 grip g), having gone 12 v² /
    (49 grip g); then it rolls on, its spin its speed over its
    radius."""
    v = 2.0
    sliding = 2.0 * v / (7.0 * GRIP * G)
    gone = 12.0 * v * v / (49.0 * GRIP * G)
    state = FLAT.advanced(BALL, resting((v, 0.0, 0.0), (0.0, 0.0, 0.0)),
                          sliding + 1.0)
    rolling = 5.0 / 7.0 * v
    self.assertAlmostEqual(state.velocity[0] / rolling, 1.0, 3)
    self.assertAlmostEqual(state.spin[1] * R / rolling, 1.0, 3)
    self.assertNear(state.place[0], gone + rolling * 1.0, 2e-3)

  def test_heat(self) -> None:
    """Sliding into rolling, the ground takes m v² / 7: what the ball
    had less what it keeps, moving and turning."""
    v = 2.0
    assembly = Assembly((BALL,))
    start = resting((v, 0.0, 0.0), (0.0, 0.0, 0.0))
    _, books = FLAT.booked(assembly, (start,), 1.0, 0.0, Books())
    self.assertAlmostEqual(books.heat() / (BALL.mass * v * v / 7.0), 1.0,
                           2)

  def test_keeps_rolling(self) -> None:
    """Set rolling, it rolls on as it was: nothing slips, so nothing
    slows it."""
    state = resting((1.0, 0.0, 0.0), (0.0, 1.0 / R, 0.0))
    state = FLAT.advanced(BALL, state, 2.0)
    self.assertNear(state.velocity, (1.0, 0.0, 0.0), 1e-6)
    self.assertNear(state.spin, (0.0, 1.0 / R, 0.0), 1e-4)
    self.assertNear(state.place[0], 2.0, 1e-6)

  def test_draw(self) -> None:
    """Slid at 1 m/s with backspin 3.5 times its speed over its radius,
    it slows, stops and comes back at (5 v + 2 r w) / 7 = -2/7 m/s."""
    state = resting((1.0, 0.0, 0.0), (0.0, -3.5 / R, 0.0))
    state = FLAT.advanced(BALL, state, 1.5)
    self.assertAlmostEqual(state.velocity[0] / (-2.0 / 7.0), 1.0, 3)
    self.assertAlmostEqual(state.spin[1] * R / state.velocity[0], 1.0, 3)

  def test_rolls_down(self) -> None:
    """On a slope of 10 degrees, gentler than its grip lets it slip,
    it rolls down at 5/7 g sin."""
    world = worldOn(10.0, False)
    state = world.advanced(BALL, resting((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
                           1.0)
    rolling = 5.0 / 7.0 * G * math.sin(math.radians(10.0))
    self.assertAlmostEqual(state.velocity[0] / rolling, 1.0, 3)
    self.assertAlmostEqual(state.spin[1] * R / state.velocity[0], 1.0, 3)

  def test_slides_down(self) -> None:
    """On a slope of 65 degrees, steeper than tan = 7/2 grip, it slides
    as it turns, at g (sin - grip cos)."""
    world = worldOn(65.0, False)
    state = world.advanced(BALL, resting((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
                           0.5)
    slope = math.radians(65.0)
    sliding = G * (math.sin(slope) - GRIP * math.cos(slope)) * 0.5
    self.assertAlmostEqual(state.velocity[0] / sliding, 1.0, 2)
    self.assertLess(state.spin[1] * R, state.velocity[0])

  def test_pieces(self) -> None:
    """Run in ten pieces it is where it is run whole: its bristle goes
    on with it."""
    start = resting((2.0, 0.5, 0.0), (1.0, -3.0, 4.0))
    whole = FLAT.advanced(BALL, start, 1.0)
    pieces = start
    for _ in range(10):
      pieces = FLAT.advanced(BALL, pieces, 0.1)
    self.assertNear(pieces.place, whole.place, 1e-12)
    self.assertNear(pieces.velocity, whole.velocity, 1e-12)
    self.assertNear(pieces.spin, whole.spin, 1e-10)

  def test_compiled(self) -> None:
    """Compiled, a ball runs as in plain Python."""
    start = resting((2.0, 0.5, 0.0), (1.0, -3.0, 4.0))
    plain = FLAT.advanced(BALL, start, 0.5)
    compiled = worldOn(0.0, True).advanced(BALL, start, 0.5)
    self.assertNear(compiled.place, plain.place, 1e-12)
    self.assertNear(compiled.velocity, plain.velocity, 1e-12)
    self.assertNear(compiled.spin, plain.spin, 1e-10)
