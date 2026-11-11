"""
TestKegleReferee covers 'KegleReferee', calling keglebillard shots as
DDBU's rules have them: a pin a white topples scores 2, red meeting
both whites 4, at most 14 together; a shot scoring nothing ends the
series without a foul; fouls score nought: a ball off the table, red
in a pocket, a pin credited to red, red from in hand striking a white
on its own half before crossing the middle line, pins twice running
without a cushion (red alone counting as one), and red three times
running without pins.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.billiards import KegleReferee, KegleShot, Streak, Touch

from . import BilliardsTest

REFEREE = KegleReferee()
RED = (Touch('ball', 'red', 'white'), Touch('ball', 'red', 'yellow'))
CUSHION = (Touch('cushion', 'white', 'foot'),)


def shot(touches: tuple = (), fallen: tuple = ()) -> KegleShot:
  """A shot: its contacts, and the pins down and whom they are
  credited to."""
  return KegleShot(tuple(touches), tuple(fallen))


def fromHand(redY: float, first: tuple | None) -> KegleShot:
  """Red made from in hand, put down at 'redY' along the table, its
  first strike on a white 'first', ('crossed', the white's 'y')."""
  return KegleShot(RED, (), True, (700.0, redY), first)


class TestKegleReferee(BilliardsTest):
  """Tests for 'KegleReferee'."""

  def test_points(self) -> None:
    """A pin a white topples scores 2, red meeting both whites 4,
    both together at most 14; red meeting one white scores nothing."""
    pins = shot(CUSHION + (Touch('ball', 'red', 'white'),),
                ((1, 'white'), (3, 'white')))
    call = REFEREE.call(pins, Streak())
    self.assertEqual((call.points, call.foul, call.pins), (4, False, 2))
    call = REFEREE.call(shot(RED), Streak())
    self.assertEqual((call.points, call.red), (4, True))
    full = shot(RED + CUSHION, tuple((k, 'yellow') for k in range(5)))
    self.assertEqual(REFEREE.call(full, Streak()).points, 14)
    single = REFEREE.call(shot(RED[:1]), Streak())
    self.assertEqual((single.points, single.foul), (0, False))
    self.assertEqual(single.streak, Streak())

  def test_fouls(self) -> None:
    """Off the table, red pocketed, a pin credited to red: fouls,
    scoring nought, whatever else the shot made."""
    for touches, fallen, rule in (
        ((Touch('off', 'yellow', ''),) + RED, (), '11'),
        (RED + (Touch('pocket', 'red', 'corner'),), (), '5.7'),
        (RED + CUSHION, ((0, 'white'), (2, 'red')), '5.8')):
      call = REFEREE.call(shot(touches, fallen), Streak())
      self.assertEqual((call.points, call.foul, call.rule), (0, True, rule))
      self.assertEqual(call.streak, Streak())
    pocketed = REFEREE.call(shot(RED + (Touch('pocket', 'white',
                                              'corner'),)), Streak())
    self.assertFalse(pocketed.foul)

  def test_in_hand(self) -> None:
    """From in hand, red must cross the middle line before it strikes
    a white, or strike one on the line or past it; from either end."""
    for redY, ownHalf, line, past in ((2500.0, 1600.0, 1420.0, 1300.0),
                                      (300.0, 1000.0, 1420.0, 1600.0)):
      near = REFEREE.call(fromHand(redY, (False, ownHalf)), Streak())
      self.assertEqual((near.foul, near.rule), (True, '9.4'))
      for first in ((True, ownHalf), (False, line), (False, past)):
        call = REFEREE.call(fromHand(redY, first), Streak())
        self.assertFalse(call.foul)
    self.assertFalse(REFEREE.call(fromHand(2500.0, None), Streak()).foul)

  def test_cushion_every_other(self) -> None:
    """Pins without a ball in a cushion are due one the next time pins
    fall; then a foul; with a cushion, or red alone between, not."""
    bare = shot((Touch('ball', 'red', 'white'),), ((0, 'white'),))
    first = REFEREE.call(bare, Streak())
    self.assertFalse(first.foul)
    self.assertTrue(first.streak.cushionDue)
    second = REFEREE.call(bare, first.streak)
    self.assertEqual((second.foul, second.rule), (True, '5.11'))
    cushioned = shot(CUSHION + (Touch('ball', 'red', 'white'),),
                     ((0, 'white'),))
    self.assertFalse(REFEREE.call(cushioned, first.streak).foul)
    between = REFEREE.call(shot(RED), first.streak)
    self.assertFalse(between.streak.cushionDue)
    self.assertFalse(REFEREE.call(bare, between.streak).foul)

  def test_third_red(self) -> None:
    """Red a third time running without pins is a foul; pins between
    begin the count again (the user: every third shot must get pin
    points)."""
    streak = Streak()
    for _ in range(2):
      call = REFEREE.call(shot(RED), streak)
      self.assertFalse(call.foul)
      streak = call.streak
    self.assertEqual(streak.reds, 2)
    third = REFEREE.call(shot(RED), streak)
    self.assertEqual((third.foul, third.rule, third.points),
                     (True, '5.12', 0))
    pins = REFEREE.call(shot(RED + CUSHION, ((0, 'white'),)), streak)
    self.assertFalse(pins.foul)
    self.assertEqual(pins.streak.reds, 0)
