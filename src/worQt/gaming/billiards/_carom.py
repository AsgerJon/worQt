"""
Carom is how two balls meet, every value adjustable, to be balanced
against how real balls part.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple


class Carom(NamedTuple):
  """
  Carom is how two balls meet, the 'karambolage', in mm and s: a stiff,
  lively spring between them for 'contact' seconds, pushing them apart
  along the line between their middles, never pulling, giving back
  'liveliness' of the speed they met at; and friction at the point they
  touch, against its slip, so a ball hands the other a share of its
  spin, the more the slower they slip: 'slowFriction' when they hardly
  slip, falling towards 'fastFriction' as the slip passes 'slipScale'
  (after Alciatore's measurements). Each takes at most its share of the
  push, so only a part of the spin passes on. 'step' is how finely a
  meeting is followed. None of these is known well: they are to be
  balanced against how balls part on a real table.
  """

  liveliness: float = 0.94
  contact: float = 0.00025
  #  Fitted 2026-11-07 to the break as a Korean guide draws it (japong.com).
  slowFriction: float = 0.1302
  fastFriction: float = 0.01
  slipScale: float = 920.0
  step: float = 1e-6

  def _ratio(self, ) -> float:
    """Returns the damping ratio giving back 'liveliness'."""
    fall = math.log(self.liveliness)
    return -fall / math.sqrt(math.pi ** 2 + fall ** 2)

  def frequency(self, ) -> float:
    """The 'frequency' method returns how fast two meeting balls swing
    on the spring between them, undamped, in rad/s: so that a meeting
    lasts 'contact'."""
    ratio = self._ratio()
    return math.pi / (self.contact * math.sqrt(1.0 - ratio * ratio))

  def pushOf(self, given: float, giving: float) -> float:
    """The 'pushOf' method returns the push on each of two balls, a
    kilogram, pressed 'given' mm together and pressing on at 'giving'
    mm/s; never a pull."""
    if given <= 0.0:
      return 0.0
    swing = self.frequency()
    push = swing * swing * given + 2.0 * self._ratio() * swing * giving
    return max(0.5 * push, 0.0)

  def storedOf(self, given: float) -> float:
    """The 'storedOf' method returns the energy the spring between two
    balls pressed 'given' mm together holds, a kilogram of one ball, in
    mm²/s²."""
    if given <= 0.0:
      return 0.0
    swing = self.frequency()
    return 0.25 * swing * swing * given * given

  def frictionAt(self, slip: float) -> float:
    """The 'frictionAt' method returns the friction between two balls
    slipping at 'slip' mm/s at the point they touch."""
    fall = math.exp(-abs(slip) / self.slipScale)
    return self.fastFriction + (self.slowFriction - self.fastFriction) * fall
