"""
Aerospike is a rocket engine whose exhaust shapes itself against the
air, so it works as well on the pad as in vacuum (user, 2026-11-16:
"aerospike ... engines whose effectiveness is independent of ambient
pressure"): one thrust and one specific impulse everywhere.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  Standard gravity, the specific impulse's own, m/s².
G0 = 9.80665
#  The magic fuel's specific impulse, s: doubled kerosene's 300 (the
#  spec: "I'd start at double").
MAGIC_ISP = 600.0


class Aerospike:
  """
  Aerospike holds an engine: its full 'thrust' (N), its specific impulse
  'isp' (s) and how far it is opened ('throttle', nought to one); what
  it pushes ('push', N) and the fuel it burns doing so ('flow', kg/s).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  thrust: float
  isp: float
  throttle: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, thrust: float, isp: float) -> None:
    if thrust <= 0.0 or isp <= 0.0:
      raise ValueError('no engine pushes %r N at %r s' % (thrust, isp))
    self.thrust, self.isp, self.throttle = float(thrust), float(isp), 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def push(self, ) -> float:
    """The 'push' property is the thrust at the throttle, N."""
    return self.thrust * self.throttle

  @property
  def flow(self, ) -> float:
    """The 'flow' property is the fuel burnt at the throttle, kg/s."""
    return self.push / (self.isp * G0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def throttled(self, throttle: float) -> None:
    """The 'throttled' method opens the engine to 'throttle', kept
    within nought and one."""
    self.throttle = min(1.0, max(0.0, float(throttle)))
