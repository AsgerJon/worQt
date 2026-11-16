"""
Universe is the gamerules of a world: the universal constants its
physics obeys (user, 2026-11-15: "a series of universal constants that
are changed to allow for shrinking of objects ... Or maybe we are going
to the moon with less g").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  Gravity on the earth and on the moon, m/s².
EARTH_GRAVITY = 9.81
MOON_GRAVITY = 1.62


class Universe:
  """
  Universe holds the constants a world's physics obeys: 'gravity', m/s²,
  pulling straight down (along the world's -z). A world obeys exactly
  one universe; two worlds may share one.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  gravity: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, gravity: float) -> None:
    if gravity < 0.0:
      raise ValueError('gravity pulls down: %r m/s² is not' % gravity)
    self.gravity = float(gravity)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def gravityVector(self, ) -> tuple[float, float, float]:
    """The 'gravityVector' method returns gravity as the physics takes
    it: m/s² along the world's axes, straight down."""
    return 0.0, 0.0, -self.gravity
