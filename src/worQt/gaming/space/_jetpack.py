"""
Jetpack is Asger's little jetpack for indoors (user, 2026-11-18: "let's
give Asger a little cute 'jetpack' for use indoors. It lets Asger move
with key_W in the direction faced key_S away and AD for strafing. Have
it be off until Asger opens his inventory where he can activate it. Put
some controls for it in the inventory"): two ducted fans on his back,
swivelled to blow the cabin's air the other way from where the keys
ask, so the air pushes him. Every room he can be in has air; the air
it blows carries the push on to the walls, so it pushes the vessel back
as hard ('_cabinworld'). Too weak to lift him where he weighs anything
(28 N against his 785 N on the pad): a way to get about weightless.
Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  Its push at full, N: two hobby jets' 64 mm ducted fans at some 14 N
#  each; the shares of it its levels give.
THRUST = 28.0
LEVELS = (0.25, 0.5, 0.75, 1.0)


class Jetpack:
  """
  Jetpack holds whether it is 'on' and its 'level' (an index of
  'LEVELS': the share of 'THRUST' it pushes); 'pushOf' the push it gives
  along a way (N), nought while off.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('on', 'level')

  #  Public Variables
  on: bool
  level: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.on, self.level = False, 1

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def thrust(self, ) -> float:
    """The 'thrust' property is how hard it pushes at its level, N."""
    return THRUST * LEVELS[self.level]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def toggled(self, ) -> None:
    """The 'toggled' method switches it on, or off."""
    self.on = not self.on

  def stronger(self, ) -> None:
    """The 'stronger' method sets it a level up (at the top it stays)."""
    self.level = min(len(LEVELS) - 1, self.level + 1)

  def weaker(self, ) -> None:
    """The 'weaker' method sets it a level down (at the foot it
    stays)."""
    self.level = max(0, self.level - 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def pushOf(self, way: tuple) -> tuple:
    """The 'pushOf' method returns its push on Asger along 'way' (a unit
    vector, or nought: no key held), N: its 'thrust' that way while on,
    else nought."""
    if not self.on:
      return 0.0, 0.0, 0.0
    return tuple(self.thrust * w for w in way)
