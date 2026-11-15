"""
TestActuator covers 'Actuator', a rigid rod with ball ends whose length
its stroke sets, with whatever force that takes: 'HeldStroke' and
'SineStroke' give their lengths, rates and accelerations by hand; a
block hung from the world by a held rod to its middle swings as a
simple pendulum at the period by hand, the rod at its length, the block
not turning, the rod pulling its weight hanging still and more swinging
through the bottom; a block on a spring and a damper under a base an
actuator shakes swings at the base's amplitude times the
transmissibility by hand, below, at and above resonance; a run cut into
pieces at their times is the run whole; however heavy the load, the
stroke is kept.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, Actuator, Assembly, Body, Damper
from worQt.phys import HeldStroke, SineStroke, Spring, State, World
from worQt.phys import boxShape, norm

from . import PhysTest

WORLD = World()
BLOCK = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
BASE = Body.of(boxShape(0.1, 0.1, 0.1), 1000.0)
ROD = Assembly((BLOCK,),
               (Actuator(None, ORIGIN, 0, ORIGIN, HeldStroke(1.0)),))
STIFFNESS = 800.0
RATE = math.sqrt(STIFFNESS / BLOCK.mass)
SHARE = 0.1
AMPLITUDE = 0.01


def shaker(ratio: float) -> Assembly:
  """The 'shaker' function returns the block hung by a spring and a
  damper (a tenth of critical) from a base hung from the world by an
  actuator swinging 'AMPLITUDE' either way about half a metre, 'ratio'
  times as fast as the block bobs."""
  damping = 2.0 * SHARE * math.sqrt(STIFFNESS * BLOCK.mass)
  stroke = SineStroke(0.5, AMPLITUDE, ratio * RATE / (2.0 * math.pi))
  return Assembly((BASE, BLOCK), (Actuator(None, ORIGIN, 0, ORIGIN, stroke),
                                  Spring(0, ORIGIN, 1, ORIGIN, STIFFNESS,
                                         0.5),
                                  Damper(0, ORIGIN, 1, ORIGIN, damping)))


class TestActuator(PhysTest):
  """Tests for 'Actuator'."""

  def test_strokes(self) -> None:
    """A held stroke is its length, still; a sine stroke is its middle
    and its amplitude's sine, growing and slowing as by hand."""
    self.assertEqual(HeldStroke(0.7).at(12.0), (0.7, 0.0, 0.0))
    swing = 2.0 * math.pi * 2.0
    self.assertNear(SineStroke(1.0, 0.1, 2.0).at(0.3),
                    (1.0 + 0.1 * math.sin(swing * 0.3),
                     0.1 * swing * math.cos(swing * 0.3),
                     -0.1 * swing * swing * math.sin(swing * 0.3)), 1e-14)

  def test_pendulum(self) -> None:
    """A block hung by a held rod to its middle, let go 30 degrees out,
    swings at the simple pendulum's period by hand (1 m long), the rod
    kept at its length, the block not turning."""
    swing = math.radians(30.0)
    states = (State((math.sin(swing), 0.0, -math.cos(swing))),)
    crossings, before = [], None
    for step in range(5000):
      states = WORLD.advancedAll(ROD, states, 0.001, 0.001 * step)
      self.assertLess(abs(norm(states[0].place) - 1.0), 1e-12)
      now = math.atan2(states[0].place[0], -states[0].place[2])
      if before is not None and before < 0.0 <= now:
        crossings.append(0.001 * (step + before / (before - now)))
      before = now
    a, b = 1.0, math.cos(0.5 * swing)
    for _ in range(40):
      a, b = 0.5 * (a + b), math.sqrt(a * b)
    period = 2.0 * math.pi * math.sqrt(1.0 / 9.81) / a
    self.assertGreaterEqual(len(crossings), 2)
    for start, end in zip(crossings, crossings[1:]):
      self.assertLess(abs((end - start) / period - 1.0), 2e-6)
    self.assertEqual(states[0].spin, (0.0, 0.0, 0.0))

  def test_pushes(self) -> None:
    """Hanging still, the rod pulls the block's weight (pushing less
    than nought); swinging through the bottom at v, its weight and m v²
    over its length more."""
    hanging = (State((0.0, 0.0, -1.0)),)
    weight = BLOCK.mass * 9.81
    self.assertNear(WORLD.pushesOf(ROD, hanging), (-weight,), 1e-12)
    swinging = (State((0.0, 0.0, -1.0), (1.0, 0.0, 0.0, 0.0),
                      (2.0, 0.0, 0.0)),)
    self.assertNear(WORLD.pushesOf(ROD, swinging),
                    (-weight - BLOCK.mass * 4.0,), 1e-12)
    self.assertEqual(WORLD.pullsOf(ROD, hanging), ())

  def test_shaker(self) -> None:
    """Shaken at half, once and twice the block's own rate, the block
    swings, once settled, at the base's amplitude times the
    transmissibility sqrt((1 + (2 z r)²) / ((1 - r²)² + (2 z r)²))."""
    sag = BLOCK.mass * 9.81 / STIFFNESS
    for ratio in (0.5, 1.0, 2.0):
      assembly = shaker(ratio)
      states = (State((0.0, 0.0, -0.5)), State((0.0, 0.0, -1.0 - sag)))
      states = WORLD.advancedAll(assembly, states, 16.0, 0.0)
      heights = []
      for step in range(1500):
        states = WORLD.advancedAll(assembly, states, 0.001,
                                   16.0 + 0.001 * step)
        heights.append(states[1].place[2])
      swing = 0.5 * (max(heights) - min(heights)) / AMPLITUDE
      both = (2.0 * SHARE * ratio) ** 2
      passed = math.sqrt((1.0 + both) / ((1.0 - ratio ** 2) ** 2 + both))
      self.assertLess(abs(swing / passed - 1.0), 2e-4)

  def test_pieces(self) -> None:
    """A shaken run cut into pieces, each begun at its time, is the run
    whole."""
    assembly = shaker(1.0)
    sag = BLOCK.mass * 9.81 / STIFFNESS
    start = (State((0.0, 0.0, -0.5)), State((0.0, 0.0, -1.0 - sag)))
    whole = WORLD.advancedAll(assembly, start, 1.0, 0.0)
    pieces = WORLD.advancedAll(assembly, WORLD.advancedAll(
      assembly, start, 0.4, 0.0), 0.6, 0.4)
    self.assertNear(pieces, whole, 1e-12)

  def test_unstoppable(self) -> None:
    """A tonne of steel shaken hard keeps to the stroke at every step,
    the actuator pushing as hard as it takes."""
    steel = Body.of(boxShape(0.5, 0.5, 0.5), 8000.0)
    stroke = SineStroke(1.0, 0.2, 5.0)
    shaken = Assembly((steel,), (Actuator(None, ORIGIN, 0, ORIGIN, stroke),))
    states = (State((0.0, 0.0, -1.0)),)
    most = 0.0
    for step in range(400):
      time = 0.001 * (step + 1)
      states = WORLD.advancedAll(shaken, states, 0.001, time - 0.001)
      self.assertLess(abs(norm(states[0].place) - stroke.at(time)[0]),
                      1e-12)
      most = max(most, abs(WORLD.pushesOf(shaken, states, time)[0]))
    self.assertGreater(most, steel.mass * 0.2 * (2.0 * math.pi * 5.0) ** 2)
