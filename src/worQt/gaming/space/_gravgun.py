"""
GravGun is the Grav-Gun (user, 2026-11-17: "the official name is 'zero
point energy field manipulator, if you really want to'. But 'gravgun'
is the code name in the code and Grav-Gun is the public name"; the 3 on
its side is no part of its name): "All it does is that when aimed at an
interactable object, right click starts a force acting between the gun
and its holder and the interactable object that increases in magnitude
with distance. Left click sends a pulse of a greater force opposite of
the right click." And (user, 2026-11-18): "gravgun pulls only when
right click held, until the item is picked up or the gun is near the
bolt. Then the connection stays and another rightclick releases it."
The field pulls the two together, 'PULL' N for every metre between them,
each the other way (a magic bolt is held by the hull, so the holder
goes to it; a loose mug is light, so it comes to him), while the button
is held ('letUp' ends it). Once what it pulls is within 'NEAR' m of the
muzzle it holds it ('hold'): a loose thing is held that far before the
muzzle, along the way it points; a bolt holds its holder that far from
it (a rod from the bolt to his middle: he may look round). The hold is
a stiff spring, 'HOLD' rad/s on the two, critically damped, solved
backward over each frame (it never rings up, however long the frame).
The pulse pushes them apart 'PUNT' times as hard as the field would for
'PULSE' s, and ends field and hold. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  The field's pull, N a metre between the gun and what it holds; the
#  pulse's push, so many times the pull at the distance, the other way;
#  how long it pushes, s.
PULL = 10.0
PUNT = 10.0
PULSE = 0.15
#  What the field pulls within this of the muzzle is held, m (a bolt:
#  the muzzle within it); held no nearer than 'LEAST', m; the hold's
#  spring, rad/s on the two (critically damped).
NEAR = 1.0
LEAST = 0.4
HOLD = 20.0
#  What the gun takes hold of: a magic bolt ('_bolts') or a loose thing
#  ('_furnishings.looseThings'), each by its index there.
KINDS = ('bolt', 'loose')


class GravGun:
  """
  GravGun holds what its field holds ('target': (kind, index), kind one
  of 'KINDS'; None: no field), how far off it holds it once it is near
  ('hold', m; None: the field still pulls, the button held) and its
  pulse ('pulse': what it pushes and for how much longer, s; None:
  none; 'pulses' counts them). 'gripped' starts the field on a target,
  'letUp' (the button let go) ends it unless it holds, 'released' ends
  field and hold, 'punted' pulses at a target; 'pushOf' returns the
  force on its holder for a frame (what it acts on feels that force the
  other way), holding what has come near.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('target', 'hold')

  #  Public Variables
  target: tuple | None
  hold: float | None
  pulse: tuple | None
  pulses: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.target, self.hold, self.pulse, self.pulses = None, None, None, 0

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

  @property
  def holding(self, ) -> bool:
    """The 'holding' property is whether it holds what came near (the
    button may be let go)."""
    return self.target is not None and self.hold is not None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def gripped(self, target: tuple) -> None:
    """The 'gripped' method starts the field on 'target' (kind, index),
    pulling while the button is held."""
    _checked(target)
    self.target, self.hold, self.pulse = tuple(target), None, None

  def letUp(self, ) -> bool:
    """The 'letUp' method takes the button's letting go: the field ends
    unless it holds what came near. Returns whether it ended."""
    if self.target is None or self.hold is not None:
      return False
    self.target = None
    return True

  def released(self, ) -> None:
    """The 'released' method ends the field, the hold and a pulse."""
    self.target, self.hold, self.pulse = None, None, None

  def punted(self, target: tuple) -> None:
    """The 'punted' method sends a pulse at 'target' (kind, index): it
    pushes 'PULSE' s; the field and the hold end."""
    _checked(target)
    self.target, self.hold = None, None
    self.pulse = tuple(target), PULSE
    self.pulses += 1

  def pushOf(self, gun: tuple, look: tuple, holder: tuple, there: tuple,
             moving: tuple, heft: float, seconds: float) -> tuple:
    """The 'pushOf' method returns the force on the gun's holder over a
    frame of 'seconds' s, N, the same axes throughout: the gun's muzzle
    at 'gun' pointing 'look' (unit), its holder's middle at 'holder',
    what it acts on at 'there' moving 'moving' (less the holder's
    velocity, m/s); 'heft' the two's mass as one (the reduced mass m1 m2
    / (m1 + m2); a bolt, held by the hull: the holder's own), kg. The
    pulse pushes away, 'PUNT' times the field (its time spent by
    'seconds'); the field pulls toward it 'PULL' a metre, holding it once
    within 'NEAR' of the muzzle; held, the hold's spring keeps a loose
    thing 'hold' before the muzzle, a bolt 'hold' from his middle. What
    it acts on feels the same force the other way."""
    off = tuple(t - g for t, g in zip(there, gun))
    if self.pulse is not None:
      target, left = self.pulse
      left -= seconds
      self.pulse = None if left <= 0.0 else (target, left)
      return tuple(-PUNT * PULL * o for o in off)
    if self.target is None:
      return 0.0, 0.0, 0.0
    bolt = self.target[0] == 'bolt'
    if self.hold is None:
      if math.hypot(*off) > NEAR:
        return tuple(PULL * o for o in off)
      self.hold = max(LEAST, math.dist(there, holder) if bolt
                      else math.hypot(*off))
    if seconds <= 0.0:
      return 0.0, 0.0, 0.0
    if bolt:
      change = _rodded(tuple(t - h for t, h in zip(there, holder)),
                       self.hold, moving, seconds)
    else:
      held = tuple(g + self.hold * w for g, w in zip(gun, look))
      change = _sprung(tuple(t - h for t, h in zip(there, held)), moving,
                       seconds)
    return tuple(-heft * c / seconds for c in change)


def _sprung(stretch: tuple, moving: tuple, seconds: float) -> tuple:
  """Returns how the hold's spring changes the velocity of what it
  holds (less the holder's, m/s) over 'seconds' s, it 'stretch' m off
  its place moving 'moving': backward Euler on the spring and damper
  ('HOLD' rad/s, critical), stable however long the step."""
  k, c = HOLD * HOLD, 2.0 * HOLD
  share = 1.0 + c * seconds + k * seconds * seconds
  return tuple((u - k * seconds * x) / share - u
               for x, u in zip(stretch, moving))


def _rodded(off: tuple, length: float, moving: tuple,
            seconds: float) -> tuple:
  """Returns how the hold changes the velocity of a bolt from its
  holder (m/s) over 'seconds' s, the bolt at 'off' from his middle
  moving 'moving': a rod 'length' long, the spring along it and the
  damper every way ('HOLD' rad/s, critical), backward Euler."""
  size = math.hypot(*off)
  if size <= 1e-9:
    return _sprung((0.0, 0.0, 0.0), moving, seconds)
  way = tuple(o / size for o in off)
  k, c = HOLD * HOLD, 2.0 * HOLD
  along = sum(u * w for u, w in zip(moving, way))
  across = tuple(u - along * w for u, w in zip(moving, way))
  share = 1.0 + c * seconds + k * seconds * seconds
  alongAfter = (along - k * seconds * (size - length)) / share
  acrossAfter = tuple(a / (1.0 + c * seconds) for a in across)
  return tuple(alongAfter * w + a - u for w, a, u in zip(
    way, acrossAfter, moving))


def _checked(target: tuple) -> None:
  """Raises unless 'target' is a kind of 'KINDS' and an index."""
  kind, index = target
  if kind not in KINDS or int(index) != index or index < 0:
    raise ValueError('the Grav-Gun takes no %r' % (target,))
