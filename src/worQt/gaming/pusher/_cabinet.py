"""
Cabinet is the shape of a two-level coin pusher, in mm and s: the table,
the pusher whose top is the shelf, the back wall over it, the side walls,
the chutes either side and the tray in front.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._coin import Coin
from ._coin_world import Box, Edge

#  The boxes 'boxes' returns, by index
TABLE, PUSHER, BACK_WALL = 0, 1, 2
LEFT_WALL, RIGHT_WALL = 3, 4
TRAY, TRAY_FRONT = 5, 6
LEFT_RAMP, RIGHT_RAMP = 7, 8
LEFT_RAIL, RIGHT_RAIL = 9, 10
#  The edges 'edges' returns, by index
TABLE_EDGE, SHELF_EDGE = 0, 1


class Cabinet(NamedTuple):
  """
  Cabinet is a two-level coin pusher, in mm and s: x across from the
  middle toward the player's left, y forward from the back wall toward
  the player, z up from the table (so the three turn as the right hand
  does). The table
  is 'width' wide between the side walls, its front edge 'front' out.
  The pusher is a block as wide, 'shelf' tall, its front face at
  'retracted' when back and 'stroke' further out at most, out and back
  in 'period'; its top is the upper level, the shelf. The back wall
  stands over the shelf 'clearance' above it, so a coin on the shelf
  meets it as the pusher draws back and is pushed off the shelf's front.
  Coins come in by the chute on either side: a brass ramp along the
  back wall, 'slope' degrees down from the side wall toward the middle,
  between the back wall and a rail. A coin slides down it lying and off
  its end onto the back of the shelf, behind the coins there, so it
  lands lying, never on its edge, and the back wall pushes it on. What
  passes the front edge falls
  into the tray, 'drop' below the table, to the player. The table is a
  solid block down to the tray's floor, and the walls stand 'height'
  over the table and run down past the tray: nothing leaves but over
  the front edge, and nothing falls anywhere but into the tray.
  """

  width: float = 360.0
  front: float = 300.0
  shelf: float = 30.0
  retracted: float = 110.0
  stroke: float = 70.0
  period: float = 4.0
  clearance: float = 0.6
  drop: float = 120.0
  height: float = 130.0
  slope: float = 30.0
  coin: Coin = Coin()

  def faceAt(self, time: float) -> float:
    """The 'faceAt' method returns where the pusher's front face is at
    'time': back at nought, out half a period later."""
    turn = 2.0 * math.pi * time / self.period
    return self.retracted + 0.5 * self.stroke * (1.0 - math.cos(turn))

  def speedAt(self, time: float) -> float:
    """The 'speedAt' method returns how fast the pusher moves out at
    'time', in mm/s; going back is below nought."""
    turn = 2.0 * math.pi * time / self.period
    return math.pi * self.stroke / self.period * math.sin(turn)

  def length(self, ) -> float:
    """The 'length' method returns how long the pusher block is, front
    to back: long enough to stay under the back wall at full stroke."""
    return self.retracted + self.stroke + 60.0

  def pusherAt(self, time: float) -> Box:
    """The 'pusherAt' method returns the pusher's block at 'time'."""
    long = self.length()
    face = self.faceAt(time)
    return Box((0.0, face - long / 2.0, self.shelf / 2.0 + 0.1),
               (self.width / 2.0 - 0.3, long / 2.0, self.shelf / 2.0 - 0.1))

  def chuteY(self, ) -> float:
    """The 'chuteY' method returns how far in front of the back wall the
    middle of the chutes runs: half a chute and a little."""
    return self.chuteWidth() / 2.0 + 4.0

  def chuteWidth(self, ) -> float:
    """The 'chuteWidth' method returns how wide a chute is between the
    back wall and its rail."""
    return 2.0 * self.coin.radius + 4.0

  def rampLine(self, side: int) -> tuple[tuple[float, float],
                                         tuple[float, float], float]:
    """The 'rampLine' method returns where the top of the ramp on 'side',
    -1 the player's left or 1 the right, runs from and to, (x, z) at its
    upper end by the side wall and at its lower end toward the middle,
    and how long it is: 'slope' degrees down along the back wall."""
    turn = math.radians(self.slope)
    long = 75.0
    upper = (-side * (self.width / 2.0 - 2.0), self.shelf + 75.0)
    lower = (upper[0] + side * long * math.cos(turn),
             upper[1] - long * math.sin(turn))
    return upper, lower, long

  def rampNormal(self, side: int) -> tuple[float, float, float]:
    """The 'rampNormal' method returns which way the top of the ramp on
    'side' faces: up, leaning toward the middle."""
    turn = math.radians(self.slope)
    return side * math.sin(turn), 0.0, math.cos(turn)

  def rampTurn(self, side: int) -> tuple[float, float, float, float]:
    """The 'rampTurn' method returns how the ramp on 'side', and a coin
    lying on it, is turned: tipped 'slope' degrees about y, its top
    facing toward the middle."""
    half = side * math.radians(self.slope) / 2.0
    return 0.0, math.sin(half), 0.0, math.cos(half)

  def rampStart(self, side: int) -> tuple[float, float, float]:
    """The 'rampStart' method returns where a coin dropped down the chute
    on 'side' starts: lying on the ramp's top, a little below its upper
    end."""
    turn = math.radians(self.slope)
    (x0, z0), _, _ = self.rampLine(side)
    along = self.coin.radius + 3.0
    nx, _, nz = self.rampNormal(side)
    up = self.coin.half + 0.05
    return (x0 + side * along * math.cos(turn) + up * nx, self.chuteY(),
            z0 - along * math.sin(turn) + up * nz)

  def ramp(self, side: int) -> Box:
    """The 'ramp' method returns the ramp of the chute on 'side': a brass
    plate 3 mm thick along the back wall, its top on 'rampLine'."""
    (x0, z0), (x1, z1), long = self.rampLine(side)
    nx, _, nz = self.rampNormal(side)
    middle = ((x0 + x1) / 2.0 - 1.5 * nx, self.chuteY(),
              (z0 + z1) / 2.0 - 1.5 * nz)
    return Box(middle, (long / 2.0, self.chuteWidth() / 2.0, 1.5),
               self.rampTurn(side))

  def rail(self, side: int) -> Box:
    """The 'rail' method returns the rail keeping a coin on the ramp on
    'side', between it and the player: a brass plate along the ramp,
    from the side wall to its lower end, ending above the coins on the
    shelf."""
    (x0, z0), (x1, z1), _ = self.rampLine(side)
    y = self.chuteY() + self.chuteWidth() / 2.0 + 0.5
    inner, outer = x1 - side * 4.0, -side * self.width / 2.0
    low, high = z1 - 4.0, z0 + 20.0
    return Box(((inner + outer) / 2.0, y, (low + high) / 2.0),
               (abs(outer - inner) / 2.0, 0.5, (high - low) / 2.0))

  def boxes(self, ) -> tuple[Box, ...]:
    """The 'boxes' method returns the cabinet's boxes, the pusher at
    time nought, in the order of 'TABLE', 'PUSHER', 'BACK_WALL',
    'LEFT_WALL', 'RIGHT_WALL', 'TRAY', 'TRAY_FRONT', 'LEFT_RAMP',
    'RIGHT_RAMP', 'LEFT_RAIL' and 'RIGHT_RAIL'."""
    w, front, shelf = self.width, self.front, self.shelf
    long = self.length()
    back = -long - 20.0
    tray = 120.0
    out = front + tray
    deep = self.drop + 20.0
    table = Box((0.0, (back + front) / 2.0, -deep / 2.0),
                (w / 2.0, (front - back) / 2.0, deep / 2.0))
    top = shelf + self.clearance
    wall = Box((0.0, (back - 1.0) / 2.0, (top + self.height) / 2.0),
               (w / 2.0, (-back + 1.0) / 2.0, (self.height - top) / 2.0))
    low = -self.drop - 30.0
    sides = (low + self.height) / 2.0, (self.height - low) / 2.0
    left = Box((w / 2.0 + 10.0, (back + out) / 2.0, sides[0]),
               (10.0, (out - back) / 2.0, sides[1]))
    right = Box((-w / 2.0 - 10.0, (back + out) / 2.0, sides[0]),
                (10.0, (out - back) / 2.0, sides[1]))
    floor = Box((0.0, front + tray / 2.0, -self.drop - 10.0),
                (w / 2.0, tray / 2.0, 10.0))
    lip = Box((0.0, out + 5.0, -self.drop + 20.0), (w / 2.0, 5.0, 40.0))
    return (table, self.pusherAt(0.0), wall, left, right, floor, lip,
            self.ramp(-1), self.ramp(1), self.rail(-1), self.rail(1))

  def edges(self, ) -> tuple[Edge, ...]:
    """The 'edges' method returns the edges a coin's face may lie over,
    as at time nought: the table's front, 'TABLE_EDGE', and the shelf's
    front, 'SHELF_EDGE'."""
    half = self.width / 2.0
    face = self.faceAt(0.0)
    return (Edge((-half, self.front, -0.05), (half, self.front, -0.05)),
            Edge((-half, face, self.shelf - 0.05),
                 (half, face, self.shelf - 0.05)))
