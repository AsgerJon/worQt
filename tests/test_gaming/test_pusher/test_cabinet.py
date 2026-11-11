"""
TestCabinet covers 'Cabinet', the two-level coin pusher's shape: the
pusher back at nought, out half a period later, back again a period on,
its speed the rate its face moves at; its block reaching under the back
wall at full stroke; the back wall over the shelf by less than a coin's
thickness; the chutes, ramps between the side walls and their rails, a
coin wide, ending over the shelf above a coin standing there; the table
solid down to the tray, the walls past it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.pusher import Cabinet
from worQt.gaming.pusher._cabinet import BACK_WALL, LEFT_RAIL, LEFT_RAMP
from worQt.gaming.pusher._cabinet import LEFT_WALL, RIGHT_RAIL, RIGHT_RAMP
from worQt.gaming.pusher._cabinet import RIGHT_WALL, TABLE, TRAY

from . import PusherTest


class TestCabinet(PusherTest):
  """Tests for 'Cabinet'."""

  def test_stroke(self) -> None:
    """The face is back at nought and after a period, a stroke out half
    a period in, never past either."""
    cabinet = Cabinet()
    back = cabinet.retracted
    self.assertAlmostEqual(cabinet.faceAt(0.0), back, 12)
    self.assertAlmostEqual(cabinet.faceAt(cabinet.period / 2.0),
                           back + cabinet.stroke, 12)
    self.assertAlmostEqual(cabinet.faceAt(cabinet.period), back, 9)
    for k in range(50):
      face = cabinet.faceAt(0.13 * k)
      self.assertGreaterEqual(face, back - 1e-9)
      self.assertLessEqual(face, back + cabinet.stroke + 1e-9)

  def test_speed(self) -> None:
    """The speed is how fast the face moves, out going forward."""
    cabinet = Cabinet()
    step = 1e-6
    for k in range(12):
      time = 0.29 * k
      moved = cabinet.faceAt(time + step) - cabinet.faceAt(time - step)
      self.assertAlmostEqual(cabinet.speedAt(time), moved / (2 * step), 4)
    self.assertGreater(cabinet.speedAt(cabinet.period / 4.0), 0.0)

  def test_block(self) -> None:
    """At full stroke the pusher's block still reaches under the back
    wall; its top is the shelf."""
    cabinet = Cabinet()
    for time in (0.0, cabinet.period / 2.0):
      block = cabinet.pusherAt(time)
      self.assertLess(block.centre[1] - block.half[1], -10.0)
      self.assertAlmostEqual(block.centre[1] + block.half[1],
                             cabinet.faceAt(time), 9)
      self.assertAlmostEqual(block.centre[2] + block.half[2], cabinet.shelf,
                             9)

  def test_back_wall(self) -> None:
    """The back wall stands over the shelf by less than a coin's
    thickness, its face at nought."""
    cabinet = Cabinet()
    wall = cabinet.boxes()[BACK_WALL]
    gap = wall.centre[2] - wall.half[2] - cabinet.shelf
    self.assertGreater(gap, 0.0)
    self.assertLess(gap, 2.0 * cabinet.coin.half)
    self.assertAlmostEqual(wall.centre[1] + wall.half[1], 0.0, 9)

  def test_chutes(self) -> None:
    """Each chute is a ramp 'slope' degrees down toward the player,
    between the side wall and a rail, a coin wide and a little; the left
    one, side -1, on the player's left (toward x). A coin starts lying
    on the ramp; the ramp ends over the shelf, above a coin standing
    there, and before the shelf's front with the pusher back."""
    cabinet = Cabinet()
    boxes = cabinet.boxes()
    coin = cabinet.coin
    (y0, z0), (y1, z1), long = cabinet.rampLine()
    self.assertAlmostEqual(math.degrees(math.atan2(z0 - z1, y1 - y0)),
                           cabinet.slope, 9)
    self.assertGreater(y0, 0.0)
    self.assertLess(y1, cabinet.retracted)
    self.assertGreater(z1, cabinet.shelf + 2.0 * coin.radius)
    for side, ramp, rail, wall in ((-1, LEFT_RAMP, LEFT_RAIL, LEFT_WALL),
                                   (1, RIGHT_RAMP, RIGHT_RAIL, RIGHT_WALL)):
      self.assertGreater(-side * cabinet.chuteX(side), 0.0)
      inner = boxes[wall].centre[0] + side * boxes[wall].half[0]
      near = boxes[rail].centre[0] - side * boxes[rail].half[0]
      self.assertGreater(abs(inner - near), 2.0 * coin.radius)
      self.assertLess(abs(inner - near), 2.0 * coin.radius + 6.0)
      self.assertAlmostEqual(cabinet.chuteX(side), boxes[ramp].centre[0], 9)
      self.assertEqual(boxes[ramp].turn, cabinet.rampTurn())
      start = cabinet.rampStart(side)
      turn = math.radians(cabinet.slope)
      normal = (math.sin(turn), math.cos(turn))
      above = ((start[1] - y0) * normal[0] + (start[2] - z0) * normal[1])
      self.assertAlmostEqual(above, coin.half + 0.05, 9)
      rail = boxes[rail]
      self.assertGreater(rail.centre[2] - rail.half[2],
                         cabinet.shelf + 2.0 * coin.radius)

  def test_closed(self) -> None:
    """The table is solid down to the tray's floor, and the side walls
    run past the tray and the back."""
    cabinet = Cabinet()
    boxes = cabinet.boxes()
    table, tray = boxes[TABLE], boxes[TRAY]
    self.assertAlmostEqual(table.centre[2] + table.half[2], 0.0, 9)
    self.assertLessEqual(table.centre[2] - table.half[2],
                         tray.centre[2] + tray.half[2])
    self.assertAlmostEqual(table.centre[1] + table.half[1], cabinet.front,
                           9)
    for wall in (boxes[LEFT_WALL], boxes[RIGHT_WALL]):
      self.assertLess(wall.centre[2] - wall.half[2],
                      tray.centre[2] - tray.half[2])
      self.assertGreater(wall.centre[1] + wall.half[1],
                         tray.centre[1] + tray.half[1])
      self.assertLess(wall.centre[1] - wall.half[1],
                      table.centre[1] - table.half[1] + 1.0)
