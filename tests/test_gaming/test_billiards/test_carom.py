"""
TestCarom covers balls meeting, through 'Motion' and 'Carom', as the
user, who plays, taught it: struck full without spin, a ball stops and
hands the other nearly all its speed, momentum kept; rolling, it leaves
the other by the 30 degree rule, 27 to 34 degrees from a quarter to a
three-quarter ball hit; only a share of its spin passes on, turned the
other way, as gears, the more the slower the hit; its top spin is the
other's draw; the meeting is found exactly; and three balls struck hard
never press deep into each other, their energy never rising, and come
to rest. Through a hit, a ball rolling far away moves on exactly as the
cloth has it, asleep, and the hits run in pieces come out as run at
once, to the last digit; the compiled kernel steps a run of hits as the
plain Python does, to a hair.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import STILL, Ball, Carom, Cloth, Hits, Motion

from . import BilliardsTest, aroundContact, ballAt, rolledOn

MOTION = Motion()
RADIUS = MOTION.table.radius
#  The same, on a felt giving nothing back as a ball stops, so energy can
#  only fall.
DEAD = Motion(MOTION.table, Cloth(*MOTION.cloth[:4], 0.0), MOTION.cushion,
              MOTION.carom)


def struck(speed: float, roll: float, side: float,
           offset: float) -> tuple:
  """White, half a mm short of red, moving straight down the table at
  'speed', its spin rolling it at 'roll' and 'side' about the vertical;
  'offset' across from red's middle; red still."""
  apart = math.sqrt((2.0 * RADIUS) ** 2 - offset * offset) + 0.5
  white = ballAt('white', 710.0 + offset, 900.0 + apart, 0.0, -speed,
                 roll / RADIUS, 0.0, side)
  red = ballAt('red', 710.0, 900.0, 0.0, 0.0, 0.0, 0.0, 0.0)
  return white, red


class TestCarom(BilliardsTest):
  """Tests for balls meeting."""

  def test_full_stun(self) -> None:
    """Struck full without spin, white keeps (1 - e) / 2 of its speed and
    red takes (1 + e) / 2, momentum kept."""
    before, after = aroundContact(MOTION, struck(1000.0, 0.0, 0.0, 0.0),
                                  0.05)
    came = before[0].vy
    lively = Carom().liveliness
    self.assertAlmostEqual(after[0].vy / came, 0.5 * (1.0 - lively), 2)
    self.assertAlmostEqual(after[1].vy / came, 0.5 * (1.0 + lively), 2)
    kept = (after[0].vy + after[1].vy) / came
    self.assertAlmostEqual(kept, 1.0, 2)
    self.assertAlmostEqual(after[1].vx, 0.0, 6)

  def test_thirty_degrees(self) -> None:
    """Rolling, white leaves red by the 30 degree rule: the angle peaks
    at 33.7 for a half ball hit, 27.3 and 27.6 for a quarter and three
    quarters."""
    for share, wanted in ((1.5, 27.3), (1.0, 33.7), (0.5, 27.6)):
      balls = struck(1000.0, 1000.0, 0.0, share * RADIUS)
      _, after = aroundContact(MOTION, balls, 0.05)
      rolled = rolledOn(MOTION, after)
      white = rolled[0]
      angle = math.degrees(math.atan2(abs(white.vx), abs(white.vy)))
      self.assertLess(abs(angle - wanted), 1.5)

  def test_gears(self) -> None:
    """Side spin on white hands red side spin the other way, a small
    share, the more the slower the hit; white's top spin is red's
    draw."""
    shares = []
    for speed in (500.0, 2000.0):
      side = 2.0 * speed / RADIUS
      before, after = aroundContact(MOTION, struck(speed, 0.0, side, 0.0),
                                    0.05)
      self.assertLess(after[1].wz * before[0].wz, 0.0)
      shares.append(abs(after[1].wz / before[0].wz))
    self.assertLess(shares[0], 0.1)
    self.assertGreater(shares[0], shares[1])
    _, after = aroundContact(MOTION, struck(1000.0, 1000.0, 0.0, 0.0),
                             0.05)
    self.assertLess(after[1].vy, 0.0)
    self.assertLess(after[1].wx, 0.0)

  def test_meet_time(self) -> None:
    """The moment two balls meet is found exactly: moved on so long,
    they just touch."""
    white = ballAt('white', 730.0, 1100.0, 0.0, -800.0, 800.0 / RADIUS,
                   0.0, 0.0)
    red = ballAt('red', 710.0, 900.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    time = MOTION.meetTime(white, red, 10.0)
    phase = MOTION.cloth.phaseOf(white, RADIUS)
    moved = MOTION.cloth.moved(white, phase, time, RADIUS)
    self.assertAlmostEqual(MOTION.pressedOf(moved, red), 0.0, 6)

  def test_rally(self) -> None:
    """Three balls, white struck hard into the others: they never press
    deep into each other, their energy never rises, on a felt giving
    nothing back, and they come to rest on the table."""
    white = ballAt('white', 892.5, 2130.0, -300.0, -2500.0,
                   2500.0 / RADIUS, -300.0 / RADIUS, 30.0)
    yellow = ballAt('yellow', 710.0, 2130.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    red = ballAt('red', 710.0, 710.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    balls = (white, yellow, red)
    last = DEAD.energyOf(balls)
    for _ in range(1500):
      balls = DEAD.advanced(balls, 0.01)
      energy = DEAD.energyOf(balls)
      self.assertLessEqual(energy, last + 1e-9)
      last = energy
      for i in range(3):
        for j in range(i + 1, 3):
          self.assertLess(MOTION.pressedOf(balls[i], balls[j]), 0.5)
    for ball in balls:
      self.assertEqual(MOTION.cloth.phaseOf(ball, RADIUS), 'still')
      self.assertGreater(ball.x, 0.0)
      self.assertLess(ball.x, MOTION.table.width)

  def test_hits(self) -> None:
    """Through a ball's hit on a cushion, a ball rolling far away moves
    on exactly as the cloth has it; the hits run in pieces, as a
    recorder samples them, come out as run at once, to the last
    digit."""
    reach = MOTION.reach()
    hitting = Ball('white', reach, 700.0, STILL, -800.0, 0.0, 0.0,
                   -800.0 / RADIUS, 0.0)
    far = Ball('red', 710.0, 2000.0, STILL, 0.0, 500.0, -500.0 / RADIUS,
               0.0, 0.0)
    balls = (hitting, far)
    self.assertTrue(MOTION.inContact(balls))
    after, used, _ = MOTION.collided(balls, 1.0, True)
    self.assertGreater(used, 0.001)
    self.assertGreater(after[0].vx, 0.0)
    self.assertEqual(after[1], MOTION.cloth.advanced(far, used, RADIUS))
    hits = MOTION.hitsOf(balls)
    pieces = 0
    last = balls
    while not hits.over:
      last = hits.run(0.0005, True)[0]
      pieces += 1
    self.assertGreater(pieces, 3)
    self.assertEqual(last, after)

  def test_compiled_agrees(self) -> None:
    """The compiled kernel ('Hits', compiled) steps a ball's hit on a
    cushion and on another ball as the plain Python does, to a hair,
    logging the same contacts."""
    reach = MOTION.reach()
    hitting = Ball('white', reach, 700.0, STILL, -800.0, 300.0, 0.0,
                   -800.0 / RADIUS, 20.0)
    other = Ball('red', 500.0, 1000.0, STILL, 900.0, 0.0, 0.0,
                 900.0 / RADIUS, 0.0)
    target = Ball('yellow', 500.0 + 2.0 * RADIUS + 1e-7, 1000.0)
    for balls in ((hitting,), (other, target)):
      fast = Hits(MOTION, balls, True).run(1.0, True)
      slow = Hits(MOTION, balls, False).run(1.0, True)
      self.assertEqual(fast[2], slow[2])
      self.assertAlmostEqual(fast[1], slow[1], 9)
      for a, b in zip(fast[0], slow[0]):
        self.assertAlmostEqual(a.x, b.x, 6)
        self.assertAlmostEqual(a.y, b.y, 6)
        self.assertAlmostEqual(a.vx, b.vx, 4)
        self.assertAlmostEqual(a.vy, b.vy, 4)
        self.assertAlmostEqual(a.wz, b.wz, 6)

