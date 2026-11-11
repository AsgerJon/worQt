"""
The 'niceAbove' function rounds a number up to one an axis is ticked at;
'niceSpan' finds an axis's ends and step either side of nought.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

_NICE = (1.0, 2.0, 2.5, 5.0, 10.0)


def niceAbove(value: float) -> float:
  """The 'niceAbove' function returns the least of 1, 2, 2.5 and 5 times
  a power of ten not below 'value'."""
  if value <= 0.0:
    return 1.0
  power = 10.0 ** math.floor(math.log10(value))
  for step in _NICE:
    if step * power >= value * (1 - 1e-12):
      return step * power
  return 10.0 * power


def niceSpan(low: float, high: float,
             least: float) -> tuple[float, float, float]:
  """The 'niceSpan' function returns the ends and the step of an axis
  reaching past 'low' and 'high', nought always on it, to round numbers
  a step apart, about six steps long, and at least 'least' long, the
  more to the side the numbers are on."""
  low, high = min(low, 0.0), max(high, 0.0)
  if high - low < least:
    if -low > high:
      low = high - least
    else:
      high = low + least
  step = niceAbove((high - low) / 6)
  return (math.floor(low / step - 1e-9) * step,
          math.ceil(high / step - 1e-9) * step, step)
