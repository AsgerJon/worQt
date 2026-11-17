"""
Night and morning where the rocket is (user, 2026-11-17: "Asger should be
able to key_E into bed to advance the time to morning if it is dark,
otherwise it should say like in Minecraft, 'you can only sleep at
night'"): dark is its anchor's shadow, as the scenery lights it
('shineOf': on the ground, the sun set; in orbit, behind the body); the
morning is when it comes out of it again, 'MORNING' s on. On the ground
the rocket rests on the turning ground (carried round with it), off it
it coasts its path. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._turns import aboutAxis, dot, norm, rotated, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  The shadow's edge: the sunlight fades over this much across it, m.
PENUMBRA = 2e4
#  Darker than this share of the sunlight is night.
DARK = 0.5
#  The morning looked for: at most this far ahead, in steps of this, s;
#  the sunrise found to within 'SUNRISE_TO' s; he wakes 'MORNING' s
#  after it (the sun up, not just rising).
LOOK_MOST = 2.0 * 86400.0
LOOK_STEP = 120.0
SUNRISE_TO = 1.0
MORNING = 600.0


def shineOf(radius: float, place: tuple, sun: tuple) -> float:
  """Returns how much of the sun's light reaches 'place' (m, from a
  body's middle, 'radius' round; the light going 'sun', a unit vector):
  nought in the body's shadow, fading over 'PENUMBRA' at its edge."""
  behind = dot(place, sun)
  if behind <= 0.0:
    return 1.0
  across = norm(tuple(p - behind * s for p, s in zip(place, sun)))
  return min(1.0, max(0.0, 0.5 + (across - radius) / PENUMBRA))


def isDark(system: SolarSystem, vessel: Vessel, t: float) -> bool:
  """Returns whether it is night where 'vessel' is at time 't' (s since
  the system's last leap)."""
  return _shineAfter(system, vessel, t, _placesOf(system, vessel),
                     0.0) < DARK


def morningIn(system: SolarSystem, vessel: Vessel,
              t: float) -> float | None:
  """Returns how long from time 't' (s since the system's last leap)
  till morning where 'vessel' is, s: 'MORNING' after it comes out of its
  anchor's shadow; None if it is not night now, or no morning comes
  within 'LOOK_MOST'."""
  places = _placesOf(system, vessel)
  if _shineAfter(system, vessel, t, places, 0.0) >= DARK:
    return None
  low, high = 0.0, None
  while low < LOOK_MOST:
    if _shineAfter(system, vessel, t, places, low + LOOK_STEP) >= DARK:
      high = low + LOOK_STEP
      break
    low += LOOK_STEP
  if high is None:
    return None
  while high - low > SUNRISE_TO:
    middle = 0.5 * (low + high)
    if _shineAfter(system, vessel, t, places, middle) >= DARK:
      high = middle
    else:
      low = middle
  return high + MORNING


def nightIn(system: SolarSystem, vessel: Vessel, t: float) -> float:
  """Returns how long from time 't' till it is dark where 'vessel' is,
  s (nought if it is now): its going into its anchor's shadow, found to
  within 'SUNRISE_TO' s."""
  places = _placesOf(system, vessel)
  if _shineAfter(system, vessel, t, places, 0.0) < DARK:
    return 0.0
  low, high = 0.0, None
  while low < LOOK_MOST:
    if _shineAfter(system, vessel, t, places, low + LOOK_STEP) < DARK:
      high = low + LOOK_STEP
      break
    low += LOOK_STEP
  if high is None:
    raise ValueError('no night within %.0f s' % LOOK_MOST)
  while high - low > SUNRISE_TO:
    middle = 0.5 * (low + high)
    if _shineAfter(system, vessel, t, places, middle) < DARK:
      high = middle
    else:
      low = middle
  return high


def _placesOf(system: SolarSystem, vessel: Vessel) -> object:
  """Returns where 'vessel' is a while on (a function of the seconds on,
  from its anchor's middle): carried round on the turning ground when
  it touches it, else along its path (still if it has none)."""
  if vessel.touching:
    body = system.bodies[vessel.anchor]
    place = vessel.place
    return lambda seconds: rotated(aboutAxis(body.pole, body.spin
                                             * seconds), place)
  conic = vessel.conicOf(system)
  if conic is None:
    return lambda seconds: vessel.place
  return lambda seconds: conic.stateAt(seconds)[0]


def _shineAfter(system: SolarSystem, vessel: Vessel, t: float,
                places: object, seconds: float) -> float:
  """Returns how much sunlight reaches 'vessel' 'seconds' s after time
  't', where 'places' has it then."""
  anchor = vessel.anchor
  place = places(seconds)
  sol = system.relative(0, anchor, t + seconds)[0]
  if norm(sol) <= 0.0:
    return 1.0
  sun = unit(tuple(p - s for p, s in zip(place, sol)))
  return shineOf(system.bodies[anchor].radius, place, sun)
