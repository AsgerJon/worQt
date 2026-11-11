"""
The private '_space' module holds the little vector sums of the scene,
on plain tuples of three floats.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

Vector = tuple[float, float, float]


def add(a: Vector, b: Vector) -> Vector:
  """The sum of 'a' and 'b'."""
  return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def sub(a: Vector, b: Vector) -> Vector:
  """'a' less 'b'."""
  return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def scaled(a: Vector, factor: float) -> Vector:
  """'a' times 'factor'."""
  return a[0] * factor, a[1] * factor, a[2] * factor


def dot(a: Vector, b: Vector) -> float:
  """The dot product of 'a' and 'b'."""
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vector, b: Vector) -> Vector:
  """The cross product of 'a' and 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])


def length(a: Vector) -> float:
  """How long 'a' is."""
  return math.sqrt(dot(a, a))


def unit(a: Vector) -> Vector:
  """'a' a unit long, or along x if it has no length."""
  size = length(a)
  if size < 1e-12:
    return 1.0, 0.0, 0.0
  return scaled(a, 1.0 / size)


def across(a: Vector) -> tuple[Vector, Vector]:
  """Two unit vectors square to 'a' and to each other."""
  axis = unit(a)
  other = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
  first = unit(cross(axis, other))
  return first, cross(axis, first)
