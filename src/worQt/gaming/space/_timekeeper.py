"""
Timekeeper keeps a solar system's time (user, 2026-11-16: "bro just put
in a leap step every 256 steps, where we adjust"; "we can time
accelerate and we just put a factor on each step"): the time since the
last leap, the leaps, how fast time runs, and warping to a moment.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem

#  Every this many steps the time since the last leap is folded into the
#  sky and starts again at nought.
LEAP = 256
#  How fast time may run, times real time (the spec: "Warp factors run
#  from 1 to 100,000").
WARPS = (1, 5, 10, 50, 100, 1000, 10000, 100000)
#  Warping to a moment, the warp is the fastest that leaves at least
#  'AIM_FRAMES' frames of 'AIM_FRAME' s to go: it eases off and lands on
#  the moment itself.
AIM_FRAMES = 4.0
AIM_FRAME = 1.0 / 60.0


class Timekeeper:
  """
  Timekeeper keeps the time of a solar system ('system'): the time since
  its last leap ('now', s: what its bodies' functions of time are
  given), the steps taken ('steps'), the leaps ('leaps': each 'LEAP'
  steps 'now' is folded into the system and starts at nought), the game
  time gone since it began ('elapsed', s: for the clock on screen) and
  how fast time runs ('factor', one of 'WARPS'). Warping to a moment
  ('aim', 'aimed'): each frame's seconds are cut so as not to pass it,
  its warp eased off as it nears, nought then.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  system: SolarSystem
  now: float
  steps: int
  leaps: int
  elapsed: float
  factor: int
  aimed: float | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, system: SolarSystem) -> None:
    self.system, self.now, self.steps, self.leaps = system, 0.0, 0, 0
    self.elapsed, self.factor, self.aimed = 0.0, 1, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def faster(self, ) -> None:
    """The 'faster' method runs time at the next warp up (none past the
    last)."""
    self.aimed = None
    self.factor = WARPS[min(len(WARPS) - 1, WARPS.index(self.factor) + 1)]

  def slower(self, ) -> None:
    """The 'slower' method runs time at the next warp down."""
    self.aimed = None
    self.factor = WARPS[max(0, WARPS.index(self.factor) - 1)]

  def realtime(self, ) -> None:
    """The 'realtime' method runs time as it is, warping to nothing."""
    self.factor, self.aimed = 1, None

  def aim(self, seconds: float) -> None:
    """The 'aim' method warps to 'seconds' s from now ('secondsOf'
    eases off and stops on it)."""
    if seconds <= 0.0:
      self.realtime()
      return
    self.aimed = self.elapsed + float(seconds)
    self._aimedFactor()

  def leapt(self, seconds: float) -> None:
    """The 'leapt' method moves time on 'seconds' s at once (a night
    slept on the ground, where it may not be warped through), folded
    into the sky at once, the warp ended."""
    self.realtime()
    self.now += float(seconds)
    self.elapsed += float(seconds)
    self.system.fold(self.now)
    self.now, self.leaps = 0.0, self.leaps + 1

  def secondsOf(self, real: float) -> float:
    """The 'secondsOf' method returns the game seconds a step of 'real'
    s covers: 'real' times the warp, cut not to pass the moment warped
    to."""
    seconds = real * self.factor
    if self.aimed is not None:
      seconds = min(seconds, max(0.0, self.aimed - self.elapsed))
    return seconds

  def ticked(self, seconds: float) -> bool:
    """The 'ticked' method moves time on 'seconds' s (a step); each
    'LEAP' steps it folds the time since the last leap into the system,
    'now' starting at nought again. It eases the warp toward the moment
    warped to, and ends it there. Returns whether it leapt."""
    self.now += seconds
    self.elapsed += seconds
    self.steps += 1
    if self.aimed is not None:
      self._aimedFactor()
    if self.steps % LEAP:
      return False
    self.system.fold(self.now)
    self.now, self.leaps = 0.0, self.leaps + 1
    return True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _aimedFactor(self, ) -> None:
    """Sets the warp for the moment warped to: the fastest leaving
    'AIM_FRAMES' frames to go; there, real time and no aim."""
    left = self.aimed - self.elapsed
    if left <= 1e-9:
      self.realtime()
      return
    fitting = [w for w in WARPS if w * AIM_FRAME * AIM_FRAMES <= left]
    self.factor = fitting[-1] if fitting else 1
