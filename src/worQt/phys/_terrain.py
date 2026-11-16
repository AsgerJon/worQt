"""
Terrain is the ground's shape where it is not flat: a grid of heights,
the ground between them bilinear (user, 2026-11-12: "a small track with
elevation changes allowing its suspension to be challenged"). 'track'
lays one out for the car: rolling ground, a hill, a dip, speed humps
and a stretch of washboard.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple

import numpy

from ._vectors import Vector


class Terrain(NamedTuple):
  """
  Terrain is heights over a grid of square cells 'cell' m wide from
  'origin' (x, y): 'heights[i][j]' (m) at x 'origin[0] + i cell', y
  'origin[1] + j cell', the ground between them bilinear, flat at
  nought outside the grid (so its edges should be nought); 'paved', if
  given, says what each of the grid's points is surfaced with, for those
  who draw it (the ground's law is the same): nought none (dirt or
  grass), 'PAVED' concrete, 'ASPHALT' asphalt.
  """

  origin: tuple
  cell: float
  heights: tuple
  paved: tuple = None

  def heightAt(self, x: float, y: float) -> float:
    """The 'heightAt' method returns how high the ground is at 'x',
    'y', m."""
    found = self._cellOf(x, y)
    if found is None:
      return 0.0
    i, j, u, v = found
    rows = self.heights
    return ((rows[i][j] * (1.0 - u) + rows[i + 1][j] * u) * (1.0 - v)
            + (rows[i][j + 1] * (1.0 - u) + rows[i + 1][j + 1] * u) * v)

  def normalAt(self, x: float, y: float) -> Vector:
    """The 'normalAt' method returns the ground's upward unit normal at
    'x', 'y' (its cell's bilinear surface's)."""
    found = self._cellOf(x, y)
    if found is None:
      return 0.0, 0.0, 1.0
    i, j, u, v = found
    rows, cell = self.heights, self.cell
    along = ((rows[i + 1][j] - rows[i][j]) * (1.0 - v)
             + (rows[i + 1][j + 1] - rows[i][j + 1]) * v) / cell
    across = ((rows[i][j + 1] - rows[i][j]) * (1.0 - u)
              + (rows[i + 1][j + 1] - rows[i + 1][j]) * u) / cell
    size = math.sqrt(along * along + across * across + 1.0)
    return -along / size, -across / size, 1.0 / size

  def top(self, ) -> float:
    """The 'top' method returns the highest the ground gets, m."""
    return _topOf(self)

  def topWithin(self, low: tuple, high: tuple) -> float:
    """The 'topWithin' method returns the highest the ground gets over
    the rectangle from 'low' (x, y) to 'high', m (its grid's heights
    there: between them it is no higher; nought where it leaves the
    grid)."""
    grid = _gridOf(self)
    x0, y0 = self.origin
    cell = self.cell
    i0 = max(0, math.floor((low[0] - x0) / cell))
    j0 = max(0, math.floor((low[1] - y0) / cell))
    i1 = min(grid.shape[0] - 1, math.ceil((high[0] - x0) / cell))
    j1 = min(grid.shape[1] - 1, math.ceil((high[1] - y0) / cell))
    top = float(grid[i0:i1 + 1, j0:j1 + 1].max()) if (
            i0 <= i1 and j0 <= j1) else 0.0
    far = (x0 + cell * (grid.shape[0] - 1), y0 + cell * (grid.shape[1] - 1))
    if (low[0] < x0 or low[1] < y0 or high[0] > far[0]
            or high[1] > far[1] or i0 > i1 or j0 > j1):
      top = max(top, 0.0)
    return top

  def planeWithin(self, low: tuple, high: tuple) -> tuple:
    """The 'planeWithin' method returns the ground over the rectangle
    from 'low' (x, y) to 'high' as a plane and how far the ground rises
    over it: (x, y, height there, slope along x, along y, the most the
    ground rises over the plane anywhere in it, the highest it gets);
    no point higher over the plane than that can meet it (between the
    grid's points the ground is bilinear, so it rises over a plane no
    more than at them). Level at the ground's top where the rectangle
    leaves the grid."""
    grid = _gridOf(self)
    x0, y0 = self.origin
    cell = self.cell
    i0 = math.floor((low[0] - x0) / cell)
    j0 = math.floor((low[1] - y0) / cell)
    i1 = math.ceil((high[0] - x0) / cell)
    j1 = math.ceil((high[1] - y0) / cell)
    if (i0 < 0 or j0 < 0 or i1 > grid.shape[0] - 1
            or j1 > grid.shape[1] - 1):
      top = self.topWithin(low, high)
      return 0.0, 0.0, top, 0.0, 0.0, 0.0, top
    part = grid[i0:i1 + 1, j0:j1 + 1]
    xs = cell * numpy.arange(part.shape[0])
    ys = cell * numpy.arange(part.shape[1])
    gx = _slopeOf(part.mean(axis=1), cell)
    gy = _slopeOf(part.mean(axis=0), cell)
    plane = gx * xs[:, None] + gy * ys[None, :]
    base = float((part - plane).mean())
    over = float((part - plane - base).max())
    return (x0 + cell * i0, y0 + cell * j0, base, gx, gy, max(over, 0.0),
            float(part.max()))

  def _cellOf(self, x: float, y: float) -> tuple | None:
    """Returns the cell 'x', 'y' lies in and where in it (its lower
    corner's indices and the shares across it), or None outside."""
    a = (x - self.origin[0]) / self.cell
    b = (y - self.origin[1]) / self.cell
    i, j = math.floor(a), math.floor(b)
    if i < 0 or j < 0 or i >= len(self.heights) - 1 or (
            j >= len(self.heights[0]) - 1):
      return None
    return i, j, a - i, b - j


_TOPS: dict = {}
_GRIDS: dict = {}


def _gridOf(terrain: Terrain) -> numpy.ndarray:
  """Returns 'terrain''s heights as an array, made once (kept by the
  heights' identity)."""
  key = id(terrain.heights)
  if key not in _GRIDS:
    _GRIDS[key] = numpy.asarray(terrain.heights, numpy.float64)
  return _GRIDS[key]


def _topOf(terrain: Terrain) -> float:
  """Returns the highest of 'terrain''s heights, worked out once (kept
  by the terrain's identity: its heights are many)."""
  key = id(terrain.heights)
  if key not in _TOPS:
    _TOPS[key] = max(max(row) for row in terrain.heights)
  return _TOPS[key]


@functools.lru_cache(maxsize=2)
def track(cell: float) -> Terrain:
  """The 'track' function returns the car's track, 100 m square about
  the origin in cells of 'cell' m: the ground rolling gently (30 cm);
  a hill 2.5 m high north-east, a dip 1.2 m deep north-west; three
  speed humps (10 cm high, 1.2 m across) across the way east of the
  start; a stretch of washboard (4 cm ripples every 1.5 m) to the west;
  flat about the start and toward the edges."""
  half = 50.0
  count = int(round(2.0 * half / cell)) + 1
  rows = []
  for i in range(count):
    x = -half + i * cell
    rows.append(tuple(_trackHeight(x, -half + j * cell)
                      for j in range(count)))
  return Terrain((-half, -half), cell, tuple(rows))


def _trackHeight(x: float, y: float) -> float:
  """Returns the track's height at 'x', 'y' (see 'track')."""
  edge = max(abs(x), abs(y))
  fade = 1.0 if edge < 40.0 else max(0.0, (48.0 - edge) / 8.0)
  start = min(1.0, math.hypot(x, y) / 12.0)
  rolling = 0.3 * math.sin(x / 7.0) * math.sin(y / 9.0) * start
  hill = 2.5 * math.exp(-((x - 25.0) ** 2 + (y - 25.0) ** 2) / 120.0)
  dip = -1.2 * math.exp(-((x + 25.0) ** 2 + (y - 25.0) ** 2) / 80.0)
  humps = 0.0
  if abs(y) < 8.0:
    for middle in (16.0, 22.0, 28.0):
      off = abs(x - middle)
      if off < 0.6:
        humps += 0.05 * (1.0 + math.cos(math.pi * off / 0.6))
  board = 0.0
  if -36.0 < x < -16.0 and abs(y) < 6.0:
    board = 0.02 * (1.0 - math.cos(2.0 * math.pi * x / 1.5))
  return fade * (rolling + hill + dip + humps + board)


#  The oval (user, 2026-11-12: "make an oval racetrack base on the
#  Dover nascar track in Delaware US"; its public figures): a mile
#  round its middle line, two straights of 328 m (1,076 ft), the turns
#  half circles between them; the racing surface 14.6 m (48 ft) wide on
#  the straights and 17.7 m (58 ft) in the turns, banked 9 and 24
#  degrees; a flat paved apron inside it, 3 m (10 ft) on the straights,
#  6.4 m (21 ft) in the turns; the banking eases from the one to the
#  other over 'OVAL_EASE' m either side of where a turn begins. Outside
#  the racing surface the bank goes on 'OVAL_RUNOFF' m (paved), then a
#  level top 'OVAL_TOP' m wide, then grass falling one in three to the
#  ground; the infield grass at nought.
OVAL_LENGTH, OVAL_STRAIGHT = 1609.3, 328.0
OVAL_RADIUS = (OVAL_LENGTH - 2.0 * OVAL_STRAIGHT) / (2.0 * math.pi)
OVAL_WIDTHS, OVAL_BANKS = (14.6, 17.7), (math.radians(9.0),
                                         math.radians(24.0))
OVAL_APRONS, OVAL_EASE = (3.0, 6.4), 40.0
OVAL_RUNOFF, OVAL_TOP, OVAL_FALL = 6.0, 10.0, 3.0


#  What a terrain's grid point is surfaced with ('Terrain.paved'):
#  concrete (an oval's banking and its run-off), asphalt (its apron:
#  user, 2026-11-12: "the 'apron', the bit of road below the bank must
#  have a different coloured tarmac than the bank").
PAVED, ASPHALT = 1, 2


def _slopeOf(values: numpy.ndarray, cell: float) -> float:
  """Returns the least-squares slope of 'values' taken 'cell' m apart
  (what 'numpy.polyfit' of degree one gives, worked out straight: its
  general solve cost ~85 us a call, 22 calls a car's frame on the oval);
  nought for fewer than two."""
  count = len(values)
  if count < 2:
    return 0.0
  xs = cell * (numpy.arange(count) - 0.5 * (count - 1))
  return float(numpy.dot(xs, values - values.mean()) / numpy.dot(xs, xs))


@functools.lru_cache(maxsize=1)
def oval(cell: float) -> Terrain:
  """The 'oval' function returns the oval (see 'OVAL_LENGTH') in cells
  of 'cell' m, its front straight along x through the origin (its
  middle line there; driven toward +x, the turns to the left, +y), the
  surfaces marked: the banking and its run-off concrete, the apron
  asphalt."""
  half, radius = 0.5 * OVAL_STRAIGHT, OVAL_RADIUS
  reach = (radius + 0.5 * OVAL_WIDTHS[1] + OVAL_RUNOFF + OVAL_TOP
           + OVAL_FALL * 12.0 + 10.0)
  low = (-half - reach, -reach)
  count = (int(math.ceil(2.0 * (half + reach) / cell)) + 1,
           int(math.ceil((2.0 * radius + 2.0 * reach) / cell)) + 1)
  xs = low[0] + cell * numpy.arange(count[0])
  ys = low[1] + cell * numpy.arange(count[1])
  x, y = numpy.meshgrid(xs, ys, indexing='ij')
  inner, width, apron, turned = ovalAcross(x, y)
  bank = numpy.tan(OVAL_BANKS[0] + (OVAL_BANKS[1] - OVAL_BANKS[0])
                   * turned)
  top = (width + OVAL_RUNOFF) * bank
  heights = numpy.clip(inner, 0.0, width + OVAL_RUNOFF) * bank
  beyond = inner - width - OVAL_RUNOFF - OVAL_TOP
  heights = numpy.where(beyond > 0.0,
                        numpy.maximum(0.0, top - beyond / OVAL_FALL),
                        heights)
  paved = numpy.where((inner >= 0.0) & (inner <= width + OVAL_RUNOFF),
                      PAVED, numpy.where((inner >= -apron) & (inner < 0.0),
                                         ASPHALT, 0))
  return Terrain(low, cell, tuple(map(tuple, heights.tolist())),
                 tuple(map(tuple, paved.astype(numpy.int8).tolist())))


def ovalAcross(x: numpy.ndarray, y: numpy.ndarray) -> tuple:
  """The 'ovalAcross' function returns, for points 'x', 'y', how far
  across the oval's racing surface they lie, out from its inside edge
  ('inner', m: below nought the apron and the infield), how wide the
  surface and the apron are there, m, and how far into a turn
  ('_ovalTurned')."""
  out, along = _ovalPlaces(x, y)
  turned = _ovalTurned(along)
  width = OVAL_WIDTHS[0] + (OVAL_WIDTHS[1] - OVAL_WIDTHS[0]) * turned
  apron = OVAL_APRONS[0] + (OVAL_APRONS[1] - OVAL_APRONS[0]) * turned
  return out + 0.5 * width, width, apron, turned


def _ovalPlaces(x: numpy.ndarray, y: numpy.ndarray) -> tuple:
  """Returns, for points 'x', 'y', how far out from the oval's middle
  line they are (out of the oval counted up) and how far round it from
  the start of the front straight, m."""
  half, radius, straight = 0.5 * OVAL_STRAIGHT, OVAL_RADIUS, OVAL_STRAIGHT
  turn = math.pi * radius
  front = y < radius
  out = numpy.where(front, -y, y - 2.0 * radius)
  along = numpy.where(front, x + half, straight + turn + half - x)
  for middle, start, ahead in ((half, straight, True),
                               (-half, 2.0 * straight + turn, False)):
    beside = x > half if ahead else x < -half
    angle = numpy.arctan2(y - radius, x - middle)
    swept = angle + 0.5 * math.pi if ahead else numpy.mod(
      angle - 0.5 * math.pi, 2.0 * math.pi)
    out = numpy.where(beside, numpy.hypot(x - middle, y - radius) - radius,
                      out)
    along = numpy.where(beside, start + radius * swept, along)
  return out, along


class OvalWall(NamedTuple):
  """
  OvalWall is a safety barrier round an oval (user, 2026-11-12: "put a
  safety barrier on the outside"): a wall standing on the ground 'out'
  m out from the middle line of an oval of straights 'half' m either
  side of the middle and turns of 'radius' m (as 'oval''s), 'height' m
  tall, its face sliding at 'grip' (a car's body on its concrete).
  'beyond' says how far a place is through its face and which way out.
  """

  half: float
  radius: float
  out: float
  height: float
  grip: float

  def beyond(self, x: float, y: float) -> tuple:
    """The 'beyond' method returns how far 'x', 'y' is out through the
    wall's face, m (below nought: inside it), and the face's outward
    normal there, level (nx, ny)."""
    half, radius = self.half, self.radius
    if x > half or x < -half:
      middle = half if x > half else -half
      dx, dy = x - middle, y - radius
      far = math.hypot(dx, dy)
      if far < 1e-9:
        return -radius - self.out, 1.0, 0.0
      return far - radius - self.out, dx / far, dy / far
    if y < radius:
      return -y - self.out, 0.0, -1.0
    return y - 2.0 * radius - self.out, 0.0, 1.0

  def heightAt(self, x: float, y: float) -> float:
    """The 'heightAt' method returns how tall the wall stands over the
    ground at 'x', 'y', m (everywhere its 'height')."""
    return self.height

  def tallest(self, ) -> float:
    """The 'tallest' method returns how tall the wall stands at its
    tallest, m (its 'height')."""
    return self.height


#  The oval's barrier: how far out from the middle line it stands (the
#  straights' run-off's outer edge; in the turns 4.45 m past the racing
#  surface), how tall, m, and how its face grips.
OVAL_WALL_OUT, OVAL_WALL_HIGH, OVAL_WALL_GRIP = (
  0.5 * OVAL_WIDTHS[0] + OVAL_RUNOFF, 1.2, 0.5)


def ovalWall() -> OvalWall:
  """The 'ovalWall' function returns the barrier round 'oval'."""
  return OvalWall(0.5 * OVAL_STRAIGHT, OVAL_RADIUS, OVAL_WALL_OUT,
                  OVAL_WALL_HIGH, OVAL_WALL_GRIP)


def ovalPlaceOf(x: float, y: float) -> tuple:
  """The 'ovalPlaceOf' function returns, for the point 'x', 'y', how far
  out from the oval's middle line it is (out of the oval counted up)
  and how far round it from the start of the front straight, m."""
  out, along = _ovalPlaces(numpy.array(x), numpy.array(y))
  return float(out), float(along)


def ovalShapeAt(along: float) -> tuple:
  """The 'ovalShapeAt' function returns the racing surface 'along' m
  round the middle line from the start of the front straight (any number
  of laps): how wide it is, m, how steeply banked, rad, and how wide
  its apron is, m."""
  turned = float(_ovalTurned(numpy.array([along % OVAL_LENGTH]))[0])
  return (OVAL_WIDTHS[0] + (OVAL_WIDTHS[1] - OVAL_WIDTHS[0]) * turned,
          OVAL_BANKS[0] + (OVAL_BANKS[1] - OVAL_BANKS[0]) * turned,
          OVAL_APRONS[0] + (OVAL_APRONS[1] - OVAL_APRONS[0]) * turned)


def ovalAt(along: float, out: float) -> tuple:
  """The 'ovalAt' function returns the point 'along' m round the oval's
  middle line from the start of the front straight (any number of laps
  either way) and 'out' m out from it, and which way the line goes
  there, driven: (x, y, heading), heading rad from +x toward +y."""
  half, radius, straight = 0.5 * OVAL_STRAIGHT, OVAL_RADIUS, OVAL_STRAIGHT
  turn = math.pi * radius
  along = along % OVAL_LENGTH
  if along < straight:
    return along - half, -out, 0.0
  if along < straight + turn:
    angle = (along - straight) / radius - 0.5 * math.pi
    middle = half
  elif along < 2.0 * straight + turn:
    return straight + turn + half - along, 2.0 * radius + out, math.pi
  else:
    angle = (along - 2.0 * straight - turn) / radius + 0.5 * math.pi
    middle = -half
  far = radius + out
  return (middle + far * math.cos(angle), radius + far * math.sin(angle),
          angle + 0.5 * math.pi)


def _ovalTurned(along: numpy.ndarray) -> numpy.ndarray:
  """Returns how far into a turn's banking and width each point 'along'
  the middle line is (nought on a straight, one in a turn), eased over
  'OVAL_EASE' m either side of where a turn begins and ends, the ease
  out of the last turn going on past the lap's end into the front
  straight (user, 2026-11-12: "the end of turn four has a crazy sharp
  drop": cut off where 'along' starts over, the bank fell from 17 to 9
  degrees, 1.4 m, within a metre)."""
  straight, turn = OVAL_STRAIGHT, math.pi * OVAL_RADIUS
  ends = (straight, straight + turn, 2.0 * straight + turn,
          2.0 * straight + 2.0 * turn)
  turned = numpy.zeros_like(along)
  for lap in (-OVAL_LENGTH, 0.0, OVAL_LENGTH):
    for begins, ends_ in ((ends[0], ends[1]), (ends[2], ends[3])):
      into = numpy.clip((along + lap - begins + OVAL_EASE)
                        / (2.0 * OVAL_EASE), 0.0, 1.0)
      outof = numpy.clip((ends_ + OVAL_EASE - along - lap)
                         / (2.0 * OVAL_EASE), 0.0, 1.0)
      share = numpy.minimum(into, outof)
      turned = numpy.maximum(turned, share * share * (3.0 - 2.0 * share))
  return turned
