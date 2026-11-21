"""
Match is a three-cushion match between two players, kept as the FFB's
Code sportif carambole has it: the lag, innings and runs, the
equalizing inning, sets.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from ._phrasebook import ENGLISH, Phrasebook
from ._referee import Call, Rules

#  What a match is waiting for: the 'lag' for the break; the lag's winner
#  to 'choose' who breaks; a 'break' or an 'equalizing' inning, played
#  from the starting position; 'play' on; or nothing, it being 'over'.
PHASES = ('lag', 'choose', 'break', 'play', 'equalizing', 'over')


class Match(NamedTuple):
  """
  Match is a three-cushion match between the two players 'names', kept
  as the FFB's Code sportif carambole has it, by its 'rules'. It never
  changes: each step returns the match as it is after it.

  The players 'lag' for the break (2.1.02), white for the first, yellow
  for the second; the winner, 'lagWinner', chooses who breaks (2.1.03);
  the one who breaks plays white, the other yellow, all match long
  (2.1.04): 'balls' says each player's ball. The 'current' player plays
  on while making points, 'run' of them this inning, and the turn passes
  on a miss or a foul (2.2.02); each player's 'scores' and 'innings' in
  the set, and over the match 'totals', 'inningsTotal' and the 'best'
  run, are kept. When the first to break ends the last inning, at the
  distance or the innings limit, the other, an inning short, plays an
  'equalizing' last inning from the starting position (2.1.09): 'final'
  says the inning is the last. A set ends there, its winner given two
  set points, a draw one each (2.1.10); the next set is broken by the
  other player (2.1.03); played to a single distance, the match ends
  with the set. 'winner' is the winning player, 2 for a draw, -1 while
  it is on.
  """

  rules: Rules = Rules()
  names: tuple = ('Player 1', 'Player 2')
  balls: tuple = ('white', 'yellow')
  phase: str = 'lag'
  current: int = 0
  starter: int = 0
  lagWinner: int = -1
  scores: tuple = (0, 0)
  innings: tuple = (0, 0)
  totals: tuple = (0, 0)
  inningsTotal: tuple = (0, 0)
  best: tuple = (0, 0)
  run: int = 0
  final: bool = False
  setPoints: tuple = (0, 0)
  setNumber: int = 1
  winner: int = -1

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def begun(self, ) -> Match:
    """The 'begun' method returns the match begun: lagging for the
    break, or with the first player breaking if there is no lag."""
    if self.rules.lag:
      return self._with(('phase', 'lag'))
    return self._chosenStarter(0)

  def cueBall(self, ) -> str:
    """The 'cueBall' method returns the ball the current player plays;
    during the lag, nothing."""
    return '' if self.phase == 'lag' else self.balls[self.current]

  def needsOpening(self, ) -> bool:
    """The 'needsOpening' method tells whether the next shot is played
    from the starting position: a break, or an equalizing inning."""
    return self.phase in ('break', 'equalizing')

  def average(self, player: int) -> float:
    """The 'average' method returns the points 'player' made an inning
    over the match."""
    played = self.inningsTotal[player]
    return self.totals[player] / played if played else 0.0

  def lagged(self, ball: str) -> Match:
    """The 'lagged' method returns the match after a lag won by 'ball',
    white the first player's, yellow the second's: the winner chooses
    who breaks; no ball, and the lag is played again."""
    if self.phase != 'lag' or not ball:
      return self
    winner = 0 if ball == 'white' else 1
    return self._with(('lagWinner', winner), ('current', winner),
                      ('phase', 'choose'))

  def chosen(self, breaks: bool) -> Match:
    """The 'chosen' method returns the match after the lag's winner
    chose to break, or to let the other break."""
    if self.phase != 'choose':
      return self
    winner = self.lagWinner
    return self._chosenStarter(winner if breaks else 1 - winner)

  def judged(self, call: Call) -> Match:
    """The 'judged' method returns the match after a shot called
    'call': a point counts and the player plays on, unless the distance
    is reached; a miss or a foul ends the inning."""
    if self.phase not in ('break', 'play', 'equalizing'):
      return self
    player = self.current
    if not call.point:
      return self._inningEnded(False)
    scores = _added(self.scores, player, 1)
    totals = _added(self.totals, player, 1)
    run = self.run + 1
    best = list(self.best)
    best[player] = max(best[player], run)
    match = self._with(('scores', scores), ('totals', totals),
                       ('run', run), ('best', tuple(best)),
                       ('phase', 'play'))
    if scores[player] >= self.rules.distance:
      return match._inningEnded(True)
    return match

  def said(self, book: Phrasebook = ENGLISH) -> str:
    """The 'said' method says how the match stands, in words, in
    'book's language."""
    if self.phase == 'over':
      if self.winner == 2:
        return book.said('match.draw')
      return book.said('match.won', self.names[self.winner])
    name = self.names[self.current]
    ball = book.theBall(self.balls[self.current])
    if self.phase == 'lag':
      return book.said('match.lag')
    if self.phase == 'choose':
      return book.said('match.choose', name)
    if self.phase == 'break':
      return book.said('match.break', name, ball)
    if self.phase == 'equalizing':
      return book.said('match.equalizing', name)
    if self.final:
      return book.said('match.last', name, ball)
    return book.said('match.play', name, ball)

  def named(self, names: tuple) -> Match:
    """The 'named' method returns the match, the players called
    'names'."""
    return self._with(('names', tuple(names)))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _with(self, *changes) -> Match:
    """Returns the match with each 'name', 'value' of 'changes' so."""
    values = list(self)
    for name, value in changes:
      values[self._fields.index(name)] = value
    return Match(*values)

  def _chosenStarter(self, starter: int) -> Match:
    """Returns the match with 'starter' breaking it, playing white, the
    other yellow."""
    balls = ('white', 'yellow') if starter == 0 else ('yellow', 'white')
    return self._with(('balls', balls), ('starter', starter),
                      ('current', starter), ('phase', 'break'),
                      ('innings', _added((0, 0), starter, 1)),
                      ('inningsTotal', _added(self.inningsTotal, starter,
                                              1)),
                      ('run', 0), ('final', False))

  def _passed(self, phase: str, final: bool) -> Match:
    """Returns the match with the turn passed to the other player, his
    inning begun in 'phase'."""
    other = 1 - self.current
    return self._with(('current', other), ('run', 0), ('phase', phase),
                      ('final', final),
                      ('innings', _added(self.innings, other, 1)),
                      ('inningsTotal', _added(self.inningsTotal, other, 1)))

  def _inningEnded(self, reached: bool) -> Match:
    """Returns the match with the current inning ended, at the distance
    or not: the turn passes, the other plays an equalizing last inning,
    or the set ends."""
    rules, player = self.rules, self.current
    other = 1 - player
    if self.final:
      return self._setEnded()
    limited = rules.innings and self.innings[player] >= rules.innings
    if reached or limited:
      if self.innings[other] < self.innings[player]:
        if rules.equalizing:
          return self._passed('equalizing', True)
        return self._passed('play', True)
      return self._setEnded()
    return self._passed('play', False)

  def _setEnded(self, ) -> Match:
    """Returns the match with the set ended: its winner given two set
    points, a draw one each; the match over, or the next set broken by
    the other player."""
    first, second = self.scores
    winner = 0 if first > second else 1 if second > first else 2
    if not self.rules.sets:
      return self._with(('phase', 'over'), ('winner', winner),
                        ('final', False))
    points = list(self.setPoints)
    if winner == 2:
      points = [points[0] + 1, points[1] + 1]
    else:
      points[winner] += 2
    needed = 2 * self.rules.sets
    if max(points) >= needed:
      over = 0 if points[0] > points[1] else 1
      over = 2 if points[0] == points[1] else over
      return self._with(('setPoints', tuple(points)), ('phase', 'over'),
                        ('winner', over), ('final', False))
    starter = 1 - self.starter
    return self._with(('setPoints', tuple(points)),
                      ('setNumber', self.setNumber + 1),
                      ('scores', (0, 0)), ('starter', starter),
                      ('current', starter), ('phase', 'break'),
                      ('innings', _added((0, 0), starter, 1)),
                      ('inningsTotal', _added(self.inningsTotal, starter,
                                              1)),
                      ('run', 0), ('final', False))


def _added(values: tuple, index: int, amount: int) -> tuple:
  """Returns 'values' with 'amount' added to the one at 'index'."""
  out = list(values)
  out[index] += amount
  return tuple(out)
