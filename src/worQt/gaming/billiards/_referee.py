"""
Rules, Shot, Call and Referee judge three-cushion shots as the French
federation's Code sportif carambole has it (FFB, 2026-2027).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

from ._motion import CUSHIONS, Motion, Touch

FROZEN = 0.1  # mm: balls this near, or a ball this near a cushion, touch


class Rules(NamedTuple):
  """
  Rules are the settings of a three-cushion match, after the FFB's Code
  sportif carambole: the 'cushions' the cue ball must touch before the
  second object ball (articles 2.2.05 and 2.2.10, three); the
  'distance', the points to win a set or the match (2.1.05); a limit of
  'innings', nought for none (2.1.10); whether the second player gets an
  'equalizing' last inning (2.1.09); 'sets' to win, nought to play a
  single distance (2.1.10); a 'shotClock' in seconds, nought for none
  (2.1.17-6); and whether the players 'lag' for the break (2.1.02).
  """

  cushions: int = 3
  distance: int = 40
  innings: int = 0
  equalizing: bool = True
  sets: int = 0
  shotClock: float = 0.0
  lag: bool = True


class Shot(NamedTuple):
  """
  Shot is a shot as the referee sees it: the 'cue' ball struck; the
  ball the player plays, 'owner', empty when any may be struck; the
  balls 'before' and 'after'; the 'touches' between, in order; whether
  it was played from the starting position, 'opening'; the cue's push,
  'aimX' and 'aimY'; whether it was struck 'early', before every ball
  was still, or 'late', over the shot clock.
  """

  cue: str
  owner: str
  before: tuple
  touches: tuple
  after: tuple
  opening: bool
  aimX: float
  aimY: float
  early: bool
  late: bool


class Call(NamedTuple):
  """
  Call is the referee's call on a shot: a 'point', a 'foul', or
  neither, a miss; the 'article' of the Code sportif it rests on; the
  call in 'words'; and the balls to 'respot' as article 2.2.07-E has it,
  those that left the table.
  """

  point: bool
  foul: bool
  article: str
  words: str
  respot: tuple


class Referee(NamedTuple):
  """
  Referee judges shots on the table of 'motion' by the 'rules', as the
  FFB's Code sportif carambole has them.

  'call' judges a shot. First the fouls, any of which voids the point
  (2.2.08): struck before every ball was still (2.1.17-1); over the shot
  clock (2.1.17-6); with the opponent's ball (2.1.17-5); into a ball or
  a cushion frozen to the cue ball (2.1.12); a ball leaving the table
  (2.1.14), put back as 2.2.07-E has it; a break not attacking the red
  directly (2.2.03). Then the point: the cue ball caroms both object
  balls (2.2.01), touching the cushions 'rules.cushions' times at least
  before the second (2.2.05). 'decidedAt' says when in the shot the
  call is known, so it may be called then; 'frozenTo' says what the cue
  ball touches at rest; 'lagCall' judges a lag.
  """

  rules: Rules = Rules()
  motion: Motion = Motion()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def frozenTo(self, balls: tuple, cue: str) -> tuple[tuple, tuple]:
    """The 'frozenTo' method returns the balls and the cushions the ball
    'cue' touches, at rest, within 'FROZEN'."""
    named = {ball.name: ball for ball in balls}
    struck = named[cue]
    near = tuple(name for name, ball in named.items() if name != cue
                 and self.motion.pressedOf(struck, ball) > -FROZEN)
    reach = self.motion.reach()
    sides = self.motion.sidesOf(struck.x, struck.y)
    walls = tuple(CUSHIONS[k] for k, (away, _, _) in enumerate(sides)
                  if away - reach < FROZEN)
    return near, walls

  def call(self, shot: Shot) -> Call:
    """The 'call' method judges 'shot': a foul, a point or a miss, in
    words, with the article it rests on."""
    foul = self._foul(shot)
    if foul is not None:
      return foul
    return self._carom(shot)

  def decidedAt(self, shot: Shot) -> int:
    """The 'decidedAt' method returns how many of the touches of 'shot'
    decide its call: nought for a foul before the cue ball moves; for a
    ball off the table, to the touch it leaves by; for a break not
    attacking the red, to the cue ball's first touch; for a point, or
    too few cushions for one, to the touch with the second object ball;
    and -1 for a call that waits until all rest, a miss."""
    if shot.early or shot.late or (shot.owner and shot.cue != shot.owner):
      return 0
    if self._frozenInto(shot):
      return 0
    for index, touch in enumerate(shot.touches):
      if touch.kind == 'off':
        return index + 1
    if shot.opening:
      for index, touch in enumerate(shot.touches):
        if shot.cue in (touch.first, touch.second):
          if touch.kind != 'ball' or 'red' not in (touch.first,
                                                   touch.second):
            return index + 1
          break
      else:
        return -1
    met = []
    for index, touch in enumerate(shot.touches):
      if touch.kind == 'ball' and shot.cue in (touch.first, touch.second):
        other = touch.second if touch.first == shot.cue else touch.first
        if other not in met:
          met.append(other)
          if len(met) == 2:
            return index + 1
    return -1

  def lagCall(self, touches: tuple, after: tuple) -> tuple[str, str]:
    """The 'lagCall' method judges a lag (articles 2.1.01 and 2.1.02):
    white and yellow, from the head string, each go to the far cushion,
    the foot one, touch it once and come back; a ball touching anything
    but the short cushions, the near one, the head, before the far one,
    or the far one more than once, loses; of the others, the one nearest
    the near cushion wins. Returns the winning ball's name, empty if the
    lag is to be played again, and the call in words."""
    faults = {}
    for name in ('white', 'yellow'):
      mine = [touch for touch in touches if name in (touch.first,
                                                     touch.second)]
      feet = [touch for touch in mine if touch.kind == 'cushion'
              and touch.second == 'foot']
      other = [touch for touch in mine if touch.kind != 'cushion'
               or touch.second not in ('foot', 'head')]
      cushions = [touch.second for touch in mine if touch.kind == 'cushion']
      if other:
        faults[name] = 'touched %s' % _what(other[0], name)
      elif cushions and cushions[0] != 'foot':
        faults[name] = 'went to the near cushion before the far one'
      elif len(feet) != 1:
        faults[name] = 'touched the far cushion %d times' % len(feet)
    if len(faults) == 2:
      return '', 'Both lags are faults: lag again (2.1.02)'
    if len(faults) == 1:
      loser = next(iter(faults))
      winner = 'yellow' if loser == 'white' else 'white'
      words = '%s wins the lag: %s %s (2.1.02)' % (
        winner.capitalize(), loser, faults[loser])
      return winner, words
    named = {ball.name: ball for ball in after}
    length = self.motion.table.length
    gaps = {name: length - named[name].y for name in ('white', 'yellow')}
    if abs(gaps['white'] - gaps['yellow']) < 0.5:
      return '', 'The lag is a tie: lag again (2.1.02)'
    winner = min(gaps, key=gaps.get)
    return winner, ('%s wins the lag, %.0f mm from the near cushion '
                    '(2.1.02)' % (winner.capitalize(),
                                  gaps[winner] - self.motion.reach()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _foul(self, shot: Shot) -> Call | None:
    """Returns the foul 'shot' is, if it is one."""
    if shot.early:
      return _fouled('2.1.17-1', 'struck before every ball was still')
    if shot.late:
      return _fouled('2.1.17-6', 'over the shot clock')
    if shot.owner and shot.cue != shot.owner:
      return _fouled('2.1.17-5', "played the opponent's ball")
    frozen = self._frozenInto(shot)
    if frozen:
      return _fouled('2.1.12', 'played into %s, frozen to the cue ball'
                     % frozen)
    off = tuple(touch.first for touch in shot.touches
                if touch.kind == 'off')
    if off:
      return Call(False, True, '2.1.14',
                  'Foul: %s left the table (2.1.14)' % ', '.join(off),
                  tuple(dict.fromkeys(off)))
    if shot.opening:
      first = next((touch for touch in shot.touches
                    if shot.cue in (touch.first, touch.second)), None)
      if first is None or first.kind != 'ball' or 'red' not in (
          first.first, first.second):
        return _fouled('2.2.03', 'the break must hit the red first')
    return None

  def _frozenInto(self, shot: Shot) -> str:
    """Returns what the cue ball, frozen to it, was played into, empty if
    nothing."""
    balls, walls = self.frozenTo(shot.before, shot.cue)
    named = {ball.name: ball for ball in shot.before}
    cue = named[shot.cue]
    for name in balls:
      other = named[name]
      if (other.x - cue.x) * shot.aimX + (other.y - cue.y) * shot.aimY > 0:
        return 'the %s' % name
    sides = dict(zip(CUSHIONS, self.motion.sidesOf(cue.x, cue.y)))
    for name in walls:
      _, ix, iy = sides[name]
      if ix * shot.aimX + iy * shot.aimY < 0.0:
        return 'the %s cushion' % name
    return ''

  def _carom(self, shot: Shot) -> Call:
    """Returns the point, or the miss, 'shot' makes: both object balls,
    the cushions before the second."""
    cue, needed = shot.cue, self.rules.cushions
    objects = [ball.name for ball in shot.before if ball.name != cue]
    met, cushions, before = [], 0, None
    for touch in shot.touches:
      if touch.kind == 'cushion' and touch.first == cue:
        cushions += 1
      elif touch.kind == 'ball' and cue in (touch.first, touch.second):
        other = touch.second if touch.first == cue else touch.first
        if other not in met:
          met.append(other)
          if len(met) == 2:
            before = cushions
            break
    if before is None:
      missed = [name for name in objects if name not in met]
      return Call(False, False, '2.2.01', 'No point: missed %s (2.2.01)'
                  % ' and '.join('the %s' % name for name in missed), ())
    last = met[1]
    if before < needed:
      return Call(False, False, '2.2.05',
                  'No point: %s before the %s (2.2.05)'
                  % (_cushions(before), last), ())
    return Call(True, False, '2.2.05', 'Point: %s before the %s (2.2.05)'
                % (_cushions(before), last), ())


def _fouled(article: str, why: str) -> Call:
  """Returns the foul at 'article' for 'why'."""
  return Call(False, True, article, 'Foul: %s (%s)' % (why, article), ())


def _cushions(count: int) -> str:
  """Says 'count' cushions in words."""
  words = ('no cushion', 'one cushion', 'two cushions', 'three cushions',
           'four cushions', 'five cushions')
  return words[count] if count < len(words) else '%d cushions' % count


def _what(touch: Touch, name: str) -> str:
  """Says what the ball 'name' touched in 'touch'."""
  if touch.kind == 'cushion':
    return 'the %s cushion' % touch.second
  if touch.kind == 'ball':
    other = touch.second if touch.first == name else touch.first
    return 'the %s' % other
  return 'the floor'
