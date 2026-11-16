"""
Walls laid on a grid, as a town's houses stand (user, 2026-11-15,
'previews/to_worqt.md': "What counts as a wall for the car comes from
the standing heights in the track files. Pick the threshold yourself").

'GridWall' is the walls as the ground holds them: at each point of a
regular grid how far it lies inside a wall, m (below nought: out in the
open, as far from the nearest face), and how tall the wall stands there
over the ground; between the points bilinear, its face where that is
nought, the way out of it the slope's. It answers as the oval's barrier
does ('_terrain.OvalWall'): 'beyond' (how far a place is through the
face, the face's outward normal there, level) and 'heightAt' (its top
over the ground), so the ground's law and the small steps take it alike.

'standingWall' makes one from a road laid along a line and how tall
things stand along it ('_crg.CrgTrack' twice, the same rows): a wall
where something stands 'least' m or more, beyond the road's edges and
more than 'corridor' m from its middle line (whatever stands over the
line is overhead: a tree's crown, an arch; the route is a road), every
place the road or its corridor reaches open whatever another stretch
says of it (a tree beside one street stands over another's lane).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

import numpy

#  How much of the road's samples' bilinear shares a grid point must get
#  to be walled, and how little of the open's it may (any open sample
#  near it and it is open), and how far the walls' faces are smoothed
#  (a Gaussian, grid points: the grid's staircase rounded off).
WALL_EVIDENCE, OPEN_EVIDENCE, WALL_SMOOTH = 0.3, 0.05, 1.0
#  How far from any wall a point is held to be at most, m (no deeper:
#  the grid's distances clipped there).
WALL_REACH = 8.0


class GridWall(NamedTuple):
  """
  GridWall is walls on a grid of square cells 'cell' m wide from
  'origin' (x, y): 'inside[i][j]' how far the point at x 'origin[0] + i
  cell', y 'origin[1] + j cell' lies inside a wall, m (below nought: out
  of every wall, that far from the nearest face), 'tops[i][j]' how tall
  the wall stands there over the ground, m; between the points
  bilinear; off the grid open. Its faces slide at 'grip'.
  """

  origin: tuple
  cell: float
  inside: numpy.ndarray
  tops: numpy.ndarray
  grip: float

  def _cellOf(self, x: float, y: float) -> tuple | None:
    """Returns the cell 'x', 'y' is in and how far across it (i, j, u,
    v), or None off the grid."""
    fx = (x - self.origin[0]) / self.cell
    fy = (y - self.origin[1]) / self.cell
    i, j = math.floor(fx), math.floor(fy)
    nx, ny = self.inside.shape
    if i < 0 or j < 0 or i >= nx - 1 or j >= ny - 1:
      return None
    return i, j, fx - i, fy - j

  def beyond(self, x: float, y: float) -> tuple:
    """The 'beyond' method returns how far 'x', 'y' is through a wall's
    face, m (below nought: out in the open), and the face's outward
    normal there, level (nx, ny: the way deeper into the wall; off the
    grid, or where the way is not to be told, along x)."""
    found = self._cellOf(x, y)
    if found is None:
      return -WALL_REACH, 1.0, 0.0
    i, j, u, v = found
    grid = self.inside
    a, b = float(grid[i, j]), float(grid[i + 1, j])
    c, d = float(grid[i, j + 1]), float(grid[i + 1, j + 1])
    depth = (a * (1.0 - u) + b * u) * (1.0 - v) + (c * (1.0 - u) + d * u) * v
    gx = (b - a) * (1.0 - v) + (d - c) * v
    gy = (c - a) * (1.0 - u) + (d - b) * u
    size = math.hypot(gx, gy)
    if size < 1e-12:
      return depth, 1.0, 0.0
    return depth, gx / size, gy / size

  def heightAt(self, x: float, y: float) -> float:
    """The 'heightAt' method returns how tall the wall stands over the
    ground at 'x', 'y', m (its cell's tallest corner; off the grid
    nought)."""
    found = self._cellOf(x, y)
    if found is None:
      return 0.0
    i, j, _, _ = found
    return float(self.tops[i:i + 2, j:j + 2].max())

  def tallest(self, ) -> float:
    """The 'tallest' method returns how tall the tallest wall stands
    over the ground, m."""
    return float(numpy.max(self.tops)) if self.tops.size else 0.0


def standingWall(track: object, tall: object, edges: tuple,
                 grid: tuple, least: float, corridor: float,
                 grip: float) -> GridWall:
  """The 'standingWall' function returns the walls by 'track' (a road
  along its rows) where 'tall' (the same rows: how tall things stand on
  the ground, m) says 'least' m or more beyond the road's 'edges' (each
  row's (right, left), m from its middle) and more than 'corridor' m
  from its middle, every place the road or the corridor reaches open
  (see the module's note), on 'grid' ((x0, y0), cell, (nx, ny): a
  terrain's), sliding at 'grip'."""
  from scipy.ndimage import distance_transform_edt, gaussian_filter
  (x0, y0), cell, (nx, ny) = grid
  right, left = (numpy.asarray(side, numpy.float64) for side in edges)
  standing = numpy.asarray(tall.heights, numpy.float64)
  across = track.across[None, :]
  beyondEdges = (across < -right[:, None]) | (across > left[:, None])
  out = numpy.abs(across) > corridor
  held = ~numpy.isnan(standing)
  high = held & (numpy.nan_to_num(standing) >= least)
  walled = high & beyondEdges & out
  opened = held & ~high | ~beyondEdges | ~out
  px = track.x[:, None] + across * track.leftX[:, None]
  py = track.y[:, None] + across * track.leftY[:, None]
  fx, fy = (px - x0) / cell, (py - y0) / cell
  i = numpy.floor(fx).astype(numpy.int64)
  j = numpy.floor(fy).astype(numpy.int64)
  ok = (i >= 0) & (j >= 0) & (i < nx - 1) & (j < ny - 1)
  u, v = fx - i, fy - j
  walls, opens = numpy.zeros(nx * ny), numpy.zeros(nx * ny)
  heights = numpy.zeros(nx * ny)
  for di, dj, share in ((0, 0, (1.0 - u) * (1.0 - v)), (1, 0, u * (1.0 - v)),
                        (0, 1, (1.0 - u) * v), (1, 1, u * v)):
    flat = (i + di) * ny + (j + dj)
    for mask, sums, values in ((walled & ok, walls, None),
                               (opened & ok, opens, None),
                               (walled & ok, heights, standing)):
      weights = share[mask] if values is None else share[mask] * values[mask]
      sums += numpy.bincount(flat[mask], weights, nx * ny)
  solid = ((walls > WALL_EVIDENCE) & (opens <= OPEN_EVIDENCE)).reshape(
    nx, ny)
  tops = numpy.where(walls > 0.0, heights / numpy.maximum(walls, 1e-12),
                     0.0).reshape(nx, ny)
  tops = numpy.where(solid, tops, 0.0).astype(numpy.float32)
  deep = distance_transform_edt(solid) * cell
  far = distance_transform_edt(~solid) * cell
  inside = numpy.where(solid, deep - 0.5 * cell, 0.5 * cell - far)
  inside = gaussian_filter(numpy.clip(inside, -WALL_REACH, WALL_REACH),
                           WALL_SMOOTH)
  return GridWall((float(x0), float(y0)), float(cell),
                  inside.astype(numpy.float32), tops, float(grip))
