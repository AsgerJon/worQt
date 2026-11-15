"""
Roads laid along a line, as uncannyball makes them (user, 2026-11-15:
"look at previews/uncannyball_readme.md": the ground of a lap of central
Copenhagen from Denmark's public height model, an ASAM OpenCRG file).

'readCrg' reads one: a header of plain text, then the rows as
big-endian float32, each the step's heading and the heights across the
road. 'CrgTrack' is the road as read: the middle line's points, the way
to the left along each row, the heights across ('nan' where a row has
no ground of its own). x east, y north, z up, m (x and y counted from a
spot the file's maker chose, so float32 holds them). 'crgTerrain' lays
the heights onto a regular grid ('_terrain.Terrain', its heights a
numpy array), every cell the mean of the road's heights in it, the
cells with none the nearest cell's that has (a car drives on what the
small steps' terrain knows).

The heights are public data; wherever they are shown or passed on,
'ATTRIBUTION' goes with them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
from typing import NamedTuple

import numpy

from ._terrain import Terrain

#  What goes with anything shown or passed on that is made from the
#  heights (uncannyball's note, 'Manners').
ATTRIBUTION = ('Contains data from Klimadatastyrelsen: Danmarks '
               'Højdemodel, DHM/Terræn and DHM/Overflade. CC BY 4.0.')
#  How much of a road's height's bilinear share a grid point must get
#  to count its own ('crgTerrain').
SPLAT_LEAST = 0.05


class CrgTrack(NamedTuple):
  """
  CrgTrack is a road laid along a line ('readCrg'): its rows 'step' m
  apart along the middle, 'x' and 'y' where each row crosses it (the
  last row the first again: a closed lap), 'leftX' and 'leftY' the unit
  way along each row to the left, 'across' where its columns lie left
  of the middle (m; below nought right), 'heights' each row's heights
  across (m, 'nan' for none), 'heading' each step's (rad from x toward
  y).
  """

  step: float
  x: numpy.ndarray
  y: numpy.ndarray
  leftX: numpy.ndarray
  leftY: numpy.ndarray
  across: numpy.ndarray
  heights: numpy.ndarray
  heading: numpy.ndarray

  def placeOf(self, row: int, across: float) -> tuple[float, float]:
    """The 'placeOf' method returns where the point 'across' m left of
    the middle on row 'row' lies, x and y."""
    return (float(self.x[row] + across * self.leftX[row]),
            float(self.y[row] + across * self.leftY[row]))


def _header(raw: bytes) -> tuple[dict, int, bytes]:
  """Returns an OpenCRG file's header's numbers by name, how many
  heights a row holds, and its rows' bytes."""
  cut = raw.index(b'\n$$')
  head = raw[:cut].decode('latin-1').splitlines()
  body = raw[raw.index(b'\n', cut + 1) + 1:]
  said = {}
  for line in head:
    key, equals, value = line.partition('=')
    if equals and key.strip().isupper():
      said[key.strip()] = float(value)
  columns = sum(1 for line in head if line.startswith('D:long section'))
  return said, columns, body


@functools.lru_cache(maxsize=2)
def readCrg(path: str) -> CrgTrack:
  """The 'readCrg' function returns the road in the OpenCRG file at
  'path' (its rows laid out from its start along their headings, each
  row's way to the left the mean of the steps either side; a closed
  lap's first and last rows meet), read once."""
  with open(path, 'rb') as file:
    raw = file.read()
  said, columns, body = _header(raw)
  numbers = numpy.frombuffer(body, '>f4')
  rows = numbers.size // (columns + 1)
  table = numbers[:rows * (columns + 1)].reshape(rows, columns + 1)
  heading = table[1:, 0].astype(numpy.float64)
  across = numpy.linspace(said['LONG_SECTION_V_RIGHT'],
                          said['LONG_SECTION_V_LEFT'], columns)
  step = said['REFERENCE_LINE_INCREMENT']
  ahead = numpy.stack((numpy.cos(heading), numpy.sin(heading)), 1)
  x = said['REFERENCE_LINE_START_X'] + step * numpy.concatenate(
    ([0.0], numpy.cumsum(ahead[:, 0])))
  y = said['REFERENCE_LINE_START_Y'] + step * numpy.concatenate(
    ([0.0], numpy.cumsum(ahead[:, 1])))
  joint = ahead[-1:] + ahead[:1]
  mean = numpy.concatenate((joint, ahead[:-1] + ahead[1:], joint))
  mean /= numpy.hypot(mean[:, 0], mean[:, 1])[:, None]
  return CrgTrack(step, x, y, -mean[:, 1], mean[:, 0], across,
                  numpy.array(table[:, 1:], numpy.float32), heading)


def crgTerrain(track: CrgTrack, cell: float, margin: float) -> Terrain:
  """The 'crgTerrain' function returns 'track''s heights laid onto a
  regular grid of 'cell' m squares over the road and 'margin' m about
  it: each of the road's heights shared out onto the grid's four points
  about it, bilinearly ('SPLAT_LEAST' of a share at least to count), each
  point the weighted mean of what it got, each with too little the
  nearest one's that has (across the empty inside of a tight corner,
  past the road's ends); a numpy array of float64, rows along x. (Each
  height given to its nearest point alone, the points it missed took
  their neighbours' and the road came out in terraces: its heights
  within 4 cm, its slopes not.)"""
  from scipy.ndimage import distance_transform_edt
  ok = ~numpy.isnan(track.heights)
  rows, columns = numpy.nonzero(ok)
  across = track.across[columns]
  px = track.x[rows] + across * track.leftX[rows]
  py = track.y[rows] + across * track.leftY[rows]
  x0, y0 = px.min() - margin, py.min() - margin
  nx = int(numpy.ceil((px.max() + margin - x0) / cell)) + 1
  ny = int(numpy.ceil((py.max() + margin - y0) / cell)) + 1
  fx, fy = (px - x0) / cell, (py - y0) / cell
  i = numpy.clip(numpy.floor(fx).astype(numpy.int64), 0, nx - 2)
  j = numpy.clip(numpy.floor(fy).astype(numpy.int64), 0, ny - 2)
  u, v = fx - i, fy - j
  values = track.heights[ok].astype(numpy.float64)
  sums, counts = numpy.zeros(nx * ny), numpy.zeros(nx * ny)
  for di, dj, share in ((0, 0, (1.0 - u) * (1.0 - v)), (1, 0, u * (1.0 - v)),
                        (0, 1, (1.0 - u) * v), (1, 1, u * v)):
    flat = (i + di) * ny + (j + dj)
    sums += numpy.bincount(flat, share * values, nx * ny)
    counts += numpy.bincount(flat, share, nx * ny)
  heights = numpy.zeros(nx * ny)
  held = counts > SPLAT_LEAST
  heights[held] = sums[held] / counts[held]
  heights = heights.reshape(nx, ny)
  held = held.reshape(nx, ny)
  nearest = distance_transform_edt(~held, None, False, True)
  heights = heights[nearest[0], nearest[1]]
  return Terrain((float(x0), float(y0)), float(cell), heights)
