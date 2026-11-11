"""
The 'si' function writes a value with the SI prefix that suits it, as
'4.7 kΩ' or '37.5 mA'; 'microfarads' writes a capacitance as
capacitors are marked, in µF.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  The prefixes, each with its power of ten, the greatest first
_PREFIXES = (
  (1e9, 'G'), (1e6, 'M'), (1e3, 'k'), (1.0, ''), (1e-3, 'm'), (1e-6, 'µ'),
  (1e-9, 'n'), (1e-12, 'p'),
)


def si(value: float, unit: str) -> str:
  """The 'si' function returns 'value' in 'unit' to three digits, with
  the prefix that keeps it between 1 and 1000: '4.7 kΩ', '37.5 mA',
  '0 V'."""
  size = abs(value)
  if not math.isfinite(size):
    return '%s %s' % (value, unit)
  if size < 1e-12:
    return '0 %s' % unit
  for scale, prefix in _PREFIXES:
    if size >= scale * 0.9995:
      break
  return '%s %s%s' % ('%.3g' % (value / scale + 0.0), prefix, unit)


def microfarads(capacitance: float) -> str:
  """The 'microfarads' function returns a capacitance in F written in
  µF, as capacitors are marked: '1000 µF', '4.7 µF', '0.1 µF'."""
  return '%g µF' % float('%.4g' % (capacitance * 1e6))
