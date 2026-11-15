"""
The vectors, matrices and turns the physics reckons with, as plain
tuples of floats, every sum written out, so a port to C++ follows it
line for line: a 'Vector' (x, y, z), a 'Matrix' (three rows), a
'Quaternion' (w, x, y, z), scalar first, a unit one a turn.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

Vector = tuple[float, float, float]
Matrix = tuple[Vector, Vector, Vector]
Quaternion = tuple[float, float, float, float]

ORIGIN = (0.0, 0.0, 0.0)
UNTURNED = (1.0, 0.0, 0.0, 0.0)
IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
AXES = IDENTITY


def plus(a: Vector, b: Vector) -> Vector:
  """The 'plus' function returns 'a' + 'b'."""
  return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def minus(a: Vector, b: Vector) -> Vector:
  """The 'minus' function returns 'a' - 'b'."""
  return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def scaled(a: Vector, factor: float) -> Vector:
  """The 'scaled' function returns 'a' times 'factor'."""
  return a[0] * factor, a[1] * factor, a[2] * factor


def dot(a: Vector, b: Vector) -> float:
  """The 'dot' function returns the dot product of 'a' and 'b'."""
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vector, b: Vector) -> Vector:
  """The 'cross' function returns the cross product 'a' x 'b'."""
  return (a[1] * b[2] - a[2] * b[1],
          a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])


def norm(a: Vector) -> float:
  """The 'norm' function returns the length of 'a'."""
  return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def applied(m: Matrix, v: Vector) -> Vector:
  """The 'applied' function returns the matrix 'm' times 'v'."""
  return dot(m[0], v), dot(m[1], v), dot(m[2], v)


def transposed(m: Matrix) -> Matrix:
  """The 'transposed' function returns 'm' transposed."""
  return ((m[0][0], m[1][0], m[2][0]),
          (m[0][1], m[1][1], m[2][1]),
          (m[0][2], m[1][2], m[2][2]))


def matrixProduct(a: Matrix, b: Matrix) -> Matrix:
  """The 'matrixProduct' function returns the matrix 'a' times 'b'."""
  columns = transposed(b)
  return (applied(columns, a[0]), applied(columns, a[1]),
          applied(columns, a[2]))


def product(p: Quaternion, q: Quaternion) -> Quaternion:
  """The 'product' function returns the quaternion 'p' times 'q':
  turned by 'q', then by 'p'."""
  return (p[0] * q[0] - p[1] * q[1] - p[2] * q[2] - p[3] * q[3],
          p[0] * q[1] + p[1] * q[0] + p[2] * q[3] - p[3] * q[2],
          p[0] * q[2] - p[1] * q[3] + p[2] * q[0] + p[3] * q[1],
          p[0] * q[3] + p[1] * q[2] - p[2] * q[1] + p[3] * q[0])


def conjugate(q: Quaternion) -> Quaternion:
  """The 'conjugate' function returns 'q' with its vector part
  reversed: a turn's way back."""
  return q[0], -q[1], -q[2], -q[3]


def normalised(q: Quaternion) -> Quaternion:
  """The 'normalised' function returns 'q' made a unit quaternion."""
  size = math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
  return q[0] / size, q[1] / size, q[2] / size, q[3] / size


def turnAbout(axis: Vector, angle: float) -> Quaternion:
  """The 'turnAbout' function returns the turn by 'angle' radians about
  'axis', anticlockwise seen from its tip."""
  size = norm(axis)
  half = 0.5 * angle
  share = math.sin(half) / size
  return math.cos(half), axis[0] * share, axis[1] * share, axis[2] * share


def rotated(q: Quaternion, v: Vector) -> Vector:
  """The 'rotated' function returns 'v' turned by the unit quaternion
  'q'."""
  w, x, y, z = q
  tx = 2.0 * (y * v[2] - z * v[1])
  ty = 2.0 * (z * v[0] - x * v[2])
  tz = 2.0 * (x * v[1] - y * v[0])
  return (v[0] + w * tx + y * tz - z * ty,
          v[1] + w * ty + z * tx - x * tz,
          v[2] + w * tz + x * ty - y * tx)


def matrixOf(q: Quaternion) -> Matrix:
  """The 'matrixOf' function returns the unit quaternion 'q' as a
  matrix: its columns are the axes turned."""
  w, x, y, z = q
  return ((1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z),
           2.0 * (x * z + w * y)),
          (2.0 * (x * y + w * z), 1.0 - 2.0 * (x * x + z * z),
           2.0 * (y * z - w * x)),
          (2.0 * (x * z - w * y), 2.0 * (y * z + w * x),
           1.0 - 2.0 * (x * x + y * y)))


def turnOf(m: Matrix) -> Quaternion:
  """The 'turnOf' function returns the unit quaternion of the rotation
  matrix 'm' (Shepperd's way: from its largest part, so never near
  dividing by nought), the scalar part not negative."""
  trace = m[0][0] + m[1][1] + m[2][2]
  if trace >= max(m[0][0], m[1][1], m[2][2]):
    s = 2.0 * math.sqrt(1.0 + trace)
    q = (0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s,
         (m[1][0] - m[0][1]) / s)
  elif m[0][0] >= m[1][1] and m[0][0] >= m[2][2]:
    s = 2.0 * math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2])
    q = ((m[2][1] - m[1][2]) / s, 0.25 * s, (m[0][1] + m[1][0]) / s,
         (m[0][2] + m[2][0]) / s)
  elif m[1][1] >= m[2][2]:
    s = 2.0 * math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2])
    q = ((m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, 0.25 * s,
         (m[1][2] + m[2][1]) / s)
  else:
    s = 2.0 * math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1])
    q = ((m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
         (m[1][2] + m[2][1]) / s, 0.25 * s)
  q = normalised(q)
  return q if q[0] >= 0.0 else (-q[0], -q[1], -q[2], -q[3])


def solved(matrix: list[list[float]], right: list[float]) -> list[float]:
  """The 'solved' function returns x with 'matrix' x = 'right'
  (Gaussian elimination, the largest pivot first). A matrix with no
  pivot, so no single solution (ties holding what is held already, or
  nothing that moves), is refused."""
  size = len(right)
  rows = [list(row) + [value] for row, value in zip(matrix, right)]
  largest = max((abs(x) for row in matrix for x in row), default=0.0)
  for k in range(size):
    pivot = max(range(k, size), key=lambda r: abs(rows[r][k]))
    if abs(rows[pivot][k]) <= 1e-12 * largest:
      raise ValueError('no single solution: held twice, or nothing held')
    rows[k], rows[pivot] = rows[pivot], rows[k]
    for r in range(k + 1, size):
      share = rows[r][k] / rows[k][k]
      if share != 0.0:
        for c in range(k, size + 1):
          rows[r][c] -= share * rows[k][c]
  solution = [0.0] * size
  for k in range(size - 1, -1, -1):
    known = sum(rows[k][c] * solution[c] for c in range(k + 1, size))
    solution[k] = (rows[k][size] - known) / rows[k][k]
  return solution
