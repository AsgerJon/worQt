"""
TestFixed covers bodies made part of the world ('Fixed'): one under
gravity stays where it is, still; a ball dropped on a fixed block lands
and rests on it as on the ground (its weight over the contact's
stiffness into it), the block not moved; a ball on a rod tied to a
fixed block swings as one tied to the world at the same point, to the
nanometre; compiled (Warp) as in plain Python.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.phys import Actuator, Assembly, Body, Contact, Fixed, HeldStroke
from worQt.phys import Sphere, State, World, boxShape, minus, norm

from . import PhysTest

G = 9.81
BLOCK = Body.of(boxShape(1.0, 1.0, 0.2), 2400.0)
BALL = Body.of(Sphere(0.05), 7850.0)
TOP = 1.1
WORLD = World((0.0, 0.0, -G), 1e-3, None, None, False)
COMPILED = World((0.0, 0.0, -G), 1e-3, None, None, True)
LAW = (2e6, 5.0, 0.5, 2e6, 2000.0)


def dropped(world: World, seconds: float) -> tuple:
  """The 'dropped' function returns a fixed block, its top at 'TOP', and
  a steel ball let go 5 cm over it, after 'seconds' in 'world'."""
  assembly = Assembly((BLOCK, BALL), (Fixed(0), Contact(0, 1, *LAW)))
  states = (State((0.0, 0.0, TOP - 0.1)),
            State((0.0, 0.0, TOP + 0.05 + 0.05)))
  return world.advancedAll(assembly, states, seconds)


def swung(world: World, fixed: bool, seconds: float) -> State:
  """The 'swung' function returns a ball on a 0.5 m rod, let go level,
  after 'seconds' in 'world': tied to a fixed block's corner (or, not
  'fixed', to the world at the same point)."""
  corner = (0.5, 0.5, 0.1)
  start = State((corner[0] + 0.5, corner[1], 1.0 + corner[2]))
  if fixed:
    assembly = Assembly((BLOCK, BALL), (
      Fixed(0), Actuator(0, corner, 1, (0.0, 0.0, 0.0), HeldStroke(0.5))))
    states = (State((0.0, 0.0, 1.0)), start)
    return world.advancedAll(assembly, states, seconds)[1]
  point = (corner[0], corner[1], 1.0 + corner[2])
  assembly = Assembly((BALL,), (
    Actuator(None, point, 0, (0.0, 0.0, 0.0), HeldStroke(0.5)),))
  return world.advancedAll(assembly, (start,), seconds)[0]


class TestFixed(PhysTest):
  """Tests for 'Fixed'."""

  def test_stays(self) -> None:
    """A fixed block under gravity, alone, stays where it is, still."""
    assembly = Assembly((BLOCK,), (Fixed(0),))
    start = State((0.3, -0.2, 2.0))
    state = WORLD.advancedAll(assembly, (start,), 0.5)[0]
    self.assertEqual(state.place, start.place)
    self.assertNear(state.velocity, (0.0, 0.0, 0.0), 0.0)
    self.assertNear(state.spin, (0.0, 0.0, 0.0), 0.0)

  def test_rests_on_it(self) -> None:
    """A ball dropped 5 cm on a fixed block lands and comes to rest on
    it, sunk its weight over the contact's stiffness (to a micrometre),
    the block where it was."""
    block, ball = dropped(WORLD, 1.0)
    self.assertEqual(block.place, (0.0, 0.0, TOP - 0.1))
    sunk = BALL.mass * G / LAW[0]
    self.assertNear(ball.place[2], TOP + 0.05 - sunk, 1e-6)
    self.assertLess(norm(ball.velocity), 1e-3)

  def test_tied_as_to_the_world(self) -> None:
    """A ball on a rod tied to a fixed block's corner swings as one tied
    to the world at the same point (to a nanometre over 0.4 s)."""
    one, two = swung(WORLD, True, 0.4), swung(WORLD, False, 0.4)
    self.assertLess(norm(minus(one.place, two.place)), 1e-9)

  def test_compiled(self) -> None:
    """Compiled (Warp), the drop and the swing go as in plain Python (to
    a nanometre)."""
    plain, warped = dropped(WORLD, 0.3), dropped(COMPILED, 0.3)
    for one, two in zip(plain, warped):
      self.assertLess(norm(minus(one.place, two.place)), 1e-9)
    self.assertLess(norm(minus(swung(WORLD, True, 0.3).place,
                               swung(COMPILED, True, 0.3).place)), 1e-9)
