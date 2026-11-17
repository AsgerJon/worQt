"""
The closest approach: when, on its path as it is, the rocket next comes
nearest the space station, how near, how fast they pass; a try-hard's
aid for the rendezvous by hand (user, 2026-11-17: "we include buttons
so that a try-hard *could* manually do the thing"): the map marks it,
the readout says it. Within the rocket's next turn round (at most
'SPAN_MOST' s), sampled 'SAMPLES' times, the nearest refined by golden
sections. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._station import Station
  from ._vessel import Vessel

#  How far ahead it looks (the rocket's turn round, at most this), s;
#  how many times along it, and how many golden sections refine it.
SPAN_MOST = 6.0 * 3600.0
SAMPLES = 128
SECTIONS = 40
GOLDEN = 0.5 * (math.sqrt(5.0) - 1.0)


def closestApproach(vessel: Vessel, system: SolarSystem, station: Station,
                    t: float) -> tuple | None:
  """Returns the rocket's next closest approach to the station from the
  system's time 't': how long till it (s), how near (m), how fast they
  pass then (m/s), where the rocket and the station are then (m, from
  the station's planet); None when the rocket goes round another body,
  is docked, or has no path."""
  if vessel.docked or vessel.anchor != station.parent:
    return None
  conic = vessel.conicOf(system)
  if conic is None:
    return None
  span = min(SPAN_MOST, conic.period) if conic.closed else SPAN_MOST

  def apart(wait: float) -> float:
    return math.dist(conic.stateAt(wait)[0], station.stateAt(t + wait)[0])

  step = span / SAMPLES
  gaps = [apart(k * step) for k in range(SAMPLES + 1)]
  k = min(range(SAMPLES + 1), key=gaps.__getitem__)
  low, high = max(0.0, (k - 1) * step), min(span, (k + 1) * step)
  for _ in range(SECTIONS):
    one = high - GOLDEN * (high - low)
    two = low + GOLDEN * (high - low)
    if apart(one) < apart(two):
      high = two
    else:
      low = one
  wait = 0.5 * (low + high)
  place, velocity = conic.stateAt(wait)
  there, moving = station.stateAt(t + wait)
  return (wait, math.dist(place, there), math.dist(velocity, moving),
          place, there)
