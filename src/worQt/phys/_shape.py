"""
Shape is the outside of a solid, any solid: a closed surface of
triangles. From it come the solid's volume, centre and moments, exact
for the surface as given (curved solids are as true as their facets).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

from ._vectors import Matrix, Quaternion, Vector
from ._vectors import cross, dot, minus, norm, plus, rotated, scaled


#  Faces meet flat, making no edge, when their normals lie closer than
#  this (the cosine of about a hundredth of a degree).
_FLAT = 1.0 - 1e-8


class Shape(NamedTuple):
  """
  Shape is a solid's surface: 'points' (x, y, z) in the solid's own
  frame, m, and 'faces', each three indices into them, anticlockwise
  seen from outside; together closed, every edge shared by two faces
  running it opposite ways. A solid of several pieces is one shape; a
  piece inside another, turned inside out, is a hollow.
  """

  points: tuple[Vector, ...]
  faces: tuple[tuple[int, int, int], ...]

  def moments(self, ) -> tuple[float, Vector, Matrix]:
    """The 'moments' method returns the solid's volume, its first moment
    (the integral of the place over it) and its second (of the place
    times itself), about its frame's origin: each face with the origin
    a tetrahedron, signed, summed (exact for any closed surface)."""
    volume, first = 0.0, (0.0, 0.0, 0.0)
    second = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    for i, j, k in self.faces:
      a, b, c = self.points[i], self.points[j], self.points[k]
      sixfold = dot(a, cross(b, c))
      volume += sixfold / 6.0
      s = plus(plus(a, b), c)
      first = plus(first, (s[0] * sixfold / 24.0, s[1] * sixfold / 24.0,
                           s[2] * sixfold / 24.0))
      for row in range(3):
        for column in range(3):
          part = (a[row] * a[column] + b[row] * b[column]
                  + c[row] * c[column] + s[row] * s[column])
          second[row][column] += part * sixfold / 120.0
    return volume, first, (tuple(second[0]), tuple(second[1]),
                           tuple(second[2]))

  def volume(self, ) -> float:
    """The 'volume' method returns the solid's volume, m³; below nought
    when its faces are turned inside out."""
    return self.moments()[0]

  def centre(self, ) -> Vector:
    """The 'centre' method returns the solid's centre (of mass, made of
    one stuff), in its own frame."""
    volume, first, _ = self.moments()
    return first[0] / volume, first[1] / volume, first[2] / volume

  def isClosed(self, ) -> bool:
    """The 'isClosed' method tells whether the faces close, every edge
    run once each way."""
    edges = {}
    for face in self.faces:
      for start, end in zip(face, face[1:] + face[:1]):
        edges[(start, end)] = edges.get((start, end), 0) + 1
    for (start, end), count in edges.items():
      if count != 1 or edges.get((end, start), 0) != 1:
        return False
    return True if edges else False

  def pieces(self, ) -> tuple[tuple[tuple[Vector, float], ...], ...]:
    """The 'pieces' method returns the solid's pieces as '_piecesOf' finds
    them, remembered."""
    return _piecesOf(self)

  def piecesFound(self, ) -> tuple[tuple[tuple[Vector, float], ...], ...]:
    """The 'piecesFound' method returns the solid's pieces (its faces
    sharing corners, each piece closed and convex, as a box, a cylinder,
    or each box of two joined), each as the planes of its faces: each
    face's outward unit normal and how far along it the face lies, so a
    point is inside the piece where it is not past any of them."""
    leader = list(range(len(self.points)))

    def leaderOf(index: int) -> int:
      """Returns the least point joined to 'index' so far."""
      while leader[index] != index:
        index = leader[index]
      return index

    for face in self.faces:
      least = min(leaderOf(index) for index in face)
      for index in face:
        leader[leaderOf(index)] = least
    pieces: dict[int, list[tuple[Vector, float]]] = {}
    for i, j, k in self.faces:
      a, b, c = self.points[i], self.points[j], self.points[k]
      facing = cross(minus(b, a), minus(c, a))
      size = norm(facing)
      if size == 0.0:
        continue
      normal = scaled(facing, 1.0 / size)
      pieces.setdefault(leaderOf(i), []).append((normal, dot(normal, a)))
    return tuple(tuple(planes) for _, planes in sorted(pieces.items()))

  def edges(self, ) -> tuple[tuple[int, int], ...]:
    """The 'edges' method returns the solid's real edges as
    'edgesFound' finds them, remembered."""
    return _edgesOf(self)

  def edgesFound(self, ) -> tuple[tuple[int, int], ...]:
    """The 'edgesFound' method returns the solid's real edges, each its two
    points' indices, least first: where two faces meet at an angle (not
    the diagonals splitting a flat face into triangles), or where a
    face has no neighbour."""
    facing = []
    for i, j, k in self.faces:
      a, b, c = self.points[i], self.points[j], self.points[k]
      across = cross(minus(b, a), minus(c, a))
      size = norm(across)
      facing.append(scaled(across, 1.0 / size) if size else (0.0,) * 3)
    sides: dict[tuple[int, int], list[int]] = {}
    for at, face in enumerate(self.faces):
      for start, end in zip(face, face[1:] + face[:1]):
        sides.setdefault((min(start, end), max(start, end)), []).append(at)
    return tuple(sorted(edge for edge, faces in sides.items()
                        if len(faces) != 2
                        or dot(facing[faces[0]], facing[faces[1]]) < _FLAT))

  def skin(self, spacing: float) -> tuple[tuple[Vector, float], ...]:
    """The 'skin' method returns the solid's skin as 'skinFound' finds
    it, remembered."""
    return _skinOf(self, spacing)

  def faceLength(self, spacing: float) -> float:
    """The 'faceLength' method returns the most edge length, m, of the
    skin 'spacing' apart lying on any one face's plane: as much as could
    press on anything at once, a face laid flat on it."""
    return _faceLengthOf(self, spacing)

  def skinFound(self, spacing: float) -> tuple:
    """The 'skinFound' method returns the solid's edges as points no
    more than 'spacing' apart, each with its share of the edges' length,
    m: the corners first, by index, then each edge's points between,
    edge by edge; a corner's share half of each piece of edge at it."""
    corners: dict[int, float] = {}
    between = []
    for start, end in self.edges():
      a, b = self.points[start], self.points[end]
      length = norm(minus(b, a))
      count = max(1, math.ceil(length / spacing - 1e-9))
      piece = length / count
      corners[start] = corners.get(start, 0.0) + 0.5 * piece
      corners[end] = corners.get(end, 0.0) + 0.5 * piece
      for k in range(1, count):
        share = k / count
        between.append((plus(a, scaled(minus(b, a), share)), piece))
    out = tuple((self.points[index], corners[index])
                for index in sorted(corners))
    return out + tuple(between)

  def moved(self, place: Vector, turn: Quaternion) -> Shape:
    """The 'moved' method returns the same solid turned by 'turn' and
    then moved by 'place', in its frame."""
    points = tuple(plus(rotated(turn, point), place)
                   for point in self.points)
    return Shape(points, self.faces)

  def joined(self, other: Shape) -> Shape:
    """The 'joined' method returns this solid and 'other' as one."""
    count = len(self.points)
    faces = tuple((i + count, j + count, k + count)
                  for i, j, k in other.faces)
    return Shape(self.points + other.points, self.faces + faces)


class Sphere(NamedTuple):
  """
  Sphere is a ball's surface, exactly round: 'radius', m, about the
  origin of its own frame. Its solid's moments are exact, and it has no
  corners: what it touches meets it at its nearest point, wherever the
  ball has turned (so far only the ground does).
  """

  radius: float

  def moments(self, ) -> tuple[float, Vector, Matrix]:
    """The 'moments' method returns the solid ball's volume, its first
    moment and its second about its frame's origin, its middle: 4/3 pi
    r³, nought, and 4/15 pi r^5 along each axis."""
    r = self.radius
    second = 4.0 / 15.0 * math.pi * r ** 5
    return (4.0 / 3.0 * math.pi * r ** 3, (0.0, 0.0, 0.0),
            ((second, 0.0, 0.0), (0.0, second, 0.0), (0.0, 0.0, second)))

  def volume(self, ) -> float:
    """The 'volume' method returns the ball's volume, m³."""
    return self.moments()[0]

  def centre(self, ) -> Vector:
    """The 'centre' method returns the ball's middle, its frame's
    origin."""
    return 0.0, 0.0, 0.0

  def isClosed(self, ) -> bool:
    """The 'isClosed' method tells that a ball is closed, always."""
    return True


def boxShape(length: float, width: float, height: float) -> Shape:
  """The 'boxShape' function returns a box 'length' along x, 'width'
  along y and 'height' along z, its middle at the origin."""
  points = tuple((0.5 * length * (1 if i & 1 else -1),
                  0.5 * width * (1 if i & 2 else -1),
                  0.5 * height * (1 if i & 4 else -1)) for i in range(8))
  faces = ((0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6),
           (0, 1, 5), (0, 5, 4), (2, 6, 7), (2, 7, 3),
           (0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5))
  return Shape(points, faces)


def wedgeShape(length: float, width: float, height: float) -> Shape:
  """The 'wedgeShape' function returns a wedge (a ramp): 'length' along
  y, 'width' along x, its top rising from nought at its back (-y) to
  'height' at its front (+y), straight up there; the middle of its
  bottom at the origin."""
  x, y = 0.5 * width, 0.5 * length
  points = ((-x, -y, 0.0), (x, -y, 0.0), (x, y, 0.0), (-x, y, 0.0),
            (-x, y, height), (x, y, height))
  faces = ((0, 2, 1), (0, 3, 2), (3, 5, 2), (3, 4, 5), (0, 1, 5),
           (0, 5, 4), (0, 4, 3), (1, 2, 5))
  return Shape(points, faces)


def cylinderShape(radius: float, width: float, sides: int) -> Shape:
  """The 'cylinderShape' function returns a round cylinder of 'radius'
  and 'width' as a wheel stands on an axle along y, its middle at the
  origin, its round a regular polygon of 'sides' corners on the
  circle."""
  ring = tuple((radius * math.cos(2.0 * math.pi * k / sides),
                radius * math.sin(2.0 * math.pi * k / sides))
               for k in range(sides))
  half = 0.5 * width
  points = tuple((x, -half, z) for x, z in ring)
  points += tuple((x, half, z) for x, z in ring)
  points += ((0.0, -half, 0.0), (0.0, half, 0.0))
  near, far = 2 * sides, 2 * sides + 1
  faces = []
  for k in range(sides):
    after = (k + 1) % sides
    faces.append((k, sides + after, after))
    faces.append((k, sides + k, sides + after))
    faces.append((near, k, after))
    faces.append((far, sides + after, sides + k))
  return Shape(points, tuple(faces))


@functools.lru_cache(maxsize=256)
def _piecesOf(shape: Shape) -> tuple:
  """Returns 'shape.piecesFound()', remembered."""
  return shape.piecesFound()


@functools.lru_cache(maxsize=256)
def _edgesOf(shape: Shape) -> tuple:
  """Returns 'shape.edgesFound()', remembered."""
  return shape.edgesFound()


@functools.lru_cache(maxsize=256)
def _skinOf(shape: Shape, spacing: float) -> tuple:
  """Returns 'shape.skinFound(spacing)', remembered."""
  return shape.skinFound(spacing)


@functools.lru_cache(maxsize=256)
def _faceLengthOf(shape: Shape, spacing: float) -> float:
  """Returns the most skin length on any one face's plane of 'shape',
  remembered."""
  skin = shape.skin(spacing)
  most = 0.0
  for planes in shape.pieces():
    for facing, offset in planes:
      length = sum(share for point, share in skin
                   if abs(dot(facing, point) - offset) <= 1e-9)
      most = max(most, length)
  return most
