"""
Knob is a FourthPeep turned through its notches (user, 2026-11-16:
"*Every* fourtpeep input ... must visibly deform when activated"): a
rotary switch clicking from one notch to the next, or, with no ends, a
knob turned on and on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._fourthpeep import FourthPeep

#  How long the hand takes to turn a knob a notch, s.
CLICK = 0.08


class Knob(FourthPeep):
  """
  Knob is a knob working 'name' on body 'body' at 'pivot', turned about
  'axis' (out of its face), its 'length' its radius: at notch 'notch'
  it stands 'near' + 'notch' 'step' rad round; 'notches' it has (None:
  no ends, turned on and on). 'turned' clicks it on (or back) notches,
  'set' puts it at a notch (what it works changed another way: it turns
  to show it); 'used' clicks it one on, from the last back to the
  first. 'value' is the notch it stands at now, turning (not nought to
  one: a notch a unit).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  notch: int
  notches: int | None
  step: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, name: str, body: object, pivot: tuple, axis: tuple,
               radius: float, near: float, step: float,
               notches: int | None, prompts: tuple = None) -> None:
    said = ('Turn %s' % name,) * 2 if prompts is None else prompts
    far = near + step * ((notches or 2) - 1)
    FourthPeep.__init__(self, name, body, pivot, axis, radius, near, far,
                        said)
    self.notch, self.notches, self.step = 0, notches, float(step)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def turned(self, notches: int) -> int:
    """The 'turned' method clicks the knob on 'notches' notches (back when
    below nought), stopping at its ends; returns how many it clicked."""
    was = self.notch
    self.set(self.notch + int(notches))
    return abs(self.notch - was)

  def set(self, notch: int) -> None:
    """The 'set' method puts the knob at notch 'notch' (within its ends),
    the hand turning it there."""
    if self.notches is not None:
      notch = max(0, min(self.notches - 1, int(notch)))
    self.notch = int(notch)
    self.target = float(self.notch)

  def used(self, ) -> None:
    """The 'used' method clicks the knob one notch on, from its last
    back to its first."""
    if self.notches is not None and self.notch >= self.notches - 1:
      self.set(0)
    else:
      self.set(self.notch + 1)

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method turns the knob 'seconds' on toward its notch, a
    notch each 'CLICK' s."""
    step = seconds / CLICK
    if self.value < self.target:
      self.value = min(self.target, self.value + step)
    elif self.value > self.target:
      self.value = max(self.target, self.value - step)

  def angle(self, ) -> float:
    """The 'angle' method returns how far the knob is turned now, rad."""
    return self.near + self.step * self.value

  def prompt(self, ) -> str:
    """The 'prompt' method returns what turning the knob does."""
    return self.prompts[0]
