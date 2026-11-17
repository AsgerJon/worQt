"""
Transfers solves Lambert's problem round a puller on a device of Warp's,
many at once (the automatic rendezvous's plan: every departure and
flight time it weighs) or one (its burns, each frame): from a place to a
place in a time, coasting. The numbers go to the device in the puller's
own units (lengths in the first start's distance, times so G M is one:
near one, float32 keeps its digits) and come back in m/s.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy


class Transfers:
  """
  Transfers solves transfers on 'device' ('solved'): for each start,
  end (m from the puller) and time (s), the velocities leaving and
  arriving (m/s) of the coast between them going round 'normal' the way
  it turns (less than a turn); NaN rows where there is none.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  device: str

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, device: str) -> None:
    import warp as wp

    from . import _transfer_kernels
    wp.init()
    wp.load_module(_transfer_kernels, device)
    self.device, self._wp, self._kernels = device, wp, _transfer_kernels

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def solved(self, mu: float, starts: object, ends: object, times: object,
             normal: tuple) -> tuple:
    """The 'solved' method returns the velocities leaving and arriving
    (two arrays, a row a transfer, m/s) of the transfers from 'starts' to
    'ends' (rows, m from the puller of G M 'mu') in 'times' (s), round
    'normal' the way it turns; NaN rows where none is."""
    wp = self._wp
    starts = numpy.asarray(starts, numpy.float64).reshape(-1, 3)
    ends = numpy.asarray(ends, numpy.float64).reshape(-1, 3)
    times = numpy.asarray(times, numpy.float64).reshape(-1)
    if not (len(starts) == len(ends) == len(times)):
      raise ValueError('%d starts, %d ends and %d times' % (
        len(starts), len(ends), len(times)))
    unit = float(numpy.linalg.norm(starts[0]))
    beat = math.sqrt(unit ** 3 / mu)
    speed = unit / beat
    device = self.device
    count = len(times)
    leaving = wp.zeros(count, wp.vec3, device)
    arriving = wp.zeros(count, wp.vec3, device)
    wp.launch(self._kernels.transfersSolved, count, [
      self._array(starts / unit, wp.vec3),
      self._array(ends / unit, wp.vec3),
      self._array(times / beat, wp.float32),
      wp.vec3(*normal), leaving, arriving], [], [], [], device)
    return (leaving.numpy().astype(numpy.float64) * speed,
            arriving.numpy().astype(numpy.float64) * speed)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _array(self, host: object, kind: object) -> object:
    """Returns 'host' (float64 rows) as float32 on the device."""
    return self._wp.array(host.astype(numpy.float32), kind, None, None,
                          None, None, self.device)
