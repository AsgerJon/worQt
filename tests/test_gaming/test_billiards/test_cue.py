"""
TestCue covers 'Cue', the stick as just another cushion, one that
moves: struck in the middle the ball leaves along the stick, faster than
the stick as the stick is heavier, without spin; off the middle it
leaves slower and squirts off the stick's line to the other side, the
less the lighter the stick's end, the classic stick its weightless
limit; struck at 'rollHeight' it rolls at once, a little above 2/5 of
the radius; below, it draws; right of the middle it spins
anticlockwise seen from above, left the mirror of it; 'sent' leaves
along the line it is sent at the speed asked; the miscue limit is where
the chalk can no longer hold the tip.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import Ball, CaromTable, Cloth, Cue

from . import BilliardsTest

RADIUS = CaromTable().radius
CLOTH = Cloth()


class TestCue(BilliardsTest):
  """Tests for 'Cue'."""

  def test_middle_along_the_stick(self) -> None:
    """Struck in the middle, the ball leaves along the stick at the
    speed asked, without spin, from where it lay, however long the aim
    is."""
    ball = Ball('white', 100.0, 200.0)
    struck = Cue().struck(ball, 3.0, 4.0, 1500.0, 0.0, 0.0, RADIUS)
    self.assertAlmostEqual(struck.vx, 900.0, 9)
    self.assertAlmostEqual(struck.vy, 1200.0, 9)
    self.assertEqual((struck.wx, struck.wy, struck.wz), (0.0, 0.0, 0.0))
    self.assertEqual((struck.x, struck.y, struck.name), (100.0, 200.0,
                                                         'white'))

  def test_faster_than_the_stick(self) -> None:
    """Struck in the middle, a ball lighter than the stick leaves
    faster than the stick came, near (1 + liveliness) times the stick's
    share of the two weights."""
    cue = Cue()
    share = cue.centreShare()
    expected = (1.0 + cue.liveliness) * cue.weight / (cue.weight
                                                      + cue.ballWeight)
    self.assertGreater(share, 1.0)
    self.assertLess(abs(share / expected - 1.0), 0.02)

  def test_slower_off_the_middle(self) -> None:
    """The same stroke off the middle sends the ball off slower, the
    more the further off."""
    cue = Cue()
    speeds = []
    for side in (0.0, 0.2, 0.4):
      right, forward = cue.strokeOf(0.0, side)[:2]
      speeds.append(math.hypot(right, forward))
    self.assertGreater(speeds[0], speeds[1])
    self.assertGreater(speeds[1], speeds[2])

  def test_squirt(self) -> None:
    """Right of the middle, the ball leaves a few degrees left of the
    stick's line, more the further off; left of it, as far right."""
    cue = Cue()
    near, far = cue.squirtOf(0.0, 0.25), cue.squirtOf(0.0, 0.5)
    self.assertLess(near, 0.0)
    self.assertLess(far, near)
    self.assertGreater(far, -5.0)
    self.assertLess(far, -1.0)
    self.assertAlmostEqual(cue.squirtOf(0.0, -0.5), -far, 12)
    struck = cue.struck(Ball('white', 0.0, 0.0), 0.0, 1.0, 1000.0, 0.0,
                        0.5, RADIUS)
    self.assertLess(struck.vx, 0.0)

  def test_lighter_end_squirts_less(self) -> None:
    """A lighter end squirts the ball less; nearly weightless, the
    stick is the classic one, pushing only along its length."""
    heavy, light = Cue(510.0, 210.0, 8.0), Cue(510.0, 210.0, 4.0)
    self.assertGreater(light.squirtOf(0.0, 0.4),
                       heavy.squirtOf(0.0, 0.4))
    classic = Cue(510.0, 210.0, 0.5)
    self.assertLess(abs(classic.squirtOf(0.0, 0.3)), 0.2)
    self.assertLess(abs(classic.rollHeight() - 0.4), 0.01)
    right, forward, _, _, spin = classic.strokeOf(0.0, 0.3)
    speed = math.hypot(right, forward)
    self.assertLess(abs(spin / (2.5 * 0.3 * speed) - 1.0), 0.02)

  def test_rolls_at_roll_height(self) -> None:
    """Struck at 'rollHeight', a ball rolls at once; that is a little
    above 2/5 of the radius, the stick's end giving."""
    cue = Cue()
    height = cue.rollHeight()
    self.assertGreater(height, 0.4)
    self.assertLess(height, cue.limit)
    struck = cue.struck(Ball('white', 0.0, 0.0), -1.0, 2.0, 2000.0,
                        height, 0.0, RADIUS)
    for slip in CLOTH.slipOf(struck, RADIUS):
      self.assertLess(abs(slip), 1e-6)
    self.assertEqual(CLOTH.phaseOf(struck, RADIUS), 'rolling')

  def test_draw(self) -> None:
    """Below the middle, a ball spins backwards, its lowest point
    slipping forwards faster than it moves."""
    struck = Cue().struck(Ball('white', 0.0, 0.0), 0.0, -1.0, 1000.0,
                          -0.3, 0.0, RADIUS)
    slip = CLOTH.slipOf(struck, RADIUS)
    self.assertLess(slip[1], struck.vy)
    self.assertAlmostEqual(slip[0], 0.0, 9)

  def test_side(self) -> None:
    """Right of the middle, a ball spins anticlockwise seen from above;
    left of it, the mirror of that."""
    ball = Ball('white', 0.0, 0.0)
    right = Cue().struck(ball, 0.0, 1.0, 1000.0, 0.0, 0.2, RADIUS)
    left = Cue().struck(ball, 0.0, 1.0, 1000.0, 0.0, -0.2, RADIUS)
    self.assertGreater(right.wz, 0.0)
    self.assertAlmostEqual(left.wz, -right.wz, 9)
    self.assertAlmostEqual(left.vx, -right.vx, 9)
    self.assertAlmostEqual(left.vy, right.vy, 9)

  def test_sent(self) -> None:
    """Sent, a ball leaves along the line it is sent at the speed asked,
    the stick laid off it by the squirt, spinning as the same stroke
    spins it."""
    cue, ball = Cue(), Ball('white', 0.0, 0.0)
    sent = cue.sent(ball, 3.0, 4.0, 4000.0, 0.38, -0.26, RADIUS)
    self.assertAlmostEqual(sent.vx, 2400.0, 9)
    self.assertAlmostEqual(sent.vy, 3200.0, 9)
    struck = cue.struck(ball, 3.0, 4.0, 4000.0, 0.38, -0.26, RADIUS)
    scale = 4000.0 / math.hypot(struck.vx, struck.vy)
    self.assertAlmostEqual(sent.wz, struck.wz * scale, 9)
    spun = math.hypot(sent.wx, sent.wy)
    self.assertAlmostEqual(spun, math.hypot(struck.wx, struck.wy) * scale,
                           9)

  def test_miscue_limit(self) -> None:
    """The limit is where the chalk can no longer hold the tip, six
    tenths of the radius by default (the user: more spin; was half, as
    Alciatore reckons); a point past it is drawn in to it, the way it
    lay."""
    cue = Cue()
    self.assertAlmostEqual(cue.limit, 0.6, 12)
    self.assertAlmostEqual(math.atan(cue.grip),
                           math.asin(cue.limit), 12)
    top, side = cue.hitOf(0.6, 0.8)
    self.assertAlmostEqual(math.hypot(top, side), cue.limit, 12)
    self.assertAlmostEqual(top / side, 0.75, 12)
    self.assertEqual(cue.hitOf(0.1, -0.2), (0.1, -0.2))
