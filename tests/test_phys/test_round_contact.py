"""
TestRoundContact covers a ball's contacts with other bodies: met at the
nearest point, one point a contact, pushed and gripped by the contact's
law (its stiffness N/m at that point), its bristle stretched only by
slipping. A ball dropped on a held slab rests sunk as its weight says;
slid on the slab it rolls on at 5/7 of its speed, the slab taking m v²
/ 7; two balls meeting head on keep their momentum and lose some energy;
a plank rolling on two balls goes on at its speed, the balls at half of
it, nothing slipping; a run in pieces is the run whole; compiled
(Warp) it runs as in plain Python, and so do eighteen balls with an oak
prism launched across them ('ballsUnderPrism').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Books, Contact, HeldPose, Hexapod
from worQt.phys import Sleep, Sphere, State, World, ballsUnderPrism
from worQt.phys import boxShape, norm
from worQt.phys._scenes import BALL_GROUND

from . import PhysTest

G = 9.81
R = 0.04
BALL = Body.of(Sphere(R), 7850.0)
SLAB = Body.of(boxShape(2.0, 2.0, 0.1), 2400.0)
HELD = HeldPose((0.0, 0.0, -0.05))
STIFF = 2e5
#  Steel on a held slab: stiffness 2e5 N/m at the point, damping 1 s/m,
#  grip 0.5, bristle 2e5 N/m, its damping 200 N s/m.
STEEL = (STIFF, 1.0, 0.5, 2e5, 200.0)
WORLD = World((0.0, 0.0, -G), 1e-3, None, None, False)
COMPILED = World((0.0, 0.0, -G), 1e-3, None, None, True)
SPACE = World((0.0, 0.0, 0.0), 1e-3, None, None, False)
SUNK = BALL.mass * G / STIFF


def onSlab(balls: tuple[State, ...], extra: tuple = ()) -> tuple:
  """The 'onSlab' function returns the slab held with its top at
  nought (its body last), 'balls' on it and any 'extra' bodies (each a
  body and its state, before the slab), every ball touching every other
  body, and how they start."""
  bodies = ((BALL,) * len(balls) + tuple(body for body, _ in extra)
            + (SLAB,))
  slab = len(bodies) - 1
  legs = Hexapod(1.0, 0.6, 20.0, 20.0, -1.0, -0.05).legs(SLAB, slab, HELD)
  count = len(bodies)
  contacts = tuple(Contact(a, b, *STEEL)
                   for a in range(len(balls)) for b in range(a + 1, count))
  states = tuple(balls) + tuple(state for _, state in extra) + (
    HELD.at(0.0).state(),)
  return Assembly(bodies, legs + contacts), states


def resting(x: float, velocity: tuple, spin: tuple) -> State:
  """The 'resting' function returns a ball on the slab at 'x', sunk as
  its weight says, moving and spinning so."""
  return State((x, 0.0, R - SUNK), (1.0, 0.0, 0.0, 0.0), velocity, spin)


class TestRoundContact(PhysTest):
  """Tests for a ball's contacts with other bodies."""

  def test_rests_on_a_slab(self) -> None:
    """Dropped 5 cm onto a held slab it comes to rest sunk as its weight
    on one point says."""
    assembly, states = onSlab((State((0.0, 0.0, R + 0.05)),))
    states = WORLD.advancedAll(assembly, states, 2.0)
    self.assertAlmostEqual(states[0].place[2], R - SUNK, 5)
    self.assertLess(norm(states[0].velocity), 1e-3)

  def test_rolls_on_a_slab(self) -> None:
    """Slid on the slab at 2 m/s without spin, it rolls on at 5/7 of
    that, spinning as it rolls; the slab took m v² / 7."""
    assembly, states = onSlab((resting(0.0, (2.0, 0.0, 0.0),
                                       (0.0, 0.0, 0.0)),))
    states, books = WORLD.booked(assembly, states, 0.8, 0.0, Books())
    rolling = 5.0 / 7.0 * 2.0
    self.assertAlmostEqual(states[0].velocity[0] / rolling, 1.0, 3)
    self.assertAlmostEqual(states[0].spin[1] * R / rolling, 1.0, 3)
    self.assertAlmostEqual(books.contacts / (BALL.mass * 4.0 / 7.0), 1.0, 2)

  def test_head_on(self) -> None:
    """Two balls meeting head on in empty space keep their momentum:
    the one hit goes on, the other slows; some energy is lost, none
    made."""
    a = State((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    b = State((0.1, 0.0, 0.0))
    contact = Contact(0, 1, *STEEL)
    assembly = Assembly((BALL, BALL), (contact,))
    after = SPACE.advancedAll(assembly, (a, b), 0.2)
    momentum = after[0].velocity[0] + after[1].velocity[0]
    self.assertAlmostEqual(momentum, 1.0, 9)
    self.assertGreater(after[1].velocity[0], after[0].velocity[0])
    energy = after[0].velocity[0] ** 2 + after[1].velocity[0] ** 2
    self.assertLessEqual(energy, 1.0 + 1e-9)
    self.assertGreater(energy, 0.5)

  def test_plank_on_rollers(self) -> None:
    """A plank rolling on two balls goes on at its speed, the balls
    rolling at half of it, nothing slipping."""
    v = 0.6
    plank = Body.of(boxShape(0.6, 0.2, 0.02), 700.0)
    load = (plank.mass * G / 2.0 + BALL.mass * G) / STIFF
    top = 2.0 * R - SUNK - plank.mass * G / 2.0 / STIFF
    balls = tuple(State((x, 0.0, R - load), (1.0, 0.0, 0.0, 0.0),
                        (v / 2.0, 0.0, 0.0), (0.0, v / 2.0 / R, 0.0))
                  for x in (-0.15, 0.15))
    on = State((0.0, 0.0, top + 0.01), (1.0, 0.0, 0.0, 0.0), (v, 0.0, 0.0))
    assembly, states = onSlab(balls, ((plank, on),))
    states = WORLD.advancedAll(assembly, states, 0.5)
    self.assertAlmostEqual(states[2].velocity[0] / v, 1.0, 2)
    for ball in states[:2]:
      self.assertAlmostEqual(ball.velocity[0] / (v / 2.0), 1.0, 2)
      self.assertAlmostEqual(ball.spin[1] * R / ball.velocity[0], 1.0, 2)

  def test_pieces(self) -> None:
    """Run in five pieces it is where it is run whole: the bristles go
    on with it."""
    assembly, start = onSlab((resting(0.0, (1.0, 0.3, 0.0),
                                      (2.0, -5.0, 3.0)),))
    whole = WORLD.advancedAll(assembly, start, 0.25)
    pieces = start
    for k in range(5):
      pieces = WORLD.advancedAll(assembly, pieces, 0.05, 0.05 * k)
    self.assertNear(pieces[0].place, whole[0].place, 1e-11)
    self.assertNear(pieces[0].velocity, whole[0].velocity, 1e-10)

  def test_compiled(self) -> None:
    """Compiled, a ball rolling and spinning on the slab runs as in
    plain Python, its bristle's stretch alike."""
    assembly, start = onSlab((resting(0.0, (1.0, 0.3, 0.0),
                                      (2.0, -5.0, 3.0)),))
    plain = WORLD.advancedAll(assembly, start, 0.3)[0]
    compiled = COMPILED.advancedAll(assembly, start, 0.3)[0]
    self.assertNear(compiled.place, plain.place, 1e-12)
    self.assertNear(compiled.velocity, plain.velocity, 1e-10)
    self.assertNear(compiled.spin, plain.spin, 1e-9)
    self.assertEqual([hold[:2] for hold in compiled.holds],
                     [hold[:2] for hold in plain.holds])
    self.assertNear([hold[2:] for hold in compiled.holds],
                    [hold[2:] for hold in plain.holds], 1e-12)

  def test_scene_compiled(self) -> None:
    """Eighteen balls with the prism launched across them, sleeping as
    they settle: compiled as in plain Python for 0.3 s."""
    assembly, start = ballsUnderPrism(18, 1)
    plain = World((0.0, 0.0, -G), 1e-3, BALL_GROUND, None, False, Sleep())
    compiled = World((0.0, 0.0, -G), 1e-3, BALL_GROUND, None, True, Sleep())
    slow = plain.advancedAll(assembly, start, 0.3)
    fast = compiled.advancedAll(assembly, start, 0.3)
    for one, other in zip(slow, fast):
      self.assertNear(other.place, one.place, 1e-10)
      self.assertNear(other.velocity, one.velocity, 1e-9)
