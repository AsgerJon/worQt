"""
TestKegleMatch covers 'KegleMatch', a keglebillard match as DDBU's
rules have it: played to 200 to 800 in hundreds; the lag's winner
chooses who lays out, the first shot from the layout, red in hand; a
series goes on while it scores and ends on a shot scoring nothing or a
foul; red pocketed, the other plays red from in hand, a ball off the
table, from a new layout; both have as many series: the one who laid
out reaching the distance, the other plays a last series from a new
layout, a draw if he reaches it too, else a loss; the other reaching it
first wins at once.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.billiards import DISTANCES, KegleCall, KegleMatch, Streak

from . import BilliardsTest


def scored(points: int) -> KegleCall:
  """A shot scoring 'points'."""
  return KegleCall(points, False, '3.4', '', False, points // 2, Streak())


def foul(rule: str) -> KegleCall:
  """A foul on 'rule'."""
  return KegleCall(0, True, rule, '', False, 0, Streak())


MISS = KegleCall(0, False, '7.1', '', False, 0, Streak())


def started(distance: int = 200) -> KegleMatch:
  """A match to 'distance', the first player laying out."""
  match = KegleMatch(('Ann', 'Bo'), distance).begun()
  return match.lagged('white').chosen(True)


class TestKegleMatch(BilliardsTest):
  """Tests for 'KegleMatch'."""

  def test_distances(self) -> None:
    """Played to 200 to 800 in hundreds, nothing else."""
    self.assertEqual(DISTANCES, tuple(range(200, 900, 100)))
    with self.assertRaises(ValueError):
      KegleMatch(('Ann', 'Bo'), 250).begun()

  def test_lag_and_layout(self) -> None:
    """The lag's winner chooses; whoever lays out starts from the
    layout, red in hand; letting the other lay out, he does."""
    match = KegleMatch(('Ann', 'Bo'), 300).begun()
    self.assertEqual(match.phase, 'lag')
    self.assertEqual(match.cueBall(), '')
    match = match.lagged('yellow')
    self.assertEqual((match.phase, match.lagWinner), ('choose', 1))
    laid = match.chosen(False)
    self.assertEqual((laid.phase, laid.starter, laid.current),
                     ('play', 0, 0))
    self.assertTrue(laid.layout and laid.inHand)
    self.assertEqual(laid.cueBall(), 'red')

  def test_series(self) -> None:
    """A series goes on while it scores, the layout gone; a shot
    scoring nothing passes the turn, as does a foul, the foul's points
    nought; red pocketed, the other plays red from in hand; a ball off
    the table, from a new layout."""
    match = started().judged(scored(6)).judged(scored(4))
    self.assertEqual((match.current, match.run, match.scores),
                     (0, 10, (10, 0)))
    self.assertFalse(match.layout or match.inHand)
    passed = match.judged(MISS)
    self.assertEqual((passed.current, passed.run, passed.series),
                     (1, 0, (1, 0)))
    self.assertEqual(passed.best, (10, 0))
    red = match.judged(foul('5.7'))
    self.assertEqual((red.current, red.scores), (1, (10, 0)))
    self.assertTrue(red.inHand)
    self.assertFalse(red.layout)
    off = match.judged(foul('11'))
    self.assertTrue(off.layout and off.inHand)

  def test_last_series(self) -> None:
    """The one who laid out reaches the distance: the other plays his
    last series from a new layout, a draw if he reaches it too, a loss
    if not."""
    match = started(200).judged(scored(200))
    self.assertEqual((match.phase, match.current, match.final),
                     ('play', 1, True))
    self.assertTrue(match.layout)
    lost = match.judged(scored(14)).judged(MISS)
    self.assertEqual((lost.phase, lost.winner), ('over', 0))
    self.assertEqual(lost.series, (1, 1))
    drawn = match.judged(scored(150)).judged(scored(50))
    self.assertEqual((drawn.phase, drawn.winner), ('over', 2))

  def test_other_reaches_first(self) -> None:
    """The other player reaching the distance first, with as many
    series, wins at once."""
    match = started(200).judged(MISS).judged(scored(200))
    self.assertEqual((match.phase, match.winner), ('over', 1))
    self.assertEqual(match.series, (1, 1))
    self.assertIn('Bo wins', match.said())
