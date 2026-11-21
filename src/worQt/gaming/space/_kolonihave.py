"""
Asger's kolonihave i rummet (user, 2026-11-17: "all aboard Asger's
kolonihave i rummet!"): allotment gardens on the space station's deck,
along the ring from the first spoke's elevator: a gravel path down the
middle, plots either side, each its lawn, its hedge (a gate to the
path), its little hut (boarded, painted, a gable roof) and a flower bed;
Asger's (the first, on the right going round) has a flagpole with
Dannebrog and a garden gnome. Each part on the curving deck where it
stands (the deck falls away 3.6 m over 80 m: its own frame each), the
station's own axes. The hedges, the huts, the beds, the pole and the
gnome are solids Asger meets ('gardenSolids'). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._shapes import boxRows, frustumRows, joined
from ._stationinterior import DECK, stationPoint, stationWay
from ._turns import quaternionOf

#  The path: half its width, m; how far along the ring it runs (either
#  way from the elevator), m.
PATH_HALF = 1.5
PATH_LONG = 60.0
#  The plots along the ring (from, to: m from the elevator going round;
#  mirrored the other way) and across it (from the path's edge to the
#  hedge at the tube's wall), m.
PLOTS = ((6.0, 20.0), (22.0, 36.0), (38.0, 52.0))
ACROSS = (2.5, 14.5)
#  A hedge: half its thickness, its height; the gate in it to the path
#  (half its width), m.
HEDGE = (0.25, 1.2)
GATE = 0.9
#  A hut: half its size (along, across), its walls' height, its roof's
#  rise and overhang, how far back from the path it stands, m; their
#  paint, round the plots.
HUT_HALF = (1.8, 1.5)
HUT_WALL = 2.3
ROOF_RISE = 1.2
ROOF_OVER = 0.3
HUT_BACK = 7.0
PAINTS = ('hut red', 'hut yellow', 'hut blue', 'hut white', 'hut green',
          'hut red')
#  A flower bed: half its size, its height; their flowers, round.
BED_HALF = (1.4, 0.5)
BED_HIGH = 0.3
FLOWERS = ('flowers red', 'flowers yellow', 'flowers violet')
#  The flagpole: its height, half its thickness; Dannebrog: its height
#  (28 parts: 12 red, 4 white, 12 red; 37 long: 12 red, 4 white, 21
#  red), half its thickness, m.
POLE = (7.0, 0.06)
FLAG_HIGH = 1.8
FLAG_THICK = 0.015
#  The garden gnome: how tall, m.
GNOME = 0.8


def deckFrame(along: float, across: float, high: float) -> tuple:
  """Returns where a point 'along' m round the ring from the elevator,
  'across' m over the deck's middle line (along the station's axis),
  'high' m over the deck is (the station's own axes) and the deck's
  frame there: along the ring, across it (against the station's axis: a
  turn, not a mirror), up (toward the axis)."""
  angle = along / DECK
  c, s = math.cos(angle), math.sin(angle)
  out = DECK - high
  return ((out * c, out * s, across), ((-s, c, 0.0), (0.0, 0.0, -1.0),
                                       (-c, -s, 0.0)))


@functools.lru_cache(maxsize=1)
def gardenParts() -> tuple:
  """Returns the garden's boxes: (look, middle, half (along, across,
  up), axes, solid) each, the station's own axes."""
  parts = []

  def box(look: str, along: float, across: float, high: float,
          half: tuple, solid: bool) -> None:
    middle, axes = deckFrame(along, across, high + half[2])
    parts.append((look, middle, half, axes, solid))

  box('path', 0.0, 0.0, 0.0, (PATH_LONG, PATH_HALF, 0.02), False)
  plot = 0
  for way in (1.0, -1.0):
    for low, high in PLOTS:
      for side in (1.0, -1.0):
        _plotted(box, plot, way * low, way * high, side)
        plot += 1
  return tuple(parts)


def _plotted(box: object, plot: int, one: float, two: float,
             side: float) -> None:
  """Lays plot 'plot' from 'one' to 'two' m round the ring, on the
  'side' (one: across up the station's axis) of the path."""
  low, high = min(one, two), max(one, two)
  middle = 0.5 * (low + high)
  near, far = side * ACROSS[0], side * ACROSS[1]
  deep = 0.5 * (ACROSS[1] - ACROSS[0])
  across = 0.5 * (near + far)
  half = 0.5 * (high - low)
  box('lawn', middle, across, 0.0, (half, deep, 0.025), False)
  thick, tall = HEDGE
  box('hedge', middle, far, 0.0, (half, thick, 0.5 * tall), True)
  for end in (low, high):
    box('hedge', end, across, 0.0, (thick, deep, 0.5 * tall), True)
  gate = half - GATE
  for shift in (1.0, -1.0):
    box('hedge', middle + shift * (GATE + 0.5 * gate), near, 0.0,
        (0.5 * gate, thick, 0.5 * tall), True)
  hut = side * (ACROSS[0] + HUT_BACK)
  box(PAINTS[plot % len(PAINTS)], middle, hut, 0.0, HUT_HALF + (
    0.5 * HUT_WALL,), True)
  box('roof', middle, hut, HUT_WALL, (HUT_HALF[0] + ROOF_OVER,
                                      HUT_HALF[1] + ROOF_OVER, 0.0), False)
  bed = side * (ACROSS[0] + 2.5)
  box(FLOWERS[plot % len(FLOWERS)], middle - 3.0, bed, 0.0,
      BED_HALF + (0.5 * BED_HIGH,), True)
  if plot == 0:
    _asgers(box, middle, side)


def _asgers(box: object, middle: float, side: float) -> None:
  """Lays what only Asger's plot has: the flagpole with Dannebrog, the
  garden gnome."""
  pole = side * (ACROSS[0] + 3.5)
  where = middle + 4.0
  high, half = POLE
  box('pole', where, pole, 0.0, (half, half, 0.5 * high), True)
  unit = FLAG_HIGH / 28.0
  lower = high - FLAG_HIGH
  box('flag red', where + 0.5 * 37.0 * unit + half, pole, lower,
      (0.5 * 37.0 * unit, FLAG_THICK, 0.5 * FLAG_HIGH), False)
  box('flag white', where + 14.0 * unit + half, pole, lower,
      (2.0 * unit, 1.5 * FLAG_THICK, 0.5 * FLAG_HIGH), False)
  box('flag white', where + 0.5 * 37.0 * unit + half, pole,
      lower + 12.0 * unit, (0.5 * 37.0 * unit, 1.5 * FLAG_THICK,
                            2.0 * unit), False)
  gnome = side * (ACROSS[0] + 2.0)
  at = middle + 1.0
  body = 0.35 * GNOME
  box('gnome coat', at, gnome, 0.0, (0.12, 0.1, 0.5 * body), True)
  box('gnome face', at, gnome, body, (0.08, 0.07, 0.08), False)
  box('gnome beard', at + 0.06, gnome, body - 0.06, (0.05, 0.07, 0.08),
      False)


@functools.lru_cache(maxsize=1)
def gardenMeshes() -> dict:
  """Returns the garden's meshes by look (rows of eight, the station's
  own axes): its boxes, the huts' gable roofs, the gnome's hat."""
  parts = {}
  for look, middle, half, axes, _ in gardenParts():
    if look == 'roof':
      rows = _roofRows(middle, half, axes)
    else:
      rows = boxRows(middle, half, (axes[0], axes[1], axes[2]))
    parts.setdefault(look, []).append(rows)
  for look, middle, half, axes, _ in gardenParts():
    if look == 'gnome face':
      top = tuple(m + 0.08 * u for m, u in zip(middle, axes[2]))
      parts.setdefault('gnome hat', []).append(frustumRows(
        top, axes[2], 0.11, 0.0, 0.45 * GNOME, 12))
  return {look: joined(rows) for look, rows in parts.items()}


def _roofRows(middle: tuple, half: tuple, axes: tuple) -> tuple:
  """Returns a gable roof over a hut (its eaves round 'middle', 'half'
  its size along and across the ridge's way, the ridge 'ROOF_RISE' up),
  its two slopes and two gables, each face outward."""
  along, across, up = (numpy.array(a) for a in axes)
  middle = numpy.array(middle)
  ridge = middle + ROOF_RISE * up
  ends = (half[0], -half[0])
  rows, faces = [], []
  for side in (1.0, -1.0):
    eave = middle + side * half[1] * across
    normal = side * ROOF_RISE * across + half[1] * up
    normal /= numpy.linalg.norm(normal)
    first = len(rows)
    for place in (eave + ends[0] * along, eave + ends[1] * along,
                  ridge + ends[1] * along, ridge + ends[0] * along):
      rows.append(tuple(place) + tuple(normal) + (0.0, 0.0))
    _faced(rows, faces, first, 4)
  for end in ends:
    normal = numpy.sign(end) * along
    first = len(rows)
    for place in (middle + end * along + half[1] * across * 0.9,
                  middle + end * along - half[1] * across * 0.9,
                  ridge + end * along):
      rows.append(tuple(place) + tuple(normal) + (0.0, 0.0))
    _faced(rows, faces, first, 3)
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _faced(rows: list, faces: list, first: int, count: int) -> None:
  """Adds a face's triangles (a fan from 'first' over 'count' corners),
  wound to face its rows' normal."""
  a = numpy.array(rows[first][:3])
  b = numpy.array(rows[first + 1][:3])
  c = numpy.array(rows[first + 2][:3])
  outward = float(numpy.dot(numpy.cross(b - a, c - a), rows[first][3:6]))
  for k in range(1, count - 1):
    if outward >= 0.0:
      faces.extend((first, first + k, first + k + 1))
    else:
      faces.extend((first, first + k + 1, first + k))


def gardenSolids(relative: tuple) -> tuple:
  """Returns the garden's solids in the docked rocket's own axes
  ('relative': its axes in the station's): each its middle, half sizes,
  turn (w x y z) and velocity (still)."""
  out = []
  for _, middle, half, axes, solid in gardenParts():
    if not solid:
      continue
    columns = tuple(stationWay(a, relative) for a in axes)
    turn = quaternionOf(tuple((columns[0][k], columns[1][k], columns[2][k])
                              for k in range(3)))
    out.append((stationPoint(middle, relative), half, turn,
                (0.0, 0.0, 0.0)))
  return tuple(out)
