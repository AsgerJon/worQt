"""
Stirrups are the links round a beam's bars, holding it together against
shear.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple


class Stirrups(NamedTuple):
  """
  Stirrups are the closed links round a beam's bars, two legs each, of
  'diameter' mm, every 'spacing' mm along the beam, the first half a
  spacing in from its left end; but none in its 'gaps', the stretches
  (from, to), in mm from its left end, left without. A diameter of
  nought is no stirrups at all. 'area' is a stirrup's two legs
  together, in mm², and 'places' where they are along a beam of a
  length. 'withGap', 'withoutGap' and 'withGapAt' return them with a
  gap added, taken away or moved.
  """

  diameter: float
  spacing: float
  gaps: tuple[tuple[float, float], ...]

  @property
  def area(self) -> float:
    """A stirrup's two legs together, in mm²."""
    return 2 * math.pi * self.diameter ** 2 / 4

  def places(self, length: float) -> tuple[float, ...]:
    """Where the stirrups are along a beam 'length' mm long."""
    if not self.diameter:
      return ()
    places = []
    x = self.spacing / 2
    while x < length:
      if not any(start <= x <= end for start, end in self.gaps):
        places.append(x)
      x += self.spacing
    return (*places,)

  def withGap(self, start: float, end: float) -> Stirrups:
    """The stirrups with none from 'start' to 'end' too."""
    return Stirrups(self.diameter, self.spacing,
                    (*self.gaps, (float(start), float(end))))

  def withoutGap(self, index: int) -> Stirrups:
    """The stirrups with the gap of 'index' filled."""
    gaps = [*self.gaps]
    del gaps[index]
    return Stirrups(self.diameter, self.spacing, (*gaps,))

  def withGapAt(self, index: int, start: float, end: float) -> Stirrups:
    """The stirrups with the gap of 'index' from 'start' to 'end'."""
    gaps = [*self.gaps]
    gaps[index] = (float(start), float(end))
    return Stirrups(self.diameter, self.spacing, (*gaps,))

  def __str__(self) -> str:
    """The stirrups as an engineer writes them: 'Ø8 c/c 150'."""
    if not self.diameter:
      return 'none'
    words = 'Ø%g c/c %g' % (self.diameter, self.spacing)
    if self.gaps:
      words += ', %d gap%s' % (len(self.gaps),
                               '' if len(self.gaps) == 1 else 's')
    return words
