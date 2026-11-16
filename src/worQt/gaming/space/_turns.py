"""
Turns as the space package keeps them on the host: quaternions w x y z
(the sandbox's order) and three-row matrices, Python's floats.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math


def rotated(turn: tuple, x: tuple) -> tuple:
  """Returns 'x' turned by the quaternion 'turn' (w x y z)."""
  w, a, b, c = turn
  tx = 2.0 * (b * x[2] - c * x[1])
  ty = 2.0 * (c * x[0] - a * x[2])
  tz = 2.0 * (a * x[1] - b * x[0])
  return (x[0] + w * tx + b * tz - c * ty,
          x[1] + w * ty + c * tx - a * tz,
          x[2] + w * tz + a * ty - b * tx)


def unrotated(turn: tuple, x: tuple) -> tuple:
  """Returns 'x' turned back by the quaternion 'turn'."""
  w, a, b, c = turn
  return rotated((w, -a, -b, -c), x)


def product(one: tuple, two: tuple) -> tuple:
  """Returns the quaternion 'one' times 'two' ('two' first, then
  'one')."""
  w1, x1, y1, z1 = one
  w2, x2, y2, z2 = two
  return (w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
          w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
          w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
          w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2)


def aboutAxis(axis: tuple, angle: float) -> tuple:
  """Returns the quaternion turning 'angle' rad about the unit 'axis'."""
  half = 0.5 * angle
  sin = math.sin(half)
  return math.cos(half), axis[0] * sin, axis[1] * sin, axis[2] * sin


def quaternionOf(rows: tuple) -> tuple:
  """Returns the quaternion (w x y z) of the turn 'rows' (three rows, a
  proper rotation)."""
  (a, b, c), (d, e, f), (g, h, i) = rows
  trace = a + e + i
  if trace > 0.0:
    s = 2.0 * math.sqrt(trace + 1.0)
    out = 0.25 * s, (h - f) / s, (c - g) / s, (d - b) / s
  elif a > e and a > i:
    s = 2.0 * math.sqrt(1.0 + a - e - i)
    out = (h - f) / s, 0.25 * s, (b + d) / s, (c + g) / s
  elif e > i:
    s = 2.0 * math.sqrt(1.0 + e - a - i)
    out = (c - g) / s, (b + d) / s, 0.25 * s, (f + h) / s
  else:
    s = 2.0 * math.sqrt(1.0 + i - a - e)
    out = (d - b) / s, (c + g) / s, (f + h) / s, 0.25 * s
  size = math.sqrt(sum(x * x for x in out))
  return tuple(x / size for x in out)


def matrixTimes(rows: tuple, x: tuple) -> tuple:
  """Returns 'x' turned by the matrix 'rows'."""
  return tuple(r[0] * x[0] + r[1] * x[1] + r[2] * x[2] for r in rows)


def matrixBack(rows: tuple, x: tuple) -> tuple:
  """Returns 'x' turned back by the matrix 'rows' (its transpose)."""
  return tuple(rows[0][k] * x[0] + rows[1][k] * x[1] + rows[2][k] * x[2]
               for k in range(3))


def cross(a: tuple, b: tuple) -> tuple:
  """Returns the cross product of 'a' and 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])


def dot(a: tuple, b: tuple) -> float:
  """Returns the dot product of 'a' and 'b'."""
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a: tuple) -> float:
  """Returns the length of 'a'."""
  return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def unit(a: tuple) -> tuple:
  """Returns 'a' made one long."""
  size = norm(a)
  return a[0] / size, a[1] / size, a[2] / size
