"""
FourthPeep is a control in the world through which the world takes
input from the player (user, 2026-11-15: "diegetic in-world controls
(lever, button) for any test input"; 2026-11-16: "4peep, send it!"):
the first a lever, its handle turned on its base between two ends, its
'value' how far toward its far end it stands, read by what it works (the
cart's brake). Drawn only: nothing in the world meets the handle.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys._vectors import UNTURNED, product, rotated, turnAbout

#  How long the hand takes to throw a lever from one end to the other, s.
THROW = 0.25


class FourthPeep:
  """
  FourthPeep is a lever working 'name' (what it works: 'brake') on body
  'body' (its index in the world; None: the world itself) at 'pivot' (in
  that body's own frame, m), its handle 'length' m long, turned about
  'axis' (in the body's own frame) by 'near' rad at its near end and
  'far' at its far end (nought: straight up the body's own z). 'value'
  is how far toward its far end it stands (nought to one), 'target' the
  end the hand last threw it to; 'used' throws it to the other end, the
  hand moving it there over 'THROW' s as the world steps ('acted').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  name: str
  body: object
  pivot: tuple
  axis: tuple
  length: float
  near: float
  far: float
  value: float
  target: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, name: str, body: object, pivot: tuple, axis: tuple,
               length: float, near: float, far: float) -> None:
    self.name, self.body, self.length = name, body, float(length)
    self.pivot = tuple(float(x) for x in pivot)
    size = math.sqrt(sum(x * x for x in axis))
    if size <= 0.0:
      raise ValueError('a lever turns about an axis, not %r' % (axis,))
    self.axis = tuple(float(x) / size for x in axis)
    self.near, self.far = float(near), float(far)
    self.value, self.target = 0.0, 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def used(self, ) -> None:
    """The 'used' method throws the lever to its other end (the hand
    moving it there as the world steps)."""
    self.target = 1.0 - self.target

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method moves the lever 'seconds' on toward the end it
    was thrown to, all the way over 'THROW' s."""
    step = seconds / THROW
    if self.value < self.target:
      self.value = min(self.target, self.value + step)
    elif self.value > self.target:
      self.value = max(self.target, self.value - step)

  def angle(self, ) -> float:
    """The 'angle' method returns how far the handle is turned about the
    axis now, rad."""
    return self.near + (self.far - self.near) * self.value

  def handleOf(self, assembly: object, states: tuple) -> tuple:
    """The 'handleOf' method returns the handle as its body in 'states'
    (of 'assembly') has it: where its pivot is in the world, its turn in
    the world (the handle along its own z) and where its knob is (its
    end)."""
    turn = turnAbout(self.axis, self.angle())
    if self.body is None:
      base, carried = self.pivot, UNTURNED
    else:
      body, state = assembly.bodies[self.body], states[self.body]
      base, carried = body.placeOf(state, self.pivot), state.turn
    turn = product(carried, turn)
    reach = rotated(turn, (0.0, 0.0, self.length))
    return base, turn, tuple(b + r for b, r in zip(base, reach))

  def prompt(self, ) -> str:
    """The 'prompt' method returns what using the lever does: 'Pull
    brake' or 'Release brake'."""
    return '%s %s' % ('Pull' if self.target < 0.5 else 'Release',
                      self.name)
