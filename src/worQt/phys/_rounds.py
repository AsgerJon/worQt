"""
The round contacts: a ball against a ball, or against any body's
shape, met at the nearest point. A round contact is one point: the
contact's push and grip act there, its stiffness N/m at that point (not
per metre of edge, as edges have it), and its bristle is a stretch kept
in the ball's holds that only slipping stretches, as on the ground.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._shape import Sphere
from ._turned import Turned
from ._vectors import Vector, applied, conjugate, dot, matrixOf, minus
from ._vectors import norm, plus, product, scaled, transposed

#  The point index a ball's contact is held under in its holds: a ball
#  has no skin to number.
ROUND = -1


def isRound(mover) -> bool:
  """The 'isRound' function tells whether a body, as stepped, is a
  ball."""
  return isinstance(mover.body.shape, Sphere)


def piecesOf(mover) -> tuple:
  """The 'piecesOf' function returns a body's shape as a ball meets it,
  along its principal axes: each piece (faces sharing corners, taken
  convex) as its faces' planes (outward normal, how far along it), the
  box about its corners (least, most), whether it is that box, and its
  triangles; and how far its farthest corner is from its centre."""
  shape, body = mover.body.shape, mover.body
  back = transposed(matrixOf(mover.axes))
  arms = [applied(back, minus(point, body.centre)) for point in shape.points]
  leader = list(range(len(shape.points)))

  def leaderOf(index: int) -> int:
    """Returns the least point joined to 'index' so far."""
    while leader[index] != index:
      index = leader[index]
    return index

  for face in shape.faces:
    least = min(leaderOf(index) for index in face)
    for index in face:
      leader[leaderOf(index)] = least
  groups: dict[int, set[int]] = {}
  for face in shape.faces:
    groups.setdefault(leaderOf(face[0]), set()).update(face)
  pieces = []
  for key in sorted(groups):
    corners = sorted(groups[key])
    points = [arms[i] for i in corners]
    low = tuple(min(p[i] for p in points) for i in range(3))
    high = tuple(max(p[i] for p in points) for i in range(3))
    size = max(high[i] - low[i] for i in range(3))
    box = len(points) == 8 and all(
      min(abs(p[i] - low[i]), abs(p[i] - high[i])) <= 1e-9 * size
      for p in points for i in range(3))
    triangles, planes = [], []
    for i, j, k in shape.faces:
      if i in groups[key]:
        a, b, c = arms[i], arms[j], arms[k]
        triangles.append((a, b, c))
        facing = _crossed(minus(b, a), minus(c, a))
        length = norm(facing)
        if length > 0.0:
          facing = scaled(facing, 1.0 / length)
          planes.append((facing, dot(facing, a)))
    pieces.append((tuple(planes), low, high, box, tuple(triangles)))
  return tuple(pieces), max((norm(arm) for arm in arms), default=0.0)


def isTurned(mover) -> bool:
  """The 'isTurned' function tells whether a body, as stepped, is a
  turned solid ('Turned')."""
  return isinstance(mover.body.shape, Turned)


def turnedTouches(ball, other) -> list[tuple]:
  """The 'turnedTouches' function returns where the ball 'ball'
  presses the turned solid 'other': for each piece of its profile it
  presses ('Turned.presses', in the cut through the ball's middle and
  the axis), the piece's place, the normal pushing the ball out, how
  deep, and the point half way between the ball's surface and the
  solid's, in the world."""
  r = ball.round
  own = matrixOf(product(other.turn, conjugate(other.axes)))
  d = minus(ball.place, other.place)
  p = plus(applied(transposed(own), d), other.body.centre)
  rho = math.sqrt(p[0] * p[0] + p[1] * p[1])
  ux, uy = (p[0] / rho, p[1] / rho) if rho > 0.0 else (1.0, 0.0)
  out = []
  for at, nr, nw, depth in other.body.shape.presses(rho, p[2], r):
    normal = applied(own, (nr * ux, nr * uy, nw))
    point = minus(ball.place, scaled(normal, r - 0.5 * depth))
    out.append((at, normal, depth, point))
  return out


def roundTouch(ball, other, pieces: tuple | None) -> tuple | None:
  """The 'roundTouch' function returns where the ball 'ball' presses
  'other' (a ball, or a body of 'pieces' as 'piecesOf' gives them): the
  normal pushing the ball out, how deep, and the point, in the world,
  half way between the ball's surface and the other's; None where they
  do not touch."""
  r = ball.round
  cx, cy, cz = ball.place
  ox, oy, oz = other.place
  dx, dy, dz = cx - ox, cy - oy, cz - oz
  far = dx * dx + dy * dy + dz * dz
  if other.round:
    reach = r + other.round
    if far >= reach * reach or far == 0.0:
      return None
    apart = math.sqrt(far)
    normal = (dx / apart, dy / apart, dz / apart)
    depth = reach - apart
  else:
    shape, reach = pieces
    if far >= (reach + r) * (reach + r):
      return None
    turning = matrixOf(other.turn)
    inside = applied(transposed(turning), (dx, dy, dz))
    found = nearestOn(shape, inside, r)
    if found is None:
      return None
    facing, depth = found
    normal = applied(turning, facing)
  point = minus(ball.place, scaled(normal, r - 0.5 * depth))
  return normal, depth, point


def nearestOn(pieces: tuple, p: Vector, radius: float) -> tuple | None:
  """The 'nearestOn' function returns how a ball of 'radius' centred
  at 'p' presses a body of 'pieces' (all along the body's principal
  axes): the normal out of the body, and how deep, at the piece it
  presses deepest; None where it touches none. Its centre inside a
  piece, it is pushed out by the face it is least deep behind; outside,
  from the piece's nearest point (a box's by clamping, else the nearest
  of its triangles)."""
  best = None
  for planes, low, high, box, triangles in pieces:
    if (p[0] < low[0] - radius or p[0] > high[0] + radius
        or p[1] < low[1] - radius or p[1] > high[1] + radius
        or p[2] < low[2] - radius or p[2] > high[2] + radius):
      continue
    behind = [(offset - dot(facing, p), facing) for facing, offset in planes]
    if all(under >= 0.0 for under, _ in behind):
      under, facing = min(behind, key=lambda pair: pair[0])
      found = (facing, radius + under)
    else:
      if box:
        q = (min(max(p[0], low[0]), high[0]),
             min(max(p[1], low[1]), high[1]),
             min(max(p[2], low[2]), high[2]))
      else:
        q = min((_onTriangle(p, *triangle) for triangle in triangles),
                key=lambda point: _distance2(point, p))
      off = minus(p, q)
      apart = norm(off)
      if apart >= radius or apart == 0.0:
        continue
      found = (scaled(off, 1.0 / apart), radius - apart)
    if best is None or found[1] > best[1]:
      best = found
  return best


def _distance2(a: Vector, b: Vector) -> float:
  """Returns how far apart 'a' and 'b' are, squared."""
  dx, dy, dz = a[0] - b[0], a[1] - b[1], a[2] - b[2]
  return dx * dx + dy * dy + dz * dz


def _crossed(a: Vector, b: Vector) -> Vector:
  """Returns 'a' crossed with 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])


def _onTriangle(p: Vector, a: Vector, b: Vector, c: Vector) -> Vector:
  """Returns the point of the triangle 'a' 'b' 'c' nearest 'p' (as
  Ericson's 'Real-Time Collision Detection' finds it: by the region of
  the triangle's corners, edges and face 'p' lies over)."""
  ab, ac, ap = minus(b, a), minus(c, a), minus(p, a)
  d1, d2 = dot(ab, ap), dot(ac, ap)
  if d1 <= 0.0 and d2 <= 0.0:
    return a
  bp = minus(p, b)
  d3, d4 = dot(ab, bp), dot(ac, bp)
  if d3 >= 0.0 and d4 <= d3:
    return b
  vc = d1 * d4 - d3 * d2
  if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
    return plus(a, scaled(ab, d1 / (d1 - d3)))
  cp = minus(p, c)
  d5, d6 = dot(ab, cp), dot(ac, cp)
  if d6 >= 0.0 and d5 <= d6:
    return c
  vb = d5 * d2 - d1 * d6
  if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
    return plus(a, scaled(ac, d2 / (d2 - d6)))
  va = d3 * d6 - d5 * d4
  if va <= 0.0 and d4 - d3 >= 0.0 and d5 - d6 >= 0.0:
    share = (d4 - d3) / ((d4 - d3) + (d5 - d6))
    return plus(b, scaled(minus(c, b), share))
  whole = 1.0 / (va + vb + vc)
  return plus(a, plus(scaled(ab, vb * whole), scaled(ac, vc * whole)))
