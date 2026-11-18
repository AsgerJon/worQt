"""
Egg is the cabin's gravity egg (user, 2026-11-18: "We need some kind of
diegetic indicator of the presence of gravity ... A glass egg with a
ball rolling around inside, a ball that emits light. On the ground the
ball is on the ground, but without gravity i just floats"; "place the
egg on a pedetal centrally in the room"): a glass egg, its blunt end
down, in a brass cup on a pedestal in the middle of the cabin (off the
hatch's axis: the way up), a glowing marble loose inside it. The marble
feels what anything loose there feels (the vessel's push the other way
and its turning: 'Accelerometer.pullAt'), the air, and the glass: it
bounces off it, rolls on it slowing, and so lies at the bottom on the
pad, is pressed down under thrust, drifts weightless, and docked to the
turning station settles slowly outward. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy

from ._cockpit import FLOOR
from ._shapes import UNTURNED, ballRows, cylinderRows, frustumRows

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._accelerometer import Accelerometer

#  The pedestal: where it stands on the floor (x, y: 1.6 m off the
#  hatch's axis, clear of the furniture, the floor's bolts and his
#  chair), its foot's radius and height, its column's radius, its top's
#  radius and height and how high its top is over the floor; the brass
#  cup the egg stands in (its radius and height), m.
PEDESTAL = (1.1, 1.1)
FOOT = (0.2, 0.03)
COLUMN = 0.06
TOP = (0.12, 0.03)
PEDESTAL_HIGH = 1.0
CUP = (0.034, 0.02)
#  The egg inside its glass: half its width, how far its blunt end is
#  down from its middle and its narrow end up; the glass's thickness;
#  the marble's radius, m.
EGG_HALF = 0.045
EGG_LOW = 0.05
EGG_HIGH = 0.07
GLASS = 0.002
BALL = 0.012
#  The marble on the glass: what share of its speed into the glass comes
#  back off it (not when it comes in no faster than the pull pressing it
#  there gives it in a step, and 'STILL_ONTO' m/s: lying on the glass it
#  stays on it); the share of the glass's push it loses of its speed
#  along it (rolling: pressed by the pull or turned along the glass's
#  curve; weightless, gliding, it does not slow); the air's drag a
#  second (as the loose things', '_cabin_kernels.AIR').
BOUNCE = 0.4
STILL_ONTO = 0.001
ROLL_DRAG = 0.02
AIR = 0.03
#  Its steps (s; no more a frame: a longer frame takes longer steps).
STEP = 1.0 / 480.0
MOST_STEPS = 60


def eggMiddle() -> tuple:
  """Returns the egg's middle (the vessel's own axes): over the
  pedestal's top, its blunt end in the cup."""
  x, y = PEDESTAL
  return x, y, FLOOR + PEDESTAL_HIGH + CUP[1] + EGG_LOW


def pedestalParts() -> tuple:
  """Returns the pedestal's meshes, each its look and its rows and
  triangles: its foot and top brass, its column oak, the cup brass."""
  x, y = PEDESTAL
  up = (0.0, 0.0, 1.0)
  top = FLOOR + PEDESTAL_HIGH
  return (('brass', cylinderRows((x, y, FLOOR), up, FOOT[0], FOOT[1], 40)),
          ('oak', cylinderRows((x, y, FLOOR + FOOT[1]), up, COLUMN,
                               top - TOP[1] - FLOOR - FOOT[1], 28)),
          ('brass', cylinderRows((x, y, top - TOP[1]), up, TOP[0], TOP[1],
                                 40)),
          ('brass', frustumRows((x, y, top), up, CUP[0] - 0.008, CUP[0],
                                CUP[1], 28)))


def pedestalSolids() -> tuple:
  """Returns the pedestal's and the egg's solid boxes, each its middle,
  half sizes and axes (the vessel's own): its foot, its column, its top
  and the egg in its cup (Asger floating meets the glass)."""
  x, y = PEDESTAL
  top = FLOOR + PEDESTAL_HIGH
  egg = eggMiddle()
  return (((x, y, FLOOR + 0.5 * FOOT[1]), (FOOT[0], FOOT[0],
                                            0.5 * FOOT[1]), UNTURNED),
          ((x, y, 0.5 * (FLOOR + top)), (COLUMN, COLUMN,
                                         0.5 * (top - FLOOR)), UNTURNED),
          ((x, y, top - 0.5 * TOP[1]), (TOP[0], TOP[0], 0.5 * TOP[1]),
           UNTURNED),
          ((x, y, 0.5 * (top + egg[2] + EGG_HIGH)),
           (EGG_HALF, EGG_HALF, 0.5 * (egg[2] + EGG_HIGH - top)), UNTURNED))


def eggRows() -> tuple:
  """Returns the egg's glass (the vessel's own axes): two half
  ellipsoids round its middle, the blunt one down, its faces out."""
  rows, faces = [], []
  rings, spokes = 32, 48
  middle = eggMiddle()
  for i in range(rings + 1):
    polar = math.pi * i / rings
    high = EGG_HIGH if polar < 0.5 * math.pi else EGG_LOW
    for j in range(spokes + 1):
      a = 2.0 * math.pi * j / spokes
      x = EGG_HALF * math.sin(polar) * math.cos(a)
      y = EGG_HALF * math.sin(polar) * math.sin(a)
      z = high * math.cos(polar)
      normal = numpy.array((x / EGG_HALF ** 2, y / EGG_HALF ** 2,
                            z / high ** 2))
      size = float(numpy.linalg.norm(normal))
      normal = normal / size if size > 0.0 else numpy.array(
        (0.0, 0.0, 1.0 if i == 0 else -1.0))
      rows.append((middle[0] + x, middle[1] + y, middle[2] + z)
                  + tuple(normal.tolist()) + (0.0, 0.0))
  for i in range(rings):
    for j in range(spokes):
      a, b = i * (spokes + 1) + j, (i + 1) * (spokes + 1) + j
      faces.extend((a, b, b + 1, a, b + 1, a + 1))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def marbleRows() -> tuple:
  """Returns the marble, about its middle."""
  return ballRows((0.0, 0.0, 0.0), BALL, 20)


class Egg:
  """
  Egg holds the marble: where it is from the egg's middle ('ball', m,
  the vessel's own axes) and how fast it moves ('moving', m/s);
  'stepped' moves it on, 'place' is where it is in the cabin, 'inside'
  how far a point is inside the room its middle has (the glass less
  its round; nought or less: at the glass).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('ball', 'moving')

  #  Public Variables
  ball: tuple
  moving: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.ball = (0.0, 0.0, -_low())
    self.moving = (0.0, 0.0, 0.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def place(self, ) -> tuple:
    """The 'place' property is where the marble's middle is (the
    vessel's own axes)."""
    return tuple(m + b for m, b in zip(eggMiddle(), self.ball))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stepped(self, seconds: float, accelerometer: Accelerometer) -> None:
    """The 'stepped' method moves the marble 'seconds' s on (real time)
    as the cabin is pushed and turns ('accelerometer': what it measured
    this frame), in steps of 'STEP' (no more than 'MOST_STEPS')."""
    if seconds <= 0.0:
      return
    steps = max(1, min(MOST_STEPS, math.ceil(seconds / STEP)))
    step = seconds / steps
    middle = eggMiddle()
    x, y, z = self.ball
    vx, vy, vz = self.moving
    for _ in range(steps):
      pull = accelerometer.pullAt((middle[0] + x, middle[1] + y,
                                   middle[2] + z), (vx, vy, vz))
      vx += (pull[0] - AIR * vx) * step
      vy += (pull[1] - AIR * vy) * step
      vz += (pull[2] - AIR * vz) * step
      x, y, z = x + vx * step, y + vy * step, z + vz * step
      (x, y, z), (vx, vy, vz) = _met((x, y, z), (vx, vy, vz), pull, step)
    self.ball, self.moving = (x, y, z), (vx, vy, vz)

  def inside(self, point: tuple) -> float:
    """The 'inside' method returns how far 'point' (from the egg's
    middle) is inside where the marble's middle may be, roughly in m
    (along its nearest axis; nought or less: at or past the glass)."""
    x, y, z = point
    high = _high() if z >= 0.0 else _low()
    share = (x * x + y * y) / _half() ** 2 + z * z / high ** 2
    return (1.0 - math.sqrt(share)) * min(_half(), high)


def _half() -> float:
  """Returns how far the marble's middle may go across the egg, m."""
  return EGG_HALF - GLASS - BALL


def _low() -> float:
  """Returns how far down the marble's middle may go, m."""
  return EGG_LOW - GLASS - BALL


def _high() -> float:
  """Returns how far up the marble's middle may go, m."""
  return EGG_HIGH - GLASS - BALL


def _met(place: tuple, moving: tuple, pull: tuple, step: float) -> tuple:
  """Returns the marble's middle and velocity after it meets the glass
  over a 'step' s, pulled 'pull' (m/s²; unchanged if it does not meet
  it): put back on it, its speed into it lost (bounced back 'BOUNCE' of
  it, but coming in no faster than the pull gives it a step: lying on
  it), its speed along it slowed 'ROLL_DRAG' of what the glass took."""
  x, y, z = place
  half = _half()
  high = _high() if z >= 0.0 else _low()
  share = (x * x + y * y) / half ** 2 + z * z / high ** 2
  if share <= 1.0:
    return place, moving
  back = 1.0 / math.sqrt(share)
  x, y, z = x * back, y * back, z * back
  nx, ny, nz = x / half ** 2, y / half ** 2, z / high ** 2
  size = math.sqrt(nx * nx + ny * ny + nz * nz)
  nx, ny, nz = nx / size, ny / size, nz / size
  vx, vy, vz = moving
  into = vx * nx + vy * ny + vz * nz
  if into <= 0.0:
    return (x, y, z), moving
  pressed = max(0.0, pull[0] * nx + pull[1] * ny + pull[2] * nz) * step
  lying = into <= 2.0 * pressed + STILL_ONTO
  lost = into * (1.0 if lying else 1.0 + BOUNCE)
  vx, vy, vz = vx - lost * nx, vy - lost * ny, vz - lost * nz
  along = vx * nx + vy * ny + vz * nz
  tx, ty, tz = vx - along * nx, vy - along * ny, vz - along * nz
  gliding = math.sqrt(tx * tx + ty * ty + tz * tz)
  if gliding > 0.0:
    kept = max(0.0, gliding - ROLL_DRAG * lost) / gliding
    tx, ty, tz = tx * kept, ty * kept, tz * kept
  return (x, y, z), (along * nx + tx, along * ny + ty, along * nz + tz)
