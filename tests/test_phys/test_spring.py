"""
TestSpring covers 'Spring', a coil spring between points on two bodies
or a body and the world: its pull along the line, stiffness times its
stretch, and the energy it holds; a block hung from the world on one
rests stretched its weight over the stiffness and bobs at sqrt(k/m),
not turning, its energy kept; two bodies sprung together out in space
bob at sqrt(k (1/m1 + 1/m2)), their centre of mass moving steadily; a
spring hooked to a corner twists the body, and its pull, always
through the hook, keeps the angular momentum about it; a spring on a
welded part pulls the welded body there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, UNTURNED, Assembly, Body, Spring, State
from worQt.phys import Weld, World, boxShape, cross, minus, norm
from worQt.phys import normalised, plus, scaled

from . import PhysTest, lShape

WORLD = World()
SPACE = World((0.0, 0.0, 0.0), 1e-3)
BLOCK = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
LONG = Body.of(boxShape(0.4, 0.2, 0.2), 1000.0)
TOP = (0.0, 0.0, 0.1)
HUNG = Assembly((BLOCK,), (Spring(None, ORIGIN, 0, TOP, 800.0, 1.0),))


def crossings(values: list[float], level: float, step: float) -> list:
  """The 'crossings' function returns when 'values', one each 'step'
  s, fall through 'level', between samples by a straight line."""
  return [step * (i + (values[i] - level) / (values[i] - values[i + 1]))
          for i in range(len(values) - 1)
          if values[i] > level >= values[i + 1]]


class TestSpring(PhysTest):
  """Tests for 'Spring'."""

  def test_pull(self) -> None:
    """A spring pulls its ends together stretched, apart squeezed,
    along the line, stiffness times its stretch, holding half the
    stiffness times that squared; of no rest length, the stiffness
    times how far apart."""
    spring = Spring(None, ORIGIN, None, ORIGIN, 100.0, 1.0)
    self.assertNear(spring.pullOf(ORIGIN, (0.0, 0.0, 1.5)),
                    (0.0, 0.0, 50.0), 1e-13)
    self.assertNear(spring.pullOf(ORIGIN, (0.6, 0.0, 0.0)),
                    (-40.0, 0.0, 0.0), 1e-13)
    self.assertAlmostEqual(spring.storedOf(ORIGIN, (0.0, 0.0, 1.5)),
                           12.5, 12)
    none = Spring(None, ORIGIN, None, ORIGIN, 100.0, 0.0)
    self.assertNear(none.pullOf((1.0, 1.0, 1.0), (1.0, 2.0, 3.0)),
                    (0.0, 100.0, 200.0), 1e-12)

  def test_hung(self) -> None:
    """A block hung on a spring let go at its rest length falls twice
    its weight over the stiffness, bobs back, at sqrt(k / m), straight
    under the hook and not turning, its energy kept."""
    states = (State((0.0, 0.0, -1.1)),)
    energy = WORLD.energyOfAll(HUNG, states)
    heights = []
    for _ in range(3000):
      states = WORLD.advancedAll(HUNG, states, 0.001)
      heights.append(states[0].place[2])
      self.assertLess(abs(WORLD.energyOfAll(HUNG, states) - energy), 2e-4)
    sag = BLOCK.mass * 9.81 / 800.0
    self.assertAlmostEqual(min(heights), -1.1 - 2.0 * sag, 6)
    self.assertAlmostEqual(max(heights), -1.1, 6)
    times = crossings(heights, -1.1 - sag, 0.001)
    period = 2.0 * math.pi / math.sqrt(800.0 / BLOCK.mass)
    self.assertGreaterEqual(len(times), 4)
    for start, end in zip(times, times[1:]):
      self.assertLess(abs((end - start) / period - 1.0), 1e-5)
    self.assertEqual(states[0].place[:2], (0.0, 0.0))
    self.assertEqual(states[0].spin, (0.0, 0.0, 0.0))

  def test_pair(self) -> None:
    """Two bodies sprung together out in space, drifting, bob at
    sqrt(k (1/m1 + 1/m2)); their centre of mass drifts on steadily."""
    pair = Assembly((BLOCK, LONG), (Spring(0, ORIGIN, 1, ORIGIN, 500.0,
                                           1.0),))
    states = (State(ORIGIN, UNTURNED, (0.1, 0.0, 0.0)),
              State((1.2, 0.0, 0.0), UNTURNED, (0.1, 0.0, 0.0)))
    gaps = []
    for _ in range(3000):
      states = SPACE.advancedAll(pair, states, 0.001)
      gaps.append(states[1].place[0] - states[0].place[0])
    times = crossings(gaps, 1.0, 0.001)
    rate = math.sqrt(500.0 * (1.0 / BLOCK.mass + 1.0 / LONG.mass))
    self.assertGreaterEqual(len(times), 3)
    for start, end in zip(times, times[1:]):
      self.assertLess(abs((end - start) * rate / (2.0 * math.pi) - 1.0),
                      1e-5)
    mass = BLOCK.mass + LONG.mass
    middle = scaled(plus(scaled(states[0].place, BLOCK.mass),
                         scaled(states[1].place, LONG.mass)), 1.0 / mass)
    self.assertNear(middle, (1.2 * LONG.mass / mass + 0.3, 0.0, 0.0),
                    1e-12)

  def test_corner(self) -> None:
    """A spring hooked to a tumbling block's corner twists it as it
    pulls; pulling always through the hook, it keeps the block's
    angular momentum about the hook, and the energy is kept."""
    hook, corner = (0.5, 0.2, 0.0), (0.1, 0.1, 0.1)
    sprung = Assembly((BLOCK,), (Spring(None, hook, 0, corner, 2000.0,
                                        0.3),))
    states = (State(ORIGIN, normalised((0.9, 0.1, 0.2, 0.3)),
                    (0.2, -0.3, 0.1), (1.0, 2.0, -1.0)),)

    def about(state: State) -> tuple:
      """Returns the block's angular momentum about the hook."""
      away = cross(minus(state.place, hook), BLOCK.momentumOf(state))
      return plus(BLOCK.angularMomentumOf(state), away)

    momentum, energy = about(states[0]), SPACE.energyOfAll(sprung, states)
    turned = False
    for _ in range(300):
      states = SPACE.advancedAll(sprung, states, 0.01)
      self.assertLess(norm(minus(about(states[0]), momentum)), 1e-12)
      self.assertLess(abs(SPACE.energyOfAll(sprung, states) / energy - 1.0),
                      1e-3)
      turned = turned or norm(minus(states[0].spin, (1.0, 2.0, -1.0))) > 1
    self.assertTrue(turned)

  def test_welded(self) -> None:
    """A spring on a part of a welded L pulls the welded body at that
    point, as it pulls the L made whole."""
    lying = Body.of(boxShape(1.0, 0.2, 0.2), 1000.0)
    standing = Body.of(boxShape(0.2, 0.2, 0.6), 1000.0)
    whole = Body.of(lShape(), 1000.0)
    hook = (0.0, 0.0, 3.0)
    welded = Assembly((lying, standing), (
      Weld((0, 1)), Spring(None, hook, 1, (0.0, 0.0, 0.3), 3000.0, 0.5)))
    made = Assembly((whole,), (Spring(None, hook, 0, (0.4, 0.0, 0.7),
                                      3000.0, 0.5),))
    turn = normalised((0.9, 0.2, -0.3, 0.4))
    start = State((0.0, 0.0, 2.0), turn, (1.0, 0.0, 4.0), (3.0, -6.0, 2.0))
    parts = []
    for middle in ((0.0, 0.0, 0.0), (0.4, 0.0, 0.4)):
      arm = minus(whole.placeOf(start, middle), start.place)
      parts.append(State(plus(start.place, arm), turn,
                         plus(start.velocity, cross(start.spin, arm)),
                         start.spin))
    parts = WORLD.advancedAll(welded, tuple(parts), 1.0)
    later = WORLD.advancedAll(made, (start,), 1.0)[0]
    for part, middle in zip(parts, ((0.0, 0.0, 0.0), (0.4, 0.0, 0.4))):
      self.assertNear(part.place, whole.placeOf(later, middle), 1e-12)
