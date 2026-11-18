"""
Ephemeris is the sky flown ahead of the game's time (user, 2026-11-18:
real gravity among the heavy bodies; "PHYSICS MUST BE REAL"): Sol, the
planets and the moons pulling each other, flown on a device of Warp's
('_sky_kernels.skyFlown') in steps of 'SPAN' s, each step's states
kept (a table). Nothing light pulls them (a rocket, Asger, the space
station), so the sky's path is the same whatever happens in the game:
it is flown ahead as far as anything looks ('AHEAD': the bed looks for
the morning up to two days on), and read anywhere in between (Hermite's
cubic from the two states either side: in 2000 s Luna goes a quarter
of a degree, the cubic misses by under a millimetre). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

#  The table's steps, s (the flight's kernel draws the sky between them:
#  '_flight_kernels.SKY_SPAN'); how far past what is asked it is flown
#  at once, s; the most steps a launch flies; how far behind the
#  earliest time still asked it keeps its rows, s.
SPAN = 2000.0
AHEAD = 3.0 * 86400.0
MOST_STEPS = 512
BEHIND = 2.0 * SPAN


class Ephemeris:
  """
  Ephemeris holds the heavy bodies' paths: their parents, depths and G
  M (Sol's first, its parent -1), and their table: 'rows' (each a step's
  states: a body's place and velocity from its parent, m and m/s,
  float64), the first at time 'start' (s since the sky's last leap), one
  each 'SPAN' s; 'version' counts the table's changes (what the flight
  has on its device follows it). 'coveredTo' flies it on to a time,
  'stateOf' reads a body's state at a time within it, 'fold' carries a
  leap's seconds into its times, 'trimmed' lets go of rows long past.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  device: str
  parents: tuple
  depths: tuple
  mus: tuple
  rows: numpy.ndarray
  start: float
  version: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, device: str, parents: tuple, depths: tuple,
               mus: tuple, states: numpy.ndarray, start: float) -> None:
    import warp as wp

    from . import _sky_kernels
    wp.init()
    self.wp, self.kernels, self.device = wp, _sky_kernels, device
    self.parents = tuple(int(p) for p in parents)
    self.depths = tuple(int(d) for d in depths)
    self.mus = tuple(float(m) for m in mus)
    count = len(self.parents)
    self._parents = wp.array(numpy.asarray(self.parents, numpy.int32),
                             wp.int32, None, None, None, None, device)
    self._depths = wp.array(numpy.asarray(self.depths, numpy.int32),
                            wp.int32, None, None, None, None, device)
    self._mus = wp.array(numpy.asarray(self.mus, numpy.float32),
                         wp.float32, None, None, None, None, device)
    self._places = wp.zeros(count, wp.vec3, device)
    self._kicks = wp.zeros(count, wp.vec3, device)
    self._table = wp.zeros(MOST_STEPS * count * _sky_kernels.ROWS,
                           wp.vec3, device)
    self._states = wp.zeros(count * _sky_kernels.ROWS, wp.vec3, device)
    self.version = 0
    self.restarted(states, start)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def end(self, ) -> float:
    """The 'end' property is the time of its last row, s."""
    return self.start + (len(self.rows) - 1) * SPAN

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def restarted(self, states: numpy.ndarray, start: float) -> None:
    """The 'restarted' method starts its table anew from 'states' (each
    body's place and velocity from its parent, float64, shape (bodies,
    2, 3); Sol's nought) at time 'start' (a new game, a saved one)."""
    states = numpy.asarray(states, numpy.float64)
    if states.shape != (len(self.parents), 2, 3):
      raise ValueError('states of shape %s for %d bodies' % (
        states.shape, len(self.parents)))
    if numpy.any(states[0] != 0.0):
      raise ValueError('Sol is the origin: its state is nought')
    self.rows, self.start = states[None].copy(), float(start)
    high = states.astype(numpy.float32)
    rest = (states - high).astype(numpy.float32)
    packed = numpy.stack([high[:, 0], rest[:, 0], high[:, 1], rest[:, 1]],
                         1).reshape(-1, 3)
    self._states.assign(packed)
    self.version += 1

  def coveredTo(self, t: float) -> None:
    """The 'coveredTo' method flies the sky on till its table reaches
    'AHEAD' past time 't' (a step or two a frame as time goes on)."""
    if self.end >= t + AHEAD:
      return
    needed = math.ceil((t + AHEAD - self.end) / SPAN)
    wp, kernels = self.wp, self.kernels
    count = len(self.parents)
    while needed > 0:
      steps = min(MOST_STEPS, needed)
      wp.launch(kernels.skyFlown, 1, [
        self._states, self._parents, self._depths, self._mus,
        self._places, self._kicks, self._table, steps, SPAN], [], [], [],
                self.device)
      flown = self._table.numpy()[:steps * count * kernels.ROWS].astype(
        numpy.float64).reshape(steps, count, kernels.ROWS, 3)
      states = numpy.stack([flown[:, :, 0] + flown[:, :, 1],
                            flown[:, :, 2] + flown[:, :, 3]], 2)
      self.rows = numpy.concatenate([self.rows, states])
      needed -= steps
    self.version += 1

  def stateOf(self, k: int, t: float) -> tuple:
    """The 'stateOf' method returns where body 'k' is from its parent and
    how fast it moves at time 't' (within the table: else it raises),
    two triples, m and m/s: Hermite's cubic between the rows either
    side."""
    if not self.start - 1e-6 <= t <= self.end + 1e-6:
      raise ValueError('the sky is flown from %.1f s to %.1f s, not at '
                       '%.1f s' % (self.start, self.end, t))
    j = min(len(self.rows) - 2, max(0, int((t - self.start) // SPAN)))
    if len(self.rows) == 1:
      place, speed = self.rows[0, k]
      return tuple(place.tolist()), tuple(speed.tolist())
    u = (t - self.start - j * SPAN) / SPAN
    (p0, v0), (p1, v1) = self.rows[j, k], self.rows[j + 1, k]
    u2, u3 = u * u, u * u * u
    place = ((2.0 * u3 - 3.0 * u2 + 1.0) * p0
             + (u3 - 2.0 * u2 + u) * SPAN * v0
             + (3.0 * u2 - 2.0 * u3) * p1 + (u3 - u2) * SPAN * v1)
    speed = ((6.0 * u2 - 6.0 * u) * p0 / SPAN
             + (3.0 * u2 - 4.0 * u + 1.0) * v0
             + (6.0 * u - 6.0 * u2) * p1 / SPAN
             + (3.0 * u2 - 2.0 * u) * v1)
    return tuple(place.tolist()), tuple(speed.tolist())

  def fold(self, seconds: float) -> None:
    """The 'fold' method carries 'seconds' s into its times (a leap:
    what was at time 'seconds' is at time nought)."""
    self.start -= float(seconds)
    self.version += 1

  def trimmed(self, t: float) -> None:
    """The 'trimmed' method lets go of the rows more than 'BEHIND' s
    before time 't' (nothing earlier is asked again)."""
    drop = int((t - BEHIND - self.start) // SPAN)
    drop = min(drop, len(self.rows) - 2)
    if drop > 0:
      self.rows = self.rows[drop:]
      self.start += drop * SPAN
      self.version += 1

  def kept(self, ) -> dict:
    """The 'kept' method returns what a saved game keeps of it: the row
    at or before time nought (the last leap; each body's place and
    velocity, float64) and its time."""
    j = max(0, min(len(self.rows) - 1, int((0.0 - self.start) // SPAN)))
    return {'start': self.start + j * SPAN,
            'states': self.rows[j].tolist()}

  def keptFrom(self, kept: dict) -> None:
    """The 'keptFrom' method starts it anew from what 'kept' had (its
    states and their time; flown on again from there, as before)."""
    self.restarted(numpy.asarray(kept['states'], numpy.float64),
                   float(kept['start']))
