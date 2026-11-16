"""
Pushbutton is a FourthPeep pressed in (user, 2026-11-16: "*Every*
fourtpeep input, remember htose?, must visibly deform when activated"):
a key that sinks into its face when used and springs back, or, held (a
cassette deck's play key), stays in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._fourthpeep import FourthPeep

#  How long a key takes to go all the way in or out, s.
PRESS = 0.06


class Pushbutton(FourthPeep):
  """
  Pushbutton is a key working 'name' on body 'body' at 'pivot' (its
  face's middle, the body's own frame, m), pressed along 'axis' (into
  its face) 'depth' m at most ('length'). Used, it goes in over 'PRESS'
  s and springs back out the same; 'latched' (as 'held' sets it) it
  stays in till let go. 'value' is how far in it is (nought to one),
  'sunk' in metres.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  latched: bool

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, name: str, body: object, pivot: tuple, axis: tuple,
               depth: float, prompts: tuple = None) -> None:
    said = ('Press %s' % name,) * 2 if prompts is None else prompts
    FourthPeep.__init__(self, name, body, pivot, axis, depth, 0.0, 0.0,
                        said)
    self.latched = False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def used(self, ) -> None:
    """The 'used' method presses the key in (it springs back out once
    in, unless latched)."""
    self.target = 1.0

  def held(self, down: bool) -> None:
    """The 'held' method latches the key in ('down') or lets it out."""
    self.latched = bool(down)
    self.target = 1.0 if down else 0.0

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method moves the key 'seconds' on, all the way in or
    out over 'PRESS' s; all the way in and not latched, it springs
    back."""
    step = seconds / PRESS
    if self.value < self.target:
      self.value = min(self.target, self.value + step)
    elif self.value > self.target:
      self.value = max(self.target, self.value - step)
    if self.value >= 1.0 and not self.latched:
      self.target = 0.0

  def sunk(self, ) -> float:
    """The 'sunk' method returns how far in the key is now, m."""
    return self.length * self.value

  def prompt(self, ) -> str:
    """The 'prompt' method returns what pressing the key does."""
    return self.prompts[0]
