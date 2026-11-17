"""
The transfer kernels solve Lambert's problem on a device of Warp's, the
sums of the automatic rendezvous (user, 2026-11-17: "we include buttons
so that a try-hard *could* manually do the thing ... But where we also
provide an automated system for the rest of"): one thread a transfer,
from a place to a place in a time round one puller, the way it turns
about a given normal, less than a turn; in universal variables, z found
by halving (sure where Newton may wander). Float32 in the caller's own
units, chosen so the numbers stay near one: lengths in some unit, times
in the unit that makes G M one.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import warp as wp

from ._flight_kernels import stumpff

#  z's bounds: below 'Z_LOW' the transfer is a hyperbola faster than any
#  asked; at (2 pi)² its time runs out of bounds (less than a turn).
Z_LOW = -100.0
Z_HIGH = 4.0 * math.pi * math.pi - 1e-3
#  How many times z's bounds are halved.
HALVINGS = 64
#  Places nearer than this to the same way (or its opposite, the plane
#  of the transfer unknown) have no transfer (cosine's distance from one).
SAME_WAY = 1e-7


@wp.kernel
def transfersSolved(starts: wp.array(dtype=wp.vec3),
                    ends: wp.array(dtype=wp.vec3),
                    times: wp.array(dtype=wp.float32),
                    normal: wp.vec3,
                    leaving: wp.array(dtype=wp.vec3),
                    arriving: wp.array(dtype=wp.vec3)) -> None:
  """Solves transfer 'i': from 'starts[i]' to 'ends[i]' in 'times[i]'
  (G M one), going round 'normal' the way it turns; its velocity leaving
  and arriving, NaN where there is none."""
  i = wp.tid()
  r1 = starts[i]
  r2 = ends[i]
  dt = times[i]
  n1 = wp.length(r1)
  n2 = wp.length(r2)
  c = wp.clamp(wp.dot(r1, r2) / (n1 * n2), -1.0, 1.0)
  nan = wp.vec3(wp.nan, wp.nan, wp.nan)
  if 1.0 - c < SAME_WAY or 1.0 + c < SAME_WAY or dt <= 0.0:
    leaving[i] = nan
    arriving[i] = nan
    return
  angle = wp.acos(c)
  if wp.dot(wp.cross(r1, r2), normal) < 0.0:
    angle = 2.0 * wp.pi - angle
  a = wp.sin(angle) * wp.sqrt(n1 * n2 / (1.0 - c))
  low = float(Z_LOW)
  high = float(Z_HIGH)
  for _ in range(HALVINGS):
    z = 0.5 * (low + high)
    cs = stumpff(z)
    y = n1 + n2 + a * (z * cs[1] - 1.0) / wp.sqrt(cs[0])
    if y <= 0.0:
      low = z
    else:
      t = wp.pow(y / cs[0], 1.5) * cs[1] + a * wp.sqrt(y)
      if t < dt:
        low = z
      else:
        high = z
  z = 0.5 * (low + high)
  cs = stumpff(z)
  y = n1 + n2 + a * (z * cs[1] - 1.0) / wp.sqrt(cs[0])
  g = a * wp.sqrt(wp.max(y, 0.0))
  if y <= 0.0 or wp.abs(g) < 1e-12:
    leaving[i] = nan
    arriving[i] = nan
    return
  f = 1.0 - y / n1
  gdot = 1.0 - y / n2
  leaving[i] = (r2 - f * r1) / g
  arriving[i] = (gdot * r2 - r1) / g
