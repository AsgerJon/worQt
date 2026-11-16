"""
The real car on the oval (user, 2026-11-15: "Quick, park the old car by
inside the grass on the Dover track, put this car there instead, have
an AI driver take the wheel"): the real car ('_realcar.realCar') set
down on the oval ('_terrain.oval': a mile round, banked 9 degrees on its
straights and 24 in its turns) on its racing driver's line at the start
line, leaning with the banking ('startOf'), the walker sat in it; the
old car (the springs' world's, '_car.carBuilt', settled as its own
window builds it) parked in the infield's grass by the front straight
('PARKED'), its every body part of the world ('Fixed': it stands as
parked, nothing in its suspension moves), the walker meeting each
('realCarOnOval'). The ground is the tyre yard's on the oval's terrain
('ovalGround'), its safety barrier round its outside ('ovalWall').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._assembly import Assembly, Contact, Fixed
from ._body import State
from ._ground import Ground
from ._vectors import Vector, minus, plus, product, rotated

#  Where the old car is parked, m (x, y: in the infield's grass, beside
#  the front straight's apron, past the start line), and which way it
#  faces (rad from x, toward the track at a slant).
PARKED, PARKED_HEADING = (-40.0, 28.0), math.radians(-35.0)
#  How the walker meets the old car: on steel, on rubber (the real car's
#  laws).
_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)
_ON_RUBBER = (1e6, 1.0, 0.9, 1e6, 2e3)


@functools.lru_cache(maxsize=1)
def ovalGround() -> Ground:
  """The 'ovalGround' function returns the real car's ground (the tyre
  yard's) on the oval's terrain, its safety barrier round it, made
  once."""
  from ._carcass import TYRE_YARD
  from ._terrain import oval, ovalWall
  return TYRE_YARD._replace(terrain=oval(1.0), wall=ovalWall())


def startOf() -> tuple[Vector, tuple]:
  """The 'startOf' function returns where the real car's frame starts on
  the oval (its place and turn, as 'realCar' takes them): on the racing
  driver's line at the start line ('LINE'), on the ground there,
  heading along it, leaning as the banking does."""
  from ._laps import LINE
  from ._robot import RACE_MARGIN
  from ._terrain import ovalAt, ovalShapeAt
  terrain = ovalGround().terrain
  x, y, heading = ovalAt(LINE, RACE_MARGIN - 0.5 * ovalShapeAt(LINE)[0])
  up = terrain.normalAt(x, y)
  tilt = math.atan2(-up[1], up[2])
  turn = product((math.cos(0.5 * heading), 0.0, 0.0,
                  math.sin(0.5 * heading)),
                 (math.cos(0.5 * tilt), math.sin(0.5 * tilt), 0.0, 0.0))
  return (x, y, terrain.heightAt(x, y)), turn


@functools.lru_cache(maxsize=1)
def parkedCar() -> tuple:
  """The 'parkedCar' function returns the old car (its 'CarBuild', as its
  own window builds it: settled, live) and its states parked at
  'PARKED', facing 'PARKED_HEADING', on the grass there (level, at
  nought), made once (seconds: the springs' world settles it)."""
  from ._car import carBuilt
  from ._world import LIVE
  car = carBuilt(0.5, LIVE)
  turn = (math.cos(0.5 * PARKED_HEADING), 0.0, 0.0,
          math.sin(0.5 * PARKED_HEADING))
  at = (PARKED[0], PARKED[1], ovalGround().terrain.heightAt(*PARKED))
  states = tuple(State(plus(at, rotated(turn, state.place)),
                       product(turn, state.turn))
                 for state in car.states)
  return car, states


def realCarOnOval(controls: object, built: object = None
                  ) -> tuple[Assembly, tuple[State, ...]]:
  """The 'realCarOnOval' function returns the real car worked by
  'controls' at the oval's start ('startOf'; built by 'built', None: the
  car of parts, '_realcar.realCar'; the stand-in car,
  '_magiccar.magicCar'), the walker sat in it, and the old car parked in
  the infield ('parkedCar'), its bodies after the real car's
  ('parkedFirst'), each part of the world, the walker meeting each with
  a shape."""
  from ._realcar import realCar
  built = realCar if built is None else built
  assembly, states = built(controls, startOf())
  car, parked = parkedCar()
  first = len(assembly.bodies)
  bodies = car.assembly.bodies
  connections = list(assembly.connections)
  connections += [Fixed(first + k) for k in range(len(bodies))]
  for k, body in enumerate(bodies):
    if body.shape is None:
      continue
    law = _ON_RUBBER if k in car.wheels else _ON_STEEL
    connections.append(Contact(0, first + k, *law))
  return (Assembly(assembly.bodies + tuple(bodies), tuple(connections)),
          states + parked)


def parkedFirst(assembly: Assembly = None) -> int:
  """The 'parkedFirst' function returns where the old car's bodies start
  among 'realCarOnOval''s 'assembly' (after the real car's; None: the
  car of parts')."""
  if assembly is not None:
    return len(assembly.bodies) - len(parkedCar()[0].assembly.bodies)
  from ._realcar import HALVES
  return HALVES[1] + 1


def parkedFinishes(assembly: Assembly = None) -> dict:
  """The 'parkedFinishes' function returns how the parked old car's
  bodies are drawn, by their index in 'realCarOnOval''s 'assembly'
  (None: the car of parts' on the oval, 'parkedFirst'): its
  chassis, column and knuckles piece by piece as its own window draws
  them (each key 'old ' and its own: 'PARKED_LOOKS'), its rack steering
  grey, its wheels' rims gold and their tyres rubber (each profile's
  pieces out past the rim's flange)."""
  from ._car import CORNERS, chassisPieces, columnPieces, knucklePieces
  from ._car import TYRE
  car, _ = parkedCar()
  first = parkedFirst(assembly)

  def keyed(pieces: tuple) -> tuple:
    """Returns the old car's pieces (solid, key) as finishes take them
    ((key, solid), each key the old car's own)."""
    return tuple(('old ' + key, solid) for solid, key in pieces)

  out = {first + car.chassis: keyed(chassisPieces()),
         first + car.column: keyed(columnPieces()),
         first + car.rack: 'old steering'}
  for knuckle, (_, side) in zip(car.knuckles, CORNERS):
    out[first + knuckle] = keyed(knucklePieces(side))
  rubberFrom = 0.5 * TYRE.bead + 0.015
  for wheel in car.wheels:
    profile = car.assembly.bodies[wheel].shape.profile
    runs, kind, run = [], None, []
    for piece in profile:
      ends = (piece[1], piece[2]) if piece[0] == 'line' else (
        piece[1], piece[1])
      tyre = min(ends[0][0], ends[1][0]) >= rubberFrom
      now = 'old rubber' if tyre else 'old rim'
      if now != kind and run:
        runs.append((kind, tuple(run)))
        run = []
      kind = now
      run.append(piece)
    if run:
      runs.append((kind, tuple(run)))
    out[first + wheel] = tuple(runs)
  return out
