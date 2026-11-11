"""
TestMatch covers 'Match', a three-cushion match kept as the FFB's Code
sportif carambole has it: the lag and the choice of who breaks, the
breaker playing white; points continuing the inning, a miss passing the
turn; runs, best runs and averages; the equalizing inning from the
start; a draw; the innings limit; sets, broken in turn; nothing counting
while there is no shot to judge.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.billiards import Call, Match, Rules

from . import BilliardsTest

POINT = Call(True, False, '2.2.05', 'Point', ())
MISS = Call(False, False, '2.2.01', 'No point', ())
FOUL = Call(False, True, '2.1.12', 'Foul', ())


def played(match: Match, calls: tuple) -> Match:
  """'match' after each of 'calls' in turn."""
  for call in calls:
    match = match.judged(call)
  return match


def plain(distance: int) -> Match:
  """A match to 'distance' with no lag, the first player breaking."""
  return Match(Rules(3, distance, 0, True, 0, 0.0, False)).begun()


class TestMatch(BilliardsTest):
  """Tests for 'Match'."""

  def test_lag(self) -> None:
    """The players lag; a lag with no winner is played again; the
    winner chooses, and whoever breaks plays white."""
    match = Match().begun()
    self.assertEqual(match.phase, 'lag')
    self.assertEqual(match.cueBall(), '')
    self.assertIs(match.lagged(''), match)
    chose = match.lagged('yellow')
    self.assertEqual((chose.phase, chose.current), ('choose', 1))
    let = chose.chosen(False)
    self.assertEqual((let.phase, let.current, let.balls),
                     ('break', 0, ('white', 'yellow')))
    broke = chose.chosen(True)
    self.assertEqual((broke.current, broke.balls), (1, ('yellow', 'white')))
    self.assertEqual(broke.cueBall(), 'white')
    self.assertTrue(broke.needsOpening())
    self.assertEqual(broke.innings, (0, 1))

  def test_innings(self) -> None:
    """Points continue the inning, a miss or a foul passes the turn; the
    run, the best run and the averages are kept."""
    match = played(plain(10), (POINT, POINT, MISS))
    self.assertEqual((match.current, match.scores, match.run),
                     (1, (2, 0), 0))
    self.assertEqual(match.innings, (1, 1))
    self.assertFalse(match.needsOpening())
    match = played(match, (POINT, FOUL, POINT, POINT, POINT, MISS))
    self.assertEqual(match.scores, (5, 1))
    self.assertEqual(match.best, (3, 1))
    self.assertEqual(match.innings, (2, 2))
    self.assertAlmostEqual(match.average(0), 2.5, 12)
    self.assertAlmostEqual(match.average(1), 0.5, 12)

  def test_equalizing(self) -> None:
    """The breaker reaching the distance, the other plays an equalizing
    last inning from the start; the match ends after it."""
    match = played(plain(2), (POINT, POINT))
    self.assertEqual((match.phase, match.current, match.final),
                     ('equalizing', 1, True))
    self.assertTrue(match.needsOpening())
    self.assertEqual(match.cueBall(), 'yellow')
    won = match.judged(MISS)
    self.assertEqual((won.phase, won.winner), ('over', 0))
    drawn = played(match, (POINT, POINT))
    self.assertEqual((drawn.phase, drawn.winner), ('over', 2))
    self.assertIn('draw', drawn.said())
    self.assertIs(won.judged(POINT), won)

  def test_second_finishes(self) -> None:
    """The second player reaching the distance in a regular inning ends
    the match at once, the innings being equal."""
    match = played(plain(2), (MISS, POINT, POINT))
    self.assertEqual((match.phase, match.winner), ('over', 1))

  def test_innings_limit(self) -> None:
    """With a limit of two innings, the match ends once both have played
    two, the second's last from the start; level, it is a draw."""
    match = Match(Rules(3, 40, 2, True, 0, 0.0, False)).begun()
    match = played(match, (POINT, MISS, MISS, POINT, MISS))
    self.assertEqual((match.phase, match.current), ('equalizing', 1))
    self.assertEqual(match.scores, (2, 0))
    match = played(match, (POINT, POINT, MISS))
    self.assertEqual((match.phase, match.winner), ('over', 2))

  def test_sets(self) -> None:
    """In sets, a set's winner gets two set points; the next set is
    broken by the other player, who keeps his ball; the match ends at
    twice the sets to win."""
    match = Match(Rules(3, 1, 0, True, 2, 0.0, False)).begun()
    match = played(match, (POINT, MISS))
    self.assertEqual((match.setPoints, match.setNumber), ((2, 0), 2))
    self.assertEqual((match.phase, match.current, match.cueBall()),
                     ('break', 1, 'yellow'))
    self.assertEqual(match.scores, (0, 0))
    match = played(match, (POINT, MISS))
    self.assertEqual((match.setPoints, match.phase), ((2, 2), 'break'))
    self.assertEqual((match.current, match.cueBall()), (0, 'white'))
    match = played(match, (POINT, MISS))
    self.assertEqual((match.phase, match.winner), ('over', 0))
    self.assertEqual(match.setPoints, (4, 2))
    self.assertEqual(match.totals, (2, 1))
