"""
TestDamper covers 'Damper', a dashpot between points on two bodies or a
body and the world: its push along the line, the damping times how
fast the line lengthens, nothing across it; a block hung on a spring
and a damper let go at the spring's rest length follows the damped
swing by hand, underdamped or critically (never passing its rest), its
energy never rising; under a damper stiff past any step it creeps at
its load over the damping, steady; two bodies joined by a damper out in
space close at a speed dying as e to the -c (1/m1 + 1/m2) t, their
momentum kept.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, UNTURNED, Assembly, Body, Damper, Spring
from worQt.phys import State, World, boxShape, plus

from . import PhysTest

WORLD = World()
SPACE = World((0.0, 0.0, 0.0), 1e-3)
BLOCK = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
LONG = Body.of(boxShape(0.4, 0.2, 0.2), 1000.0)
TOP = (0.0, 0.0, 0.1)
STIFFNESS = 800.0
RATE = math.sqrt(STIFFNESS / BLOCK.mass)
SAG = BLOCK.mass * 9.81 / STIFFNESS


def damped(damping: float) -> Assembly:
  """The 'damped' function returns the block hung from the world on the
  spring and a damper of 'damping' N s/m beside it."""
  return Assembly((BLOCK,), (Spring(None, ORIGIN, 0, TOP, STIFFNESS, 1.0),
                             Damper(None, ORIGIN, 0, TOP, damping)))


def swung(assembly: Assembly, seconds: float) -> tuple[list, float]:
  """The 'swung' function returns how far above its rest the block
  hung in 'assembly', let go at the spring's rest length, is each
  millisecond for 'seconds', and the most its energy rose in one."""
  states = (State((0.0, 0.0, -1.1)),)
  energy, rise, heights = WORLD.energyOfAll(assembly, states), 0.0, []
  for _ in range(round(seconds / 0.001)):
    states = WORLD.advancedAll(assembly, states, 0.001)
    heights.append(states[0].place[2] + 1.1 + SAG)
    now = WORLD.energyOfAll(assembly, states)
    rise, energy = max(rise, now - energy), now
  return heights, rise


class TestDamper(PhysTest):
  """Tests for 'Damper'."""

  def test_push(self) -> None:
    """A damper pushes its ends along the line between them, the
    damping times how fast that lengthens; moving across it, or at one
    place, nothing."""
    damper = Damper(None, ORIGIN, None, ORIGIN, 30.0)
    far = (0.0, 0.0, 2.0)
    self.assertNear(damper.pushOf(ORIGIN, far, ORIGIN, (0.0, 0.0, 0.5)),
                    (0.0, 0.0, 15.0), 1e-13)
    self.assertNear(damper.pushOf(ORIGIN, far, (0.0, 0.0, 0.5), ORIGIN),
                    (0.0, 0.0, -15.0), 1e-13)
    self.assertNear(damper.pushOf(ORIGIN, far, ORIGIN, (1.0, 2.0, 0.0)),
                    ORIGIN, 0.0)
    self.assertNear(damper.pushOf(far, far, ORIGIN, (0.0, 0.0, 1.0)),
                    ORIGIN, 0.0)

  def test_underdamped(self) -> None:
    """Damped to a tenth of critical, the block swings as by hand: SAG
    e^(-z w t) (cos wd t + z w / wd sin wd t), its energy never
    rising."""
    share = 0.1
    heights, rise = swung(damped(share * 2.0 * math.sqrt(
      STIFFNESS * BLOCK.mass)), 4.0)
    slower = RATE * math.sqrt(1.0 - share * share)
    for step, height in enumerate(heights):
      t = 0.001 * (step + 1)
      swing = math.cos(slower * t) + share * RATE / slower * math.sin(
        slower * t)
      self.assertLess(abs(height - SAG * math.exp(-share * RATE * t)
                          * swing), 1e-5)
    self.assertLess(rise, 1e-12)

  def test_critical(self) -> None:
    """Damped critically, the block sinks to its rest as by hand, SAG
    (1 + w t) e^(-w t), never passing it."""
    heights, rise = swung(damped(2.0 * math.sqrt(STIFFNESS * BLOCK.mass)),
                          4.0)
    for step, height in enumerate(heights):
      t = 0.001 * (step + 1)
      self.assertLess(abs(height - SAG * (1.0 + RATE * t)
                          * math.exp(-RATE * t)), 1e-5)
      self.assertGreater(height, -1e-12)
    self.assertLess(rise, 1e-12)

  def test_stiff(self) -> None:
    """Under a damper a million N s/m stiff, far past what a step of a
    millisecond could follow, the block creeps down steadily at its
    weight, less the spring's pull, over the damping."""
    states = (State((0.0, 0.0, -1.1)),)
    for _ in range(10):
      states = WORLD.advancedAll(damped(1e6), states, 0.1)
      stretch = -1.1 - states[0].place[2]
      creep = -(BLOCK.mass * 9.81 - STIFFNESS * stretch) / 1e6
      self.assertLess(abs(states[0].velocity[2] / creep - 1.0), 1e-3)
    self.assertGreater(states[0].place[2], -1.1 - 1e-3)

  def test_pair(self) -> None:
    """Two bodies joined at their middles by a damper, out in space,
    meeting at 1 m/s, close ever slower, as e^(-c (1/m1 + 1/m2) t), their
    momentum kept."""
    pair = Assembly((BLOCK, LONG), (Damper(0, ORIGIN, 1, ORIGIN, 30.0),))
    states = (State(ORIGIN, UNTURNED, (0.5, 0.0, 0.0)),
              State((1.0, 0.0, 0.0), UNTURNED, (-0.5, 0.0, 0.0)))
    momentum = plus(BLOCK.momentumOf(states[0]), LONG.momentumOf(states[1]))
    rate = 30.0 * (1.0 / BLOCK.mass + 1.0 / LONG.mass)
    for step in range(10):
      states = SPACE.advancedAll(pair, states, 0.1)
      closing = states[1].velocity[0] - states[0].velocity[0]
      self.assertLess(abs(closing / -math.exp(-rate * 0.1 * (step + 1))
                          - 1.0), 1e-5)
    self.assertNear(plus(BLOCK.momentumOf(states[0]),
                         LONG.momentumOf(states[1])), momentum, 1e-13)
