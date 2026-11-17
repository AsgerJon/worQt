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
  'isp' (s) and how far it is opened ('throttle', nought to one); the
  most it may push ('most', N: its limiter, user, 2026-11-17: "another
  engine control that restricts the engine output to a particular g";
  'limited'); what it pushes ('push', N: the throttle's share of its
  thrust, no more than 'most') and the fuel it burns doing so ('flow',
  kg/s); whether it is 'lit' (user, 2026-11-17: "only after the launch
  button will the rocket actually move": on the pad it stays dark,
  however far it is opened, until the LAUNCH key lights it).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  thrust: float
  isp: float
  throttle: float
  most: float
  lit: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, thrust: float, isp: float) -> None:
    if thrust <= 0.0 or isp <= 0.0:
      raise ValueError('no engine pushes %r N at %r s' % (thrust, isp))
    self.thrust, self.isp, self.throttle = float(thrust), float(isp), 0.0
    self.most, self.lit = self.thrust, True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def push(self, ) -> float:
    """The 'push' property is the thrust at the throttle, no more than
    the limiter lets it ('most'), N; nought unlit."""
    if not self.lit:
      return 0.0
    return min(self.most, self.thrust * self.throttle)

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

  def limited(self, most: float) -> None:
    """The 'limited' method lets the engine push no more than 'most' N
    (its thrust at most)."""
    if most <= 0.0:
      raise ValueError('an engine limited to %r N pushes nothing' % most)
    self.most = min(self.thrust, float(most))
