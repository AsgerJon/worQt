"""
TestCloth covers 'Cloth', a single ball moving on the felt, to see that
nothing crazy happens: a still ball stays still; a rolling ball rolls
straight, its lowest point never slipping, slows at 5/7 of the rolling
offset times gravity and stops where it should, for good; a ball struck
without spin slides 2|u|/(7 mu g) and then rolls at 5/7 of its speed;
top spin speeds a ball up and draw slows or returns it, to (5 v + 2
roll) / 7; side spin dies steadily and never bends the path, a ball
spinning in place spinning down until it is still; a slip
across the path bends it until the ball rolls; the motion is the same
in pieces as at once; its energy never rises; the dots turn by the
distance over the radius.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import STILL, Ball, CaromTable, Cloth

from . import BilliardsTest

RADIUS = CaromTable().radius


def struck(vx: float, vy: float, wx: float, wy: float,
           wz: float) -> Ball:
  """A white ball at the head spot, moving and spinning so."""
  return Ball('white', 710.0, 2130.0, STILL, vx, vy, wx, wy, wz)


def rolling(vx: float, vy: float) -> Ball:
  """A white ball at the head spot, rolling so."""
  return struck(vx, vy, -vy / RADIUS, vx / RADIUS, 0.0)


class TestCloth(BilliardsTest):
  """Tests for 'Cloth'."""

  def test_still(self) -> None:
    """A still ball stays exactly as it is."""
    ball = Ball('red', 710.0, 710.0)
    cloth = Cloth()
    self.assertEqual(cloth.phaseOf(ball, RADIUS), 'still')
    self.assertEqual(cloth.advanced(ball, 10.0, RADIUS), ball)

  def test_rolling(self) -> None:
    """A rolling ball rolls straight, never slipping, slowing steadily,
    and stops where it should, then settles back 'rollBack', for good."""
    cloth = Cloth()
    slow = cloth.rollingDecay()
    self.assertAlmostEqual(slow, 5.0 / 7.0 * 0.01 * 9810.0, 9)
    ball = rolling(0.0, -500.0)
    self.assertEqual(cloth.phaseOf(ball, RADIUS), 'rolling')
    for time in (0.5, 2.0, 5.0):
      later = cloth.advanced(ball, time, RADIUS)
      self.assertEqual(cloth.phaseOf(later, RADIUS), 'rolling')
      self.assertAlmostEqual(later.vy, -500.0 + slow * time, 6)
      self.assertAlmostEqual(later.y, 2130.0 - 500.0 * time
                             + 0.5 * slow * time * time, 6)
      self.assertEqual(later.x, 710.0)
      for slip in cloth.slipOf(later, RADIUS):
        self.assertAlmostEqual(slip, 0.0, 9)
    rest = cloth.advanced(ball, 30.0, RADIUS)
    self.assertEqual(cloth.phaseOf(rest, RADIUS), 'still')
    self.assertAlmostEqual(rest.y, 2130.0 - 500.0 ** 2 / (2.0 * slow)
                           + cloth.rollBack, 6)
    self.assertEqual(cloth.advanced(rest, 5.0, RADIUS), rest)

  def test_stun(self) -> None:
    """Struck without spin, a ball slides 2|u| / (7 mu g), then rolls at
    5/7 of its speed."""
    cloth = Cloth()
    ball = struck(0.0, -700.0, 0.0, 0.0, 0.0)
    self.assertEqual(cloth.phaseOf(ball, RADIUS), 'sliding')
    slide = 2.0 * 700.0 / (7.0 * cloth.sliding * cloth.gravity)
    before = cloth.advanced(ball, 0.99 * slide, RADIUS)
    self.assertEqual(cloth.phaseOf(before, RADIUS), 'sliding')
    after = cloth.advanced(ball, slide, RADIUS)
    self.assertAlmostEqual(after.vy, -500.0, 6)
    later = cloth.advanced(ball, slide + 0.01, RADIUS)
    self.assertEqual(cloth.phaseOf(later, RADIUS), 'rolling')

  def test_top_and_draw(self) -> None:
    """Top spin speeds a sliding ball up, draw slows it or brings it
    back: it rolls on at (5 v + 2 roll) / 7, 'roll' the speed its spin
    would roll at."""
    cloth = Cloth()
    for roll in (900.0, 300.0, -300.0, -900.0):
      ball = struck(0.0, -300.0, roll / RADIUS, 0.0, 0.0)
      after = cloth.advanced(ball, 0.5, RADIUS)
      wanted = (5.0 * -300.0 + 2.0 * -roll) / 7.0
      slow = cloth.rollingDecay()
      grip = cloth.sliding * cloth.gravity
      slide = 2.0 * abs(-300.0 + roll) / (7.0 * grip)
      wanted += math.copysign(slow * (0.5 - slide), -wanted)
      self.assertAlmostEqual(after.vy, wanted, 6)
      self.assertEqual(cloth.phaseOf(after, RADIUS), 'rolling')

  def test_side_spin(self) -> None:
    """Side spin dies steadily, never bending the path or slowing the
    roll; once it is gone it stays gone."""
    cloth = Cloth()
    decay = cloth.spinDecay(RADIUS)
    plain = rolling(0.0, -400.0)
    spun = struck(0.0, -400.0, 400.0 / RADIUS, 0.0, 60.0)
    for time in (1.0, 3.0):
      left = cloth.advanced(spun, time, RADIUS)
      same = cloth.advanced(plain, time, RADIUS)
      self.assertAlmostEqual(left.wz, 60.0 - decay * time, 9)
      self.assertEqual((left.x, left.y), (same.x, same.y))
    gone = cloth.advanced(spun, 30.0, RADIUS)
    self.assertEqual(gone.wz, 0.0)

  def test_spin_in_place(self) -> None:
    """A ball spinning in place spins down steadily while the spin is
    high, then fades, its phase ending as the spin dies, the ball then
    still; any spin of a turn in three seconds or more lasts three
    seconds at least (the user); split anywhere, it spins down the
    same."""
    cloth = Cloth()
    decay = cloth.spinDecay(RADIUS)
    ball = struck(0.0, 0.0, 0.0, 0.0, -40.0)
    self.assertEqual(cloth.phaseOf(ball, RADIUS), 'spinning')
    knee = decay * cloth.spinTail
    lasts = (40.0 - knee) / decay + cloth.spinTail * math.log(
      knee / cloth.spinStop)
    self.assertAlmostEqual(cloth.phaseTime(ball, 'spinning', RADIUS),
                           lasts, 12)
    later = cloth.advanced(ball, 1.0, RADIUS)
    self.assertAlmostEqual(later.wz, -40.0 + decay, 9)
    self.assertEqual((later.x, later.y), (ball.x, ball.y))
    for spin in (2.0, 5.0, 20.0):
      self.assertGreaterEqual(cloth.spinningTime(spin, RADIUS),
                              3.0 - 1e-9)
    split = cloth.advanced(cloth.advanced(ball, 3.0, RADIUS), 2.0, RADIUS)
    self.assertAlmostEqual(split.wz, cloth.advanced(ball, 5.0, RADIUS).wz,
                           12)
    done = cloth.settled(ball, 'spinning', RADIUS)
    self.assertEqual(done.wz, 0.0)
    self.assertEqual(cloth.phaseOf(done, RADIUS), 'still')
    gone = cloth.advanced(ball, lasts + 1.0, RADIUS)
    self.assertEqual(gone.wz, 0.0)
    self.assertEqual(cloth.phaseOf(gone, RADIUS), 'still')

  def test_curve(self) -> None:
    """A slip across the path bends it while the ball slides; rolling,
    it runs straight."""
    cloth = Cloth()
    ball = struck(0.0, -600.0, 600.0 / RADIUS, 300.0 / RADIUS, 0.0)
    rolled = cloth.advanced(ball, 0.5, RADIUS)
    self.assertEqual(cloth.phaseOf(rolled, RADIUS), 'rolling')
    self.assertGreater(rolled.x, 710.0 + 1.0)
    first = cloth.advanced(rolled, 0.5, RADIUS)
    second = cloth.advanced(rolled, 1.0, RADIUS)
    across = (first.x - rolled.x, second.x - first.x)
    along = (first.y - rolled.y, second.y - first.y)
    self.assertAlmostEqual(across[0] * along[1], across[1] * along[0], 6)

  def test_pieces(self) -> None:
    """Moved in forty pieces, a ball ends exactly as moved at once."""
    cloth = Cloth()
    ball = struck(120.0, -700.0, 3.0, -9.0, 40.0)
    once = cloth.advanced(ball, 4.0, RADIUS)
    piece = ball
    for _ in range(40):
      piece = cloth.advanced(piece, 0.1, RADIUS)
    for name in ('x', 'y', 'vx', 'vy', 'wx', 'wy', 'wz'):
      self.assertAlmostEqual(getattr(once, name), getattr(piece, name), 6)
    for a, b in zip(once.turn, piece.turn):
      self.assertAlmostEqual(a, b, 4)

  def test_energy(self) -> None:
    """The energy of motion never rises, and is gone in the end, on a
    felt giving nothing back as a ball stops."""
    cloth = Cloth(*Cloth()[:4], 0.0)
    for ball in (struck(300.0, -500.0, -20.0, 15.0, 60.0),
                 struck(0.0, -300.0, -30.0, 0.0, 0.0),
                 rolling(200.0, 100.0)):
      last = cloth.energyOf(ball, RADIUS)
      for _ in range(300):
        ball = cloth.advanced(ball, 0.05, RADIUS)
        energy = cloth.energyOf(ball, RADIUS)
        self.assertLessEqual(energy, last + 1e-12)
        last = energy
      self.assertEqual(last, 0.0)

  def test_roll_back(self) -> None:
    """As a roll ends the felt pushes the ball back 'rollBack' the way it
    came, rolling, giving back the energy of that little roll; once:
    rolled back, it rests, until struck again; a felt giving nothing
    back leaves it where it stopped."""
    cloth = Cloth()
    ball = rolling(0.0, -300.0)
    slow = cloth.rollingDecay()
    stop = 2130.0 - 300.0 ** 2 / (2.0 * slow)
    stopped = cloth.advanced(ball, 300.0 / slow + 1e-6, RADIUS)
    self.assertTrue(stopped.settling)
    self.assertGreater(stopped.vy, 0.0)
    for slip in cloth.slipOf(stopped, RADIUS):
      self.assertAlmostEqual(slip, 0.0, 9)
    back = math.sqrt(2.0 * slow * cloth.rollBack)
    self.assertAlmostEqual(stopped.vy, back, 3)
    self.assertAlmostEqual(cloth.energyOf(stopped, RADIUS),
                           0.5e-6 * 1.4 * back * back, 7)
    rest = cloth.advanced(stopped, 5.0, RADIUS)
    self.assertEqual(cloth.phaseOf(rest, RADIUS), 'still')
    self.assertAlmostEqual(rest.y, stop + cloth.rollBack, 6)
    self.assertEqual(cloth.advanced(rest, 5.0, RADIUS), rest)
    again = cloth.advanced(Ball('red', rest.x, rest.y, rest.turn, 0.0,
                                -300.0, 300.0 / RADIUS, 0.0, 0.0), 30.0,
                           RADIUS)
    self.assertAlmostEqual(again.y, rest.y - 300.0 ** 2 / (2.0 * slow)
                           + cloth.rollBack, 6)
    dead = Cloth(*Cloth()[:4], 0.0)
    self.assertAlmostEqual(dead.advanced(ball, 30.0, RADIUS).y, stop, 6)

  def test_turn(self) -> None:
    """Rolled to rest and settled back, a ball has turned by the distance
    it rolled on, less the distance it settled back, over its radius,
    about the axis across its path."""
    cloth = Cloth()
    ball = rolling(0.0, -50.0)
    rest = cloth.advanced(ball, 10.0, RADIUS)
    distance = 50.0 ** 2 / (2.0 * cloth.rollingDecay()) - cloth.rollBack
    w, x, y, z = rest.turn
    self.assertAlmostEqual(2.0 * math.acos(w), distance / RADIUS, 6)
    self.assertGreater(x, 0.0)
    self.assertAlmostEqual(y, 0.0, 12)
    self.assertAlmostEqual(z, 0.0, 12)
    self.assertAlmostEqual(w * w + x * x + y * y + z * z, 1.0, 12)
