"""
KegleReferee calls keglebillard shots as Den Danske Billard Union's
rules have it: the points, the fouls, and how the series stands.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from ._kegle_table import KegleTable
from ._referee import Referee

PIN_POINTS = 2  # each pin a white topples (3.4)
RED_POINTS = 4  # red meeting both whites, 'rødt' (3.5)


class KegleShot(NamedTuple):
  """
  KegleShot is a keglebillard shot as the referee sees it, red the cue
  ball: the contacts as they began, 'touches', each a 'Touch' as
  'Motion' logs them, 'pocket' for a ball into a pocket, 'off' for one
  off the table; the pins down once all rest, 'fallen', each its number
  and the ball it is credited to, the ball that first hit it, or the
  ball whose pin did, red when red and a white hit it at once (8.1);
  whether red was played from in hand, 'inHand', put down within a
  quarter of the length of a short cushion, at the start or after it
  was pocketed, and from where, 'redFrom'; and, as red first struck a
  white, whether it had crossed the middle line between the middle
  pockets first and where across the table's length the white lay,
  'firstWhite', ('crossed', 'y'), 'None' if it struck none.
  """

  touches: tuple = ()
  fallen: tuple = ()
  inHand: bool = False
  redFrom: tuple = (0.0, 0.0)
  firstWhite: tuple | None = None


class Streak(NamedTuple):
  """
  Streak is how a series stands for the rules that look back: whether
  the last shot to score pins had no ball in a cushion, so the next
  must, 'cushionDue' (5.11), and how many reds were made in a row
  without pins, 'reds' (5.12). A player may always ask (7.2).
  """

  cushionDue: bool = False
  reds: int = 0


class KegleCall(NamedTuple):
  """
  KegleCall is the referee's call on a keglebillard shot: the 'points'
  it scores, nought for a foul; whether it is a 'foul', on the paragraph
  'rule' of the rules; the call in 'words'; whether 'red' was made; how
  many 'pins' the whites toppled; and the series' 'streak' after it,
  begun anew when the series ends.
  """

  points: int
  foul: bool
  rule: str
  words: str
  red: bool
  pins: int
  streak: Streak


class KegleReferee(NamedTuple):
  """
  KegleReferee calls keglebillard shots on its 'table' as Den Danske
  Billard Union's rules for 2026-27 have them (previews/rules): each pin
  a white topples scores 2, red meeting both whites, 'rødt', 4 (3.4,
  3.5), together at most 14; a series goes on while the shots score
  (7.1). Fouls, each passing the turn, the shot scoring nought: a ball
  off the table (11), red into a pocket (5.7), a pin credited to red
  (5.8), red from in hand striking a white before crossing the middle
  line, the white on red's own half short of the line (3.2, 9.4, the
  user), pins a second time running without a ball in a
  cushion, red alone counting as a cushion (5.11), and red a third time
  running without pins (5.12).
  """

  table: KegleTable = KegleTable()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def call(self, shot: KegleShot, streak: Streak) -> KegleCall:
    """The 'call' method calls 'shot', the series standing as 'streak'
    before it."""
    red = self.madeRed(shot)
    pins = sum(1 for _, ball in shot.fallen if ball != 'red')
    foul = self._foul(shot, streak, red, pins)
    if foul is not None:
      rule, words = foul
      return KegleCall(0, True, rule, 'Foul: %s (%s).' % (words, rule),
                       red, pins, Streak())
    points = PIN_POINTS * pins + (RED_POINTS if red else 0)
    if not points:
      return KegleCall(0, False, '7.1', 'No score: no pin, no red.',
                       False, 0, Streak())
    if pins:
      after = Streak(not self.cushioned(shot), 0)
    else:
      after = Streak(False, streak.reds + 1)
    return KegleCall(points, False, '3.4' if pins else '3.5',
                     _scoreWords(red, pins, points), red, pins, after)

  def lagCall(self, touches: tuple, after: tuple) -> tuple[str, str]:
    """The 'lagCall' method judges a lag, exactly as in carom (the
    user), 'Referee.lagCall': white and yellow each to the far cushion
    once and back, nearest the near cushion winning; a ball touching
    anything else, a long cushion, a ball, a pin or a pocket, loses
    (2.4)."""
    return Referee().lagCall(touches, after)

  def madeRed(self, shot: KegleShot) -> bool:
    """The 'madeRed' method tells whether red met both whites in
    'shot'."""
    met = set()
    for touch in shot.touches:
      if touch.kind == 'ball' and 'red' in (touch.first, touch.second):
        met.add(touch.second if touch.first == 'red' else touch.first)
    return len(met) >= 2

  def cushioned(self, shot: KegleShot) -> bool:
    """The 'cushioned' method tells whether any ball met a cushion in
    'shot'."""
    return any(touch.kind == 'cushion' for touch in shot.touches)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _foul(self, shot: KegleShot, streak: Streak, red: bool,
            pins: int) -> tuple[str, str] | None:
    """Returns the rule and the words of the first foul in 'shot',
    'None' if there is none."""
    for touch in shot.touches:
      if touch.kind == 'off':
        return '11', 'a ball left the table'
    for touch in shot.touches:
      if touch.kind == 'pocket' and touch.first == 'red':
        return '5.7', 'red went into a pocket'
    if any(ball == 'red' for _, ball in shot.fallen):
      return '5.8', 'red toppled a pin'
    if shot.inHand and shot.firstWhite is not None:
      crossed, whiteY = shot.firstWhite
      middle = 0.5 * self.table.table.length
      if shot.redFrom[1] > middle:
        beyond = whiteY <= middle
      else:
        beyond = whiteY >= middle
      if not crossed and not beyond:
        return '9.4', ('from in hand red struck a white on its own half '
                       'before crossing the middle line')
    if pins and streak.cushionDue and not self.cushioned(shot):
      return '5.11', 'pins twice running without a ball in a cushion'
    if red and not pins and streak.reds >= 2:
      return '5.12', 'red three times running without pins'
    return None


def _scoreWords(red: bool, pins: int, points: int) -> str:
  """Returns a scoring shot in words."""
  parts = []
  if red:
    parts.append('red')
  if pins:
    parts.append('%d pin%s' % (pins, '' if pins == 1 else 's'))
  return '%s: %d points.' % (' and '.join(parts).capitalize(), points)
