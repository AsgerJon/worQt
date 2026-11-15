"""
The steering wheel as drawn (user, 2026-11-14: "make it look like a
cool steering wheel"): a racing wheel's flat-bottomed rim ('RIM', its
bottom 'FLAT' under its middle), an oval grip swept round it, thicker
where the thumbs lie (at three and nine), in perforated leather
('grip') with an orange mark at its top ('marker'); three dished alloy
spokes ('spoke'); a dark hub ('hub') on its quick release, a Soufflé
badge in its middle ('badge'); the column down to its pinion ('column',
'pinion'). All in the column body's own frame ('_axle.columnBody'): the
wheel's middle at the origin, its face toward +z, its top +y. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from .._axle import COLUMN, FLAT, GRIP, RIM, columnLength
from .._shape import boxShape
from .._tyred import _loop
from .._vectors import turnAbout

#  How finely the rim is swept: points round it, round its grip; how
#  thick the grip is across the wheel's face (half, m), how much thicker
#  under the thumbs; how round the flat bottom's corners are (m); how
#  many times the leather's picture runs round; the top mark's half
#  width (rad).
ROUND, ACROSS = 144, 16
DEPTH, THUMBS = 0.013, 0.004
SOFT = 0.018
LEATHER_ROUND = 48
MARK = 0.07


def rimPath() -> numpy.ndarray:
  """The 'rimPath' function returns the rim's middle line, 'ROUND'
  points anticlockwise from three o'clock (x, y), a circle of 'RIM'
  flattened at the bottom 'FLAT' under the middle, its corners
  rounded ('SOFT')."""
  angles = 2.0 * math.pi * numpy.arange(ROUND) / ROUND
  x, y = RIM * numpy.cos(angles), RIM * numpy.sin(angles)
  lifted = -FLAT + SOFT * numpy.logaddexp(0.0, (y + FLAT) / SOFT)
  return numpy.stack((x, lifted), axis=1), angles


def rimRows() -> dict[str, numpy.ndarray]:
  """The 'rimRows' function returns the rim's grip swept round its path
  ('rimPath') as rows (place, normal, picture: once round and across,
  'LEATHER_ROUND' times round), by key: the top mark ('marker') and the
  rest ('grip')."""
  path, angles = rimPath()
  ahead = numpy.roll(path, -1, axis=0) - numpy.roll(path, 1, axis=0)
  ahead /= numpy.linalg.norm(ahead, axis=1)[:, None]
  out = numpy.zeros((ROUND, 3))
  out[:, 0], out[:, 1] = ahead[:, 1], -ahead[:, 0]
  thumbs = numpy.maximum(0.0, numpy.cos(angles)) ** 8 + numpy.maximum(
    0.0, -numpy.cos(angles)) ** 8
  wide, deep = GRIP + THUMBS * thumbs, DEPTH + 0.5 * THUMBS * thumbs
  turns = 2.0 * math.pi * numpy.arange(ACROSS + 1) / ACROSS
  c, s = numpy.cos(turns), numpy.sin(turns)
  middle = numpy.zeros((ROUND, 3))
  middle[:, :2] = path
  places = (middle[:, None, :] + (wide[:, None] * c[None, :])[..., None]
            * out[:, None, :])
  places[..., 2] += deep[:, None] * s[None, :]
  normals = (c[None, :] / wide[:, None])[..., None] * out[:, None, :]
  normals[..., 2] += s[None, :] / deep[:, None]
  normals /= numpy.linalg.norm(normals, axis=2)[..., None]
  u = LEATHER_ROUND * numpy.arange(ROUND + 1) / ROUND
  v = numpy.arange(ACROSS + 1) / ACROSS
  rows = {'grip': [], 'marker': []}
  top = numpy.abs(((angles - 0.5 * math.pi + math.pi) % (2.0 * math.pi))
                  - math.pi) < MARK
  for i in range(ROUND):
    j = (i + 1) % ROUND
    key = 'marker' if top[i] else 'grip'
    for k in range(ACROSS):
      corners = ((i, k, u[i], v[k]), (j, k, u[i + 1], v[k]),
                 (j, k + 1, u[i + 1], v[k + 1]),
                 (i, k + 1, u[i], v[k + 1]))
      quad = [numpy.concatenate((places[a, b], normals[a, b], (uu, vv)))
              for a, b, uu, vv in corners]
      rows[key].extend((quad[0], quad[1], quad[2], quad[0], quad[2],
                        quad[3]))
  return {key: numpy.array(found) for key, found in rows.items()}


def spokeShapes() -> tuple:
  """The 'spokeShapes' function returns the three spokes as boxes:
  from the hub out to the rim at four and eight o'clock (a little low,
  as a racing wheel's) and straight down to the flat bottom, dished
  behind the rim's face."""
  out = []
  for start, end in (((-0.045, -0.01), (-RIM + 0.012, -0.035)),
                     ((0.045, -0.01), (RIM - 0.012, -0.035)),
                     ((0.0, -0.045), (0.0, -FLAT + 0.012))):
    dx, dy = end[0] - start[0], end[1] - start[1]
    middle = (0.5 * (start[0] + end[0]), 0.5 * (start[1] + end[1]), -0.012)
    out.append(boxShape(math.hypot(dx, dy), 0.042, 0.008).moved(
      middle, turnAbout((0.0, 0.0, 1.0), math.atan2(dy, dx))))
  shape = out[0]
  for piece in out[1:]:
    shape = shape.joined(piece)
  return shape


def badgeRows() -> numpy.ndarray:
  """The 'badgeRows' function returns the hub's badge, a disc 42 mm
  across the middle facing the driver, its picture laid flat on it."""
  radius, at, sides = 0.042, 0.0045, 48
  angles = 2.0 * math.pi * numpy.arange(sides + 1) / sides
  rows = []
  for k in range(sides):
    points = ((0.0, 0.0), (radius * math.cos(angles[k]),
                           radius * math.sin(angles[k])),
              (radius * math.cos(angles[k + 1]),
               radius * math.sin(angles[k + 1])))
    for x, y in points:
      rows.append((x, y, at, 0.0, 0.0, 1.0, 0.5 + 0.5 * x / radius,
                   0.5 + 0.5 * y / radius))
  return numpy.array(rows)


@functools.lru_cache(maxsize=4)
def columnFinish(length: float = None) -> tuple:
  """The 'columnFinish' function returns how the steering wheel and its
  column are drawn ('finishedRows' items): the rim's grip and mark, the
  spokes, the hub and its quick release, the badge, the column ('length'
  m to its pinion; None: the steering bench's, 'columnLength'), its
  pinion; made once (its rows are kept: the view knows a finish it
  cannot hash by the object)."""
  length = columnLength() if length is None else length
  rim = rimRows()
  hub = _loop([(0.0, -0.035), (0.05, -0.035), (0.05, 0.004),
               (0.0, 0.004)])
  quick = _loop([(0.0, -0.065), (0.03, -0.065), (0.03, -0.035),
                 (0.0, -0.035)])
  shaft = _loop([(0.0, -length + 0.03), (COLUMN, -length + 0.03),
                 (COLUMN, -0.065), (0.0, -0.065)])
  pinion = _loop([(0.0, -length - 0.04), (0.016, -length - 0.04),
                  (0.016, -length + 0.03), (0.0, -length + 0.03)])
  return (('grip', ('rows', rim['grip'])),
          ('marker', ('rows', rim['marker'])),
          ('spoke', spokeShapes()),
          ('hub', hub), ('quick', quick), ('badge', ('rows', badgeRows())),
          ('column', shaft), ('pinion', pinion))


def axleFinishes(assembly: object) -> dict:
  """The 'axleFinishes' function returns how the steering bench's bodies
  are drawn, by index ('_axle.steeringBench'): the rig and the knuckles
  by their parts, the steering wheel and column ('columnFinish'), the
  rack whole, the wheels as the brake bench's (their rims, tyres and
  discs)."""
  from .._axle import knucklePieces, rigPieces
  from .._brakes import discRuns
  from .._carcass import rimRuns
  from .._tyred import tyreRuns
  wheel = rimRuns() + tyreRuns() + discRuns()
  return {1: rigPieces(), 2: columnFinish(), 3: 'rack',
          4: knucklePieces(1.0), 5: knucklePieces(-1.0), 6: wheel,
          7: wheel}
