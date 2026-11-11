"""
KegleMatch is a keglebillard match between two players, kept as Den
Danske Billard Union's rules have it: the lag, the series, the
distance, as many series each.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from ._kegle_referee import KegleCall, Streak

#  The distances a match may be played to (the user: 200 to 800 in 100s).
DISTANCES = (200, 300, 400, 500, 600, 700, 800)
KEGLE_PHASES = ('lag', 'choose', 'play', 'over')


class KegleMatch(NamedTuple):
  """
  KegleMatch is a keglebillard match between the two players 'names',
  played to 'distance' points, one of 'DISTANCES', as DDBU's rules for
  2026-27 have it (previews/rules). It never changes: each step returns
  the match as it is after it. Both play red, the cue ball, at the
  whites.

  The players 'lag' (2.1), white for the first, yellow for the second;
  the winner, 'lagWinner', chooses who lays out ('udlæg'), the
  'starter'. The 'current' player plays on while he scores, 'run'
  points this series, and his series ends on a shot scoring nothing, a
  foul, or the distance (3.6, 7.1); each player's 'scores', 'series'
  and 'best' series are kept, and how his series stands, 'streak'. A
  'layout' starts the next shot from the layout, whites on their spots
  and red in hand: at the start (3.1), after a ball off the table
  (11.2), and to start the other's last series (7.5); red pocketed, the
  next shot is from in hand, 'inHand', the whites as they lie (9.4).
  In hand, at the layout too, is as after red went into a pocket (the
  user): red put down within a quarter of either short cushion
  ('KegleTable.inHand'), to cross the middle line before it strikes a
  white on its own half. Both have as many series (7.4): the
  starter reaching the distance, the other plays his series, the last,
  'final'; both reaching it, the match is a draw (7.6). 'winner' is the
  winning player, 2 for a draw, -1 while it is on.
  """

  names: tuple = ('Player 1', 'Player 2')
  distance: int = 400
  phase: str = 'lag'
  current: int = 0
  starter: int = 0
  lagWinner: int = -1
  scores: tuple = (0, 0)
  series: tuple = (0, 0)
  best: tuple = (0, 0)
  run: int = 0
  streak: Streak = Streak()
  layout: bool = False
  inHand: bool = False
  final: bool = False
  winner: int = -1

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def begun(self, ) -> KegleMatch:
    """The 'begun' method returns the match begun, lagging for the
    layout, at a distance it may be played to."""
    if self.distance not in DISTANCES:
      raise ValueError('a keglebillard match is played to one of %s, '
                       'not %r' % (DISTANCES, self.distance))
    return KegleMatch(self.names, self.distance)

  def cueBall(self, ) -> str:
    """The 'cueBall' method returns the ball the current player plays:
    red, after the lag."""
    return '' if self.phase == 'lag' else 'red'

  def average(self, player: int) -> float:
    """The 'average' method returns the points 'player' made a series."""
    played = self.series[player]
    return self.scores[player] / played if played else 0.0

  def lagged(self, ball: str) -> KegleMatch:
    """The 'lagged' method returns the match after a lag won by 'ball',
    white the first player's, yellow the second's: the winner chooses
    who lays out; no ball, and the lag is played again."""
    if self.phase != 'lag' or not ball:
      return self
    winner = 0 if ball == 'white' else 1
    return self._with(('lagWinner', winner), ('current', winner),
                      ('phase', 'choose'))

  def chosen(self, lays: bool) -> KegleMatch:
    """The 'chosen' method returns the match after the lag's winner
    chose to lay out, or to let the other: the starter's first series
    begins from the layout."""
    if self.phase != 'choose':
      return self
    winner = self.lagWinner
    starter = winner if lays else 1 - winner
    return self._with(('starter', starter), ('current', starter),
                      ('phase', 'play'), ('layout', True),
                      ('inHand', True))

  def judged(self, call: KegleCall) -> KegleMatch:
    """The 'judged' method returns the match after a shot called
    'call': its points counted, the series going on while it scores
    short of the distance, else ended."""
    if self.phase != 'play':
      return self
    player = self.current
    scores = _added(self.scores, player, call.points)
    run = self.run + call.points
    best = list(self.best)
    best[player] = max(best[player], run)
    match = self._with(('scores', scores), ('run', run),
                       ('best', tuple(best)), ('streak', call.streak),
                       ('layout', False), ('inHand', False))
    reached = scores[player] >= self.distance
    if call.points and not call.foul and not reached:
      return match
    return match._seriesEnded(call, reached)

  def said(self, ) -> str:
    """The 'said' method returns how the match stands, in words."""
    first, second = self.names
    score = '%s %d, %s %d of %d' % (first, self.scores[0], second,
                                    self.scores[1], self.distance)
    if self.phase == 'lag':
      return 'Lag for the layout. ' + score
    if self.phase == 'choose':
      return '%s won the lag: lay out, or let the other. %s' % (
        self.names[self.lagWinner], score)
    if self.phase == 'over':
      if self.winner == 2:
        return 'A draw. ' + score
      return '%s wins. %s' % (self.names[self.winner], score)
    last = ', the last series' if self.final else ''
    return '%s to play, %d this series%s. %s' % (
      self.names[self.current], self.run, last, score)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _with(self, *changes) -> KegleMatch:
    """Returns the match with each 'name', 'value' of 'changes' so."""
    values = list(self)
    for name, value in changes:
      values[self._fields.index(name)] = value
    return KegleMatch(*values)

  def _seriesEnded(self, call: KegleCall, reached: bool) -> KegleMatch:
    """Returns the match with the current series ended after 'call', at
    the distance or not: the turn passes, the other plays his last
    series, or the match is over."""
    player, other = self.current, 1 - self.current
    series = _added(self.series, player, 1)
    match = self._with(('series', series))
    if self.final or (reached and player != self.starter):
      return match._over()
    layout = call.rule == '11'
    if reached:
      layout, final = True, True
    else:
      final = False
    return match._with(('current', other), ('run', 0),
                       ('streak', Streak()), ('final', final),
                       ('layout', layout),
                       ('inHand', layout or call.rule == '5.7'))

  def _over(self, ) -> KegleMatch:
    """Returns the match over: won by whoever reached the distance, a
    draw if both did."""
    first, second = (score >= self.distance for score in self.scores)
    winner = 2 if first and second else 0 if first else 1
    return self._with(('phase', 'over'), ('winner', winner),
                      ('run', 0), ('final', False))


def _added(values: tuple, index: int, amount: int) -> tuple:
  """Returns 'values' with 'amount' added to the one at 'index'."""
  out = list(values)
  out[index] += amount
  return tuple(out)
