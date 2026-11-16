"""
Atmosphere is the air of a heavenly body: it drags, thins with height,
turns with its body, and heats nothing (user, 2026-11-16: "friction
can't cause heating").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  Terra's air, the US Standard Atmosphere 1976's densities, kg/m³, every
#  10 km from the ground to 100 km; above that none (the spec: "above
#  100 km we call it zero, so orbits don't slowly decay").
TERRA_STEP = 10e3
TERRA_DENSITIES = (1.225, 0.4135, 0.08891, 0.01841, 0.003996, 0.001027,
                   3.097e-4, 8.283e-5, 1.846e-5, 3.416e-6, 5.604e-7)


class Atmosphere:
  """
  Atmosphere holds a body's air: its density every 'step' m up from the
  ground ('densities', kg/m³, the last at its 'top'), in between the
  logarithm's straight line, below the ground as on it, from its 'top'
  up none.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  step: float
  densities: tuple
  logs: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, step: float, densities: tuple) -> None:
    if step <= 0.0 or len(densities) < 2 or min(densities) <= 0.0:
      raise ValueError('no air every %r m of %r' % (step, densities))
    self.step, self.densities = float(step), tuple(densities)
    self.logs = tuple(math.log(x) for x in densities)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def top(self, ) -> float:
    """The 'top' property is the height the air ends at, m."""
    return self.step * (len(self.densities) - 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def densityAt(self, height: float) -> float:
    """The 'densityAt' method returns the air's density 'height' m over
    the ground, kg/m³."""
    if height >= self.top:
      return 0.0
    if height <= 0.0:
      return self.densities[0]
    k = min(int(height / self.step), len(self.logs) - 2)
    share = height / self.step - k
    return math.exp(self.logs[k] + share * (self.logs[k + 1]
                                            - self.logs[k]))


TERRA_AIR = Atmosphere(TERRA_STEP, TERRA_DENSITIES)
