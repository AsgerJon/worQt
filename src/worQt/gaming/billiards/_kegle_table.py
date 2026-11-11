"""
KegleTable is a keglebillard table as Den Danske Billard Union's
material rules have it: the carom match table with six pockets, five
pins standing in a cross in the middle, two layout spots and the baulk
line.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._carom_table import PARKED_BELOW, Ball, CaromTable
from ._motion import Pockets

#  The holes by name, as 'KegleTable.holes' gives them.
HOLE_NAMES = ('foot left', 'foot right', 'head left', 'head right',
              'left middle', 'right middle')
PARKED = -20000.0  # mm: where pocketed balls are kept, far off the table
PARKED_APART = 1000.0  # mm between the places of balls in different holes


class KegleTable(NamedTuple):
  """
  KegleTable is a keglebillard table, in mm, as DDBU's material rules
  for 2026-27 have it (previews/rules): the carom match table, 'table',
  2840 by 1420 between the noses, the noses 37 mm up, the balls 61.5 mm,
  with six pockets ('huller') 'pocket' across, one in each corner and
  one in the middle of each long cushion (bilag G), the cushions cut
  away over them in straight slots ('pockets'); a ball gone into one is
  kept far off the table while the shot goes on ('parkedAt',
  'pocketOf'), the holes named as 'HOLE_NAMES'. The player stands at
  the head, the 'bottom cushion' ('bundbande') at his feet, and plays
  towards the foot, the 'top cushion' ('øverste bande').

  Five pins ('kegler'), all alike, of wood, 'pinHeight' tall, 'pinFoot'
  across the foot, 'pinMass' grams, stand on white spots in a cross in
  the middle of the table, 'pinApart' between the middles of a pin and
  the next (bilag H: 164 mm across, 68 mm between the feet): the middle
  pin first, then those across the table, then those along it. A ball
  passes between two pins with a few mm to spare. The pins stand on
  their spots at the start of every shot. Each spot is a ring drawn
  'ring' across round the foot; a pin still standing counts as knocked
  over unless its foot lies wholly inside its ring (the user; 8.2).

  The two layout spots ('udlægspletter') lie on the long middle line a
  quarter of the length from either short cushion, the foot's first.
  The baulk line ('salvolinien') runs across the table 'salvo', a
  quarter of the length, from the bottom cushion, through the layout
  spot nearer it (bilag I). Red is put down by hand within a quarter of
  the length of
  either short cushion, past the baulk line or past its twin at the
  foot, after it went into a pocket (the user; 9.4), and at the start as
  if it just had (the user; 3.1 has it behind the baulk line only),
  'inHand'. A pin is set up only where it stands
  clear of every ball (8.3, the user): 'pinBody' is its widest, the
  body.
  """

  table: CaromTable = CaromTable()
  pocket: float = 80.0
  pinApart: float = 82.0
  pinHeight: float = 120.0
  pinFoot: float = 14.0
  pinMass: float = 10.5
  salvo: float = 710.0
  ring: float = 18.0
  pinBody: float = 20.0
  holeIn: float = 29.0
  mouth: float = 1.1

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def holes(self, ) -> tuple[tuple[float, float], ...]:
    """The 'holes' method returns the middles of the six holes milled
    into the table (the user: a carom table and a drill), 'pocket'
    across, each reaching 'holeIn' in front of the noses' lines (bilag
    G), its middle as far behind them as that leaves: the four corners,
    foot first, then the middles of the left and right cushions."""
    back = 0.5 * self.pocket - self.holeIn
    width, length = self.table.width, self.table.length
    return ((-back, -back), (width + back, -back),
            (-back, length + back), (width + back, length + back),
            (-back, 0.5 * length), (width + back, 0.5 * length))

  def pockets(self, ) -> Pockets:
    """The 'pockets' method returns the pockets as 'Motion' meets them:
    the cushions cut away over each in a straight slot (the user, after a
    table's photo), over the middle ones as wide as the hole where it
    crosses the noses' line, at the corners far enough back from the
    noses' corner that the mouth between the two jaws is 'mouth' times a
    ball wide (an ASSUMPTION: cut back no further than the hole, no ball
    could reach it); the holes taking a ball whose middle comes over
    them."""
    radius = 0.5 * self.pocket
    back = radius - self.holeIn
    half = math.sqrt(radius * radius - back * back)
    corner = self.mouth * 2.0 * self.table.radius / math.sqrt(2.0)
    return Pockets(max(corner, half - back), half, self.holes(), radius)

  def parkedAt(self, hole: int) -> tuple[float, float]:
    """The 'parkedAt' method returns where a ball gone into hole 'hole',
    by its place in 'holes', is kept while the shot goes on: far off the
    table, where nothing meets it."""
    return PARKED - PARKED_APART * hole, PARKED

  def pocketOf(self, ball: Ball) -> int:
    """The 'pocketOf' method returns the hole 'ball' went into, by its
    place in 'holes', parked ('parkedAt'); -1 for a ball on the
    table."""
    if ball.y >= PARKED_BELOW:
      return -1
    return int(round((PARKED - ball.x) / PARKED_APART))

  def middle(self, ) -> tuple[float, float]:
    """The 'middle' method returns the middle of the cloth, where the
    middle pin stands."""
    return 0.5 * self.table.width, 0.5 * self.table.length

  def pinSpots(self, ) -> tuple[tuple[float, float], ...]:
    """The 'pinSpots' method returns where the five pins stand: the
    middle pin, then the two across the table from it, then the two
    along it, foot side first."""
    x, y = self.middle()
    apart = self.pinApart
    return ((x, y), (x - apart, y), (x + apart, y), (x, y - apart),
            (x, y + apart))

  def pinStands(self, number: int, x: float, y: float,
                upright: bool) -> bool:
    """The 'pinStands' method tells whether pin 'number', its foot's
    middle at 'x', 'y', stands as it was set up: 'upright', on its foot,
    and the foot wholly inside its ring; else it counts as knocked
    over."""
    spotX, spotY = self.pinSpots()[number]
    off = math.hypot(x - spotX, y - spotY)
    return upright and off + 0.5 * self.pinFoot <= 0.5 * self.ring

  def spots(self, ) -> tuple[tuple[float, float], tuple[float, float]]:
    """The 'spots' method returns the two layout spots, the foot's
    first."""
    x, length = 0.5 * self.table.width, self.table.length
    return (x, 0.25 * length), (x, 0.75 * length)

  def salvoLine(self, ) -> float:
    """The 'salvoLine' method returns where the baulk line runs across
    the table, 'y'."""
    return self.table.length - self.salvo

  def inHand(self, x: float, y: float) -> bool:
    """The 'inHand' method tells whether red may be put down by hand
    with its middle at 'x', 'y': on the cloth within a quarter of the
    length of either short cushion, its middle on the quarter line or
    past it, at the start as after it went into a pocket (the user)."""
    return self.inHandEnd(x, y) != 0

  def inHandEnd(self, x: float, y: float) -> int:
    """The 'inHandEnd' method returns the end of the table a ball with
    its middle at 'x', 'y', on the cloth, lies within a quarter of the
    length of, its middle on the quarter line or past it (9.4: the field
    the bottom cushion and the layout line bound): 1 the head, the
    bottom cushion's, -1 the foot, the top cushion's; 0 for neither."""
    radius, table = self.table.radius, self.table
    if not radius <= x <= table.width - radius:
      return 0
    if self.salvoLine() <= y <= table.length - radius:
      return 1
    if radius <= y <= table.length - self.salvoLine():
      return -1
    return 0

  def pinsPlaced(self, balls: tuple) -> tuple[int, ...]:
    """The 'pinsPlaced' method returns the pins set up for a shot with
    'balls' lying so: each that stands clear of every ball, air between
    them; one that would touch a ball waits for a shot to free its spot
    (8.3, the user)."""
    reach = self.table.radius + 0.5 * self.pinBody
    return tuple(k for k, (x, y) in enumerate(self.pinSpots())
                 if all(math.hypot(ball.x - x, ball.y - y) > reach
                        for ball in balls))

  def farHalf(self, y: float) -> bool:
    """The 'farHalf' method tells whether 'y' lies on the half of the
    table away from the player, past the middle."""
    return y < 0.5 * self.table.length

  def opening(self, redX: float = None, redY: float = None) -> tuple:
    """The 'opening' method returns the balls laid out as a game
    starts (3.1): the whites on the layout spots, the marked one,
    'yellow', on the foot's, white on the head's; red in hand, as if it
    had just gone into a pocket (the user), at 'redX', 'redY' within a
    quarter of either short cushion ('inHand'), by default on the head
    string beside the head spot, a ball's width further out than
    three-cushion's breaker on its spot 4 (the user: "another Asger eye
    gap further out")."""
    foot, head = self.spots()
    if redX is None or redY is None:
      redX, redY = self.table.spot(4)
      redX += 2.0 * self.table.radius
    return (Ball('white', *head), Ball('yellow', *foot),
            Ball('red', redX, redY))

  def respotted(self, balls: tuple, name: str) -> tuple:
    """The 'respotted' method returns 'balls' with the white 'name',
    pocketed, back on the layout spot opposite the other white (9.1):
    on the head's if the other lies on the foot's half, else the foot's;
    the other exactly on the middle line, on the spot of the half away
    from red (9.3)."""
    named = {ball.name: ball for ball in balls}
    other = next(ball for ball in balls
                 if ball.name not in (name, 'red'))
    foot, head = self.spots()
    middle = 0.5 * self.table.length
    if other.y == middle:
      spot = foot if named['red'].y > middle else head
    else:
      spot = head if other.y < middle else foot
    return tuple(Ball(name, *spot) if ball.name == name else ball
                 for ball in balls)

  def spotTaken(self, balls: tuple, name: str) -> bool:
    """The 'spotTaken' method tells whether red lies where the white
    'name' would be respotted, so the player may ask for a new layout
    (9.1)."""
    placed = {ball.name: ball for ball in self.respotted(balls, name)}
    white, red = placed[name], placed['red']
    apart = math.hypot(white.x - red.x, white.y - red.y)
    return apart < 2.0 * self.table.radius
