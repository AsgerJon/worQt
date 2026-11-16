"""
Coach is a carriage of the steam train (user, 2026-11-16: "a bunch of
cars being pulled by it"; then "make the train, however realistic or
not, such that we can walk from the locomotive and back through each
car. Then put some memes on the inside walls"): a long body, hollow, a
door in each end and a gangway ahead of its front door to the car ahead
(a plate to walk over and bellows either side), windows down its sides,
benches under them, posters above them and on its ends; on two bogies
pivoted under it, each on two wheelsets in axleboxes; buffers at both
ends, coupled to the car ahead by a screw coupling.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from worQt.phys._assembly import Hinge
from worQt.phys._body import Body, State
from worQt.phys._shape import boxShape
from worQt.phys.rail import JOURNAL_AT, Axlebox, wheelsetBody, wheelsetOn
from worQt.phys.rail._wheelset import RADIUS
from worQt.phys._vectors import UNTURNED, turnOf

from worQt.gaming.sandbox._vehicle import Vehicle

from ._coupling import BUFFER_LONG, BUFFER_SIDE, BUFFER_UP, CarEnd
from ._coupling import carApart, couplingOf
from ._dress import boxQuads, partsOf, posterRows
from ._locomotive import TRAIN_LAW, _blocks
from ._memes import MEME_LOOK, MEMES, memeCell
from ._offrails import putBack, tookOff

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import World

#  The coach's body, m (in its own frame: x ahead, y left, its middle on
#  the rails' top): half its length, half its width, its walls' thickness;
#  its floor (bottom, top) and roof; its windows' sills and heads over the
#  rails' top, how many down each side, how long; the end walls' and the
#  doors' (half wide, top); the headstocks under the ends (the buffers on
#  them); the benches under the windows (out from the middle, top).
COACH_HALF, COACH_WIDE, WALL = 9.5, 1.4, 0.08
FLOOR, ROOF = (1.05, 1.15), (3.85, 3.95)
SILL, HEAD = 2.05, 3.0
WINDOWS, WINDOW_LONG, WINDOWS_HALF = 7, 1.5, 8.0
END_WALL, DOOR_HALF, DOOR_TOP = 0.1, 0.45, 3.25
HEADSTOCK, HEADSTOCK_LOW = 0.2, 0.8
BENCH_FROM, BENCH_TOP = 0.95, 1.6
#  The gangway ahead of the front door: as long as the gap to the car
#  ahead's end less 4 cm (its buffers touching), its plate's top level
#  with the floor, its bellows (thick) either side of the door, its roof.
GANGWAY_LONG, BELLOWS, GANGWAY_TOP = 1.2, 0.1, 3.25
#  Its mass, kg (a wooden coach of its time, ~26 t without its bogies).
COACH_MASS = 26e3
#  The bogies: their pivots this far either side of the middle, m; their
#  wheelsets this far either side of a pivot, m (2.5 m wheelbase); a
#  bogie's frame, kg; its axleboxes (stiffness, damping as the engine's).
PIVOT_AT, AXLE_HALF = 6.5, 1.25
BOGIE_MASS = 3.0e3
BOX = ((3e7, 1e7, 1.5e6), (1e4, 1e4, 2e4))
#  Where a rider's ball is held: on the floor, m; a coach's length over
#  its buffers, m (cars standing buffer to buffer this far apart).
SEAT = (0.0, 0.0, 1.45)
COACH_LONG = 2.0 * (COACH_HALF + BUFFER_LONG)
#  How a coach is drawn inside (a look each: colour, metalness, roughness):
#  its lining, floor, benches, the gangway's plate and bellows, buffers.
COACH_LOOKS = {'lining': ((222, 208, 176), 0.0, 0.8),
               'floor': ((118, 82, 52), 0.0, 0.7),
               'bench': ((52, 78, 140), 0.0, 0.9),
               'plate': ((120, 122, 126), 0.4, 0.5),
               'bellows': ((38, 38, 40), 0.0, 0.9),
               'buffer': ((30, 30, 32), 0.3, 0.5)}
#  The posters: above each window (wide, high, its middle's height), on
#  the end walls either side of the door (wide, high, its middle's
#  height), off the lining, m.
POSTER, POSTER_UP = (1.0, 0.75), 3.425
END_POSTER, END_POSTER_UP = (0.72, 0.54), 2.6
LINING, POSTER_OFF = 0.01, 0.004


def _windowsOf() -> tuple:
  """Returns where the windows are along a side (from x, to x, m),
  'WINDOWS' of 'WINDOW_LONG' spread evenly within 'WINDOWS_HALF'."""
  pier = (2.0 * WINDOWS_HALF - WINDOWS * WINDOW_LONG) / (WINDOWS - 1)
  return tuple((-WINDOWS_HALF + k * (WINDOW_LONG + pier),
                -WINDOWS_HALF + k * (WINDOW_LONG + pier) + WINDOW_LONG)
               for k in range(WINDOWS))


def _shellBoxes() -> tuple:
  """Returns the coach's shell as boxes (from, to: corners, m): floor,
  headstocks, roof, each side's panel under and over the windows and
  the piers between them, each end's walls either side of the door and
  over it."""
  x, half, inner = COACH_HALF, COACH_WIDE, COACH_WIDE - WALL
  out = [((-x, -half, FLOOR[0]), (x, half, FLOOR[1])),
         ((-x, -half, ROOF[0]), (x, half, ROOF[1]))]
  for end in (1.0, -1.0):
    near, far = sorted((end * (x - HEADSTOCK), end * x))
    out.append(((near, -half, HEADSTOCK_LOW), (far, half, FLOOR[0])))
    near, far = sorted((end * (x - END_WALL), end * x))
    out.append(((near, -DOOR_HALF, DOOR_TOP), (far, DOOR_HALF, ROOF[0])))
    for side in (1.0, -1.0):
      low, high = sorted((side * DOOR_HALF, side * inner))
      out.append(((near, low, FLOOR[1]), (far, high, ROOF[0])))
  edges = [-x] + [e for window in _windowsOf() for e in window] + [x]
  for side in (1.0, -1.0):
    low, high = sorted((side * inner, side * half))
    out.append(((-x, low, FLOOR[1]), (x, high, SILL)))
    out.append(((-x, low, HEAD), (x, high, ROOF[0])))
    for k in range(0, len(edges), 2):
      out.append(((edges[k], low, SILL), (edges[k + 1], high, HEAD)))
  return tuple(out)


def _benchBoxes() -> tuple:
  """Returns the benches under the windows, one down each side."""
  inner, out = COACH_WIDE - WALL, []
  for side in (1.0, -1.0):
    low, high = sorted((side * BENCH_FROM, side * inner))
    out.append(((-WINDOWS_HALF, low, FLOOR[1]),
                (WINDOWS_HALF, high, BENCH_TOP)))
  return tuple(out)


def _gangwayBoxes() -> tuple:
  """Returns the gangway ahead of the front door as boxes: its plate,
  its bellows either side, its roof."""
  x0, x1 = COACH_HALF, COACH_HALF + GANGWAY_LONG
  out = [((x0, -DOOR_HALF, FLOOR[1] - 0.05), (x1, DOOR_HALF, FLOOR[1])),
         ((x0, -DOOR_HALF - BELLOWS, GANGWAY_TOP),
          (x1, DOOR_HALF + BELLOWS, GANGWAY_TOP + 0.08))]
  for side in (1.0, -1.0):
    low, high = sorted((side * DOOR_HALF, side * (DOOR_HALF + BELLOWS)))
    out.append(((x0, low, FLOOR[1]), (x1, high, GANGWAY_TOP)))
  return tuple(out)


def shapeOf(boxes: tuple) -> object:
  """The 'shapeOf' function returns 'boxes' (each its two corners, m)
  as one shape."""
  shape = None
  for low, high in boxes:
    piece = boxShape(*(b - a for a, b in zip(low, high))).moved(
      tuple(0.5 * (a + b) for a, b in zip(low, high)), UNTURNED)
    shape = piece if shape is None else shape.joined(piece)
  return shape


@functools.lru_cache(None)
def coachBody() -> Body:
  """Returns the coach's body, hollow (its shell, benches and gangway:
  '_shellBoxes', '_benchBoxes', '_gangwayBoxes'), 'COACH_MASS' kg."""
  shape = shapeOf(_shellBoxes() + _benchBoxes() + _gangwayBoxes())
  return Body.of(shape, COACH_MASS / Body.of(shape, 1.0).mass)


@functools.lru_cache(None)
def coachBogie() -> Body:
  """Returns a coach's bogie frame ('BOGIE_MASS' kg), its pivot at its
  own origin's top."""
  shape = _blocks(((-1.6, 1.6, 1.0, 0.55, 0.8),))
  return Body.of(shape, BOGIE_MASS / Body.of(shape, 1.0).mass)


def _liningBoxes() -> tuple:
  """Returns the lining inside the shell (thin boxes just inside its
  walls, ends and ceiling)."""
  x, inner = COACH_HALF - END_WALL, COACH_WIDE - WALL
  edges = [-x] + [e for window in _windowsOf() for e in window] + [x]
  out = [((-x, -inner, ROOF[0] - LINING), (x, inner, ROOF[0]))]
  for side in (1.0, -1.0):
    low, high = sorted((side * (inner - LINING), side * inner))
    out.append(((-x, low, FLOOR[1]), (x, high, SILL)))
    out.append(((-x, low, HEAD), (x, high, ROOF[0])))
    for k in range(0, len(edges), 2):
      out.append(((edges[k], low, SILL), (edges[k + 1], high, HEAD)))
  for end in (1.0, -1.0):
    near, far = sorted((end * (x - LINING), end * x))
    out.append(((near, -DOOR_HALF, DOOR_TOP), (far, DOOR_HALF, ROOF[0])))
    for side in (1.0, -1.0):
      low, high = sorted((side * DOOR_HALF, side * inner))
      out.append(((near, low, FLOOR[1]), (far, high, ROOF[0])))
  return tuple(out)


def _bufferBoxes() -> tuple:
  """Returns the buffers drawn at both ends: a stock off the headstock
  and a head on it, either side."""
  out = []
  for end in (1.0, -1.0):
    for side in (1.0, -1.0):
      y, z = side * BUFFER_SIDE, BUFFER_UP
      stock = sorted((end * COACH_HALF, end * (COACH_HALF + 0.55)))
      head = sorted((end * (COACH_HALF + 0.55),
                     end * (COACH_HALF + BUFFER_LONG)))
      out.append(((stock[0], y - 0.09, z - 0.09),
                  (stock[1], y + 0.09, z + 0.09)))
      out.append(((head[0], y - 0.22, z - 0.18),
                  (head[1], y + 0.22, z + 0.18)))
  return tuple(out)


def _posters(number: int) -> list:
  """Returns the posters as rows of eight (place, normal, where on the
  memes' picture): above each window on both sides, on the end walls
  either side of the door; the coach 'number' showing the memes from
  its own place round."""
  inner = COACH_WIDE - WALL - LINING - POSTER_OFF
  wall = COACH_HALF - END_WALL - LINING - POSTER_OFF
  places = []
  for start, end in _windowsOf():
    middle = 0.5 * (start + end)
    places.append(((middle, inner, POSTER_UP), (0.0, -1.0, 0.0),
                   (1.0, 0.0, 0.0), POSTER))
    places.append(((-middle, -inner, POSTER_UP), (0.0, 1.0, 0.0),
                   (-1.0, 0.0, 0.0), POSTER))
  y = 0.5 * (DOOR_HALF + COACH_WIDE - WALL)
  for side in (1.0, -1.0):
    places.append(((wall, side * y, END_POSTER_UP), (-1.0, 0.0, 0.0),
                   (0.0, -1.0, 0.0), END_POSTER))
    places.append(((-wall, side * y, END_POSTER_UP), (1.0, 0.0, 0.0),
                   (0.0, 1.0, 0.0), END_POSTER))
  out = []
  for k, (middle, normal, right, size) in enumerate(places):
    cell = memeCell((number * 7 + k) % len(MEMES))
    out.append(posterRows(middle, normal, right, size[0], size[1], cell))
  return out


def coachParts(livery: str, number: int, centre: tuple) -> tuple:
  """The 'coachParts' function returns how a coach in 'livery' (a look)
  is drawn, about its body's 'centre': its shell outside in its livery,
  lined inside, its floor, benches, gangway, buffers and the posters of
  coach 'number' (the memes)."""
  def quads(boxes: tuple) -> list:
    return [quad for low, high in boxes for quad in boxQuads(low, high)]
  x, inner = COACH_HALF - END_WALL, COACH_WIDE - WALL
  floor = ((-x, -inner, FLOOR[1]), (x, inner, FLOOR[1] + 0.005))
  gangway = _gangwayBoxes()
  return partsOf({livery: quads(_shellBoxes()),
                  'lining': quads(_liningBoxes()),
                  'floor': quads((floor,)),
                  'bench': quads(_benchBoxes()),
                  'plate': quads(gangway[:1]),
                  'bellows': quads(gangway[1:]),
                  'buffer': quads(_bufferBoxes()),
                  'memes': _posters(number)}, centre)


class Coach(Vehicle):
  """
  Coach is a carriage on its world's track 'line', its middle at 'along'
  m (standing still where it is put): its body ('coachBody', its frame:
  the seat 'SEAT' on its floor; drawn in 'livery' with the memes from
  its 'number''s place round), two bogies ('coachBogie') on pivots
  'PIVOT_AT' either side, each on two wheelsets ('wheelsets') in
  axleboxes ('boxes'); its buffers at both ends ('front', 'back': its
  'CarEnd's), coupled to the car ahead ('leading': a vehicle with a
  'back', None: standing loose). Its body meets every other car's not
  coupled to it. A wheelset the rail world finds off its rails it takes
  off ('_offrails.tookOff', its body and bogies then meeting the
  ground: 'off'); put back, it is as it was made ('restored').
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
  livery: str
  number: int
  wheelsets: tuple
  boxes: tuple
  off: dict

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, along: float, line: int, leading: object,
               livery: str = 'coach', number: int = 0) -> None:
    Vehicle.__init__(self, )
    self.along, self.line, self.leading = along, line, leading
    self.livery, self.number = livery, number
    self.wheelsets, self.boxes, self.off = (), (), {}

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def front(self, ) -> CarEnd:
    """The 'front' property is its front end: its buffers' heads
    'BUFFER_LONG' ahead of its body."""
    return CarEnd(self.frame, COACH_HALF + BUFFER_LONG, 1.0, self)

  @property
  def back(self, ) -> CarEnd:
    """The 'back' property is its back end, where the car behind couples:
    its buffers' heads 'BUFFER_LONG' behind its body."""
    return CarEnd(self.frame, -COACH_HALF - BUFFER_LONG, -1.0, self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def placed(self, world: World) -> None:
    """The 'placed' method puts the coach, its bogies and wheelsets in
    'world', still, each journal in its axlebox, each bogie on its
    pivot, coupled to the car ahead. Its body meets the cars not coupled
    to it ('world.cars'); nothing else of it touches another part of the
    train or the world's own bodies; what is spawned later meets it."""
    self.world = world
    track = world.tracks[self.line]
    body = self._spawned(track, coachBody(), self.along, self.livery,
                         carApart(world, self, self.leading))
    world.cars.append((body, self))
    bodies, wheelsets, boxes = [body], [], []
    for pivot in (PIVOT_AT, -PIVOT_AT):
      bogie = self._spawned(track, coachBogie(), self.along + pivot,
                            'black', frozenset(range(len(world.states))))
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
      world.connected(couplingOf(self.front, self.leading.back))
    world.dressedWith(body, coachParts(self.livery, self.number,
                                       coachBody().centre),
                      {**COACH_LOOKS, 'memes': MEME_LOOK})
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

  def _spawned(self, track: object, body: Body, along: float, look: str,
               apart: frozenset) -> int:
    """Puts 'body' at 'along' m on 'track' (its own frame's origin on the
    rails' top there, turned as the track), apart from 'apart', drawn as
    'look'; returns its index."""
    world = self.world
    place, frame = track.frameAt(along)
    rows = tuple(tuple(float(x) for x in row) for row in frame)
    centre = tuple(float(place[i]) + sum(rows[i][j] * body.centre[j]
                                         for j in range(3))
                   for i in range(3))
    return world.spawned(body, State(centre, turnOf(rows)), TRAIN_LAW,
                         look, apart)
