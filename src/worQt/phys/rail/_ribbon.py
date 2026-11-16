"""
The track as a ribbon ('Ribbon'; the spec "Trains: the math first",
Track geometry): a centre line R(s) at the rails' top and a frame A(s)
along it, s the distance along it, m, from its start,

  dR/ds = A e_x,   dA/ds = A [k(s)]x,

k the frame's turn rates per metre about its own axes (twist, pitch,
yaw: '_piece'), each piece's going linearly along it. A piece turning
at one rate (a straight, an arc, a loop) is followed exactly: its frame
turns by the rate's matrix exponential, its centre line by that turn's
integral (Rodrigues, in closed form). A piece whose rates move (eased,
a clothoid) is cut into steps of 'EASED_STEP' m at its build, each
turning by fourth-order Magnus (its middle rate, and the commutator of
the rate and its change: exact where the rates keep their axis), its
centre line along each step's arc; between the cuts the same arcs, so a
question between them and at them agree. In float64, built once.

The specific force a vehicle running along the centre line feels, in
the track's frame ('feltAt'), at speed V gaining V' a second:

  f = (V', V^2 yaw, -V^2 pitch) - A^T g.

Its z part must stay above nought for the wheels to press (at a loop's
top, V^2 > g R).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import bisect
import math

import numpy

from .._vectors import Vector
from ._piece import Piece

#  The length of the steps an eased piece is cut into, m (its centre
#  line then within a micrometre over a hundred metres of easing).
EASED_STEP = 0.005
#  Gravity, m/s^2, z up.
GRAVITY = (0.0, 0.0, -9.81)
#  Below this turn (rad) a step's turn is summed by its series.
_SMALL = 1e-4


def _cross(k: numpy.ndarray) -> numpy.ndarray:
  """Returns the cross product matrix of 'k': [k]x v = k x v."""
  return numpy.array(((0.0, -k[2], k[1]), (k[2], 0.0, -k[0]),
                      (-k[1], k[0], 0.0)))


def turnOf(rate: numpy.ndarray, length: float) -> tuple:
  """The 'turnOf' function returns how a frame turning at 'rate' (per
  metre, about its own axes) turns over 'length' m (the rotation
  exp(length [rate]x)) and how far its x axis carries the centre line
  in the frame's own axes (the integral of the rotation's x column):
  (rotation, step), both exact."""
  w = float(numpy.linalg.norm(rate))
  theta = w * length
  big = _cross(rate)
  square = big @ big
  if theta < _SMALL:
    h2, h3 = length * length, length * length * length
    s1 = length - w * w * h3 / 6.0
    s2 = 0.5 * h2 - w * w * h2 * h2 / 24.0
    s3 = h3 / 6.0 - w * w * h3 * h2 / 120.0
  else:
    s1 = math.sin(theta) / w
    s2 = (1.0 - math.cos(theta)) / (w * w)
    s3 = (theta - math.sin(theta)) / (w * w * w)
  rotation = numpy.eye(3) + s1 * big + s2 * square
  step = (length * numpy.eye(3) + s2 * big + s3 * square)[:, 0]
  return rotation, step


class Ribbon:
  """
  Ribbon is a track as a centre line and a frame along it ('pieces',
  each a 'Piece', one after another), from 'place' (its start, m) and
  'frame' (its frame there: columns its x, y and z axes in the world),
  'length' m long. 'frameAt' answers where it is and how it lies at any
  s, 'rateAt' its turn rates there, 'feltAt' what a vehicle along it
  feels.
  """

  __slots__ = ('pieces', 'length', '_starts', '_places', '_frames',
               '_rates', '_ends', '_bounds')

  def __init__(self, pieces: tuple, place: Vector = (0.0, 0.0, 0.0),
               frame: numpy.ndarray = None) -> None:
    self.pieces = tuple(pieces)
    if not self.pieces:
      raise ValueError('a ribbon needs at least one piece')
    here = numpy.array(place, numpy.float64)
    turned = numpy.eye(3) if frame is None else numpy.array(frame,
                                                            numpy.float64)
    starts, places, frames, rates, bounds = [], [], [], [], []
    s = 0.0
    for piece in self.pieces:
      if piece.length <= 0.0:
        raise ValueError('a piece of no length: %r' % (piece,))
      bounds.append(s)
      start = numpy.array(piece.start, numpy.float64)
      end = numpy.array(piece.end, numpy.float64)
      steady = numpy.array_equal(start, end)
      count = 1 if steady else max(1, math.ceil(piece.length / EASED_STEP))
      h = piece.length / count
      change = (end - start) / piece.length
      for k in range(count):
        middle = start + change * (k + 0.5) * h
        rate = middle + h * h / 12.0 * numpy.cross(middle, change)
        starts.append(s + k * h)
        places.append(here)
        frames.append(turned)
        rates.append(rate)
        rotation, step = turnOf(rate, h)
        here = here + turned @ step
        turned = turned @ rotation
      s += piece.length
    self.length = s
    self._starts = starts
    self._places = numpy.array(places)
    self._frames = numpy.array(frames)
    self._rates = numpy.array(rates)
    self._ends = (here, turned)
    self._bounds = bounds

  def frameAt(self, s: float) -> tuple[numpy.ndarray, numpy.ndarray]:
    """The 'frameAt' method returns where the centre line is at 's' m
    along (m) and the frame there (columns its x, y and z axes in the
    world); past either end, held at it."""
    s = min(max(float(s), 0.0), self.length)
    if s >= self.length:
      return self._ends[0].copy(), self._ends[1].copy()
    i = max(0, bisect.bisect_right(self._starts, s) - 1)
    rotation, step = turnOf(self._rates[i], s - self._starts[i])
    frame = self._frames[i]
    return self._places[i] + frame @ step, frame @ rotation

  def segments(self, ) -> tuple:
    """The 'segments' method returns the ribbon as plain floats, for
    those who follow it step by step (the rail world): each step's start
    (m), its centre line's place there (x, y, z), its frame there (nine
    numbers, row by row) and its turn rates (twist, pitch, yaw), as
    four lists alike; from a step's start the frame turns at its rates
    exactly ('turnOf')."""
    return (list(self._starts),
            [tuple(float(x) for x in place) for place in self._places],
            [tuple(float(x) for x in frame.ravel())
             for frame in self._frames],
            [tuple(float(x) for x in rate) for rate in self._rates])

  def rateAt(self, s: float) -> numpy.ndarray:
    """The 'rateAt' method returns the frame's turn rates at 's' m along
    (twist, pitch, yaw; rad/m), as its piece has them."""
    s = min(max(float(s), 0.0), self.length)
    i = max(0, bisect.bisect_right(self._bounds, s) - 1)
    piece = self.pieces[i]
    share = (s - self._bounds[i]) / piece.length
    start = numpy.array(piece.start, numpy.float64)
    return start + share * (numpy.array(piece.end, numpy.float64) - start)

  def feltAt(self, s: float, speed: float, gain: float,
             gravity: Vector = GRAVITY) -> numpy.ndarray:
    """The 'feltAt' method returns the specific force a vehicle feels at
    's' m along, running at 'speed' m/s and gaining 'gain' m/s a second,
    in the track's frame (along, left, up), m/s^2: its acceleration less
    gravity."""
    _, frame = self.frameAt(s)
    rate = self.rateAt(s)
    moving = numpy.array((gain, speed * speed * rate[2],
                          -speed * speed * rate[1]))
    return moving - frame.T @ numpy.array(gravity, numpy.float64)
