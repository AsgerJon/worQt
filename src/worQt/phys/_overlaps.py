"""
Where an assembly's parts cut into each other (user, 2026-11-15: "a
sanity check of the geometries that they don't overlap or anything
stupid like that": the car-tests). Each body's solid (its shape, or the
one it is designed as: 'overlapsOf''s 'solids') is placed by its state;
where two solids' world boxes meet, the space they share is sampled on
a grid 'SPACING' apart, and the points inside both are their overlap
('Overlap': its volume, its middle, its box). 'jointsOf' says which
bodies are joined and how (a joint's hardware may share space: a ball
in its socket, a rod in its tube), and which merely touch or are
sprung (sharing space, they cut into each other).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

import numpy

from ._shape import Sphere
from ._turned import Turned, _outline

#  How far apart the overlap's sample points lie, m (each stands for a
#  cube of it: a volume found is good to about a cube a side).
SPACING = 0.005
#  How many points an arc of a turned solid's profile is outlined by.
ARC_POINTS = 16
#  The fields that name the bodies a connection joins, by its kind's
#  name: the joints only (a contact, a spring, a damper, a tyre or a
#  housing's 'Housed' join nothing: parts that touch, or hang on a
#  spring, sharing space cut into each other).
JOINTS = {'Hinge': ('first', 'second'), 'Tie': ('first', 'second'),
          'Slide': ('first', 'second'), 'Actuator': ('first', 'second'),
          'Motor': ('first', 'second', 'bearer'),
          'GearMesh': ('first', 'second'), 'DiscBrake': ('disc', 'caliper'),
          'RackAndPinion': ('pinion', 'rack', 'housing'),
          'TurnPoint': ('body', 'holder')}


class Overlap(NamedTuple):
  """
  Overlap is the space two bodies' solids share: the bodies ('first'
  the lesser index, 'second'), its 'volume' (m³), its 'middle' and the
  least and most corners of its box ('low', 'high'), m in the world.
  """

  first: int
  second: int
  volume: float
  middle: tuple
  low: tuple
  high: tuple


def _matrixOf(turn: tuple) -> numpy.ndarray:
  """Returns the rotation matrix of 'turn' (w, x, y, z)."""
  w, x, y, z = turn
  return numpy.array((
    (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w),
     2.0 * (x * z + y * w)),
    (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z),
     2.0 * (y * z - x * w)),
    (2.0 * (x * z - y * w), 2.0 * (y * z + x * w),
     1.0 - 2.0 * (x * x + y * y))))


def _cornersOf(solid: object) -> numpy.ndarray:
  """Returns points in 'solid''s own frame whose box holds it."""
  if isinstance(solid, Sphere):
    r = solid.radius
    return numpy.array([(x, y, z) for x in (-r, r) for y in (-r, r)
                        for z in (-r, r)])
  if isinstance(solid, Turned):
    outline = numpy.array(_outline(solid.profile, ARC_POINTS))
    r = outline[:, 0].max()
    return numpy.array([(x, y, w) for x in (-r, r) for y in (-r, r)
                        for w in (outline[:, 1].min(), outline[:, 1].max())])
  return numpy.array(solid.points, numpy.float64)


def _inPolygon(polygon: numpy.ndarray,
               points: numpy.ndarray) -> numpy.ndarray:
  """Returns which of 'points' (n, 2) lie inside 'polygon' (a closed
  loop of corners, (m, 2)), by the crossings of a ray along x."""
  x, y = points[:, 0], points[:, 1]
  inside = numpy.zeros(len(points), bool)
  for k in range(len(polygon)):
    (x1, y1), (x2, y2) = polygon[k], polygon[(k + 1) % len(polygon)]
    if y1 == y2:
      continue
    crosses = (y1 > y) != (y2 > y)
    at = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
    inside ^= crosses & (x < at)
  return inside


def insideOf(solid: object, points: numpy.ndarray) -> numpy.ndarray:
  """The 'insideOf' function returns which of 'points' (n, 3, in the
  solid's own frame) lie inside 'solid': a ball ('Sphere', about its
  frame's origin), a turned solid ('Turned': its profile, by the
  distance from its axis and the height along it, arcs outlined by
  'ARC_POINTS'), or a shape of convex pieces ('Shape.pieces': inside
  one, behind each of its faces)."""
  if isinstance(solid, Sphere):
    return numpy.einsum('ij,ij->i', points, points) < solid.radius ** 2
  if isinstance(solid, Turned):
    outline = numpy.array(_outline(solid.profile, ARC_POINTS))
    rho = numpy.hypot(points[:, 0], points[:, 1])
    return _inPolygon(outline, numpy.stack((rho, points[:, 2]), 1))
  inside = numpy.zeros(len(points), bool)
  for piece in solid.pieces():
    within = numpy.ones(len(points), bool)
    for normal, offset in piece:
      within &= points @ numpy.array(normal) < offset
    inside |= within
  return inside


def jointsOf(assembly: object) -> dict:
  """The 'jointsOf' function returns the bodies 'assembly''s joints join
  ('JOINTS'), by pair (the lesser index first): the kinds joining
  them."""
  joined = {}
  for connection in assembly.connections:
    names = JOINTS.get(type(connection).__name__)
    if names is None:
      continue
    bodies = sorted({getattr(connection, name) for name in names} - {None})
    for k, first in enumerate(bodies):
      for second in bodies[k + 1:]:
        kinds = joined.setdefault((first, second), set())
        kinds.add(type(connection).__name__)
  return {pair: tuple(sorted(kinds)) for pair, kinds in joined.items()}


def overlapsOf(assembly: object, states: tuple, solids: dict = None,
               spacing: float = SPACING,
               bodies: tuple = None) -> tuple[Overlap, ...]:
  """The 'overlapsOf' function returns where the solids of 'assembly''s
  bodies (each its shape, or 'solids'' by index: what it is designed
  as, in its own frame; none, nothing) cut into each other, placed as
  'states' have them, among 'bodies' (indices; None: all), largest
  first: for each two whose world boxes meet, the points of a grid
  'spacing' apart over the box they share that lie inside both."""
  solids = {} if solids is None else solids
  every = range(len(assembly.bodies)) if bodies is None else bodies
  placed = {}
  for index in every:
    body = assembly.bodies[index]
    solid = solids.get(index, body.shape)
    if solid is None:
      continue
    state = states[index]
    turn = _matrixOf(state.turn)
    centre, place = numpy.array(body.centre), numpy.array(state.place)
    world = (_cornersOf(solid) - centre) @ turn.T + place
    placed[index] = (solid, turn, centre, place, world.min(0),
                     world.max(0))
  found = []
  order = sorted(placed)
  for k, first in enumerate(order):
    for second in order[k + 1:]:
      low = numpy.maximum(placed[first][4], placed[second][4])
      high = numpy.minimum(placed[first][5], placed[second][5])
      if numpy.any(high <= low):
        continue
      axes = [numpy.arange(a + 0.5 * spacing, b, spacing)
              for a, b in zip(low, high)]
      if any(len(axis) == 0 for axis in axes):
        continue
      grid = numpy.stack(numpy.meshgrid(*axes, indexing='ij'),
                         -1).reshape(-1, 3)
      both = numpy.ones(len(grid), bool)
      for index in (first, second):
        solid, turn, centre, place = placed[index][:4]
        both[both] = insideOf(solid, (grid[both] - place) @ turn + centre)
        if not both.any():
          break
      count = int(both.sum())
      if count:
        shared = grid[both]
        found.append(Overlap(first, second, count * spacing ** 3,
                             tuple(shared.mean(0)), tuple(shared.min(0)),
                             tuple(shared.max(0))))
  return tuple(sorted(found, key=lambda overlap: -overlap.volume))
