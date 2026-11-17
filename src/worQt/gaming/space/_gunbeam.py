"""
The Temu gravity gun's beam (user, 2026-11-17: "the temu-gravgun should
try to pick up one of the glowing bolts but instead pull Asger towards
it. Also, give the gravity gun some cool animations, like a laser beam
between it and the bolts"): while the gun holds a magic bolt, a beam
from its muzzle to the bolt: a glowing core (a ball of light at the
muzzle, a wobble along it), two strands coiling round it (twisting on as
time goes), a ring gripping the bolt (pulsing, as if it tugged at a
bolt that will not come). Its 'strength' swells as it grabs (a flash)
and settles to one. Meshes made each frame (rows of eight: place,
normal, picture), in the vessel's own axes from the muzzle. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._gunmodel import gunParts

TAU = 2.0 * math.pi
#  The core: its radius (at strength one), the muzzle's ball's, how far
#  it wobbles, its cuts round and along.
CORE = 0.008
MUZZLE_BALL = 0.022
WOBBLE = 0.012
CORE_CUTS = (8, 40)
#  The coils: two, this far round the core, a turn every 'COIL_TURN' m,
#  their thickness, their cuts along (a metre) and round.
COILS = 2
COIL_OUT = 0.03
COIL_TURN = 0.22
COIL_THICK = 0.004
COIL_CUTS = (100, 5)
#  The grip round the bolt: its radius (pulsing by 'GRIP_PULSE' of it),
#  its thickness, its cuts round and round its tube.
GRIP = 0.085
GRIP_PULSE = 0.25
GRIP_THICK = 0.007
GRIP_CUTS = (32, 6)
#  The grab's flash: how strong it starts and how fast it settles, s.
FLASH = 2.2
FLASH_FADES = 0.25


@functools.lru_cache(maxsize=1)
def muzzle() -> tuple:
  """Returns the gun's muzzle in his eyes' frame (right, up, back): the
  middle of its foremost part."""
  rows = numpy.concatenate([part[2][:, :3] for part in gunParts()])
  front = rows[rows[:, 2] < rows[:, 2].min() + 0.03]
  return tuple(float(x) for x in front.mean(axis=0))


def strengthOf(since: float) -> float:
  """Returns the beam's strength 'since' s after it grabbed: 'FLASH'
  settling to one."""
  return 1.0 + (FLASH - 1.0) * math.exp(-max(0.0, since) / FLASH_FADES)


def beamRows(way: tuple, phase: float, strength: float) -> tuple:
  """Returns the beam's two meshes from the muzzle (its origin) along
  'way' (to the bolt, m: the vessel's own axes) at 'phase' (rad: time
  moving it on) and 'strength': the core (the muzzle's ball, the
  wobbling core, the grip round the bolt) and the coils."""
  way = numpy.array(way, numpy.float64)
  long = float(numpy.linalg.norm(way))
  if long < 1e-6:
    way, long = numpy.array((0.0, 0.0, -1.0)), 1e-6
  ahead = way / long
  other = numpy.array((0.0, 0.0, 1.0)) if abs(ahead[2]) < 0.9 else (
    numpy.array((1.0, 0.0, 0.0)))
  side = numpy.cross(ahead, other)
  side /= numpy.linalg.norm(side)
  up = numpy.cross(ahead, side)
  core = [_ballRows(numpy.zeros(3), MUZZLE_BALL * strength),
          _coreRows(ahead, side, up, long, phase, strength),
          _gripRows(ahead, side, up, long, phase, strength)]
  coils = [_coilRows(ahead, side, up, long, phase + TAU * k / COILS,
                     strength) for k in range(COILS)]
  return _joined(core), _joined(coils)


def _centre(ahead: numpy.ndarray, side: numpy.ndarray, up: numpy.ndarray,
            share: numpy.ndarray, long: float, phase: float) -> tuple:
  """Returns the core's line at 'share's of its length: its places, the
  wobble nought at both ends."""
  sway = WOBBLE * numpy.sin(math.pi * share) * numpy.sin(
    3.0 * TAU * share - 2.0 * phase)
  return (share[:, None] * long * ahead + sway[:, None] * side
          + 0.5 * sway[:, None] * up)


def _coreRows(ahead: numpy.ndarray, side: numpy.ndarray,
              up: numpy.ndarray, long: float, phase: float,
              strength: float) -> tuple:
  """Returns the core: a tube along the wobbling line."""
  sides, along = CORE_CUTS
  share = numpy.linspace(0.0, 1.0, along + 1)
  line = _centre(ahead, side, up, share, long, phase)
  return _tubeRows(line, ahead, side, up, CORE * strength, sides)


def _coilRows(ahead: numpy.ndarray, side: numpy.ndarray,
              up: numpy.ndarray, long: float, phase: float,
              strength: float) -> tuple:
  """Returns a coil winding round the core, a turn every 'COIL_TURN' m,
  turning on with 'phase'."""
  along, sides = COIL_CUTS
  count = max(8, int(along * long))
  share = numpy.linspace(0.0, 1.0, count + 1)
  angle = TAU * share * long / COIL_TURN + phase
  out = COIL_OUT * (0.6 + 0.4 * strength) * numpy.sin(math.pi * share) ** 0.3
  line = (_centre(ahead, side, up, share, long, phase)
          + (out * numpy.cos(angle))[:, None] * side
          + (out * numpy.sin(angle))[:, None] * up)
  return _tubeRows(line, ahead, side, up, COIL_THICK * strength, sides)


def _gripRows(ahead: numpy.ndarray, side: numpy.ndarray,
              up: numpy.ndarray, long: float, phase: float,
              strength: float) -> tuple:
  """Returns the ring gripping the bolt, round the beam's end, pulsing."""
  round_, tube = GRIP_CUTS
  radius = GRIP * (1.0 + GRIP_PULSE * math.sin(3.0 * phase)) * (
    0.8 + 0.2 * strength)
  a = numpy.linspace(0.0, TAU, round_ + 1)[:, None, None]
  b = numpy.linspace(0.0, TAU, tube + 1)[None, :, None]
  out = numpy.cos(a) * side + numpy.sin(a) * up
  normals = numpy.cos(b) * out + numpy.sin(b) * ahead
  places = long * ahead + radius * out + GRIP_THICK * strength * normals
  rows = numpy.concatenate([places, normals, numpy.zeros(
    places.shape[:2] + (2,))], axis=2).reshape(-1, 8)
  k = numpy.arange(round_)[:, None] * (tube + 1) + numpy.arange(
    tube)[None, :]
  a, b = k.ravel(), k.ravel() + tube + 1
  faces = numpy.stack([a, b, b + 1, a, b + 1, a + 1], axis=1).ravel()
  return rows, faces.astype(numpy.uint32)


def _tubeRows(line: numpy.ndarray, ahead: numpy.ndarray,
              side: numpy.ndarray, up: numpy.ndarray, radius: float,
              sides: int) -> tuple:
  """Returns a thin tube along 'line' (places), 'radius' round."""
  angles = numpy.linspace(0.0, TAU, sides + 1)
  ring = (numpy.cos(angles)[:, None] * side
          + numpy.sin(angles)[:, None] * up)
  places = line[:, None, :] + radius * ring[None, :, :]
  normals = numpy.broadcast_to(ring[None, :, :], places.shape)
  rows = numpy.concatenate([places, normals, numpy.zeros(
    places.shape[:2] + (2,))], axis=2).reshape(-1, 8)
  count = len(line)
  k = numpy.arange(count - 1)[:, None] * (sides + 1) + numpy.arange(
    sides)[None, :]
  a, b = k.ravel(), k.ravel() + sides + 1
  faces = numpy.stack([a, b, b + 1, a, b + 1, a + 1], axis=1).ravel()
  return rows, faces.astype(numpy.uint32)


def _ballRows(middle: numpy.ndarray, radius: float) -> tuple:
  """Returns a small ball of light."""
  rows, faces = _unitBall()
  out = rows.copy()
  out[:, :3] = middle + radius * rows[:, 3:6]
  return out, faces


@functools.lru_cache(maxsize=1)
def _unitBall() -> tuple:
  """Returns a unit ball's rows and triangles (made once)."""
  rings, spokes = 6, 10
  lat = numpy.linspace(-0.5 * math.pi, 0.5 * math.pi, rings + 1)[:, None]
  lon = numpy.linspace(0.0, TAU, spokes + 1)[None, :]
  normal = numpy.stack(numpy.broadcast_arrays(
    numpy.cos(lat) * numpy.cos(lon), numpy.cos(lat) * numpy.sin(lon),
    numpy.sin(lat)), axis=2)
  rows = numpy.concatenate([normal, normal, numpy.zeros(
    normal.shape[:2] + (2,))], axis=2).reshape(-1, 8)
  k = numpy.arange(rings)[:, None] * (spokes + 1) + numpy.arange(
    spokes)[None, :]
  a, b = k.ravel(), k.ravel() + spokes + 1
  faces = numpy.stack([a, b, b + 1, a, b + 1, a + 1], axis=1).ravel()
  return rows, faces.astype(numpy.uint32)


def _joined(parts: list) -> tuple:
  """Returns 'parts' as one mesh."""
  rows, faces, count = [], [], 0
  for part, indices in parts:
    rows.append(numpy.asarray(part, numpy.float64))
    faces.append(numpy.asarray(indices, numpy.uint32) + count)
    count += len(part)
  return numpy.concatenate(rows), numpy.concatenate(faces).astype(
    numpy.uint32)
