"""
CaromTable is the shape of a three-cushion table, a carom table without
pockets, and Ball a ball on it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

Turn = tuple[float, float, float, float]
STILL: Turn = (1.0, 0.0, 0.0, 0.0)
#  mm: a ball this far below the table's foot is off it, gone into a
#  pocket and kept there ('KegleTable.parkedAt'), out of play.
PARKED_BELOW = -10000.0


def isParked(x: float, y: float) -> bool:
  """The 'isParked' function tells whether a ball with its middle at 'x',
  'y' is off the table, gone into a pocket and kept far off it."""
  return y < PARKED_BELOW


def turnOf(degrees: float, x: float, y: float, z: float) -> Turn:
  """The 'turnOf' function returns the turn by 'degrees' about the axis
  'x', 'y', 'z' as the table has them, a unit quaternion: its scalar
  first, then its vector."""
  length = math.sqrt(x * x + y * y + z * z)
  half = 0.5 * math.radians(degrees)
  share = math.sin(half) / length
  return math.cos(half), x * share, y * share, z * share


class Ball(NamedTuple):
  """
  Ball is a ball on a carom table, a rigid sphere on the cloth: its
  'name', 'white', 'yellow' or 'red'; where its middle is, 'x' and 'y'
  in mm as the table has them; how it is turned, 'turn', a unit
  quaternion, its scalar first; how fast it moves, 'vx' and 'vy' in
  mm/s; how fast it spins, 'wx', 'wy' and 'wz' in rad/s about the
  table's axes, 'wz' about the vertical, the side spin; and whether it
  is 'settling', its roll over, rolling back the little the felt pushes
  it as it comes to rest, which it does once until struck or hit again.

  A sphere rolls the same however it is turned, so the physics need not
  know; but the balls carry dots, and the dots show it.
  """

  name: str
  x: float
  y: float
  turn: Turn = STILL
  vx: float = 0.0
  vy: float = 0.0
  wx: float = 0.0
  wy: float = 0.0
  wz: float = 0.0
  settling: bool = False


class CaromTable(NamedTuple):
  """
  CaromTable is the shape of a three-cushion table, in mm, seen from
  above: 'x' across from the nose of the left cushion, 'y' along from
  the nose of the foot cushion; the cloth at height nought.

  The cloth between the cushions' noses is 'length' by 'width', a match
  table's 2840 by 1420 mm. Its balls are of 'radius' 30.75 mm, 61.5 mm
  across. The cushions meet a ball at their nose, 'nose' above the
  cloth, 37 mm as the UMB has it, and reach 'cushion' back to the
  wooden rail, 'rail' wide on top; the cushions' and rails' tops are
  'top' above the cloth. The cloth lies 'bed' above the floor. The
  diamonds' middles are 'diamondOut' out from the noses, 90 mm as the
  FFB has it (Code sportif, article 1.1.03).

  The foot spot, where the red ball starts, lies on the long middle line
  a quarter of the length from the foot cushion; the head spot as far
  from the head cushion; the head string runs across through it. At the
  opening the opponent's ball lies on the head spot and the starting
  player's ball on the head string 'apart' to the side, 182.5 mm. As the
  FFB draws the spots (article 1.3.01), the foot spot is its spot 1, the
  head spot its 3, the breaker standing at the head facing the foot:
  spot 4 is on his left, the table's larger 'x', spot 5 on his right.
  """

  length: float = 2840.0
  width: float = 1420.0
  radius: float = 30.75
  nose: float = 37.0
  cushion: float = 50.0
  rail: float = 130.0
  bed: float = 800.0
  apart: float = 182.5
  top: float = 45.0
  diamondOut: float = 90.0

  def footSpot(self, ) -> tuple[float, float]:
    """The 'footSpot' method returns the foot spot, where the red ball
    starts."""
    return 0.5 * self.width, 0.25 * self.length

  def headSpot(self, ) -> tuple[float, float]:
    """The 'headSpot' method returns the head spot, where the
    opponent's ball starts."""
    return 0.5 * self.width, 0.75 * self.length

  def centreSpot(self, ) -> tuple[float, float]:
    """The 'centreSpot' method returns the middle of the cloth."""
    return 0.5 * self.width, 0.5 * self.length

  def spot(self, number: int) -> tuple[float, float]:
    """The 'spot' method returns where spot 'number' is, as the FFB
    numbers them (Code sportif, article 1.3.01): 1 the foot spot, red's;
    2 the middle; 3 the head spot; 4 and 5 on the head string, 'apart'
    either side of spot 3."""
    middle = 0.5 * self.width
    places = {1: self.footSpot(), 2: self.centreSpot(), 3: self.headSpot(),
              4: (middle + self.apart, 0.75 * self.length),
              5: (middle - self.apart, 0.75 * self.length)}
    return places[number]

  def opening(self, ) -> tuple[Ball, Ball, Ball]:
    """The 'opening' method returns the balls as a game opens, white
    breaking from spot 4 (article 2.2.03)."""
    return self.openingFor('white', 4)

  def openingFor(self, cue: str, number: int) -> tuple[Ball, Ball, Ball]:
    """The 'openingFor' method returns the balls, 'white', 'yellow',
    'red', as the player of 'cue' breaks (article 2.2.03): the cue ball
    on spot 'number', 4 or 5 as the player chooses; red on spot 1; the
    other ball on spot 3. Each lies turned its own way, as a hand put it
    there."""
    other = 'yellow' if cue == 'white' else 'white'
    places = {cue: self.spot(number), other: self.spot(3),
              'red': self.spot(1)}
    return self._laid(places)

  def lagPosition(self, ) -> tuple[Ball, Ball, Ball]:
    """The 'lagPosition' method returns the balls as the players lag
    for the break (article 2.1.01): red on spot 1, white and yellow on
    the head string, 200 mm from the long cushions either side."""
    line = 0.75 * self.length
    return self._laid({'white': (self.width - 200.0, line),
                       'yellow': (200.0, line), 'red': self.spot(1)})

  def respotted(self, balls: tuple, cue: str,
                concerned: tuple[str, ...]) -> tuple:
    """The 'respotted' method returns 'balls' with only those
    'concerned' put back on their spots, still, as the FFB has it for
    three-cushion (article 2.2.07-E): the cue ball, of the player about to
    play, on spot 3; red on spot 1; the other ball on spot 2. A ball whose
    spot is taken goes on the spot of the ball taking it; failing that,
    on the first free spot."""
    other = 'yellow' if cue == 'white' else 'white'
    spots = {cue: 3, 'red': 1, other: 2}
    placed = {ball.name: ball for ball in balls}
    for name in concerned:
      ball = placed[name]
      number = spots[name]
      taker = self._takerOf(placed, name, self.spot(number))
      if taker is not None:
        number = spots[taker]
        if self._takerOf(placed, name, self.spot(number)) is not None:
          number = next(k for k in (1, 2, 3, 4, 5)
                        if self._takerOf(placed, name, self.spot(k)) is None)
      x, y = self.spot(number)
      placed[name] = Ball(name, x, y, ball.turn)
    return tuple(placed[ball.name] for ball in balls)

  def diamonds(self, ) -> tuple[tuple[float, float], ...]:
    """The 'diamonds' method returns the diamonds on the rails' tops,
    each where it is, 'x' and 'y': on the middle of each rail, seven on
    each long rail at every eighth of the length, three on each short
    rail at every quarter of the width, lined up with the noses,
    'diamondOut' out from them."""
    out = self.diamondOut
    left, right = -out, self.width + out
    foot, head = -out, self.length + out
    along = [self.length * k / 8.0 for k in range(1, 8)]
    across = [self.width * k / 4.0 for k in range(1, 4)]
    return (*[(left, y) for y in along],
            *[(right, y) for y in along],
            *[(x, foot) for x in across],
            *[(x, head) for x in across])

  def _laid(self, places: dict) -> tuple[Ball, Ball, Ball]:
    """Returns white, yellow and red laid still where 'places' says,
    each turned its own way, as a hand put it there."""
    turns = {'white': turnOf(28.0, 1.0, 2.0, 0.5),
             'yellow': turnOf(41.0, -1.0, 0.5, 1.0),
             'red': turnOf(17.0, 2.0, -1.0, 1.0)}
    return tuple(Ball(name, *places[name], turns[name])
                 for name in ('white', 'yellow', 'red'))

  def _takerOf(self, placed: dict, name: str,
               where: tuple[float, float]) -> str | None:
    """Returns the name of a ball, other than 'name', lying too near
    'where' for a ball to be put there; 'None' if none does."""
    for other, ball in placed.items():
      if other == name:
        continue
      apart = math.hypot(ball.x - where[0], ball.y - where[1])
      if apart < 2.0 * self.radius:
        return other
    return None
