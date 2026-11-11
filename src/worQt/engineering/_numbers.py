"""
The private '_numbers' module reads and writes the numbers in the
texts of the engineering model, and checks the values a model holds.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math


def formatNumber(value: float) -> str:
  """
  The 'formatNumber' function writes 'value' as briefly as it reads
  back: '6' rather than '6.0', and never '-0'.
  """
  return '%.12g' % (float(value) + 0.0)


def snapTo(value: float, step: float) -> float:
  """
  The 'snapTo' function returns the multiple of 'step' nearest 'value',
  free of the float noise a product leaves: 2.85, never
  2.8500000000000001.
  """
  return round(round(value / step) * step, 9) + 0.0


def parseNumber(word: str, name: str) -> float:
  """
  The 'parseNumber' function reads the number 'name' from 'word', and
  refuses what is no finite number.
  """
  try:
    value = float(word)
  except ValueError as exception:
    infoSpec = """the %s must be a number, not '%s'"""
    raise ValueError(infoSpec % (name, word)) from exception
  if math.isfinite(value):
    return value
  infoSpec = """the %s must be a finite number, not '%s'"""
  raise ValueError(infoSpec % (name, word))


def checkPositive(name: str, value: float) -> float:
  """
  The 'checkPositive' function returns 'value' if it is a finite number
  above zero, and refuses it otherwise.
  """
  if math.isfinite(value) and value > 0:
    return float(value)
  infoSpec = """the %s must be above zero, not %s"""
  raise ValueError(infoSpec % (name, formatNumber(value)))


def checkStretch(start: float, end: float) -> None:
  """
  The 'checkStretch' function refuses a stretch of an edge that starts
  before the edge does, or does not end after it starts: whatever acts
  on an edge acts over a width, never at a point.
  """
  if not (math.isfinite(start) and math.isfinite(end)):
    raise ValueError("""a stretch is between finite positions""")
  if start < 0:
    infoSpec = """a stretch starts at 0 or later, not at %s"""
    raise ValueError(infoSpec % formatNumber(start))
  if end <= start:
    infoSpec = """a stretch ends after it starts: %s to %s"""
    raise ValueError(infoSpec % (formatNumber(start), formatNumber(end)))
