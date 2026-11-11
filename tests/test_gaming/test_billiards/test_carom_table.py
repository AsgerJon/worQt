"""
TestCaromTable covers 'CaromTable', the shape of a three-cushion table:
a match table's sizes; the foot, head and centre spots on the long
middle line; the balls as a game opens, red on the foot spot, yellow on
the head spot, white on the head string 182.5 mm beside it, each turned
its own way; the FFB's spots, 4 on the breaker's left as he faces the
foot from the head, 5 on his right, the lag on the head string 200 mm
from the long cushions; turns as unit quaternions; and the diamonds,
seven a long rail, three a short one, at even steps, 90 mm out from the
noses as the FFB has it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import STILL, Ball, CaromTable, turnOf

from . import BilliardsTest


class TestCaromTable(BilliardsTest):
  """Tests for 'CaromTable'."""

  def test_match_table(self) -> None:
    """A match table: 2840 by 1420 mm between the noses, balls 61.5 mm
    across, the noses 37 mm above the cloth."""
    table = CaromTable()
    self.assertEqual((table.length, table.width), (2840.0, 1420.0))
    self.assertAlmostEqual(2.0 * table.radius, 61.5, 12)
    self.assertEqual(table.nose, 37.0)
    self.assertEqual(table.length, 2.0 * table.width)

  def test_spots(self) -> None:
    """The spots lie on the long middle line: the foot spot a quarter
    of the length from the foot cushion, the head spot as far from the
    head cushion, the centre spot half way."""
    table = CaromTable()
    self.assertEqual(table.footSpot(), (710.0, 710.0))
    self.assertEqual(table.headSpot(), (710.0, 2130.0))
    self.assertEqual(table.centreSpot(), (710.0, 1420.0))
    small = CaromTable(2000.0, 1000.0)
    self.assertEqual(small.footSpot(), (500.0, 500.0))
    self.assertEqual(small.headSpot(), (500.0, 1500.0))

  def test_opening(self) -> None:
    """As a game opens, red lies on the foot spot, yellow on the head
    spot, white on the head string 182.5 mm beside it; all on the
    cloth, none touching another."""
    table = CaromTable()
    white, yellow, red = table.opening()
    self.assertEqual([ball.name for ball in (white, yellow, red)],
                     ['white', 'yellow', 'red'])
    self.assertIsInstance(white, Ball)
    self.assertEqual((red.x, red.y), table.footSpot())
    self.assertEqual((yellow.x, yellow.y), table.headSpot())
    self.assertEqual(white.y, yellow.y)
    self.assertAlmostEqual(white.x - yellow.x, 182.5, 12)
    for ball in (white, yellow, red):
      self.assertGreater(ball.x, table.radius)
      self.assertLess(ball.x, table.width - table.radius)
      self.assertGreater(ball.y, table.radius)
      self.assertLess(ball.y, table.length - table.radius)
    self.assertGreater(white.x - yellow.x, 2.0 * table.radius)

  def test_ffb_spots(self) -> None:
    """The FFB's spots (article 1.3.01) on a 3.10 m table: 1 and 3 71 cm
    from the short cushions, 2 in the middle; 4 and 5 on the head string
    18.25 cm either side of 3, 4 on the left of the breaker standing at
    the head facing the foot, the table's larger 'x', 5 on his right.
    Breaking from spot 5, the cue ball lies there, the others as from
    4. In the lag, white and yellow lie on the head string 20 cm from
    the long cushions, red on spot 1 (article 2.1.01)."""
    table = CaromTable()
    self.assertEqual(table.spot(1), (710.0, 710.0))
    self.assertEqual(table.spot(2), (710.0, 1420.0))
    self.assertEqual(table.spot(3), (710.0, 2840.0 - 710.0))
    self.assertEqual(table.spot(4), (710.0 + 182.5, 2130.0))
    self.assertEqual(table.spot(5), (710.0 - 182.5, 2130.0))
    breakerFacing = (0.0, -1.0)
    left = (-breakerFacing[1], breakerFacing[0])
    four, five = table.spot(4), table.spot(5)
    self.assertGreater((four[0] - 710.0) * left[0], 0.0)
    self.assertLess((five[0] - 710.0) * left[0], 0.0)
    white, yellow, red = table.openingFor('white', 5)
    self.assertEqual((white.x, white.y), table.spot(5))
    self.assertEqual((yellow.x, yellow.y), table.spot(3))
    self.assertEqual((red.x, red.y), table.spot(1))
    white, yellow, red = table.openingFor('yellow', 4)
    self.assertEqual((yellow.x, yellow.y), table.spot(4))
    self.assertEqual((white.x, white.y), table.spot(3))
    white, yellow, red = table.lagPosition()
    self.assertEqual({white.x, yellow.x}, {200.0, 1220.0})
    self.assertEqual((white.y, yellow.y), (2130.0, 2130.0))
    self.assertEqual((red.x, red.y), table.spot(1))

  def test_turns(self) -> None:
    """A ball lies still unless turned; 'turnOf' is the unit quaternion
    of a turn about an axis; the opening's balls lie each turned its own
    way."""
    self.assertEqual(Ball('white', 1.0, 2.0).turn, STILL)
    self.assertEqual(turnOf(0.0, 0.0, 0.0, 1.0), STILL)
    w, x, y, z = turnOf(90.0, 0.0, 0.0, 2.0)
    self.assertAlmostEqual(w, math.sqrt(0.5), 12)
    self.assertAlmostEqual(z, math.sqrt(0.5), 12)
    self.assertEqual((x, y), (0.0, 0.0))
    turns = [ball.turn for ball in CaromTable().opening()]
    for turn in turns:
      self.assertAlmostEqual(sum(part * part for part in turn), 1.0, 12)
      self.assertNotEqual(turn, STILL)
    self.assertEqual(len(set(turns)), 3)

  def test_diamonds(self) -> None:
    """Seven diamonds on each long rail at every eighth of the length,
    three on each short rail at every quarter of the width, their
    middles 90 mm out from the noses (article 1.1.03), on the wood."""
    table = CaromTable()
    diamonds = table.diamonds()
    self.assertEqual(len(diamonds), 20)
    out = table.diamondOut
    self.assertEqual(out, 90.0)
    self.assertGreater(out, table.cushion)
    self.assertLess(out, table.cushion + table.rail)
    left = sorted(y for x, y in diamonds if x == -out)
    right = sorted(y for x, y in diamonds if x == table.width + out)
    foot = sorted(x for x, y in diamonds if y == -out)
    head = sorted(x for x, y in diamonds if y == table.length + out)
    along = [355.0 * k for k in range(1, 8)]
    across = [355.0 * k for k in range(1, 4)]
    for found, wanted in ((left, along), (right, along),
                          (foot, across), (head, across)):
      self.assertEqual(len(found), len(wanted))
      for got, expected in zip(found, wanted):
        self.assertAlmostEqual(got, expected, 9)
