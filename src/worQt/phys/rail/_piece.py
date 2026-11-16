"""
A stretch of track as its frame turns along it ('Piece'; user,
2026-11-15: "it's loop de loop time, but on rails!", and the spec
"Trains: the math first", Track geometry: the track is a ribbon, a
centre line and a frame along it, both exact functions of the distance
along it), and the stretches a track is built from: 'straight', 'bend'
(a circular arc about one of the frame's own axes), 'eased' (the turn
rates going linearly from one to another: a clothoid) and 'loop' (one
whole turn up and over, drifting sideways as it goes, a helix).

The frame is the track's: x along it, y to its left, z up from the
rails' plane; its turn rates per metre (twist, pitch, yaw) are about
those axes, right-handed: a pitch above nought turns the way down, a
yaw above nought turns it left, a twist above nought rolls it to the
right (its left side up).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from .._vectors import Vector, scaled

#  No turn.
LEVEL = (0.0, 0.0, 0.0)


class Piece(NamedTuple):
  """
  Piece is a stretch of a ribbon ('Ribbon'): 'length' m long, its frame
  turning per metre about its own axes by 'start' at its start and by
  'end' at its end, linearly between, each (twist, pitch, yaw), rad/m.
  """

  length: float
  start: Vector
  end: Vector


def straight(length: float) -> Piece:
  """The 'straight' function returns a straight stretch 'length' m
  long."""
  return Piece(float(length), LEVEL, LEVEL)


def bend(angle: float, radius: float, axis: Vector) -> Piece:
  """The 'bend' function returns a circular arc of 'radius' m turning
  the frame by 'angle' rad about 'axis' (a unit vector in the frame's
  own axes: (0, 1, 0) turns the way down, (0, -1, 0) up, (0, 0, 1)
  left)."""
  if radius <= 0.0 or angle <= 0.0:
    raise ValueError('a bend turns a positive angle on a positive radius')
  rate = scaled(axis, 1.0 / radius)
  return Piece(angle * radius, rate, rate)


def eased(length: float, start: Vector, end: Vector) -> Piece:
  """The 'eased' function returns a stretch 'length' m long whose turn
  rates go linearly from 'start' to 'end' (a clothoid where one rate
  moves)."""
  return Piece(float(length), tuple(start), tuple(end))


def loop(radius: float, drift: float) -> Piece:
  """The 'loop' function returns one whole turn up and over, 'radius' m
  from its axis, drifting 'drift' m to the left over the turn (a helix:
  its frame turns at one rate throughout, pitching up and twisting a
  little; below nought, to the right), so its way out runs beside its
  way in, as it was."""
  pitch = drift / (2.0 * math.pi)
  across = radius * radius + pitch * pitch
  rate = (-pitch / across, -radius / across, 0.0)
  return Piece(2.0 * math.pi * math.sqrt(across), rate, rate)
