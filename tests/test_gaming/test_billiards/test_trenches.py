"""
TestTrenches covers 'Trenches', the ways ball 1 and ball 2 go as a shot
sends them, and 'trenchMesh', the trench drawn: a soft shot on open
cloth stops where the cloth brings the ball to rest, with follow, draw
or English too; a hard one ends touching the cushion; one aimed at a
ball ends touching it, and that ball sets off along the line of their
middles, as far as the cloth lets it go at the speed it is given; ball
1 goes on from the hit square to that line and, rolling into a half-ball
hit, bends to leave some 30 degrees off the aim, as the user's rule has
it; struck full rolling, it follows on along the line; aimed past a
ball, it is not met; the trench is a band a ball wide, ending round.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.billiards import STILL, Ball, CaromTable, Cloth, Cue
from worQt.gaming.billiards import Trenches, trenchMesh

from . import BilliardsTest

TABLE = CaromTable()
RADIUS = TABLE.radius
#  The cloth as the trenches have it: the felt's roll back at rest left
#  out, a mm and a half the trench does not show.
CLOTH = Cloth(*Cloth()[:4], 0.0, *Cloth()[5:])
TRENCHES = Trenches(TABLE, CLOTH, Cue())
OPENING = TABLE.opening()
WHITE, RED = OPENING[0], OPENING[2]


def wayOf(start: tuple, end: tuple) -> tuple[float, float]:
  """The way from 'start' to 'end', of length one."""
  dx, dy = end[0] - start[0], end[1] - start[1]
  size = math.hypot(dx, dy)
  return dx / size, dy / size


def restOf(ball: Ball) -> Ball:
  """'ball' at rest on the cloth, a minute on."""
  return CLOTH.advanced(ball, 60.0, RADIUS)


def speedAt(ball: Ball, distance: float) -> float:
  """How fast 'ball', going along +x or -x, goes as it has come
  'distance' from where it is, by halving the time."""
  low, high = 0.0, 60.0
  for _ in range(80):
    middle = 0.5 * (low + high)
    moved = CLOTH.advanced(ball, middle, RADIUS)
    gone = math.hypot(moved.x - ball.x, moved.y - ball.y)
    low, high = (middle, high) if gone < distance else (low, middle)
  moved = CLOTH.advanced(ball, low, RADIUS)
  return math.hypot(moved.vx, moved.vy)


class TestTrenches(BilliardsTest):
  """Tests for 'Trenches' and 'trenchMesh'."""

  def test_stops(self) -> None:
    """A soft shot along the head string into open cloth stops where
    the cloth brings it to rest: plain, with follow, draw and English."""
    for top, side in ((0.0, 0.0), (0.4, 0.0), (-0.4, 0.0), (0.0, 0.4)):
      trenches = TRENCHES.trenchesOf(OPENING, 'white', 1.0, 0.0, 250.0,
                                     top, side)
      self.assertEqual(len(trenches), 1)
      trench = trenches[0]
      self.assertEqual((trench.name, trench.end), ('white', 'stop'))
      sent = Cue().sent(WHITE, 1.0, 0.0, 250.0, top, side, RADIUS)
      rest = restOf(sent)
      self.assertAlmostEqual(trench.distance(), rest.x - WHITE.x, 6)

  def test_cushion(self) -> None:
    """A hard shot along the head string ends as the ball touches the
    right cushion's nose, its middle as far in from the nose line as
    the nose is from it."""
    trench, = TRENCHES.trenchesOf(OPENING, 'white', 1.0, 0.0, 4000.0,
                                  0.0, 0.0)
    self.assertEqual(trench.end, 'cushion')
    inside = math.sqrt(RADIUS ** 2 - (TABLE.nose - RADIUS) ** 2)
    x, y = trench.endPlace()
    self.assertAlmostEqual(x, TABLE.width - inside, 6)
    self.assertAlmostEqual(y, WHITE.y, 6)

  def test_meets_ball(self) -> None:
    """Aimed half a radius past red's middle, the trench ends where the
    cue ball touches red, and red's sets off from red along the line of
    their middles then."""
    aimX, aimY = RED.x + 0.5 * RADIUS - WHITE.x, RED.y - WHITE.y
    first, second = TRENCHES.trenchesOf(OPENING, 'white', aimX, aimY,
                                         2000.0, 0.0, 0.0)[:2]
    self.assertEqual((first.end, first.met), ('ball', 'red'))
    gx, gy = first.endPlace()
    self.assertAlmostEqual(math.hypot(RED.x - gx, RED.y - gy),
                           2.0 * RADIUS, 6)
    self.assertEqual(second.name, 'red')
    self.assertEqual(second.startPlace(), (RED.x, RED.y))
    dx, dy = wayOf(second.points[0], second.points[1])
    self.assertAlmostEqual(dx, (RED.x - gx) / (2.0 * RADIUS), 9)
    self.assertAlmostEqual(dy, (RED.y - gy) / (2.0 * RADIUS), 9)

  def test_ball_two_stops(self) -> None:
    """Red struck full and softly from close by stops where the cloth
    brings a ball to rest that sets off, without spin, as fast as the
    cue ball came."""
    white = Ball('white', RED.x, RED.y + 400.0)
    balls = (white, OPENING[1], RED)
    first, second = TRENCHES.trenchesOf(balls, 'white', 0.0, -1.0, 600.0,
                                        0.0, 0.0)[:2]
    self.assertEqual((first.end, second.end), ('ball', 'stop'))
    sent = Cue().sent(white, 0.0, -1.0, 600.0, 0.0, 0.0, RADIUS)
    came = speedAt(sent, first.distance())
    rest = restOf(Ball('red', RED.x, RED.y, STILL, 0.0, -came))
    self.assertAlmostEqual(second.distance(), RED.y - rest.y, 1)

  def test_ball_one_after(self) -> None:
    """Rolling into a half-ball hit on red, ball 1 goes on from the hit
    square to the line of their middles, then bends till it rolls, some
    30 degrees off the aim (27 to 34, the user); struck full, rolling, it
    follows on along the line."""
    aimX, aimY = RED.x + RADIUS - WHITE.x, RED.y - WHITE.y
    size = math.hypot(aimX, aimY)
    first, second, after = TRENCHES.trenchesOf(
      OPENING, 'white', aimX, aimY, 2000.0, 0.0, 0.0)
    self.assertEqual(after.name, 'white')
    self.assertEqual(after.startPlace(), first.endPlace())
    gx, gy = first.endPlace()
    nx, ny = (RED.x - gx) / (2.0 * RADIUS), (RED.y - gy) / (2.0 * RADIUS)
    dx, dy = wayOf(after.points[0], after.points[1])
    self.assertLess(abs(dx * nx + dy * ny), 0.01)
    dx, dy = wayOf(after.points[-2], after.points[-1])
    off = math.degrees(math.acos(min(
      (dx * aimX + dy * aimY) / size, 1.0)))
    self.assertTrue(27.0 <= off <= 34.0, off)
    aimX = RED.x - WHITE.x
    first, second, after = TRENCHES.trenchesOf(
      OPENING, 'white', aimX, aimY, 2000.0, 0.0, 0.0)
    dx, dy = wayOf(after.points[0], after.points[-1])
    sx, sy = wayOf(second.points[0], second.points[-1])
    self.assertGreater(dx * sx + dy * sy, 0.9999)

  def test_missed(self) -> None:
    """Aimed a hair more than a ball's width past red's middle, red is
    not met."""
    aimX = RED.x + 2.0 * RADIUS + 0.5 - WHITE.x
    trenches = TRENCHES.trenchesOf(OPENING, 'white', aimX, RED.y - WHITE.y,
                                   2000.0, 0.0, 0.0)
    self.assertEqual(len(trenches), 1)
    self.assertNotEqual(trenches[0].end, 'ball')

  def test_mesh(self) -> None:
    """The trench drawn is a band a ball wide from where the ball sets
    off to where it ends, rounded off there by half the ball's outline,
    flat and facing up."""
    rows = trenchMesh(((0.0, 0.0), (300.0, 0.0)), RADIUS, 0.8, 24)
    self.assertEqual(rows.shape, (6 + 3 * 24, 6))
    self.assertTrue(numpy.allclose(rows[:, 1], 0.8))
    self.assertTrue(numpy.allclose(rows[:, 3:], (0.0, 1.0, 0.0)))
    self.assertAlmostEqual(float(rows[:, 0].max()), 300.0 + RADIUS, 6)
    self.assertAlmostEqual(float(rows[:, 2].max()), RADIUS, 6)
    self.assertAlmostEqual(float(rows[:, 0].min()), 0.0, 6)
    far = numpy.hypot(rows[6:, 0] - 300.0, rows[6:, 2])
    self.assertTrue((far <= RADIUS + 1e-9).all())
