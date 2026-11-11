"""
TestReferee covers 'Referee', judging three-cushion shots as the FFB's
Code sportif carambole has it: a point is both object balls with three
cushions at least before the second, the same cushion counting again,
those after or by other balls not counting; missing a ball, or too few
cushions, is no point; fouls void the point: struck early, over the
clock, with the opponent's ball, into a ball or cushion frozen to the
cue ball, a ball off the table (to be respotted), a break not hitting
the red first; the lag is won nearest the head cushion, lost touching
anything but the short cushions; a call is known at the touch deciding
it, or once all rest; and the user's first break, played through the
engine, is a point.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.billiards import Ball, CaromTable, Motion
from worQt.gaming.billiards import Referee, Rules, Shot, Touch

from . import BilliardsTest, breakAim, firstBreak

TABLE = CaromTable()
REFEREE = Referee()
OPENING = TABLE.opening()


def cushion(ball: str, side: str) -> Touch:
  """'ball' touching the cushion 'side'."""
  return Touch('cushion', ball, side)


def meets(first: str, second: str) -> Touch:
  """Balls 'first' and 'second' meeting."""
  return Touch('ball', first, second)


def shot(touches: tuple, opening: bool) -> Shot:
  """White struck from the opening position, the touches so, aimed down
  the table, on time, by its owner."""
  return Shot('white', 'white', OPENING, touches, OPENING, opening, 0.0,
              -1.0, False, False)


class TestReferee(BilliardsTest):
  """Tests for 'Referee'."""

  def test_point(self) -> None:
    """Red, three cushions, yellow: a point, in words with the
    article."""
    touches = (meets('white', 'red'), cushion('white', 'foot'),
               cushion('white', 'left'), cushion('red', 'right'),
               cushion('white', 'head'), meets('yellow', 'white'))
    call = REFEREE.call(shot(touches, False))
    self.assertTrue(call.point)
    self.assertFalse(call.foul)
    self.assertEqual(call.article, '2.2.05')
    self.assertIn('three cushions before the yellow', call.words)

  def test_same_cushion_counts(self) -> None:
    """The same cushion touched again counts again."""
    touches = (cushion('white', 'foot'), cushion('white', 'foot'),
               meets('white', 'red'), cushion('white', 'foot'),
               meets('white', 'yellow'))
    self.assertTrue(REFEREE.call(shot(touches, False)).point)

  def test_no_point(self) -> None:
    """Two cushions before the second ball is no point; cushions after
    it, or touched by other balls, do not help; missing a ball is no
    point."""
    touches = (meets('white', 'red'), cushion('white', 'foot'),
               cushion('red', 'left'), cushion('white', 'left'),
               meets('white', 'yellow'), cushion('white', 'head'))
    call = REFEREE.call(shot(touches, False))
    self.assertFalse(call.point)
    self.assertFalse(call.foul)
    self.assertIn('two cushions before the yellow', call.words)
    missed = REFEREE.call(shot((meets('white', 'red'),), False))
    self.assertFalse(missed.point)
    self.assertIn('missed the yellow', missed.words)
    nothing = REFEREE.call(shot((), False))
    self.assertIn('missed the yellow and the red', nothing.words)
    fewer = Referee(Rules(1)).call(shot(touches, False))
    self.assertTrue(fewer.point)

  def test_fouls(self) -> None:
    """Struck early, late or with the opponent's ball, a carom is a
    foul and no point."""
    touches = (meets('white', 'red'), cushion('white', 'foot'),
               cushion('white', 'left'), cushion('white', 'head'),
               meets('white', 'yellow'))
    for early, late, owner, article in ((True, False, 'white', '2.1.17-1'),
                                        (False, True, 'white', '2.1.17-6'),
                                        (False, False, 'yellow',
                                         '2.1.17-5')):
      call = REFEREE.call(Shot('white', owner, OPENING, touches, OPENING,
                               False, 0.0, -1.0, early, late))
      self.assertTrue(call.foul)
      self.assertFalse(call.point)
      self.assertEqual(call.article, article)

  def test_frozen(self) -> None:
    """Frozen to the red, white played into it is a foul, played away
    is not; frozen to a cushion, played into it is a foul."""
    reach = Motion().reach()
    white = Ball('white', 400.0, 1000.0)
    red = Ball('red', 400.0 - 2.0 * TABLE.radius, 1000.0)
    yellow = Ball('yellow', 1000.0, 2000.0)
    balls = (white, yellow, red)
    self.assertEqual(REFEREE.frozenTo(balls, 'white'), (('red',), ()))
    into = Shot('white', '', balls, (), balls, False, -1.0, 0.2, False,
                False)
    call = REFEREE.call(into)
    self.assertTrue(call.foul)
    self.assertEqual(call.article, '2.1.12')
    away = Shot('white', '', balls, (), balls, False, 1.0, 0.2, False,
                False)
    self.assertFalse(REFEREE.call(away).foul)
    walled = (Ball('white', 700.0, reach), yellow, Ball('red', 710.0,
                                                         710.0))
    self.assertEqual(REFEREE.frozenTo(walled, 'white'), ((), ('foot',)))
    call = REFEREE.call(Shot('white', '', walled, (), walled, False, 0.3,
                             -1.0, False, False))
    self.assertTrue(call.foul)
    self.assertIn('foot cushion', call.words)

  def test_off_the_table(self) -> None:
    """A ball leaving the table is a foul, the ball to be respotted."""
    touches = (meets('white', 'red'), Touch('off', 'red', ''))
    call = REFEREE.call(shot(touches, False))
    self.assertTrue(call.foul)
    self.assertEqual(call.article, '2.1.14')
    self.assertEqual(call.respot, ('red',))

  def test_break(self) -> None:
    """The break must hit the red first, directly."""
    yellowFirst = (meets('white', 'yellow'), meets('white', 'red'))
    call = REFEREE.call(shot(yellowFirst, True))
    self.assertTrue(call.foul)
    self.assertEqual(call.article, '2.2.03')
    cushionFirst = (cushion('white', 'foot'), meets('white', 'red'))
    self.assertTrue(REFEREE.call(shot(cushionFirst, True)).foul)
    redFirst = (meets('red', 'white'), cushion('white', 'foot'))
    self.assertFalse(REFEREE.call(shot(redFirst, True)).foul)

  def test_lag(self) -> None:
    """The lag is won nearest the head cushion, the near one; touching
    anything but the short cushions, the near one before the far one, or
    the far one twice, loses it; both faulty or a tie, it is played
    again."""
    lag = TABLE.lagPosition()
    white = Ball('white', 1220.0, TABLE.length - 100.0)
    yellow = Ball('yellow', 200.0, TABLE.length - 300.0)
    after = (white, yellow, lag[2])
    fair = (cushion('white', 'foot'), cushion('yellow', 'foot'))
    self.assertEqual(REFEREE.lagCall(fair, after)[0], 'white')
    touched = fair + (cushion('white', 'right'),)
    self.assertEqual(REFEREE.lagCall(touched, after)[0], 'yellow')
    twice = fair + (cushion('yellow', 'foot'),)
    self.assertEqual(REFEREE.lagCall(twice, after)[0], 'white')
    backwards = (cushion('white', 'head'), cushion('white', 'foot'),
                 cushion('yellow', 'foot'))
    winner, words = REFEREE.lagCall(backwards, after)
    self.assertEqual(winner, 'yellow')
    self.assertIn('near cushion before the far one', words)
    back = fair + (cushion('white', 'head'),)
    self.assertEqual(REFEREE.lagCall(back, after)[0], 'white')
    self.assertIn('from the near cushion', REFEREE.lagCall(fair, after)[1])
    both = (meets('white', 'yellow'), cushion('white', 'foot'))
    self.assertEqual(REFEREE.lagCall(both, after)[0], '')
    level = (Ball('white', 1220.0, 2500.0), Ball('yellow', 200.0, 2500.0),
             lag[2])
    self.assertEqual(REFEREE.lagCall(fair, level)[0], '')

  def test_decided_at(self) -> None:
    """A call is known: a point, or too few cushions, at the touch with
    the second object ball; a foul before the cue ball moves at once; a
    ball off the table at the touch it leaves by; a break not hitting
    the red first at the cue ball's first touch; a miss once all
    rest."""
    point = (meets('white', 'red'), cushion('white', 'foot'),
             cushion('white', 'left'), cushion('white', 'head'),
             meets('yellow', 'white'), cushion('white', 'right'))
    self.assertEqual(REFEREE.decidedAt(shot(point, False)), 5)
    short = (meets('white', 'red'), cushion('white', 'foot'),
             meets('white', 'yellow'), cushion('white', 'left'))
    self.assertEqual(REFEREE.decidedAt(shot(short, False)), 3)
    late = Shot('white', 'white', OPENING, point, OPENING, False, 0.0,
                -1.0, False, True)
    self.assertEqual(REFEREE.decidedAt(late), 0)
    off = (meets('white', 'red'), Touch('off', 'red', ''),
           cushion('white', 'foot'))
    self.assertEqual(REFEREE.decidedAt(shot(off, False)), 2)
    cushionFirst = (cushion('white', 'foot'), meets('white', 'red'))
    self.assertEqual(REFEREE.decidedAt(shot(cushionFirst, True)), 1)
    redFirst = (meets('red', 'white'), cushion('white', 'foot'))
    self.assertEqual(REFEREE.decidedAt(shot(redFirst, True)), -1)
    missed = (meets('white', 'red'), cushion('white', 'foot'),
              meets('red', 'yellow'))
    self.assertEqual(REFEREE.decidedAt(shot(missed, False)), -1)

  def test_first_break(self) -> None:
    """The user's first break, 4.0 m/s, 0.38 R up, 0.26 R left, past
    the red's right ('breakAim'), sent as the window sends it, played
    through the engine: three cushions before the yellow, a point."""
    white, yellow, red = OPENING
    aimX, aimY = breakAim(white, red, TABLE.radius)
    after, touches = Motion().played(firstBreak(), 30.0)
    call = REFEREE.call(Shot('white', 'white', OPENING, touches, after,
                             True, aimX, aimY, False, False))
    self.assertTrue(call.point)
    self.assertIn('before the yellow', call.words)
