"""
Autopilot keeps a vessel pointed (user, 2026-11-16: "an autopilot that
can lock their orientation in place or locked to following a path
towards apogee, or the opposite point"; "roll-insensitive controls that
work only in the parallel of travel, so that it basically means above
and below apoapsis"): it says how, the flight's kernel turns the
reaction wheels to do it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  What it can do, by the number the kernel knows it by: nothing; hold
#  the turn it was given; point the nose along the path (prograde: the
#  velocity over the ground in the air, the orbit's above it); point it
#  against the path (retrograde); point it where it is aimed (the aim:
#  a pitch over the horizon, along the path's heading and a turn off it,
#  or along a compass heading before there is a path; the vessel's roll
#  plays no part); hold a turn that turns ('match': the space station's
#  docking, user, 2026-11-17: its held turn set anew each frame, its
#  'spin' fed forward so it keeps up).
MODES = ('off', 'hold', 'prograde', 'retrograde', 'aim', 'match')


class Autopilot:
  """
  Autopilot holds what a vessel's autopilot does ('mode', one of
  'MODES'); holding, the turn it holds ('held', w x y z: the vessel's
  to the ecliptic's axes); aiming, the aim: 'pitch' (rad over the
  horizon), 'turn' (rad off the path, to the right), 'heading' (rad from
  north toward east: the compass heading while there is no path yet)
  and whether the aim follows the path ('travel'). The kernel does it:
  within a frame by the reaction wheels (the turn's error to a rate,
  the rate's to a torque), within a long step of time warp at once (the
  warp's rails).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('mode', 'held', 'spin', 'pitch', 'turn', 'heading', 'travel')

  #  Public Variables
  mode: str
  held: tuple
  spin: tuple
  pitch: float
  turn: float
  heading: float
  travel: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.mode, self.held = 'off', (1.0, 0.0, 0.0, 0.0)
    self.spin = (0.0, 0.0, 0.0)
    self.pitch, self.turn = 0.5 * math.pi, 0.0
    self.heading, self.travel = 0.5 * math.pi, False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def index(self, ) -> int:
    """The 'index' property is the mode's number, as the kernel knows
    it."""
    return MODES.index(self.mode)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def engaged(self, mode: str, turn: tuple) -> None:
    """The 'engaged' method sets the autopilot to 'mode', holding the
    vessel's 'turn' (w x y z) if it holds."""
    if mode not in MODES:
      raise ValueError('no autopilot mode %r: %r' % (mode, MODES))
    self.mode = mode
    if mode == 'hold':
      self.held = tuple(float(x) for x in turn)

  def matched(self, turn: tuple, spin: tuple) -> None:
    """The 'matched' method holds the vessel at 'turn' (w x y z) turning
    at 'spin' (rad/s, the ecliptic's axes): matching a turning thing."""
    self.mode = 'match'
    self.held = tuple(float(x) for x in turn)
    self.spin = tuple(float(x) for x in spin)

  def aimedAt(self, pitch: float, turn: float, heading: float,
              travel: bool) -> None:
    """The 'aimedAt' method aims the autopilot: 'pitch' over the horizon
    (kept within a right angle up or down), 'turn' off the path (kept
    within a right angle), along the path if 'travel' else the compass
    'heading' (within one turn)."""
    right = 0.5 * math.pi
    self.mode = 'aim'
    self.pitch = max(-right, min(right, float(pitch)))
    self.turn = max(-right, min(right, float(turn)))
    self.heading = float(heading) % (2.0 * math.pi)
    self.travel = bool(travel)


def aimOf(place: tuple, path: tuple, spin: tuple, pitch: float,
          turn: float, heading: float, travel: bool) -> tuple:
  """Returns where the aim mode points (a unit vector, the ecliptic's
  axes), as the kernel's 'aimed' does: 'pitch' over the horizon at
  'place' (from the anchor's middle), along 'path''s heading (flattened
  onto the horizon) and 'turn' off it to the right when 'travel', else
  along the compass 'heading' on a body turning at 'spin'."""
  up = _unit(place)
  axis = _unit(spin) if _norm(spin) > 1e-12 else (0.0, 0.0, 1.0)
  east = _cross(axis, up)
  if _norm(east) < 1e-6:
    east = _cross((1.0, 0.0, 0.0), up)
  east = _unit(east)
  north = _cross(up, east)
  way = tuple(n * math.cos(heading) + e * math.sin(heading)
              for n, e in zip(north, east))
  if travel:
    along = sum(a * b for a, b in zip(path, up))
    flat = tuple(a - along * b for a, b in zip(path, up))
    if _norm(flat) > 1e-3:
      way = _unit(flat)
  right = _cross(way, up)
  level = tuple(w * math.cos(pitch) + u * math.sin(pitch)
                for w, u in zip(way, up))
  return _unit(tuple(a * math.cos(turn) + r * math.sin(turn)
                     for a, r in zip(level, right)))


def _norm(a: tuple) -> float:
  """Returns the length of 'a'."""
  return math.sqrt(sum(x * x for x in a))


def _unit(a: tuple) -> tuple:
  """Returns 'a' made one long."""
  size = _norm(a)
  return tuple(x / size for x in a)


def _cross(a: tuple, b: tuple) -> tuple:
  """Returns the cross product of 'a' and 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])
