"""
Slider is a FourthPeep slid along its track (user, 2026-11-16: "*Every*
fourtpeep input ... must visibly deform when activated"; the throttle as
a 1970s slide control): its knob moves from the near end to the far.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._fourthpeep import FourthPeep

#  How long the hand takes to slide the knob from end to end, s.
SLIDE = 0.15


class Slider(FourthPeep):
  """
  Slider is a slide control working 'name' on body 'body', its track
  from 'pivot' (its near end) 'length' m along 'axis'. 'slid' sends its
  knob to a share of the way (nought to one), the hand moving it there,
  end to end over 'SLIDE' s; 'value' is where it is now, 'along' in
  metres from the near end. 'used' sends it to the other end.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, name: str, body: object, pivot: tuple, axis: tuple,
               length: float, prompts: tuple = None) -> None:
    said = ('Slide %s' % name,) * 2 if prompts is None else prompts
    FourthPeep.__init__(self, name, body, pivot, axis, length, 0.0, 0.0,
                        said)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def slid(self, share: float) -> None:
    """The 'slid' method sends the knob to 'share' of the way along its
    track (kept within nought and one)."""
    self.target = min(1.0, max(0.0, float(share)))

  def used(self, ) -> None:
    """The 'used' method sends the knob to the other end."""
    self.slid(0.0 if self.target > 0.5 else 1.0)

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method moves the knob 'seconds' on toward where it was
    sent, end to end over 'SLIDE' s."""
    step = seconds / SLIDE
    if self.value < self.target:
      self.value = min(self.target, self.value + step)
    elif self.value > self.target:
      self.value = max(self.target, self.value - step)

  def along(self, ) -> float:
    """The 'along' method returns how far along its track the knob is
    now, m."""
    return self.length * self.value

  def prompt(self, ) -> str:
    """The 'prompt' method returns what sliding the knob does."""
    return self.prompts[0]
