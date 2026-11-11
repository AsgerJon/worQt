"""
Cushion is how a table's cushions push back: Mathavan et al.'s (2010)
cushion where it holds, the user's past it, every value adjustable.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple


class Cushion(NamedTuple):
  """
  Cushion is how the cushions push back, in mm and s: Mathavan, Jackson
  and Parkin's (2010) cushion, the best the literature has, wherever it
  holds, and the user's own past it.

  As Mathavan et al. have it ('mathavanRebound'): the nose pushes along
  the line from it to the ball's middle as the ball meets it, so also
  down into the slate; friction at the nose, 'grip', their measured
  0.14, against the slip there whichever way it slips, and at the slate,
  the cloth's 'sliding', under the nose's push down and the ball's
  weight, each a Coulomb friction; it gives back 'liveliness', their
  0.98, of the speed into it. The push is a very under-damped spring and
  damper (the user), never pulling, giving 'deflection' at most to a
  ball coming 'firm' straight in, followed in steps of 'step', so hits
  at once are honest; 'stiffening' is how the push grows with how far
  the cushion gives, 1 a straight spring.

  Their cushion barely gives: they hold it good up to 'squaringFrom',
  2.5 m/s straight in. Past it the rubber gives (the user): a ball met
  hard and near square is pulled squarer, the more the harder and the
  nearer square, as the rubber it sinks into holds it from running on
  along the cushion. That pull, 'squaring' of the push for each m/s past
  'squaringFrom', comes in smoothly over 'squaringOnset' (nought at and
  below 'squaringFrom', so where Mathavan et al. hold they alone
  decide), and only for balls coming in nearer square than about
  'squaringBelow' degrees, fading in over 'squaringWidth' (a softplus,
  never pulling the other way). It acts at the ball's middle, as the
  rubber's give leans the push, and never turns a ball back along the
  cushion. Wiped wet cushions grip less (the user: their balls leave
  further from square); worn ones square less.
  """

  liveliness: float = 0.98
  deflection: float = 6.0
  firm: float = 2000.0
  grip: float = 0.14
  stiffening: float = 1.0
  step: float = 1e-5
  squaring: float = 0.01
  squaringFrom: float = 2500.0
  squaringOnset: float = 500.0
  squaringBelow: float = 20.0
  squaringWidth: float = 3.0

  def stiffness(self, ) -> float:
    """The 'stiffness' method returns the spring's push a kilogram of
    ball at a mm given, raised to 'stiffening': as stiff as stores a
    'firm' ball's energy at 'deflection'."""
    power = self.stiffening + 1.0
    return power * self.firm ** 2 / (2.0 * self.deflection ** power)

  def damping(self, ) -> float:
    """The 'damping' method returns the damper's push a kilogram of
    ball at a mm/s, in 1/s: as a straight spring as stiff at
    'deflection' needs to give back 'liveliness' of the speed."""
    fall = math.log(self.liveliness)
    ratio = -fall / math.sqrt(math.pi ** 2 + fall ** 2)
    return 2.0 * ratio * self.firm / self.deflection

  def pushOf(self, given: float, giving: float) -> float:
    """The 'pushOf' method returns the cushion's push a kilogram of
    ball, given 'given' mm and giving more at 'giving' mm/s; never a
    pull."""
    if given <= 0.0:
      return 0.0
    spring = self.stiffness() * given ** self.stiffening
    return max(spring + self.damping() * giving, 0.0)

  def squaringOf(self, comes: float, along: float) -> float:
    """The 'squaringOf' method returns the share of the cushion's push
    that pulls a ball square, coming in at 'comes' mm/s straight in and
    'along' mm/s along the cushion: nought where Mathavan et al. hold,
    up to 'squaringFrom', then growing as it comes harder, and as it
    comes nearer square than about 'squaringBelow' degrees."""
    over = comes - self.squaringFrom
    if over <= 0.0 or self.squaring <= 0.0:
      return 0.0
    hard = over * over / (over + self.squaringOnset)
    angle = math.atan2(abs(along), comes)
    width = math.radians(self.squaringWidth)
    below = math.radians(self.squaringBelow)
    near = softplus((below - angle) / width) / softplus(below / width)
    return self.squaring * 0.001 * hard * near


def softplus(x: float) -> float:
  """The 'softplus' function returns ln(1 + e^x): nought far below
  nought, 'x' far above, smooth between, never below nought."""
  if x > 0.0:
    return x + math.log(1.0 + math.exp(-x))
  return math.log(1.0 + math.exp(x))
