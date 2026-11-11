"""
BarLayer is a layer of reinforcing bars along a beam.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple


class BarLayer(NamedTuple):
  """
  BarLayer is a layer of reinforcing bars running the length of a beam,
  in mm: 'count' bars of 'diameter', 'cover' of concrete between them
  and the face they are along. 'area' is the bars' area together, in
  mm², and 'depth' how far their centres are from that face.
  """

  count: int
  diameter: float
  cover: float

  @property
  def area(self) -> float:
    """The area of the bars together, in mm²."""
    return self.count * math.pi * self.diameter ** 2 / 4

  @property
  def depth(self) -> float:
    """How far the bars' centres are from the face they are along."""
    return self.cover + self.diameter / 2

  def __str__(self) -> str:
    """The layer as an engineer writes it: '3 Ø16, cover 30'."""
    if not self.count:
      return 'none'
    return '%d Ø%g, cover %g' % (self.count, self.diameter, self.cover)
