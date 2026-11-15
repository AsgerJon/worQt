"""
The real car's bodywork (user, 2026-11-15: "let's do something about
our minecraft ass blocky car. Move the seat back, front engine. Maybe
something like the Lotus 12 from 1958? as copyright allows of course?":
a late fifties' front-engined single seater's shape, no name or mark of
anyone's), drawn only: the frame carries the car, the shell meets
nothing. Qt-free, numpy: rows of eight a corner (place in the car's
frame, m, its normal, its picture's two coordinates), every triangle's
corners in turn, as '_meshes.finishedRows' takes them ('rows').

The shell is lofted: at each of 'STATIONS' along the car a rounded
section (a superellipse, 'ROUNDNESS': how square its shoulders are) of
its half width, its bottom and its top, smoothly between them (monotone
cubic: no bulge past a station); the cockpit cut out of its top, the
cut opening as it nears the cockpit's middle ('cockpitOf'); drawn on
both faces (inside 'SKIN' in), smooth shaded. Over it behind the driver
a headrest's fairing running down to the tail ('HEADREST'); in its
nose, the air's intake ('grilleRows'); before the driver, a low screen
bent round the cockpit's front ('screenRows').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

#  The shell's stations, nose to tail: where along the car (x, m), its
#  half width, its bottom and its top there, m (round the frame, its
#  tub, the engine's head, the column, the steering wheel's foot, the
#  gearbox and the tank: 'test_car_geometry.test_inside'; inside the
#  wheels; its tail full and high behind the cockpit, as the period's,
#  the rear struts' tops under its skin: user, 2026-11-15, the picture
#  previews/Lotus_12_Donington.jpg).
STATIONS = ((0.58, 0.14, 0.22, 0.40),
            (0.45, 0.21, 0.15, 0.46),
            (0.20, 0.32, 0.10, 0.60),
            (0.00, 0.325, 0.10, 0.63),
            (-0.30, 0.34, 0.11, 0.68),
            (-0.90, 0.355, 0.11, 0.71),
            (-1.35, 0.37, 0.11, 0.71),
            (-1.90, 0.37, 0.11, 0.70),
            (-2.40, 0.365, 0.115, 0.74),
            (-2.80, 0.35, 0.125, 0.76),
            (-3.10, 0.29, 0.155, 0.66),
            (-3.32, 0.17, 0.23, 0.52),
            (-3.44, 0.05, 0.31, 0.40))
#  How square the sections' shoulders are, over and under their middle
#  (two: an ellipse; the underside flatter, round the frame's rails).
ROUNDNESS, BOTTOM_ROUNDNESS = 3.0, 6.0
#  How finely the shell is cut: along the car, m, and round a section.
ALONG, ROUND = 0.03, 64
#  The skin's thickness, m (its inside drawn that far in).
SKIN = 0.003
#  The cockpit: where it opens and closes along the car, m (its edge's
#  ends eased over 'COCKPIT_EASE'), and how far round from the top the
#  cut reaches at its widest, rad.
COCKPIT_FRONT, COCKPIT_BACK, COCKPIT_EASE = -1.30, -2.06, 0.14
COCKPIT_OPEN = math.radians(52.0)
#  The headrest's fairing: from where to where along the car, its
#  peak's place, how far over the shell's top at its peak, m, its half
#  width there and at its tail.
HEADREST = (-2.04, -3.15, -2.16, 0.17, 0.10, 0.03)
#  The intake in the nose: its half width and half height, m, how far
#  in from the nose's end the grille sits.
INTAKE = (0.115, 0.075, 0.05)
#  The screen: its foot's place along the car, how far round the
#  cockpit's front it bends (rad either side of ahead), how high it
#  stands over the shell and how far it leans back, m.
SCREEN = (-1.28, math.radians(70.0), 0.13, 0.10)


def _smooth(t: numpy.ndarray) -> numpy.ndarray:
  """Returns the smoothstep of 't' (held within nought and one)."""
  t = numpy.clip(t, 0.0, 1.0)
  return t * t * (3.0 - 2.0 * t)


def _stationsAt(x: numpy.ndarray) -> tuple:
  """Returns the shell's half width, bottom and top at 'x' (each a
  monotone cubic through 'STATIONS')."""
  from scipy.interpolate import PchipInterpolator
  table = numpy.array(STATIONS)[::-1]
  return tuple(PchipInterpolator(table[:, 0], table[:, k])(x)
               for k in (1, 2, 3))


def insideShell(points: numpy.ndarray) -> numpy.ndarray:
  """The 'insideShell' function returns which of 'points' (n, 3, in the
  car's frame) lie inside the shell's outside (its sections closed over
  the cockpit: what it hides)."""
  points = numpy.asarray(points, numpy.float64)
  x = points[:, 0]
  widths, bottoms, tops = _stationsAt(x)
  middle, half = 0.5 * (tops + bottoms), 0.5 * (tops - bottoms)
  power = numpy.where(points[:, 2] >= middle, ROUNDNESS, BOTTOM_ROUNDNESS)
  inside = (numpy.abs(points[:, 1] / widths) ** power + numpy.abs(
    (points[:, 2] - middle) / half) ** power) <= 1.0
  return inside & (x <= STATIONS[0][0]) & (x >= STATIONS[-1][0])


def cockpitOf(x: numpy.ndarray) -> numpy.ndarray:
  """The 'cockpitOf' function returns how far round from the top the
  cockpit's cut reaches at 'x', rad (nought outside it)."""
  front = _smooth((COCKPIT_FRONT - x) / COCKPIT_EASE)
  back = _smooth((x - COCKPIT_BACK) / COCKPIT_EASE)
  return COCKPIT_OPEN * front * back


def _section(phi: numpy.ndarray, width: float, bottom: float,
             top: float) -> tuple:
  """Returns the points (y, z) round a section at angles 'phi' from its
  top (toward the left first): its upper half 'ROUNDNESS' square, its
  lower 'BOTTOM_ROUNDNESS'."""
  s, c = numpy.sin(phi), numpy.cos(phi)
  power = numpy.where(c >= 0.0, 2.0 / ROUNDNESS, 2.0 / BOTTOM_ROUNDNESS)
  y = width * numpy.sign(s) * numpy.abs(s) ** power
  z = 0.5 * (top + bottom) + 0.5 * (top - bottom) * numpy.sign(c) * (
    numpy.abs(c) ** power)
  return y, z


def _grid() -> numpy.ndarray:
  """Returns the shell's outside as a grid of points (along the car,
  round each section: from the cockpit's cut's left edge round under
  to its right edge; closed where there is no cut), m."""
  first, last = STATIONS[0][0], STATIONS[-1][0]
  xs = numpy.linspace(first, last, int(round((first - last) / ALONG)) + 1)
  widths, bottoms, tops = _stationsAt(xs)
  cuts = cockpitOf(xs)
  u = numpy.linspace(0.0, 1.0, ROUND + 1)
  grid = numpy.zeros((len(xs), len(u), 3))
  for k, x in enumerate(xs):
    phi = cuts[k] + u * (2.0 * math.pi - 2.0 * cuts[k])
    y, z = _section(phi, widths[k], bottoms[k], tops[k])
    grid[k, :, 0], grid[k, :, 1], grid[k, :, 2] = x, y, z
  return grid


def _normalsOf(grid: numpy.ndarray) -> numpy.ndarray:
  """Returns a grid's smooth unit normals (by its differences along both
  ways), turned out from the car's middle line."""
  along = numpy.gradient(grid, axis=0)
  round_ = numpy.gradient(grid, axis=1)
  normal = numpy.cross(along, round_)
  middle = grid.copy()
  middle[..., 1] = 0.0
  middle[..., 2] = numpy.mean(grid[..., 2], axis=1, keepdims=True)
  outward = numpy.einsum('ijk,ijk->ij', normal, grid - middle)
  normal *= numpy.where(outward < 0.0, -1.0, 1.0)[..., None]
  size = numpy.linalg.norm(normal, axis=-1, keepdims=True)
  return normal / numpy.maximum(size, 1e-12)


def _gridRows(grid: numpy.ndarray, normal: numpy.ndarray,
              outward: bool) -> numpy.ndarray:
  """Returns a grid's quads as triangles' rows (place, normal, picture),
  wound so they face along 'normal' (or against it: the inside)."""
  n, m = grid.shape[:2]
  i, j = numpy.meshgrid(numpy.arange(n - 1), numpy.arange(m - 1),
                        indexing='ij')
  i, j = i.ravel(), j.ravel()
  corners = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j), (i + 1, j + 1),
             (i, j + 1))
  place = numpy.stack([grid[a, b] for a, b in corners], 1)
  normals = numpy.stack([normal[a, b] for a, b in corners], 1)
  face = numpy.cross(place[:, 1] - place[:, 0], place[:, 2] - place[:, 0])
  facing = numpy.einsum('ij,ij->i', face, normals.mean(1))
  flip = (facing < 0.0) if outward else (facing > 0.0)
  for k in (0, 3):
    swapped = place[flip, k + 1].copy()
    place[flip, k + 1] = place[flip, k + 2]
    place[flip, k + 2] = swapped
    swapped = normals[flip, k + 1].copy()
    normals[flip, k + 1] = normals[flip, k + 2]
    normals[flip, k + 2] = swapped
  if not outward:
    normals = -normals
  rows = numpy.zeros((len(place) * 6, 8))
  rows[:, :3] = place.reshape(-1, 3)
  rows[:, 3:6] = normals.reshape(-1, 3)
  return rows


def _skinned(grid: numpy.ndarray) -> numpy.ndarray:
  """Returns a grid drawn outside and in ('SKIN' in), as rows."""
  normal = _normalsOf(grid)
  return numpy.concatenate((_gridRows(grid, normal, True),
                            _gridRows(grid - SKIN * normal, normal, False)))


def _headrestGrid() -> numpy.ndarray:
  """Returns the headrest's fairing as a grid of points: half ellipses
  over the shell's top, rising to its peak and running down to its
  tail."""
  start, end, peak, high, wide, narrow = HEADREST
  xs = numpy.linspace(start, end, int(round((start - end) / ALONG)) + 1)
  _, _, tops = _stationsAt(xs)
  rise = numpy.where(xs > peak, _smooth((start - xs) / (start - peak)),
                     1.0 - _smooth((peak - xs) / (peak - end)) ** 0.8)
  heights = high * rise
  widths = narrow + (wide - narrow) * numpy.where(
    xs > peak, 1.0, (xs - end) / (peak - end))
  phi = numpy.linspace(-0.5 * math.pi, 0.5 * math.pi, ROUND // 2 + 1)
  grid = numpy.zeros((len(xs), len(phi), 3))
  for k, x in enumerate(xs):
    grid[k, :, 0] = x
    grid[k, :, 1] = widths[k] * numpy.sin(phi)
    grid[k, :, 2] = tops[k] - 0.02 + (heights[k] + 0.02) * numpy.cos(phi)
  return grid


def shellRows() -> numpy.ndarray:
  """The 'shellRows' function returns the shell and its headrest's
  fairing as rows (both faces), in the car's frame."""
  return numpy.concatenate((_skinned(_grid()), _skinned(_headrestGrid())))


def grilleRows() -> numpy.ndarray:
  """The 'grilleRows' function returns the intake's grille: an oval set
  'INTAKE' in from the nose's end, facing ahead (and back), as rows."""
  wide, high, inset = INTAKE
  x = STATIONS[0][0] - inset
  middle = 0.5 * (STATIONS[0][2] + STATIONS[0][3])
  angles = numpy.linspace(0.0, 2.0 * math.pi, ROUND + 1)
  rows = []
  for a, b in zip(angles[:-1], angles[1:]):
    rim = [(x, wide * math.cos(angle), middle + high * math.sin(angle))
           for angle in (a, b)]
    for ahead, (first, second) in ((1.0, rim), (-1.0, rim[::-1])):
      for point in ((x, 0.0, middle), first, second):
        rows.append(point + (ahead, 0.0, 0.0, 0.0, 0.0))
  return numpy.array(rows)


def screenRows() -> numpy.ndarray:
  """The 'screenRows' function returns the screen: a band bent round the
  cockpit's front on the shell's top, standing 'SCREEN' high and
  leaning back, both faces, as rows."""
  foot, bend, high, lean = SCREEN
  width, bottom, top = (float(value[0]) for value in _stationsAt(
    numpy.array([foot])))
  phi = numpy.linspace(-bend, bend, ROUND // 2 + 1)
  y, z = _section(phi, width * 0.92, bottom, top)
  grid = numpy.zeros((2, len(phi), 3))
  grid[0, :, 0], grid[0, :, 1], grid[0, :, 2] = foot, y, z - 0.01
  grid[1, :, 0] = foot - lean
  grid[1, :, 1], grid[1, :, 2] = 0.9 * y, z + high
  normal = numpy.zeros_like(grid)
  normal[..., 0], normal[..., 2] = high, lean
  normal /= numpy.linalg.norm(normal, axis=-1, keepdims=True)
  return numpy.concatenate((_gridRows(grid, normal, True),
                            _gridRows(grid, normal, False)))
