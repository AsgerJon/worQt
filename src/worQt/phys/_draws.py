"""
The grease's random draws, made the same in plain Python and in the
compiled stepping: a counting hash (splitmix64), not a running
generator, so each draw is its seed's, its step's, its half's and its
body's alone, and Box and Muller's normals from it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

_MASK = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15
_FIRST = 0xBF58476D1CE4E5B9
_SECOND = 0x94D049BB133111EB
_UNIT = 1.0 / 9007199254740992.0  # 2^-53
TWO_PI = 2.0 * math.pi


def mixed(value: int) -> int:
  """The 'mixed' function returns 'value' hashed (splitmix64), 64 bit."""
  value = (value + _GOLDEN) & _MASK
  value = ((value ^ (value >> 30)) * _FIRST) & _MASK
  value = ((value ^ (value >> 27)) * _SECOND) & _MASK
  return value ^ (value >> 31)


def normalDraws(seed: int, step: int, half: int,
                body: int) -> tuple[float, ...]:
  """The 'normalDraws' function returns six standard normal draws for
  'seed', the step 'step', its 'half' and the body 'body'."""
  key = mixed(seed & _MASK)
  key = mixed(key ^ (step & _MASK))
  key = mixed(key ^ (half & _MASK))
  key = mixed(key ^ (body & _MASK))
  out = []
  for pair in range(3):
    first = mixed(key ^ (2 * pair + 1))
    second = mixed(key ^ (2 * pair + 2))
    near = (float(first >> 11) + 0.5) * _UNIT
    round_ = float(second >> 11) * _UNIT
    size = math.sqrt(-2.0 * math.log(near))
    out.append(size * math.cos(TWO_PI * round_))
    out.append(size * math.sin(TWO_PI * round_))
  return tuple(out)
