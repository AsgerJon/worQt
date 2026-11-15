"""
The hinge bench (user, 2026-11-14: "hinges, rigid and rubber-bushed or
whatever"; "for double wishbone suspension eventually"): a steel gantry
2 m before the walker, from its beam two wishbones (A-arms, steel, 0.5 m
long, their pivots 0.3 m apart) hanging on two hinges each along one
line: the left on rigid pins in steel sleeves, the right in rubber
bushings ('Bush()', drawn black); on the gantry's right post an oak
door on two rigid hinges. Punt them, grab them, walk into them. Its
world is greased ('HINGE_GREASE').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._assembly import Assembly, Bush, Contact, Fixed, Hinge
from ._body import Body, State
from ._shape import Shape, boxShape
from ._vectors import Vector, plus, turnAbout

#  Where the gantry stands (its feet's middle), the height of its
#  wishbones' pins, how far apart their pivots are and how long they
#  hang; how the steps are greased, m (a tenth of a micrometre:
#  measured, the door on two hinges rests and swings alike).
GANTRY = (0.0, 2.0, 0.0)
PIN_HEIGHT, PIVOTS, ARM = 1.2, 0.3, 0.5
ARMS_AT = (-0.5, 0.5)
HINGE_GREASE = 1e-7
#  The door: its size (wide, high, thick), its hinges' heights.
DOOR = (0.8, 1.1, 0.04)
DOOR_HINGES = (0.25, 1.05)
STEEL, OAK = 7850.0, 700.0
#  The walker on steel and on oak; steel on steel, oak on steel.
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)
_WALKER_ON_OAK = (1e6, 1.0, 0.6, 1e6, 2e3)
_STEEL_ON_STEEL = (1e7, 0.1, 0.3, 1e7, 100.0)
#  How far apart the skin points the wishbones and the door meet the
#  gantry with lie, m (every centimetre, the gantry's edges against the
#  three made 8580 of 10989 touches, 179 ms a frame on the CPU).
_FRAME_SPACING = 0.05


def _box(low: Vector, high: Vector) -> Shape:
  """Returns a box from corner 'low' to corner 'high'."""
  middle = tuple(0.5 * (a + b) for a, b in zip(low, high))
  return boxShape(*(b - a for a, b in zip(low, high))).moved(
    middle, (1.0, 0.0, 0.0, 0.0))


def _bar(start: Vector, end: Vector, thick: float) -> Shape:
  """Returns a square bar 'thick' across from 'start' to 'end' (both in
  the plane y nought)."""
  dx, dz = end[0] - start[0], end[2] - start[2]
  middle = tuple(0.5 * (a + b) for a, b in zip(start, end))
  return boxShape(math.hypot(dx, dz), thick, thick).moved(
    middle, turnAbout((0.0, 1.0, 0.0), math.atan2(-dz, dx)))


def _joined(pieces: tuple) -> Shape:
  """Returns 'pieces' as one shape."""
  shape = pieces[0]
  for piece in pieces[1:]:
    shape = shape.joined(piece)
  return shape


def gantryPieces() -> tuple[tuple[str, Shape], ...]:
  """The 'gantryPieces' function returns the gantry by its parts, in
  its own frame (the world's axes, from its feet's middle): ('frame',
  its feet, posts and beam), ('bracket', a steel bracket either side of
  each wishbone pivot, down from the beam to the pins, and the door's
  hinge blocks on the right post)."""
  top = PIN_HEIGHT + 0.06
  frame = (_box((-1.1, -0.15, 0.0), (-0.9, 0.15, 0.03)),
           _box((0.9, -0.15, 0.0), (1.1, 0.15, 0.03)),
           _box((-1.04, -0.04, 0.03), (-0.96, 0.04, top + 0.08)),
           _box((0.96, -0.04, 0.03), (1.04, 0.04, top + 0.08)),
           _box((-1.04, -0.04, top), (1.04, 0.04, top + 0.08)))
  brackets = []
  for at in ARMS_AT:
    for side in (-1.0, 1.0):
      x = at + side * (0.5 * PIVOTS + 0.045)
      brackets.append(_box((x - 0.01, -0.03, PIN_HEIGHT - 0.03),
                           (x + 0.01, 0.03, top)))
  for z in DOOR_HINGES:
    brackets.append(_box((1.04, -0.03, z - 0.04), (1.07, 0.03, z + 0.04)))
  return ('frame', _joined(frame)), ('bracket', _joined(tuple(brackets)))


def armPieces(bushed: bool) -> tuple[tuple[str, Shape], ...]:
  """The 'armPieces' function returns a wishbone by its parts, in its
  own frame (its pin's line along x through the origin, hanging down
  z): ('arm', its two legs from the pivots to the ball end, a brace
  and the ball end's block), and its sleeves on the pin ('rubber' if
  'bushed', else 'sleeve')."""
  half = 0.5 * PIVOTS
  end = (0.0, 0.0, -ARM)
  arm = (_bar((-half, 0.0, 0.0), end, 0.03), _bar((half, 0.0, 0.0), end,
                                                  0.03),
         _box((-0.1, -0.0125, -0.18), (0.1, 0.0125, -0.155)),
         _box((-0.035, -0.035, -ARM - 0.035), (0.035, 0.035, -ARM + 0.035)))
  sleeves = tuple(_box((x - 0.03, -0.025, -0.025), (x + 0.03, 0.025,
                                                   0.025))
                  for x in (-half, half))
  return ('arm', _joined(arm)), ('rubber' if bushed else 'sleeve',
                                 _joined(sleeves))


@functools.lru_cache(maxsize=2)
def armBody(bushed: bool) -> Body:
  """The 'armBody' function returns a wishbone, steel (13.4 kg)."""
  return Body.of(_joined(tuple(shape for _, shape in armPieces(bushed))),
                 STEEL)


@functools.lru_cache(maxsize=1)
def gantryBody() -> Body:
  """The 'gantryBody' function returns the gantry (part of the world on
  the bench: 'Fixed')."""
  return Body.of(_joined(tuple(shape for _, shape in gantryPieces())),
                 STEEL)


@functools.lru_cache(maxsize=1)
def doorBody() -> Body:
  """The 'doorBody' function returns the door, oak, its middle at its
  own frame's origin."""
  return Body.of(boxShape(*DOOR), OAK)


def hingeBench() -> tuple[Assembly, tuple[State, ...]]:
  """The 'hingeBench' function returns the hinge bench: the walker
  (body 0) 2 m before the gantry (1, part of the world), the rigid
  wishbone (2) and the bushed one (3) hanging still from its beam, each
  on two hinges on its pin's line (its pivots'), the door (4) on two
  rigid hinges on the right post, shut along the gantry. The walker
  meets everything; the wishbones and the door meet the gantry."""
  from ._scenes import WALKER
  pins = PIN_HEIGHT
  states = [State((0.0, 0.0, WALKER.radius)),
            State(plus(GANTRY, gantryBody().centre))]
  connections = [Fixed(1)]
  for index, (at, bush) in enumerate(zip(ARMS_AT, (None, Bush()))):
    body = armBody(bush is not None)
    middle = plus(GANTRY, (at, 0.0, pins))
    states.append(State(plus(middle, body.centre)))
    for side in (-0.5, 0.5):
      own = (side * PIVOTS, 0.0, 0.0)
      connections.append(Hinge(1, plus((at, 0.0, pins), own),
                                (1.0, 0.0, 0.0), 2 + index, own,
                                (1.0, 0.0, 0.0), bush))
  edge = 1.07
  middle = plus(GANTRY, (edge + 0.5 * DOOR[0] + 0.005, 0.0,
                         0.5 * (DOOR_HINGES[0] + DOOR_HINGES[1])))
  states.append(State(middle))
  for z in DOOR_HINGES:
    own = (-0.5 * DOOR[0] - 0.005, 0.0, z - (middle[2] - GANTRY[2]))
    connections.append(Hinge(1, (edge, 0.0, z), (0.0, 0.0, 1.0), 4, own,
                             (0.0, 0.0, 1.0)))
  bodies = (WALKER.body(), gantryBody(), armBody(False), armBody(True),
            doorBody())
  connections += [Contact(0, k, *(_WALKER_ON_OAK if k == 4 else
                                  _WALKER_ON_STEEL)) for k in (1, 2, 3, 4)]
  connections += [Contact(k, 1, *_STEEL_ON_STEEL, _FRAME_SPACING)
                  for k in (2, 3, 4)]
  return Assembly(bodies, tuple(connections)), tuple(states)


def benchFinishes(assembly: Assembly) -> dict:
  """The 'benchFinishes' function returns how the bench's bodies are
  drawn, by index: the gantry and the wishbones by their parts, the
  door whole ('door')."""
  return {1: gantryPieces(), 2: armPieces(False), 3: armPieces(True),
          4: 'door'}

