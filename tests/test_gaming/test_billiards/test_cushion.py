"""
TestCushion covers a single ball off the cushions, through 'Motion':
up to 2.5 m/s straight in, as Mathavan et al. (2010) have it, their
rigid cushion's way out and speed to within a degree and 2 %; past it,
a ball near square pulled squarer the harder it comes (the user), never
past square, a ball at a wide angle as before; and as the user, who
plays, taught it: rolled straight in, it comes straight
back; rolled in at 45 degrees it comes out flatter than a mirror would
send it, its top spin steering it; running side spin flattens it more,
reverse side spin at 45 degrees barely moves it, near square side spin
turns it a lot either way, the more so the slower the ball;
draw into a cushion turns to follow out of it, ordinary draw too, and
follow into it to draw; slow, with heavy side spin, straight in, a
ball is kicked along the cushion, slower than it came (Mathavan et
al. decide, for now: the user has seen one leave faster); slow, with
heavy top spin, it
hits the same cushion again; a ball resting against a cushion stays as
it is; a hard ball keeps to the table, its energy never rising, and
comes to rest; into a corner, it comes back out.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import STILL, Ball, Cloth, Cushion, Motion
from worQt.gaming.billiards import mathavanRebound
from worQt.gaming.billiards._motion import Hits

from . import BilliardsTest, aroundContact, ballAt, rolledOn

MOTION = Motion()
RADIUS = MOTION.table.radius
REACH = MOTION.reach()
#  The same, on a felt giving nothing back as a ball stops, so energy can
#  only fall.
DEAD = Motion(MOTION.table, Cloth(*MOTION.cloth[:4], 0.0), MOTION.cushion,
              MOTION.carom)


def angleOf(vx: float, vy: float) -> float:
  """The angle a path along 'vx', 'vy' makes with the foot cushion, in
  degrees."""
  return math.degrees(math.atan2(abs(vy), abs(vx)))


def offLeft(motion: Motion, speed: float, angle: float,
            side: float) -> Ball:
  """A ball rolling at 'speed' 'angle' degrees off square into the left
  cushion, with 'side' of rolling as side spin, touching it: as it
  leaves, stepped through the hit alone."""
  a = math.radians(angle)
  vx, vy = -speed * math.cos(a), speed * math.sin(a)
  ball = Ball('white', motion.reach() - 1e-6, 1000.0, STILL, vx, vy,
              -vy / RADIUS, vx / RADIUS, side * speed / RADIUS)
  return Hits(motion, (ball,), True).run(0.2, True)[0][0]


def rigidOffLeft(speed: float, angle: float, side: float) -> tuple:
  """The same ball off Mathavan et al.'s rigid cushion: as it leaves,
  (vx, vy) on the table."""
  a = math.radians(angle)
  inward, along = speed * math.cos(a), speed * math.sin(a)
  #  The cushion's frame: x along it (the table's y), y into it (the
  #  table's -x); rolling, the spin across the cloth is the speed's.
  out = mathavanRebound(along, inward, -inward / RADIUS, along / RADIUS,
                        side * speed / RADIUS, RADIUS, MOTION.table.nose,
                        MOTION.cushion.liveliness, MOTION.cushion.grip,
                        MOTION.cloth.sliding)
  return -out[1], out[0]


def outAngle(vx: float, vy: float) -> float:
  """The angle a ball leaving the left cushion makes with square, in
  degrees, above nought the way it came along."""
  return math.degrees(math.atan2(vy, vx))


def offFoot(side: float, speed: float) -> tuple[float, float]:
  """A ball rolled at 45 degrees into the foot cushion at 'speed' with
  'side' spin: the angle it leaves at, and the angle it rolls on at
  once its spin has steered it."""
  along = speed / math.sqrt(2.0)
  ball = ballAt('white', 710.0, REACH + 3.0, along, -along,
                along / RADIUS, along / RADIUS, side)
  _, after = aroundContact(MOTION, (ball,), 0.2)
  rolled = rolledOn(MOTION, after)
  return angleOf(after[0].vx, after[0].vy), angleOf(rolled[0].vx,
                                                    rolled[0].vy)


class TestCushion(BilliardsTest):
  """Tests for a ball off the cushions."""

  def test_reach(self) -> None:
    """A ball touches the nose, 37 mm up, with its middle a little less
    than its radius from it."""
    wanted = math.sqrt(RADIUS ** 2 - (37.0 - RADIUS) ** 2)
    self.assertAlmostEqual(REACH, wanted, 12)
    self.assertLess(REACH, RADIUS)

  def test_mathavan(self) -> None:
    """Up to 2.5 m/s, rolling in at any angle, with side spin either
    way, a ball leaves as Mathavan et al.'s rigid cushion sends it,
    within a degree and 2 % of the speed."""
    for speed in (500.0, 1000.0, 2500.0):
      for angle in (0.0, 10.0, 30.0, 45.0, 60.0):
        for side in (0.0, 0.5, -0.5):
          left = offLeft(MOTION, speed, angle, side)
          vx, vy = rigidOffLeft(speed, angle, side)
          self.assertLess(abs(outAngle(left.vx, left.vy)
                              - outAngle(vx, vy)), 1.0)
          self.assertLess(abs(math.hypot(left.vx, left.vy)
                              - math.hypot(vx, vy)), 0.02 * speed)

  def test_squaring(self) -> None:
    """Where Mathavan et al. hold, up to 2.5 m/s straight in, the
    squaring changes nothing; past it a ball coming in near square
    leaves squarer, the harder the more, never past square; at a wide
    angle as before (the user)."""
    plain = Motion(MOTION.table, MOTION.cloth,
                   Cushion(*MOTION.cushion[:6], 0.0, *MOTION.cushion[7:]),
                   MOTION.carom)
    for angle in (5.0, 15.0, 40.0):
      self.assertEqual(offLeft(MOTION, 2400.0, angle, 0.0),
                       offLeft(plain, 2400.0, angle, 0.0))
    squarer = []
    for speed in (4000.0, 6000.0):
      left = offLeft(MOTION, speed, 6.0, 0.0)
      before = offLeft(plain, speed, 6.0, 0.0)
      squarer.append(outAngle(before.vx, before.vy)
                     - outAngle(left.vx, left.vy))
      self.assertGreaterEqual(outAngle(left.vx, left.vy), 0.0)
      wide = offLeft(MOTION, speed, 40.0, 0.0)
      before = offLeft(plain, speed, 40.0, 0.0)
      self.assertLess(abs(outAngle(wide.vx, wide.vy)
                          - outAngle(before.vx, before.vy)), 0.05)
    self.assertGreater(squarer[0], 0.3)
    self.assertGreater(squarer[1], squarer[0])
    self.assertEqual(Cushion().squaringOf(2500.0, 300.0), 0.0)
    self.assertGreater(Cushion().squaringOf(5000.0, 300.0),
                       Cushion().squaringOf(5000.0, 1500.0))

  def test_straight_back(self) -> None:
    """Rolled straight in, a ball comes straight back, never leaving
    its line."""
    ball = ballAt('white', 710.0, 500.0, 0.0, -1000.0, 1000.0 / RADIUS,
                  0.0, 0.0)
    balls, fastest = (ball,), 0.0
    for _ in range(300):
      balls = MOTION.advanced(balls, 0.01)
      self.assertEqual(balls[0].x, 710.0)
      fastest = max(fastest, balls[0].vy)
    self.assertGreater(fastest, 500.0)
    self.assertLess(fastest, 1000.0)

  def test_flatter_than_a_mirror(self) -> None:
    """Rolled in at 45 degrees, a ball leaves steeper, then its top spin
    steers it on flatter than the mirror's 45."""
    leaves, rolls = offFoot(0.0, 990.0)
    self.assertLess(rolls, 45.0)
    self.assertGreater(rolls, 15.0)
    self.assertGreater(leaves, rolls)

  def test_side_spin(self) -> None:
    """Running side spin flattens the way out; at 45 degrees reverse
    side spin barely moves it, as Mathavan et al.'s cushion has it, the
    slip at the nose already all along the cushion; near square side
    spin turns the way out a lot either way; the slower the ball, the
    more side spin moves it."""
    plain = offFoot(0.0, 990.0)[1]
    running = offFoot(-40.0, 990.0)[1]
    reverse = offFoot(40.0, 990.0)[1]
    self.assertLess(running, plain - 5.0)
    self.assertLess(abs(reverse - plain), 2.0)
    square = offLeft(MOTION, 1000.0, 10.0, 0.0)
    square = outAngle(square.vx, square.vy)
    wider = offLeft(MOTION, 1000.0, 10.0, 0.5)
    squarer = offLeft(MOTION, 1000.0, 10.0, -0.5)
    self.assertGreater(outAngle(wider.vx, wider.vy), square + 5.0)
    self.assertLess(outAngle(squarer.vx, squarer.vy), square - 5.0)
    slow = offFoot(40.0, 500.0)[0] - offFoot(0.0, 500.0)[0]
    hard = offFoot(40.0, 2000.0)[0] - offFoot(0.0, 2000.0)[0]
    self.assertGreater(slow, hard)
    self.assertGreater(hard, 0.0)

  def test_draw_to_follow(self) -> None:
    """Draw into a cushion is follow out of it: the ball speeds up once
    off it; top spin into it slows it, back into the cushion."""
    drawn = ballAt('white', 710.0, REACH + 2.0, 0.0, -300.0,
                   -1500.0 / RADIUS, 0.0, 0.0)
    _, after = aroundContact(MOTION, (drawn,), 0.2)
    rolled = rolledOn(MOTION, after)
    self.assertGreater(after[0].vy, 0.0)
    self.assertGreater(rolled[0].vy, after[0].vy)
    topped = ballAt('white', 710.0, REACH + 2.0, 0.0, -300.0,
                    1500.0 / RADIUS, 0.0, 0.0)
    _, after = aroundContact(MOTION, (topped,), 0.2)
    rolled = rolledOn(MOTION, after)
    self.assertLess(rolled[0].vy, after[0].vy)

  def test_spin_turned_round(self) -> None:
    """Met square on, a cushion turns the spin round with the way, as
    it keeps a share of it: a ball coming in with ordinary draw leaves
    with follow, one coming in with follow leaves drawing; neither
    sticks at the nose, leaving the same whatever it brought."""

    def share(roll: float) -> float:
      """Rolled at 2 m/s square into the foot cushion with its spin
      'roll' of rolling, below nought drawing: its spin as it leaves, a
      share of rolling, below nought drawing."""
      ball = ballAt('white', 710.0, REACH + 2.0, 0.0, -2000.0,
                    roll * 2000.0 / RADIUS, 0.0, 0.0)
      _, after = aroundContact(MOTION, (ball,), 0.2)
      vy, wx = after[0].vy, after[0].wx
      self.assertGreater(vy, 0.0)
      return -wx * RADIUS / vy

    drawn, followed = share(-0.9), share(0.9)
    self.assertGreater(drawn, 0.1)
    self.assertLess(followed, -0.1)

  def test_side_spin_kicks(self) -> None:
    """Straight in, slow, with heavy side spin, a ball leaves kicked
    along the cushion, against the way its spin turns at the nose, more
    than 10 degrees off square, and slower than it came: at Mathavan et
    al.'s grip the cushion cannot turn enough of the spin into speed
    (the user has seen one leave faster; Mathavan et al. decide, for
    now)."""
    for spin in (150.0, -150.0):
      ball = ballAt('white', 710.0, REACH + 2.0, 0.0, -300.0, 0.0, 0.0,
                    spin)
      before, after = aroundContact(MOTION, (ball,), 0.2)
      vx, vy = after[0].vx, after[0].vy
      self.assertGreater(vy, 0.0)
      self.assertLess(vx * spin, 0.0)
      self.assertGreater(abs(math.degrees(math.atan2(vx, vy))), 10.0)
      came = math.hypot(before[0].vx, before[0].vy)
      self.assertLess(math.hypot(vx, vy), came)

  def test_tokyo_drift(self) -> None:
    """Slow, with heavy top spin, a ball comes off a cushion and its
    spin drives it into the same cushion again."""
    ball = ballAt('white', 710.0, REACH + 5.0, 0.0, -500.0,
                  3000.0 / RADIUS, 0.0, 0.0)
    balls, was, hits = (ball,), False, 0
    for _ in range(6000):
      balls = MOTION.advanced(balls, 0.001)
      touching = MOTION.inContact(balls)
      hits += 1 if touching and not was else 0
      was = touching
    self.assertGreaterEqual(hits, 2)

  def test_resting_against(self) -> None:
    """A ball resting against a cushion stays exactly as it is."""
    ball = ballAt('white', 710.0, REACH, 0.0, 0.0, 0.0, 0.0, 0.0)
    self.assertEqual(MOTION.advanced((ball,), 5.0), (ball,))

  def test_hard_ball(self) -> None:
    """A hard ball off many cushions keeps to the table, never pressing
    a cushion twice as far as a firm ball does, its energy never
    rising, on a felt giving nothing back, and comes to rest."""
    ball = ballAt('white', 892.5, 2130.0, -700.0, -2400.0,
                  2400.0 / RADIUS, -700.0 / RADIUS, 40.0)
    balls = (ball,)
    last = DEAD.energyOf(balls)
    deepest = REACH - 2.0 * MOTION.cushion.deflection
    table = MOTION.table
    for _ in range(3000):
      balls = DEAD.advanced(balls, 0.005)
      energy = DEAD.energyOf(balls)
      self.assertLessEqual(energy, last + 1e-9)
      last = energy
      self.assertGreater(balls[0].x, deepest)
      self.assertLess(balls[0].x, table.width - deepest)
      self.assertGreater(balls[0].y, deepest)
      self.assertLess(balls[0].y, table.length - deepest)
    self.assertEqual(MOTION.cloth.phaseOf(balls[0], RADIUS), 'still')

  def test_corner(self) -> None:
    """Rolled into a corner, a ball comes back out the way it went in,
    within the little the order the two cushions push in leaves."""
    ball = ballAt('white', 300.0, 300.0, -800.0, -800.0, 800.0 / RADIUS,
                  -800.0 / RADIUS, 0.0)
    balls = MOTION.advanced((ball,), 1.0)
    self.assertGreater(balls[0].vx, 0.0)
    self.assertGreater(balls[0].vy, 0.0)
    self.assertLess(abs(balls[0].x - balls[0].y), 3.0)
