"""
Buffers and couplings (user, 2026-11-16: "make trains have collision and
all that", yes to real buffers and couplings): every end of a car (an
engine's front, a tender's back, a coach's two, a buffer stop's face) a
'CarEnd' with two side buffers; between every front and every back of
two others ('buffered') a pair of buffer springs that only push, slack
until the buffers' heads meet ('BUFFER_LONG' each from its base: the
heads touching, the bases twice that apart), however the cars came
together (a train run into loose coaches, a coach shoved into a stop);
cars coupled ('coupled') also a screw coupling between their ends' middles
that only pulls, tightened just short of the buffers touching.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.phys._assembly import Spring

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import World

#  The side buffers (where the engine's model has its own): this far
#  either side of the middle, their middles this high over the rails'
#  top, m; a buffer's head this far from its base, m (a buffer's stroke
#  is 0.1 m: the spring only begins at the heads touching); its spring,
#  N/m (a coach's 26 t at 2 m/s into a stop takes ~0.1 m of two), its
#  damping, N s/m (light: worked at each kick).
BUFFER_SIDE, BUFFER_UP, BUFFER_LONG = 0.88, 1.06, 0.62
BUFFER_STIFF, BUFFER_DAMP = 5e6, 5e4
#  The screw coupling: its spring, N/m (the draw gear's), damping, N s/m;
#  tightened this much short of the buffers' heads touching, m (a few kN
#  pressing them together standing).
COUPLING_STIFF, COUPLING_DAMP = 5e6, 5e4
COUPLING_TIGHT = 0.003


class CarEnd:
  """
  CarEnd is an end of a car: its 'body' (index), where its buffers'
  heads stand along its own x ('head', m, in the body's own frame) and
  which way they face ('facing': 1 ahead, a front; -1 back, a back);
  'vehicle' whose end it is (None: a buffer stop's).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, body: int, head: float, facing: float,
               vehicle: object) -> None:
    self.body, self.head, self.facing = body, head, facing
    self.vehicle = vehicle

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def base(self, side: float) -> tuple:
    """The 'base' method returns the base of its buffer on 'side' (1 the
    left, -1 the right, 0 the middle: the coupling's hook), in its body's
    own frame: 'BUFFER_LONG' back from the head."""
    return (self.head - self.facing * BUFFER_LONG, side * BUFFER_SIDE,
            BUFFER_UP)


def buffersOf(front: CarEnd, back: CarEnd) -> tuple:
  """The 'buffersOf' function returns the buffer springs between a car's
  'front' and another's 'back' (left on left, right on right): pushing
  only, slack until the heads meet, 'BUFFER_STIFF' and 'BUFFER_DAMP'."""
  return tuple(Spring(front.body, front.base(side), back.body,
                      back.base(side), BUFFER_STIFF, 2.0 * BUFFER_LONG,
                      BUFFER_DAMP, False, True) for side in (1.0, -1.0))


def couplingOf(front: CarEnd, back: CarEnd) -> Spring:
  """The 'couplingOf' function returns the screw coupling from a car's
  'back' to the 'front' of the car behind it: pulling only, between the
  ends' middles, 'COUPLING_TIGHT' short of the heads touching."""
  return Spring(front.body, front.base(0.0), back.body, back.base(0.0),
                COUPLING_STIFF, 2.0 * BUFFER_LONG - COUPLING_TIGHT,
                COUPLING_DAMP, True, False)


def buffered(world: World, ends: tuple) -> tuple:
  """The 'buffered' function puts in 'world' the buffers between every
  front among 'ends' ('CarEnd's) and every back of another vehicle (or
  a stop), slack till they meet; returns them."""
  out = []
  for front in ends:
    if front.facing < 0.0:
      continue
    for back in ends:
      if back.facing > 0.0 or (back.vehicle is not None
                               and back.vehicle is front.vehicle):
        continue
      for spring in buffersOf(front, back):
        world.connected(spring)
        out.append(spring)
  return tuple(out)


def carApart(world: World, vehicle: object, coupled: object) -> frozenset:
  """The 'carApart' function returns what a car body of 'vehicle' about
  to be spawned in 'world' does not meet: every body already there but
  the car bodies of other vehicles ('world.cars': (index, vehicle)) not
  coupled to it ('coupled': the vehicle it couples to, None: none). Cars
  coupled meet by their buffers; any other two meet as bodies too (a
  train run into a loose coach's side)."""
  meets = {index for index, owner in world.cars
           if owner is not vehicle and owner is not coupled}
  return frozenset(range(len(world.states))) - meets
