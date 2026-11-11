"""
TestUnfolded covers 'Unfolded', the table unfolded: a copy is the cloth
less a ball's reach at each side, the table itself copy (0, 0); a ball
shows mirrored across in odd copies across and along in odd copies
along; the map shows the copies asked for. The cue ball's way runs
from it straight along the aim to the first cushion's line, as the ball
runs, then turns there as the engine's cushions turn a ball: coming off
flatter, a mirror at most, the English pushing it along the cushion to
its right with right English, the other way in a mirrored copy; it is
straight between the lines and stops leaving the map. Its
crossings are the cushions' lines it crosses, in order, a straight line
across the table meeting the long cushions where it should. The arc
meets a ball's image two radii from its middle, exactly, how far off
the middle known; the cue ball stunned near the tip, rolling far off,
drawing struck low; at a half-ball hit, rolling, the cue ball leaves
near 34 degrees off its way and the ball met at 30, stunned along the
tangent line; a fan holds three ways a ball, as many points each, the
aim off one standard deviation either side and as aimed; it spreads
the wider the further the ball is met; at a graze the cue ball's far
way misses, going on past, and the ball met's is its thinnest cut. A
ball struck sets off as the cue has it, stunned in the middle, rolling
at the roll height, drawing below; on the cloth a sliding ball's speed
and spin draw together to rolling, a rolling one slows steadily, and
it stops; at a cushion met square on its speed comes back as 'bounce'
of it and its spin is turned round, so draw comes off as follow and,
the cushion keeping the spin, speeds the ball up; the arc ends where
the ball stops, as 'stateAfter' has it along the arc.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import Ball, CaromTable, Cloth, Cue, Motion
from worQt.gaming.billiards import Recorder, Unfolded

from . import BilliardsTest

TABLE = CaromTable()
UNFOLDED = Unfolded()
REACH = 2.0 * TABLE.radius
#  The aim exact: the hit as aimed.
EXACT = Unfolded(TABLE, 2, 1, 10.0, 0.0)


def _unitOf(x: float, y: float) -> tuple[float, float]:
  """'x', 'y' made of length one."""
  length = math.hypot(x, y)
  return x / length, y / length


def leftOf(start: tuple, aim: tuple, place: tuple) -> float:
  """How far 'place' lies left of the line from 'start' along 'aim', of
  length one, seen from above; below nought, right of it."""
  dx, dy = place[0] - start[0], place[1] - start[1]
  return aim[0] * dy - aim[1] * dx


class TestUnfolded(BilliardsTest):
  """Tests for 'Unfolded'."""

  def test_tile(self) -> None:
    """A copy is the cloth less a ball's reach at each side; the table
    itself is copy (0, 0)."""
    reach = Motion().reach()
    across, along = UNFOLDED.tile()
    self.assertAlmostEqual(across, TABLE.width - 2.0 * reach, 9)
    self.assertAlmostEqual(along, TABLE.length - 2.0 * reach, 9)
    expected = (reach, reach, TABLE.width - reach, TABLE.length - reach)
    for corner, value in zip(UNFOLDED.corners(0, 0), expected):
      self.assertAlmostEqual(corner, value, 9)

  def test_images(self) -> None:
    """On the table itself a ball is where it lies; across, mirrored in
    the cushion's line; along, mirrored in the short cushion's; one copy
    on both ways, mirrored both ways."""
    reach = UNFOLDED.reach()
    x, y = 400.0, 900.0
    image = UNFOLDED.imageOf(x, y, 0, 0)
    self.assertAlmostEqual(image[0], x, 9)
    self.assertAlmostEqual(image[1], y, 9)
    right = TABLE.width - reach
    image = UNFOLDED.imageOf(x, y, 1, 0)
    self.assertAlmostEqual(image[0], 2.0 * right - x, 9)
    self.assertAlmostEqual(image[1], y, 9)
    image = UNFOLDED.imageOf(x, y, 0, -1)
    self.assertAlmostEqual(image[0], x, 9)
    self.assertAlmostEqual(image[1], 2.0 * reach - y, 9)
    image = UNFOLDED.imageOf(x, y, -1, 1)
    head = TABLE.length - reach
    self.assertAlmostEqual(image[0], 2.0 * reach - x, 9)
    self.assertAlmostEqual(image[1], 2.0 * head - y, 9)
    across, _ = UNFOLDED.tile()
    image = UNFOLDED.imageOf(x, y, 2, 0)
    self.assertAlmostEqual(image[0], x + 2.0 * across, 9)

  def test_copies(self) -> None:
    """The map shows 'across' copies either side across and 'along'
    either side along, the table among them; its bounds hold them."""
    copies = UNFOLDED.copies()
    self.assertEqual(len(copies), (2 * UNFOLDED.across + 1)
                     * (2 * UNFOLDED.along + 1))
    self.assertIn((0, 0), copies)
    low = UNFOLDED.bounds()
    for i, j in copies:
      corners = UNFOLDED.corners(i, j)
      self.assertGreaterEqual(corners[0], low[0] - 1e-9)
      self.assertLessEqual(corners[3], low[3] + 1e-9)

  def test_straight_without_side(self) -> None:
    """Without side, at cushions keeping the whole part across, as
    mirrors, the arc is a straight line along the aim."""
    start, aim = (500.0, 1000.0), (0.6, 0.8)
    mirrors = Unfolded(TABLE, 2, 1, 10.0, 0.25, 0.9, 0.4, 0.0, 0.97,
                       1.0, 0.0, 0.0)
    arc = mirrors.arcOf(*start, *aim, 0.0, 3000.0)
    self.assertGreater(len(arc), 10)
    self.assertEqual(arc[0], start)
    for place in arc:
      self.assertAlmostEqual(leftOf(start, aim, place), 0.0, 6)

  def test_bends_the_way_of_the_english(self) -> None:
    """With English the way runs straight along the aim to the first
    cushion's line, as the ball does, then turns there: right English to
    the right of the way without English, seen from above, left English
    to the left; between the lines it is straight."""
    start, aim = (500.0, 1000.0), (0.6, 0.8)
    plain = UNFOLDED.arcOf(*start, *aim, 0.0, 3000.0)
    right = UNFOLDED.arcOf(*start, *aim, 0.3, 3000.0)
    left = UNFOLDED.arcOf(*start, *aim, -0.3, 3000.0)
    for way in (plain, right, left):
      first = UNFOLDED.crossingsOf(way)[0]
      reach = math.hypot(first.x - start[0], first.y - start[1])
      for place in way:
        if math.hypot(place[0] - start[0], place[1] - start[1]) <= reach:
          self.assertAlmostEqual(leftOf(start, aim, place), 0.0, 6)

    def after(way: tuple) -> tuple[float, float]:
      first = UNFOLDED.crossingsOf(way)[0]
      k = way.index((first.x, first.y))
      return _unitOf(way[k + 1][0] - way[k][0], way[k + 1][1] - way[k][1])

    self.assertLess(leftOf((0.0, 0.0), after(plain), after(right)), 0.0)
    self.assertGreater(leftOf((0.0, 0.0), after(plain), after(left)), 0.0)
    corners = [(c.x, c.y) for c in UNFOLDED.crossingsOf(right)[:2]]
    (x0, y0), (x1, y1) = corners
    between = [p for p in right
               if min(x0, x1) <= p[0] <= max(x0, x1)
               and min(y0, y1) <= p[1] <= max(y0, y1)]
    way = _unitOf(x1 - x0, y1 - y0)
    for place in between:
      self.assertAlmostEqual(leftOf((x0, y0), way, place), 0.0, 6)

  def test_kicked(self) -> None:
    """At a cushion's line the way keeps 'flatten' of its part across,
    a mirror at one; right English pushes it along the cushion to the
    ball's right by 'sidePush' times the side times the part across, the
    other way in a mirrored copy."""
    mirror = Unfolded(TABLE, 2, 1, 10.0, 0.25, 0.88, 0.1, -0.4, 1.0, 1.0,
                      0.0, 0.0, 0.0)
    rolling = (2000.0, 2000.0)
    self.assertEqual(mirror.kicked(0.6, 0.8, True, rolling, 0.0, False),
                     (0.6, 0.8))
    half = Unfolded(TABLE, 2, 1, 10.0, 0.25, 0.88, 0.1, -0.4, 1.0, 0.5,
                    0.0, 0.0, 0.0)
    hx, hy = half.kicked(0.6, 0.8, True, rolling, 0.0, False)
    self.assertAlmostEqual(hx / hy, 0.3 / 0.8, 9)
    pushed = Unfolded(TABLE, 2, 1, 10.0, 0.25, 0.88, 0.1, -0.4, 1.0, 1.0,
                      0.0, 0.0, 1.0)
    hx, hy = pushed.kicked(1.0, 0.0, True, rolling, 0.5, False)
    self.assertLess(hy, 0.0)
    hx, hy = pushed.kicked(1.0, 0.0, True, rolling, 0.5, True)
    self.assertGreater(hy, 0.0)
    hx, hy = pushed.kicked(1.0, 0.0, True, rolling, -0.5, False)
    self.assertGreater(hy, 0.0)
    hx, hy = UNFOLDED.kicked(0.6, 0.8, True, rolling, 0.0, False)
    self.assertLess(abs(hx), 0.6)

  def test_ends(self) -> None:
    """The arc stops as it leaves the map, its last point just past the
    edge."""
    low = UNFOLDED.bounds()
    arc = UNFOLDED.arcOf(500.0, 1000.0, 0.0, 1.0, 0.0, 3000.0)
    self.assertGreater(arc[-1][1], low[3])
    self.assertLessEqual(arc[-2][1], low[3])

  def test_crossings(self) -> None:
    """A straight line across the table crosses the long cushions' lines
    one copy apart, where it crosses them, nothing else."""
    reach = UNFOLDED.reach()
    across, _ = UNFOLDED.tile()
    arc = UNFOLDED.arcOf(500.0, 1000.0, 1.0, 0.0, 0.0, 3000.0)
    crossings = UNFOLDED.crossingsOf(arc)
    self.assertGreaterEqual(len(crossings), 2)
    for k, crossing in enumerate(crossings[:2]):
      self.assertTrue(crossing.long)
      self.assertAlmostEqual(crossing.x, reach + (k + 1) * across, 6)
      self.assertAlmostEqual(crossing.y, 1000.0, 6)

  def test_corner_crossings(self) -> None:
    """A line toward a corner crosses a long and a short cushion's line,
    in the order it meets them."""
    reach = UNFOLDED.reach()
    start = (TABLE.width - reach - 100.0, TABLE.length - reach - 300.0)
    arc = UNFOLDED.arcOf(*start, 1.0, 1.0, 0.0, 3000.0)
    crossings = UNFOLDED.crossingsOf(arc)
    self.assertTrue(crossings[0].long)
    self.assertFalse(crossings[1].long)
    self.assertAlmostEqual(crossings[0].x, TABLE.width - reach, 6)
    self.assertAlmostEqual(crossings[1].y, TABLE.length - reach, 6)

  def test_images_of(self) -> None:
    """Every ball but the cue ball shows in every copy."""
    balls = TABLE.opening()
    images = UNFOLDED.imagesOf(balls, 'white')
    self.assertEqual(len(images), 2 * len(UNFOLDED.copies()))
    self.assertNotIn('white', {name for name, _, _ in images})
    self.assertIn(('red', *TABLE.footSpot()), images)

  def test_hit(self) -> None:
    """A straight arc meets a ball two radii from its middle, exactly,
    knowing how far it went and how far left of its way the ball lies;
    an arc passing wide meets none."""
    arc = UNFOLDED.arcOf(300.0, 700.0, 1.0, 0.0, 0.0, 3000.0)
    hit = UNFOLDED.hitOf(arc, (('red', 900.0, 710.0),))
    self.assertEqual(hit.name, 'red')
    self.assertAlmostEqual(hit.x, 900.0 - math.sqrt(REACH ** 2 - 100.0), 6)
    self.assertAlmostEqual(hit.y, 700.0, 9)
    self.assertAlmostEqual(hit.offset, 10.0, 6)
    self.assertAlmostEqual(hit.travelled, hit.x - 300.0, 6)
    self.assertEqual((hit.dx, hit.dy), (1.0, 0.0))
    self.assertIsNone(UNFOLDED.hitOf(arc, (('red', 900.0, 800.0),)))

  def test_state_of(self) -> None:
    """Struck in the middle, a ball sets off stunned; at the roll height,
    rolling; below the middle, drawing; as fast as it is sent."""
    speed, spin = UNFOLDED.stateOf(0.0, 0.0, 3000.0)
    self.assertAlmostEqual(speed, 3000.0, 6)
    self.assertAlmostEqual(spin, 0.0, 6)
    speed, spin = UNFOLDED.stateOf(Cue().rollHeight(), 0.0, 3000.0)
    self.assertAlmostEqual(spin / speed, 1.0, 6)
    self.assertLess(UNFOLDED.stateOf(-0.4, 0.0, 3000.0)[1], 0.0)

  def test_half_ball(self) -> None:
    """At a half-ball hit the ball met leaves 30 degrees off the cue
    ball's way; the cue ball, rolling, near 34 the other way (the 30
    degree rule at its most), stunned along the tangent line, square to
    the ball met's way."""
    arc = EXACT.arcOf(300.0, 700.0, 1.0, 0.0, 0.0, 3000.0)
    hit = EXACT.hitOf(arc, (('red', 900.0, 700.0 + TABLE.radius),))

    def heading(path: tuple) -> float:
      (x0, y0), (x1, y1) = path[0], path[1]
      return math.degrees(math.atan2(y1 - y0, x1 - x0))

    rolling = EXACT.fanOf(hit, (3000.0, 3000.0), 0.0, 3000.0)
    self.assertAlmostEqual(heading(rolling.struck[1]), 30.0, 6)
    self.assertAlmostEqual(heading(rolling.cue[1]), -33.67, 1)
    stunned = EXACT.fanOf(hit, (3000.0, 0.0), 0.0, 3000.0)
    self.assertAlmostEqual(heading(stunned.cue[1]), -60.0, 6)

  def test_fan_spreads(self) -> None:
    """A fan holds three ways a ball, as many points each; the ball
    met's ways spread the wider the further the cue ball came."""

    def spread(start: float) -> float:
      arc = UNFOLDED.arcOf(start, 700.0, 1.0, 0.0, 0.0, 3000.0)
      hit = UNFOLDED.hitOf(arc, (('red', 1300.0, 700.0 + 20.0),))
      fan = UNFOLDED.fanOf(hit, (3000.0, 3000.0), 0.0, 3000.0)
      self.assertEqual((len(fan.cue), len(fan.struck)), (3, 3))
      self.assertEqual(len({len(path) for path in fan.cue + fan.struck}),
                       1)
      ways = [math.atan2(p[1][1] - p[0][1], p[1][0] - p[0][0])
              for p in fan.struck]
      return max(ways) - min(ways)

    self.assertGreater(spread(100.0), spread(900.0))

  def test_graze_misses(self) -> None:
    """At a graze the cue ball's way one standard deviation further off
    misses, going on past the ball the way it came; the ball met's way
    there is its thinnest cut, near square to the cue ball's way."""
    arc = UNFOLDED.arcOf(100.0, 700.0, 1.0, 0.0, 0.0, 3000.0)
    hit = UNFOLDED.hitOf(arc, (('red', 1300.0, 700.0 + REACH - 2.0),))
    fan = UNFOLDED.fanOf(hit, (3000.0, 3000.0), 0.0, 3000.0)
    far = fan.cue[2]
    self.assertAlmostEqual(far[1][1] - far[0][1], 0.0, 9)
    self.assertGreater(far[1][0] - far[0][0], 0.0)
    cut = fan.struck[2]
    angle = math.degrees(math.atan2(cut[1][1] - cut[0][1],
                                    cut[1][0] - cut[0][0]))
    self.assertGreater(angle, 85.0)

  def test_rolled_on(self) -> None:
    """A rolling ball slows steadily, its speed squared falling by twice
    the slowing a mm, and stops; a stunned one slides, its speed falling
    and its spin rising until it rolls at five sevenths of its speed; a
    ball with more spin than speed is sped up by it."""
    slow = Cloth().rollingDecay() * UNFOLDED.slowing
    (speed, spin), gone = UNFOLDED.rolledOn((2000.0, 2000.0), 1000.0)
    self.assertAlmostEqual(speed * speed, 2000.0 ** 2 - 2.0 * slow * 1000.0,
                           3)
    self.assertEqual((speed, gone), (spin, 1000.0))
    state, gone = UNFOLDED.rolledOn((500.0, 500.0), 1.0e6)
    self.assertEqual(state, (0.0, 0.0))
    self.assertAlmostEqual(gone, 500.0 ** 2 / (2.0 * slow), 6)
    (speed, spin), _ = UNFOLDED.rolledOn((2000.0, 0.0), 1500.0)
    self.assertAlmostEqual(speed, spin, 6)
    self.assertLess(speed, 5.0 / 7.0 * 2000.0)
    (speed, spin), _ = UNFOLDED.rolledOn((2000.0, 0.0), 1.0)
    self.assertLess(speed, 2000.0)
    self.assertGreater(spin, 0.0)
    (speed, _), _ = UNFOLDED.rolledOn((1000.0, 2000.0), 5.0)
    self.assertGreater(speed, 1000.0)

  def test_bounced(self) -> None:
    """At a cushion met square on, the speed comes back as 'bounce' of
    it and the spin is turned round: draw comes off as follow, which,
    the cushion keeping the spin, speeds the ball up after; met along
    it, nothing changes. As the engine's cushions do, a share of the
    spin is kept, turned round: draw comes off as follow."""
    keeping = Unfolded(TABLE, 2, 1, 10.0, 0.25, 0.8, 1.0, 0.0, 1.0)
    speed, spin = keeping.bounced((1200.0, -1200.0), 1.0)
    self.assertAlmostEqual(speed, 0.8 * 1200.0, 6)
    self.assertAlmostEqual(spin, 1200.0, 6)
    (after, _), _ = keeping.rolledOn((speed, spin), 20.0)
    self.assertGreater(after, speed)
    self.assertEqual(keeping.bounced((1000.0, 300.0), 0.0), (1000.0, 300.0))
    speed, spin = UNFOLDED.bounced((1200.0, -1200.0), 1.0)
    self.assertGreater(spin, 0.0)

  def test_arc_stops(self) -> None:
    """Set off rolling with no cushion on the way, the arc ends where
    the ball stops: its speed squared over twice the slowing on."""
    slow = Cloth().rollingDecay() * UNFOLDED.slowing
    reach = UNFOLDED.reach()
    speed = math.sqrt(2.0 * slow * 600.0)
    arc = UNFOLDED.arcOf(500.0, reach + 100.0, 0.0, 1.0, 0.0, 3000.0,
                         (speed, speed))
    self.assertAlmostEqual(arc[-1][1], reach + 700.0, 6)
    self.assertAlmostEqual(arc[-1][0], 500.0, 9)
    far = UNFOLDED.arcOf(500.0, reach + 100.0, 0.0, 1.0, 0.0, 3000.0)
    self.assertGreater(len(far), len(arc))

  def test_state_agrees(self) -> None:
    """Where the arc stops, 'stateAfter' along the arc has the ball
    still, through corners and lines alike; a step short of the end,
    still moving."""
    full = Unfolded(TABLE, 3, 3)
    white = TABLE.opening()[0]
    for degrees, speed, top in ((-46.0, 4000.0, 0.2), (-42.0, 4000.0, -0.4),
                                (30.0, 2000.0, 0.44), (-70.0, 3000.0, 0.0)):
      aim = (math.cos(math.radians(degrees)),
             math.sin(math.radians(degrees)))
      state = full.stateOf(top, 0.3, speed)
      arc = full.arcOf(white.x, white.y, *aim, 0.3, speed, state)
      low = full.bounds()
      if not (low[0] < arc[-1][0] < low[2] and low[1] < arc[-1][1] < low[3]):
        continue
      self.assertAlmostEqual(full.stateAfter(arc, state)[0], 0.0, 3)
      self.assertGreater(full.stateAfter(arc[:-1], state)[0], 0.0)

  def test_way_of(self) -> None:
    """The engine's way of a ball, unfolded, sets off where the ball lay
    and runs on without a break, a sample at most its speed over the
    rate apart, through as many cushions' lines as it met cushions; each
    sample with the ball's speed and spin then."""
    white = TABLE.opening()[0]
    aim = (math.cos(math.radians(-42.0)), math.sin(math.radians(-42.0)))
    struck = Cue().sent(white, *aim, 4000.0, -0.3, 0.3, TABLE.radius)
    recording = Recorder(Motion(), 250.0).recorded((struck,))
    full = Unfolded(TABLE, 3, 3)
    way = full.wayOf(recording, 'white')
    self.assertEqual(len(way), recording.count())
    self.assertEqual(way[0][:2], (white.x, white.y))
    self.assertAlmostEqual(way[0][2], 4000.0, 6)
    for one, other in zip(way, way[1:]):
      apart = math.hypot(other[0] - one[0], other[1] - one[1])
      self.assertLessEqual(apart, max(one[2], other[2]) / 250.0 + 1.0)
    met = sum(1 for _, touch in recording.touches if touch.kind == 'cushion')
    places = tuple((x, y) for x, y, _, _ in way)
    self.assertEqual(len(full.crossingsOf(places)), met)
    self.assertEqual(way[-1][2], 0.0)

  def test_run_of(self) -> None:
    """A shot as the engine played it, every ball's way unfolded: the
    cue ball sets off where it lay; a ball it meets sets off from the
    copy it was met in, a little over two radii from the cue ball then;
    every way has a sample for each of the shot's."""
    balls = TABLE.opening()
    white, yellow, red = balls
    #  Off one cushion into the red, from -46 to -48 degrees alike, on
    #  Mathavan et al.'s cushion (-42 met nothing once it came in).
    aim = (math.cos(math.radians(-47.0)), math.sin(math.radians(-47.0)))
    struck = Cue().sent(white, *aim, 4000.0, 0.2, 0.3, TABLE.radius)
    recording = Recorder(Motion(), 250.0).recorded((struck, yellow, red))
    run = Unfolded(TABLE, 3, 3).runOf(recording)
    self.assertEqual(run.cue, 'white')
    self.assertTrue(run.meets)
    for name, way in run.ways:
      self.assertEqual(len(way), recording.count())
    cue = run.wayOf('white')
    self.assertEqual(cue[0][:2], (white.x, white.y))
    _, met = run.meets[0]
    self.assertTrue(run.moved(met))
    other = run.wayOf(met)
    first = next(k for k, sample in enumerate(other) if sample[2] > 0.0)
    apart = math.hypot(other[first][0] - cue[first][0],
                       other[first][1] - cue[first][1])
    self.assertGreater(apart, 2.0 * TABLE.radius - 1.0)
    self.assertLess(apart, 2.0 * TABLE.radius + 20.0)
