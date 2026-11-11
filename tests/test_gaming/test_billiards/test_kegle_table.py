"""
TestKegleTable covers 'KegleTable', the keglebillard table as DDBU's
material rules have it: the carom match table with 80 mm pockets; five
pins alike, 120 mm tall, 14 mm across the foot, about ten grams, in a
cross in the middle, 82 mm apart, 68 mm between the feet, so a ball
passes between two with a few mm to spare; a pin standing counts as
knocked over unless its foot lies wholly inside its ring; the layout
spots a quarter
of the length from either short cushion; the baulk line through the
nearer; red in hand within a quarter of either short cushion, its
middle past the quarter line; the opening, the whites on the spots,
red in hand as if it had just gone into a pocket, at either end (the
user); a pocketed white back on
the spot opposite the other, or opposite red with the other on the
middle line, the player told when red lies there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import Ball, CaromTable, KegleTable

from . import BilliardsTest

TABLE = KegleTable()
CAROM = CaromTable()


class TestKegleTable(BilliardsTest):
  """Tests for 'KegleTable'."""

  def test_measures(self) -> None:
    """The carom match table, the noses 37 mm up, 80 mm pockets, pins
    120 mm tall, 14 mm across the foot, ten and a half grams."""
    self.assertEqual(TABLE.table, CAROM)
    self.assertEqual((CAROM.length, CAROM.width, CAROM.nose),
                     (2840.0, 1420.0, 37.0))
    self.assertEqual(TABLE.pocket, 80.0)
    holes = TABLE.holes()
    self.assertEqual(len(holes), 6)
    x, y = holes[4]
    self.assertAlmostEqual(x + 0.5 * TABLE.pocket, 29.0, 9)
    self.assertEqual(y, 1420.0)
    self.assertEqual((TABLE.pinHeight, TABLE.pinFoot), (120.0, 14.0))
    self.assertTrue(10.0 <= TABLE.pinMass <= 11.0)

  def test_pins(self) -> None:
    """Five pins in a cross, the middle one first, in the middle of the
    table, the others 82 mm from it along and across, 68 mm between the
    feet; a ball passes between two with a few mm to spare."""
    spots = TABLE.pinSpots()
    self.assertEqual(len(spots), 5)
    self.assertEqual(spots[0], (710.0, 1420.0))
    for x, y in spots[1:]:
      self.assertAlmostEqual(math.hypot(x - 710.0, y - 1420.0), 82.0, 9)
      self.assertTrue(x == 710.0 or y == 1420.0)
    gap = TABLE.pinApart - TABLE.pinFoot
    self.assertAlmostEqual(gap, 68.0, 9)
    self.assertGreater(gap, 2.0 * CAROM.radius)
    self.assertLess(gap - 2.0 * CAROM.radius, 10.0)

  def test_ring(self) -> None:
    """A pin counts as standing only upright with its foot wholly
    inside its ring; nudged so the foot leaves the ring, or fallen, it
    counts as knocked over."""
    x, y = TABLE.pinSpots()[3]
    slack = 0.5 * (TABLE.ring - TABLE.pinFoot)
    self.assertGreater(slack, 0.0)
    self.assertTrue(TABLE.pinStands(3, x, y, True))
    self.assertTrue(TABLE.pinStands(3, x + 0.9 * slack, y, True))
    self.assertFalse(TABLE.pinStands(3, x + 1.1 * slack, y, True))
    self.assertFalse(TABLE.pinStands(3, x, y, False))
    self.assertFalse(TABLE.pinStands(0, x, y, True))

  def test_spots_and_line(self) -> None:
    """The layout spots lie on the long middle line a quarter of the
    length from either short cushion; the baulk line runs through the
    nearer; red lies in hand with its middle on it or past it, and as
    well on or past the twin line at the foot, on the cloth (9.4)."""
    self.assertEqual(TABLE.spots(), ((710.0, 710.0), (710.0, 2130.0)))
    line = TABLE.salvoLine()
    self.assertEqual(line, 2130.0)
    self.assertTrue(TABLE.inHand(400.0, line))
    self.assertTrue(TABLE.inHand(400.0, line + 1.0))
    self.assertFalse(TABLE.inHand(400.0, line - 1.0))
    self.assertTrue(TABLE.inHand(400.0, 709.0))
    self.assertFalse(TABLE.inHand(400.0, 1420.0))
    self.assertFalse(TABLE.inHand(10.0, line + 100.0))
    self.assertTrue(TABLE.farHalf(1000.0))
    self.assertFalse(TABLE.farHalf(1500.0))

  def test_in_hand_ends(self) -> None:
    """Red put down by hand lies within a quarter of the length of the
    head or the foot cushion, its middle past the quarter line."""
    self.assertEqual(TABLE.inHandEnd(400.0, 2500.0), 1)
    self.assertEqual(TABLE.inHandEnd(400.0, 300.0), -1)
    self.assertEqual(TABLE.inHandEnd(400.0, 1420.0), 0)
    self.assertEqual(TABLE.inHandEnd(400.0, 711.0), 0)
    self.assertEqual(TABLE.inHandEnd(400.0, 710.0), -1)
    self.assertEqual(TABLE.inHandEnd(5.0, 300.0), 0)

  def test_pins_placed(self) -> None:
    """A pin is set up only where it stands clear of every ball; one a
    ball would touch waits."""
    balls = TABLE.opening()
    self.assertEqual(TABLE.pinsPlaced(balls), (0, 1, 2, 3, 4))
    x, y = TABLE.pinSpots()[2]
    reach = CAROM.radius + 0.5 * TABLE.pinBody
    near = balls[:2] + (Ball('red', x + reach - 0.5, y),)
    self.assertEqual(TABLE.pinsPlaced(near), (0, 1, 3, 4))
    clear = balls[:2] + (Ball('red', x + reach + 0.5, y),)
    self.assertEqual(TABLE.pinsPlaced(clear), (0, 1, 2, 3, 4))

  def test_opening(self) -> None:
    """At the start the whites lie on the layout spots, red in hand as
    if it had just gone into a pocket (the user), where the player puts
    it, by default on the head string beside the head spot, a ball's
    width further out than three-cushion's breaker on spot 4 (the
    user); at the foot end as well."""
    white, yellow, red = TABLE.opening()
    self.assertEqual((white.x, white.y), (710.0, 2130.0))
    self.assertEqual((yellow.x, yellow.y), (710.0, 710.0))
    self.assertEqual(red.name, 'red')
    self.assertEqual(TABLE.inHandEnd(red.x, red.y), 1)
    breaker = CAROM.spot(4)
    self.assertEqual((red.x, red.y),
                     (breaker[0] + 2.0 * CAROM.radius, breaker[1]))
    for x, y in ((300.0, 2500.0), (1000.0, 300.0)):
      placed = TABLE.opening(x, y)[2]
      self.assertEqual((placed.x, placed.y), (x, y))
      self.assertTrue(TABLE.inHand(placed.x, placed.y))

  def test_pockets(self) -> None:
    """The cushions are cut away over the pockets: over the middle ones
    as wide as the hole where it crosses the noses' line, at the corners
    so a ball fits between the jaws; a ball gone into a pocket is kept
    far off the table, which hole told by where."""
    pockets = TABLE.pockets()
    self.assertAlmostEqual(2.0 * pockets.half, 77.0, 0)
    self.assertGreater(pockets.corner * math.sqrt(2.0),
                       2.0 * CAROM.radius)
    self.assertEqual(pockets.holes, TABLE.holes())
    for hole in range(6):
      ball = Ball('red', *TABLE.parkedAt(hole))
      self.assertEqual(TABLE.pocketOf(ball), hole)
    self.assertEqual(TABLE.pocketOf(Ball('red', 10.0, 10.0)), -1)

  def test_respotted(self) -> None:
    """A pocketed white goes back on the layout spot opposite the other
    white; the other on the middle line, on the spot away from red; red
    on the spot, the player is told."""
    balls = (Ball('white', 0.0, 0.0), Ball('yellow', 400.0, 900.0),
             Ball('red', 1000.0, 2500.0))
    white = TABLE.respotted(balls, 'white')[0]
    self.assertEqual((white.x, white.y), (710.0, 2130.0))
    balls = (Ball('white', 0.0, 0.0), Ball('yellow', 400.0, 2000.0),
             Ball('red', 1000.0, 2500.0))
    self.assertEqual(TABLE.respotted(balls, 'white')[0].y, 710.0)
    balls = (Ball('white', 0.0, 0.0), Ball('yellow', 400.0, 1420.0),
             Ball('red', 1000.0, 2500.0))
    self.assertEqual(TABLE.respotted(balls, 'white')[0].y, 710.0)
    self.assertFalse(TABLE.spotTaken(balls, 'white'))
    balls = (Ball('white', 0.0, 0.0), Ball('yellow', 400.0, 2000.0),
             Ball('red', 730.0, 720.0))
    self.assertTrue(TABLE.spotTaken(balls, 'white'))
