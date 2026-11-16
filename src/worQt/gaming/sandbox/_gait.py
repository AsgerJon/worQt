"""
Gait is how the avatar's eyes sway as it walks (user, 2026-11-16: "add
view bobbing"): drawn only, never where it aims.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  How far a stride (two steps) carries the avatar, m; how far the eyes
#  rise and fall each step and sway each stride at full swing, m; the
#  speed at which the swing is full, m/s; how fast the swing follows
#  walking, standing still or leaving the ground, a second.
STRIDE = 3.0
RISE, SWAY = 0.035, 0.02
#  How far the hands sway and dip against the eyes, at full swing, m
#  (user, 2026-11-16: "view bobbing should affect the gun too").
CARRY_SWAY, CARRY_DIP = 0.012, 0.018
FULL = 6.0
EASE = 8.0


class Gait:
  """
  Gait keeps the avatar's stride: 'phase' (rad, a turn a stride, moving
  on with the ground covered) and 'swing' (nought to one: how much of
  the sway shows, following the speed along the ground while standing,
  easing out standing still or in the air). 'offset' is where it puts
  the eyes: so far right and so far up, m; 'carried' where it puts the
  hands against the eyes (dipping as the eyes rise).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  phase: float
  swing: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.phase, self.swing = 0.0, 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def stepped(self, speed: float, grounded: bool, seconds: float) -> None:
    """The 'stepped' method moves the stride on by 'seconds' of walking
    at 'speed' m/s along the ground ('grounded': standing on something;
    else the swing eases out)."""
    wanted = min(1.0, speed / FULL) if grounded else 0.0
    share = min(1.0, EASE * seconds)
    self.swing += (wanted - self.swing) * share
    self.phase = (self.phase + 2.0 * math.pi * speed * seconds
                  / STRIDE) % (2.0 * math.pi)

  def offset(self, ) -> tuple[float, float]:
    """The 'offset' method returns how far right and how far up the eyes
    are put now, m: a rise and fall each step, a sway each stride."""
    return (self.swing * SWAY * math.sin(self.phase),
            self.swing * RISE * math.sin(2.0 * self.phase))

  def carried(self, ) -> tuple[float, float]:
    """The 'carried' method returns how far right and how far up the
    hands are put against the eyes now, m: a sway each stride and a dip
    as the eyes rise."""
    return (self.swing * CARRY_SWAY * math.sin(self.phase),
            -self.swing * CARRY_DIP * math.sin(2.0 * self.phase))
