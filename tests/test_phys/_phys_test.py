"""
PhysTest is the base class for the tests of 'worQt.phys': it subclasses
'BaseTest', adding 'assertNear' for vectors, matrices and turns.

'lShape' is an L of two boxes, 1 x 0.2 x 0.2 m along x at the origin and
0.2 x 0.2 x 0.6 m standing on its end at x 0.4, z 0.4, touching it: by
hand, 0.04 and 0.024 m³, its centre at x 0.15, z 0.15.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.phys import UNTURNED, Shape, boxShape


def lShape() -> Shape:
  """The 'lShape' function returns the L of two boxes."""
  lying = boxShape(1.0, 0.2, 0.2)
  standing = boxShape(0.2, 0.2, 0.6).moved((0.4, 0.0, 0.4), UNTURNED)
  return lying.joined(standing)


def _flat(value: object) -> tuple:
  """The '_flat' function returns the numbers in 'value', nested tuples
  of numbers, in order."""
  if isinstance(value, (tuple, list)):
    return tuple(x for part in value for x in _flat(part))
  return float(value),


class PhysTest(BaseTest):
  """PhysTest is the base class for the tests of 'worQt.phys'."""

  def assertNear(self, value: object, expected: object,
                 within: float) -> None:
    """Asserts that 'value' and 'expected', numbers or nested tuples of
    numbers, are alike within 'within' in each part."""
    got, wanted = _flat(value), _flat(expected)
    self.assertEqual(len(got), len(wanted))
    worst = max((abs(a - b) for a, b in zip(got, wanted)), default=0.0)
    self.assertLessEqual(worst, within, '%r against %r' % (value,
                                                          expected))

  def assertSameTurn(self, turn: tuple, expected: tuple,
                     within: float) -> None:
    """Asserts that the unit quaternions 'turn' and 'expected' are the
    same turn, within 'within' in each part (a quaternion and its
    negative are one turn)."""
    if sum(a * b for a, b in zip(turn, expected)) < 0.0:
      turn = tuple(-a for a in turn)
    self.assertNear(turn, expected, within)
