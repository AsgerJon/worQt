"""
TestSight covers the Grav-Gun's line of sight (user, 2026-11-17: "the
gravgun should not be able to grab bolts through walls"; then "the
fucking gravity gun still works through walls": its rooms were looked
at every 15 cm, stepping over the hull's 5 cm, and solids were not
looked at at all): no wall between two rooms is stepped over however
thin, a solid box in the way blocks it (turned or not), out of the way
it does not.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.space._sight import SHORT, inSight

from . import SpaceTest

#  Two rooms either side of a wall 5 cm thick (x from 0 to 0.05).
WALL = 0.05


def _rooms(point: tuple) -> float:
  """Returns how deep 'point' is in two boxes, x -4 .. 0 and 0.05 .. 4
  (y and z -2 .. 2), m."""
  x, y, z = point
  across = min(2.0 - abs(y), 2.0 - abs(z))
  return max(min(x + 4.0, -x, across), min(x - WALL, 4.0 - x, across))


def _boxes(*boxes: tuple) -> tuple:
  """Returns 'boxes' (each its middle, half sizes and turn about z, rad)
  as 'inSight' takes them."""
  if not boxes:
    return numpy.zeros((0, 3)), numpy.zeros((0, 3)), numpy.zeros((0, 3, 3))
  middles = numpy.array([b[0] for b in boxes], numpy.float64)
  halves = numpy.array([b[1] for b in boxes], numpy.float64)
  axes = numpy.array([[[math.cos(b[2]), -math.sin(b[2]), 0.0],
                       [math.sin(b[2]), math.cos(b[2]), 0.0],
                       [0.0, 0.0, 1.0]] for b in boxes], numpy.float64)
  return middles, halves, axes


class TestSight(SpaceTest):
  """Tests for the Grav-Gun's line of sight."""

  def test_thin_wall(self) -> None:
    """Across a wall 5 cm thick between two rooms it sees nothing, from
    near it or far, square or slanting; within a room it sees."""
    nothing = _boxes()
    for eye, there in (((-0.5, 0.0, 0.0), (3.0, 0.0, 0.0)),
                       ((-3.9, 1.0, 0.5), (3.9, -1.0, -0.5)),
                       ((-0.01, 0.0, 0.0), (0.3, 0.0, 0.0))):
      self.assertFalse(inSight(eye, there, _rooms, nothing))
    self.assertTrue(inSight((-3.0, 1.0, 0.0), (-0.3, -1.0, 0.5), _rooms,
                            nothing))

  def test_solids(self) -> None:
    """A solid box in the way blocks it, turned or not; beside the way,
    or beyond what it aims at, it does not."""
    eye, there = (-3.5, 0.0, 0.0), (-0.5, 0.0, 0.0)
    self.assertTrue(inSight(eye, there, _rooms, _boxes()))
    for turn in (0.0, 0.7):
      blocking = _boxes(((-2.0, 0.0, 0.0), (0.1, 0.4, 0.4), turn))
      self.assertFalse(inSight(eye, there, _rooms, blocking))
    aside = _boxes(((-2.0, 1.0, 0.0), (0.1, 0.4, 0.4), 0.0))
    self.assertTrue(inSight(eye, there, _rooms, aside))
    beyond = _boxes(((-0.5 + 0.5 * SHORT, 0.0, 0.0), (0.05, 0.4, 0.4),
                     0.0))
    self.assertTrue(inSight(eye, there, _rooms, beyond))
