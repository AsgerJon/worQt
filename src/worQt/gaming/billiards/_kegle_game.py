"""
KegleGame is a keglebillard game as it is played, shot by shot: the
match kept, how the balls lie for each shot, and the call on each.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple, TYPE_CHECKING

from ._carom_table import Ball
from ._kegle_match import DISTANCES, KegleMatch
from ._kegle_referee import KegleCall, KegleReferee, KegleShot
from ._kegle_table import KegleTable
from ._phrasebook import ENGLISH, Phrasebook

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._kegle_motion import KegleRecorder
  from ._recorder import Recording


class KegleGame(NamedTuple):
  """
  KegleGame is a keglebillard game on 'table', its 'match' kept
  ('KegleMatch'), the game loop as three-cushion's is in the window: it
  never changes, each step returns the game after it.

  The players lag exactly as in three-cushion (the user; 2.1),
  'lagBalls'; the winner chooses who lays out, 'chosen'; the layout has
  the whites on their spots and red in hand, 'layoutBalls'. Red in hand,
  at the layout as after it went into a pocket (the user), is put down
  within a quarter of either short cushion, clear of the whites,
  'redPlaced'. 'shotOf' reads a recorded shot as the referee sees it:
  the touches, the pins left down, whether red was in hand and from
  where, and whether red had crossed the middle line as it first struck
  a white; 'called' calls it as the series stands; 'judged' keeps the
  match and lays the balls for the next shot: from the layout again
  after a ball off the table or for the other's last series, red in
  hand again after it went into a pocket, else as they lie, a white gone
  into a pocket back on its spot ('unparked').
  """

  table: KegleTable = KegleTable()
  match: KegleMatch = KegleMatch()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def begun(self, ) -> KegleGame:
    """The 'begun' method returns the game begun anew, lagging for the
    layout, to the match's distance."""
    return KegleGame(self.table, self.match.begun())

  def withDistance(self, distance: int) -> KegleGame:
    """The 'withDistance' method returns the game begun anew to
    'distance', one of 'DISTANCES'."""
    match = KegleMatch(self.match.names, distance)
    return KegleGame(self.table, match.begun())

  def nextDistance(self, ) -> KegleGame:
    """The 'nextDistance' method returns the game begun anew to the next
    distance there is, after the last the first (the user: 200 to 800 in
    hundreds)."""
    index = DISTANCES.index(self.match.distance) if (
      self.match.distance in DISTANCES) else -1
    return self.withDistance(DISTANCES[(index + 1) % len(DISTANCES)])

  def lagBalls(self, ) -> tuple[Ball, Ball, Ball]:
    """The 'lagBalls' method returns the balls as the players lag, as
    for three-cushion (the user): the whites on the head string, red on
    the foot spot."""
    return self.table.table.lagPosition()

  def layoutBalls(self, ) -> tuple[Ball, Ball, Ball]:
    """The 'layoutBalls' method returns the balls laid out: the whites
    on their spots, red in hand at the head end, to be put down where
    the player likes ('redPlaced')."""
    return self.table.opening()

  def redPlaced(self, balls: tuple[Ball, ...], x: float,
                y: float) -> tuple[Ball, ...] | None:
    """The 'redPlaced' method returns 'balls' with red put down by hand
    at 'x', 'y', within a quarter of either short cushion and clear of
    the other balls; 'None' where it may not lie."""
    if not self.table.inHand(x, y):
      return None
    reach = 2.0 * self.table.table.radius
    for ball in balls:
      if ball.name != 'red' and math.hypot(ball.x - x, ball.y - y) < reach:
        return None
    return tuple(Ball('red', x, y, ball.turn) if ball.name == 'red'
                 else ball for ball in balls)

  def lagged(self, ball: str) -> KegleGame:
    """The 'lagged' method returns the game after a lag won by 'ball',
    white the first player's, yellow the second's; no ball, and the lag
    is played again."""
    return KegleGame(self.table, self.match.lagged(ball))

  def chosen(self, lays: bool) -> KegleGame:
    """The 'chosen' method returns the game after the lag's winner chose
    to lay out, or to let the other."""
    return KegleGame(self.table, self.match.chosen(lays))

  def shotOf(self, recording: Recording, recorder: KegleRecorder,
             inHand: bool) -> KegleShot:
    """The 'shotOf' method returns the shot 'recording', played by
    'recorder', as the referee sees it: its touches, the pins it left
    down, whether red was played from 'inHand', where from, and whether
    red had crossed the middle line as it first struck a white."""
    start = {ball.name: ball for ball in recording.ballsAt(0.0)}
    red = start.get('red')
    redFrom = (red.x, red.y) if red is not None else (0.0, 0.0)
    return KegleShot(recording.touchesOf(), recorder.fallenOf(recording),
                     inHand, redFrom, self._firstWhite(recording))

  def called(self, recording: Recording, recorder: KegleRecorder,
             book: Phrasebook = ENGLISH) -> KegleCall:
    """The 'called' method returns the referee's call on the shot
    'recording', played by 'recorder', as the series stands, in
    'book's language."""
    shot = self.shotOf(recording, recorder, self.match.inHand)
    return KegleReferee(self.table, book).call(shot, self.match.streak)

  def named(self, names: tuple) -> KegleGame:
    """The 'named' method returns the game, the players called
    'names'."""
    return KegleGame(self.table, self.match.named(names))

  def judged(self, call: KegleCall,
             balls: tuple[Ball, ...]) -> tuple[KegleGame, tuple]:
    """The 'judged' method returns the game after the shot called
    'call', the balls lying as 'balls' once all rest, and the balls as
    the next shot is played from: laid out anew, red in hand again, or
    as they lie."""
    match = self.match.judged(call)
    game = KegleGame(self.table, match)
    balls = self.unparked(balls)
    if match.phase == 'over':
      return game, balls
    if match.layout:
      return game, self.layoutBalls()
    if match.inHand:
      red = self.layoutBalls()[2]
      placed = self.redPlaced(balls, red.x, red.y)
      return game, placed if placed is not None else balls
    return game, balls

  def unparked(self, balls: tuple[Ball, ...]) -> tuple[Ball, ...]:
    """The 'unparked' method returns 'balls' with those gone into a
    pocket back on the table: a white on the layout spot opposite the
    other white (9.1), red in hand where the layout has it (9.4)."""
    out = tuple(balls)
    for ball in balls:
      if ball.name != 'red' and self.table.pocketOf(ball) >= 0:
        out = self.table.respotted(out, ball.name)
    named = {ball.name: ball for ball in out}
    if 'red' in named and self.table.pocketOf(named['red']) >= 0:
      red = self.layoutBalls()[2]
      placed = self.redPlaced(out, red.x, red.y)
      if placed is not None:
        out = placed
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _firstWhite(self, recording: Recording) -> tuple | None:
    """Returns, as red first struck a white in 'recording', whether it
    had crossed the middle line between the middle pockets first, and
    where across the table's length that white lay, ('crossed', 'y');
    'None' if it struck none."""
    middle = 0.5 * self.table.table.length
    names = recording.names
    if 'red' not in names:
      return None
    red = names.index('red')
    for time, touch in recording.touches:
      if touch.kind != 'ball' or 'red' not in (touch.first, touch.second):
        continue
      other = touch.second if touch.first == 'red' else touch.first
      stop = int(math.floor(time * recording.rate)) + 1
      ys = recording.placesOf(0, stop)[:, red, 1]
      start = float(ys[0]) if len(ys) else middle
      side = 1.0 if start > middle else -1.0
      crossed = bool(len(ys)) and bool(((ys - middle) * side <= 0.0).any())
      white = {ball.name: ball for ball in recording.ballsAt(time)}[other]
      return crossed, white.y
    return None
