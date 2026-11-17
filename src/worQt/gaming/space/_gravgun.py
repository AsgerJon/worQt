"""
GravGun is the Grav-Gun (user, 2026-11-17: "the official name is 'zero
point energy field manipulator, if you really want to'. But 'gravgun'
is the code name in the code and Grav-Gun is the public name"; the 3 on
its side is no part of its name): "All it does is that when aimed at an
interactable object, right click starts a force acting between the gun
and its holder and the interactable object that increases in magnitude
with distance. Left click sends a pulse of a greater force opposite of
the right click." The field pulls the two together, 'PULL' N for every
metre between them, each the other way (the object's push is the
holder's turned round: a magic bolt is held by the hull, so the holder
goes to it; a loose mug is light, so it comes to him); a right click
again lets it go. The pulse pushes them apart 'PUNT' times as hard for
'PULSE' s, and ends the field. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  The field's pull, N a metre between the gun and what it holds; the
#  pulse's push, so many times the pull at the distance, the other way;
#  how long it pushes, s.
PULL = 10.0
PUNT = 10.0
PULSE = 0.15
#  What the gun takes hold of: a magic bolt ('_bolts') or a loose thing
#  ('_furnishings.looseThings'), each by its index there.
KINDS = ('bolt', 'loose')


class GravGun:
  """
  GravGun holds what its field holds ('target': (kind, index), kind one
  of 'KINDS'; None: no field) and its pulse ('pulse': what it pushes and
  for how much longer, s; None: none). 'gripped' starts the field on a
  target, 'released' ends it, 'punted' pulses at a target (ending the
  field); 'pushOf' returns the force on its holder for a frame, the gun
  and its target where they are (the target's is that force the other
  way).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  target: tuple | None
  pulse: tuple | None
  pulses: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.target, self.pulse, self.pulses = None, None, 0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def acting(self, ) -> tuple | None:
    """The 'acting' property is what the gun acts on now (the pulse's
    target while it pushes, else the field's; None: nothing)."""
    if self.pulse is not None:
      return self.pulse[0]
    return self.target

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def gripped(self, target: tuple) -> None:
    """The 'gripped' method starts the field on 'target' (kind, index)."""
    _checked(target)
    self.target = tuple(target)

  def released(self, ) -> None:
    """The 'released' method ends the field (and a pulse)."""
    self.target, self.pulse = None, None

  def punted(self, target: tuple) -> None:
    """The 'punted' method sends a pulse at 'target' (kind, index): it
    pushes 'PULSE' s; the field ends."""
    _checked(target)
    self.target, self.pulse = None, (tuple(target), PULSE)
    self.pulses += 1

  def pushOf(self, gun: tuple, there: tuple, seconds: float) -> tuple:
    """The 'pushOf' method returns the force on the gun's holder over a
    frame of 'seconds' s, N, the gun at 'gun' and what it acts on at
    'there' (the same axes): the field's pull toward it, 'PULL' a metre
    apart; or the pulse's push away, 'PUNT' times that (its time spent by
    'seconds'). What it acts on feels the same force the other way."""
    off = tuple(t - g for t, g in zip(there, gun))
    if self.pulse is not None:
      target, left = self.pulse
      left -= seconds
      self.pulse = None if left <= 0.0 else (target, left)
      return tuple(-PUNT * PULL * o for o in off)
    if self.target is None:
      return 0.0, 0.0, 0.0
    return tuple(PULL * o for o in off)


def _checked(target: tuple) -> None:
  """Raises unless 'target' is a kind of 'KINDS' and an index."""
  kind, index = target
  if kind not in KINDS or int(index) != index or index < 0:
    raise ValueError('the Grav-Gun takes no %r' % (target,))
