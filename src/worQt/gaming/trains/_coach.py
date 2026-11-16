"""
Coach is a carriage of the steam train (user, 2026-11-16: "a bunch of
cars being pulled by it"): a long body, hollow (a floor, sides, ends
and a roof: sat in, walked in), on two bogies pivoted under it, each
on two wheelsets in axleboxes; coupled to whatever is ahead of it by a
drawbar.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from worQt.phys._assembly import Hinge, Tie
from worQt.phys._body import Body, State
from worQt.phys.rail import JOURNAL_AT, Axlebox, wheelsetBody, wheelsetOn
from worQt.phys.rail._wheelset import RADIUS
from worQt.phys._vectors import turnOf

from worQt.gaming.sandbox._vehicle import Vehicle

from ._locomotive import TRAIN_LAW, _blocks, _sides, barBody
from ._offrails import putBack, tookOff

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import World

#  The coach's body, m (in its own frame: x ahead, its middle on the
#  rails' top): its floor, its two ends (a door's gap in each), its roof,
#  as the engine's pieces; its sides (x from, x to, y from, y to, z from,
#  z to); its mass, kg (a wooden coach of its time, ~26 t without its
#  bogies).
COACH_HALF = 9.5
COACH_PIECES = ((-9.5, 9.5, 1.4, 1.05, 1.15),
                (-9.5, 9.5, 1.4, 3.85, 3.95))
COACH_SIDES = ((-9.5, 9.5, 1.32, 1.4, 1.15, 3.85),
               (9.4, 9.5, 0.45, 1.32, 1.15, 3.85),
               (-9.5, -9.4, 0.45, 1.32, 1.15, 3.85))
COACH_MASS = 26e3
#  The bogies: their pivots this far either side of the middle, m; their
#  wheelsets this far either side of a pivot, m (2.5 m wheelbase); a
#  bogie's frame, kg; its axleboxes (stiffness, damping as the engine's).
PIVOT_AT, AXLE_HALF = 6.5, 1.25
BOGIE_MASS = 3.0e3
BOX = ((3e7, 1e7, 1.5e6), (1e4, 1e4, 2e4))
#  Where a rider's ball is held: on the floor, m; where the coach couples
#  (its nose and its tail, x, and the height, m); the gap to the car
#  ahead, m.
SEAT = (0.0, 0.0, 1.45)
NOSE, TAIL, HITCH_UP = 9.5, -9.5, 1.0
GAP = 1.0


@functools.lru_cache(None)
def coachBody() -> Body:
  """Returns the coach's body, hollow ('COACH_PIECES', 'COACH_SIDES'),
  'COACH_MASS' kg."""
  shape = _sides(COACH_SIDES, _blocks(COACH_PIECES))
  return Body.of(shape, COACH_MASS / Body.of(shape, 1.0).mass)


@functools.lru_cache(None)
def coachBogie() -> Body:
  """Returns a coach's bogie frame ('BOGIE_MASS' kg), its pivot at its
  own origin's top."""
  shape = _blocks(((-1.6, 1.6, 1.0, 0.55, 0.8),))
  return Body.of(shape, BOGIE_MASS / Body.of(shape, 1.0).mass)


class Coach(Vehicle):
  """
  Coach is a carriage on its world's track 'line', its middle at 'along'
  m (standing still where it is put): its body ('coachBody', its frame:
  the seat 'SEAT' on its floor), two bogies ('coachBogie') on pivots
  'PIVOT_AT' either side, each on two wheelsets ('wheelsets') in
  axleboxes ('boxes'); a drawbar from its nose to the 'tail' of the car
  ahead ('leading': a vehicle with a 'tail', None: none), a ball joint
  at either end. Its own 'tail' is its body's back. A wheelset the rail
  world finds off its rails it takes off ('_offrails.tookOff', its body
  and bogies then meeting the ground: 'off'); put back, it is as it was
  made ('restored').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  seat = SEAT
  name = 'Coach'

  #  Public Variables
  along: float
  line: int
  leading: object
  wheelsets: tuple
  boxes: tuple
  off: dict

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, along: float, line: int, leading: object) -> None:
    Vehicle.__init__(self, )
    self.along, self.line, self.leading = along, line, leading
    self.wheelsets, self.boxes, self.off = (), (), {}

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def tail(self, ) -> tuple:
    """The 'tail' property is where the car behind couples: its body's
    index and the point on its back, in its own frame."""
    return self.frame, (TAIL, 0.0, HITCH_UP)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def placed(self, world: World) -> None:
    """The 'placed' method puts the coach, its bogies and wheelsets in
    'world', still, each journal in its axlebox, each bogie on its
    pivot, and its drawbar to the car ahead. Nothing of it touches
    another part of the train or the world's own bodies; what is
    spawned later meets it."""
    self.world = world
    track = world.tracks[self.line]
    body = self._spawned(track, coachBody(), self.along, 'coach')
    bodies, wheelsets, boxes = [body], [], []
    for pivot in (PIVOT_AT, -PIVOT_AT):
      bogie = self._spawned(track, coachBogie(), self.along + pivot,
                            'black')
      world.connected(Hinge(body, (pivot, 0.0, 0.8), (0.0, 0.0, 1.0),
                            bogie, (0.0, 0.0, 0.8), (0.0, 0.0, 1.0)))
      bodies.append(bogie)
      for x in (AXLE_HALF, -AXLE_HALF):
        wheelset = world.spawned(
          wheelsetBody(), wheelsetOn(track, self.along + pivot + x, 0.0),
          TRAIN_LAW, 'wheel', frozenset(range(len(world.states))))
        wheelsets.append(wheelset)
        stiffness, damping = BOX
        pressed = (COACH_MASS + 2.0 * BOGIE_MASS) / 8.0 * 9.81 / (
          stiffness[2])
        for side in (1.0, -1.0):
          box = Axlebox(wheelset, side, bogie, (
            x, side * JOURNAL_AT, RADIUS - pressed), stiffness, damping)
          world.connected(box)
          boxes.append(box)
    self.wheelsets, self.boxes = tuple(wheelsets), tuple(boxes)
    self.bodies = tuple(bodies) + self.wheelsets
    self._frames = tuple(bodies)
    if self.leading is not None:
      self.bodies += (self._coupled(world),)
    world.addActor(self)

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method takes off each of its wheelsets the rail world
    found off its rails in its last call."""
    derailed = getattr(self.world.solver, 'derailed', ())
    for index in self.wheelsets:
      if index in derailed and index not in self.off:
        frames = () if self.off else self._frames
        self.off[index] = tookOff(self.world, index, states, TRAIN_LAW,
                                  frames)

  def restored(self, ) -> None:
    """The 'restored' method puts every wheelset taken off back on its
    rails as it was made."""
    for index, record in self.off.items():
      putBack(self.world, index, record)
    self.off = {}

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _spawned(self, track: object, body: Body, along: float,
               look: str) -> int:
    """Puts 'body' at 'along' m on 'track' (its own frame's origin on the
    rails' top there, turned as the track), apart from every body
    already in the world, drawn as 'look'; returns its index."""
    world = self.world
    place, frame = track.frameAt(along)
    rows = tuple(tuple(float(x) for x in row) for row in frame)
    centre = tuple(float(place[i]) + sum(rows[i][j] * body.centre[j]
                                         for j in range(3))
                   for i in range(3))
    return world.spawned(body, State(centre, turnOf(rows)), TRAIN_LAW,
                         look, frozenset(range(len(world.states))))

  def _coupled(self, world: World) -> int:
    """Puts the drawbar from this coach's nose to the tail of the car
    ahead in 'world'; returns its index."""
    ahead, point = self.leading.tail
    states, bodies = world.states, world.assembly.bodies
    tail = bodies[ahead].placeOf(states[ahead], point)
    nose = bodies[self.frame].placeOf(states[self.frame],
                                      (NOSE, 0.0, HITCH_UP))
    long = sum((t - n) ** 2 for t, n in zip(tail, nose)) ** 0.5
    along = tuple((t - n) / long for t, n in zip(tail, nose))
    left = (-along[1], along[0], 0.0)
    size = (left[0] ** 2 + left[1] ** 2) ** 0.5
    left = (left[0] / size, left[1] / size, 0.0)
    up = (along[1] * left[2] - along[2] * left[1],
          along[2] * left[0] - along[0] * left[2],
          along[0] * left[1] - along[1] * left[0])
    rows = tuple((along[i], left[i], up[i]) for i in range(3))
    middle = tuple(0.5 * (t + n) for t, n in zip(tail, nose))
    bar = world.spawned(barBody(long), State(middle, turnOf(rows)),
                        TRAIN_LAW, 'rod', frozenset(range(len(states))))
    world.connected(Tie(bar, (0.5 * long, 0.0, 0.0), ahead, point))
    world.connected(Tie(bar, (-0.5 * long, 0.0, 0.0), self.frame,
                        (NOSE, 0.0, HITCH_UP)))
    return bar
