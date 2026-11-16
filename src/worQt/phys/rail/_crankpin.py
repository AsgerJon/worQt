"""
CrankPin is a pin on a wheel off its axle, held in the eye of a rod
(user, 2026-11-16: a steam locomotive, its connecting and coupling rods
on its driving wheels' crank pins): to the rail world the same as an
axlebox ('Axlebox': a point of a wheelset held in a point of another
body by springs and dampers, traded with the world the body is in),
the point off the axle and the eye free to turn on it (no bearing's
torque, no brake, no motor).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._axlebox import Axlebox

#  A bearing that holds nothing back (Palmgren's f0, f1 nought).
FREE_PIN = (0.0, 0.0, 0.0, 1.0)


class CrankPin(Axlebox):
  """
  CrankPin is the pin at 'pin' on wheelset 'wheelset' (its index; a
  point in its own frame, off its axle, its own z) held in the eye at
  'eye' of body 'rod' (its index; a point in the rod's own frame) by
  'stiffness' (N/m) and 'damping' (N s/m) each way of the rod's own axes
  (along it, across it: along the pin, where the eye slides between
  its collars, up), free to turn in it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, wheelset: int, pin: tuple, rod: int, eye: tuple,
               stiffness: tuple, damping: tuple) -> None:
    side = 1.0 if pin[2] >= 0.0 else -1.0
    Axlebox.__init__(self, wheelset, side, rod, eye, stiffness, damping,
                     FREE_PIN)
    self.journal = tuple(float(x) for x in pin)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def renumbered(self, wheelset: int, frame: int) -> CrankPin:
    """The 'renumbered' method returns the pin with its bodies' indices
    'wheelset' and 'rod' ('frame') instead."""
    return CrankPin(wheelset, self.journal, frame, self.box,
                    self.stiffness, self.damping)
