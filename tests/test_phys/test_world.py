"""
TestWorld covers 'World', bodies stepped on under gravity, free of
anything else: a body's centre falls exactly as by hand, spinning or
not, and gravity turns nothing; cut into pieces a run is the same, and
run backwards it comes back; spinning about a principal axis it turns
steadily about it; tumbling, its angular momentum is kept exactly and
its energy within a hair; a symmetric top's spin goes round as Euler's
equations say and its axis round the angular momentum, the error a
quarter for half the step; and spun about its middle axis a body flips
over and back (the tennis racket), about the others not.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import AXES, ORIGIN, UNTURNED, Body, State, World
from worQt.phys import applied, boxShape, matrixOf, minus, norm
from worQt.phys import normalised, rotated, scaled, transposed, turnAbout

from . import PhysTest, lShape

WORLD = World()
BOX = Body.of(boxShape(0.4, 0.3, 0.2), 1000.0)
TUMBLING = State((0.0, 0.0, 2.0), normalised((0.9, 0.2, -0.3, 0.4)),
                 (1.0, 0.0, 4.0), (3.0, -6.0, 2.0))
TOP = Body(3.0, ORIGIN, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                         (0.0, 0.0, 2.0)))
TOP_SPUN = State(ORIGIN, UNTURNED, ORIGIN, (1.0, 0.0, 3.0))


def heldOf(state: State) -> tuple:
  """The 'heldOf' function returns a state's spin along the body's own
  axes."""
  return applied(transposed(matrixOf(state.turn)), state.spin)


def topMiss(step: float, seconds: float) -> tuple[float, float]:
  """The 'topMiss' function returns how far the symmetric top 'TOP',
  spun as 'TOP_SPUN', stepped by 'step' for 'seconds', misses by hand:
  its spin along its own axes (Euler's equations: the part across its
  axis goes round at (C - A)/A times the part along), and its axis
  (round the angular momentum at |L|/A)."""
  state = World((0.0, 0.0, -9.81), step).advanced(TOP, TOP_SPUN, seconds)
  rate = (2.0 - 1.0) * 3.0 / 1.0
  spin = (math.cos(rate * seconds), math.sin(rate * seconds), 3.0)
  momentum = TOP.angularMomentumOf(TOP_SPUN)
  round_ = turnAbout(momentum, norm(momentum) * seconds / 1.0)
  axis = rotated(round_, AXES[2])
  spinMiss = max(abs(a - b) for a, b in zip(heldOf(state), spin))
  axisMiss = norm(minus(rotated(state.turn, AXES[2]), axis))
  return spinMiss, axisMiss


class TestWorld(PhysTest):
  """Tests for 'World'."""

  def test_free_fall(self) -> None:
    """A spinning box thrown up falls as by hand: its centre on the
    parabola, its velocity losing g each second."""
    thrown = State((0.0, 0.0, 10.0), UNTURNED, (1.0, -2.0, 3.0),
                   (2.0, -5.0, 7.0))
    state = WORLD.advanced(BOX, thrown, 1.3)
    t = 1.3
    self.assertNear(state.place, (t, -2.0 * t,
                                  10.0 + 3.0 * t - 0.5 * 9.81 * t * t),
                    1e-12)
    self.assertNear(state.velocity, (1.0, -2.0, 3.0 - 9.81 * t), 1e-12)

  def test_gravity_turns_nothing(self) -> None:
    """Gravity pulls the centre: a tumbling body turns the same in it
    as out of it."""
    body = Body.of(lShape(), 1000.0)
    falling = WORLD.advanced(body, TUMBLING, 2.0)
    floating = World((0.0, 0.0, 0.0), 1e-3).advanced(body, TUMBLING, 2.0)
    self.assertEqual(falling.turn, floating.turn)
    self.assertEqual(falling.spin, floating.spin)
    self.assertEqual(floating.velocity, TUMBLING.velocity)

  def test_pieces(self) -> None:
    """A run cut into pieces of whole steps is the run whole; run back
    from where it ended, velocity and spin reversed, it comes back."""
    body = Body.of(lShape(), 1000.0)
    whole = WORLD.advanced(body, TUMBLING, 3.0)
    pieces = WORLD.advanced(body, WORLD.advanced(body, TUMBLING, 1.2), 1.8)
    self.assertNear(pieces, whole, 1e-13)
    back = State(whole.place, whole.turn, scaled(whole.velocity, -1.0),
                 scaled(whole.spin, -1.0))
    back = WORLD.advanced(body, back, 3.0)
    self.assertNear(back.place, TUMBLING.place, 1e-12)
    self.assertSameTurn(back.turn, TUMBLING.turn, 1e-12)
    self.assertNear(back.velocity, scaled(TUMBLING.velocity, -1.0), 1e-12)
    self.assertNear(back.spin, scaled(TUMBLING.spin, -1.0), 1e-12)

  def test_steady_spin(self) -> None:
    """Spun about a principal axis a box turns steadily about it, as
    far as its spin times the time."""
    for axis in range(3):
      spin = scaled(AXES[axis], 4.0)
      state = WORLD.advanced(BOX, State(ORIGIN, UNTURNED, ORIGIN, spin),
                             2.0)
      self.assertSameTurn(state.turn, turnAbout(AXES[axis], 8.0), 1e-13)
      self.assertNear(state.spin, spin, 1e-13)

  def test_kept(self) -> None:
    """Tumbling in the air an L keeps its angular momentum, exactly but
    for rounding, and its energy within a hair."""
    body = Body.of(lShape(), 1000.0)
    momentum = body.angularMomentumOf(TUMBLING)
    energy = WORLD.energyOf(body, TUMBLING)
    state = TUMBLING
    for _ in range(50):
      state = WORLD.advanced(body, state, 0.1)
      kept = body.angularMomentumOf(state)
      self.assertLess(norm(minus(kept, momentum)) / norm(momentum), 1e-13)
      self.assertLess(abs(WORLD.energyOf(body, state) / energy - 1.0),
                      1e-6)

  def test_symmetric_top(self) -> None:
    """A symmetric top's spin goes round its axis and its axis round
    the angular momentum as by hand; halving the step quarters the
    miss."""
    spinMiss, axisMiss = topMiss(1e-3, 2.0)
    self.assertLess(spinMiss, 5e-5)
    self.assertLess(axisMiss, 1e-5)
    coarse, fine = topMiss(2e-3, 2.0), topMiss(1e-3, 2.0)
    for coarseMiss, fineMiss in zip(coarse, fine):
      self.assertAlmostEqual(coarseMiss / fineMiss, 4.0, 1)

  def test_tennis_racket(self) -> None:
    """Spun about its middle axis, a hair off, a body flips over and
    back; about its least or greatest it stays."""
    racket = Body(1.0, ORIGIN, ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0),
                                (0.0, 0.0, 3.0)))
    for axis in range(3):
      spin = [1e-3, 1e-3, 1e-3]
      spin[axis] = 5.0
      state = State(ORIGIN, UNTURNED, ORIGIN, tuple(spin))
      along = []
      for _ in range(100):
        state = WORLD.advanced(racket, state, 0.1)
        along.append(heldOf(state)[axis])
      if axis == 1:
        self.assertLess(min(along), -4.9)
        self.assertGreater(max(along), 4.9)
      else:
        self.assertNear(along, [5.0] * 100, 1e-5)
