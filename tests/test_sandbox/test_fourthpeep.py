"""
TestFourthPeep covers a control in the world ('FourthPeep'), a lever:
used, it is thrown to its other end over 'THROW' s as the world steps,
and used again back; its handle turns from its near angle to its far
one with it, its knob at the handle's end, carried by its body; its
prompt says what using it does (its own, given).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.sandbox import FourthPeep
from worQt.gaming.sandbox._fourthpeep import THROW

from . import SandboxTest


class TestFourthPeep(SandboxTest):
  """Tests for a lever."""

  def lever(self, ) -> FourthPeep:
    """Returns a lever on the world 1 m up, turning about y from 0.4 rad
    to -0.4 rad, its handle 0.5 m long."""
    return FourthPeep('brake', None, (0.0, 0.0, 1.0), (0.0, 2.0, 0.0),
                      0.5, 0.4, -0.4)

  def test_thrown(self) -> None:
    """Used, it goes to its far end over 'THROW' s, no further; used
    again, back."""
    lever = self.lever()
    self.assertEqual((lever.value, lever.target), (0.0, 0.0))
    lever.used()
    lever.acted([], 0.5 * THROW)
    self.assertAlmostEqual(lever.value, 0.5, 12)
    lever.acted([], THROW)
    self.assertEqual(lever.value, 1.0)
    lever.used()
    lever.acted([], 0.25 * THROW)
    self.assertAlmostEqual(lever.value, 0.75, 12)

  def test_handle(self) -> None:
    """Its knob is at the handle's end, turned about its axis by its
    angle (released at the near one, pulled at the far one)."""
    lever = self.lever()
    for value, angle in ((0.0, 0.4), (1.0, -0.4)):
      with self.subTest(value=value):
        lever.value = value
        self.assertAlmostEqual(lever.angle(), angle, 12)
        base, _, knob = lever.handleOf(None, ())
        self.assertEqual(base, (0.0, 0.0, 1.0))
        for got, wanted in zip(knob, (0.5 * math.sin(angle), 0.0,
                                      1.0 + 0.5 * math.cos(angle))):
          self.assertAlmostEqual(got, wanted, 12)

  def test_carried(self) -> None:
    """On a body, its handle goes with the body."""
    world, _ = self.islandWorld()
    lever = FourthPeep('brake', 0, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 0.5,
                       0.0, 0.0)
    base, _, knob = lever.handleOf(world.assembly, world.states)
    body = world.assembly.bodies[0]
    for got, wanted in zip(base, body.placeOf(world.states[0],
                                              (0.0, 0.0, 0.0))):
      self.assertAlmostEqual(got, wanted, 12)
    self.assertAlmostEqual(math.dist(base, knob), 0.5, 12)

  def test_prompt(self) -> None:
    """Its prompt says what using it does: 'Pull' and 'Release' its name,
    or its own prompts for its two ends."""
    lever = self.lever()
    self.assertEqual(lever.prompt(), 'Pull brake')
    lever.used()
    self.assertEqual(lever.prompt(), 'Release brake')
    points = FourthPeep('points', None, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                        0.8, -0.4, 0.4, ('Set for the siding',
                                         'Set for the line'))
    self.assertEqual(points.prompt(), 'Set for the siding')
    points.used()
    self.assertEqual(points.prompt(), 'Set for the line')

  def test_refused(self) -> None:
    """A lever about no axis is refused."""
    with self.assertRaises(ValueError):
      FourthPeep('brake', None, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.5,
                 0.0, 1.0)
