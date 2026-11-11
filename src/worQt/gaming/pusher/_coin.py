"""
Coin is the shape and weight of a coin: the Danish 20-krone coin unless
told otherwise.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple


class Coin(NamedTuple):
  """
  Coin is a coin as a sharp edged disc, in mm and g: its 'radius', half
  its thickness, 'half', and its 'mass'. By default the Danish 20-krone
  coin: 27.0 mm across, 2.35 mm thick, 9.3 g.
  """

  radius: float = 13.5
  half: float = 1.175
  mass: float = 9.3

  def inertia(self, ) -> tuple[float, float]:
    """The 'inertia' method returns the coin's moments of inertia, in g
    mm², about a diameter and about its axis."""
    r, h, m = self.radius, self.half, self.mass
    return m * (3.0 * r * r + 4.0 * h * h) / 12.0, m * r * r / 2.0
