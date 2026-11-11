"""
TestKegleGame covers 'KegleGame', keglebillard's game loop: the lag laid
out as three-cushion's; the winner lays out or lets the other, red in
hand; the distance stepped through 200 to 800; red put down by hand
only within a quarter of either short cushion, clear of the whites;
whether red crossed the middle line before it first struck a white, as
the engine played it; a shot from in hand striking a white on red's own
half first called a foul; the balls laid for the next shot as the call
has it: as they lie, laid out anew after a ball off the table, red in
hand again after it went into a pocket, a white gone into one back on
the spot opposite the other.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.billiards import DISTANCES, Ball, Cue, KegleCall
from worQt.gaming.billiards import KegleGame, KegleMotion, KegleRecorder
from worQt.gaming.billiards import KegleTable, Streak

from . import BilliardsTest

TABLE = KegleTable()
RADIUS = TABLE.table.radius


def laidOut() -> KegleGame:
  """A game lagged, white winning, and laid out by its first player."""
  return KegleGame(TABLE).begun().lagged('white').chosen(True)


def redAt(game: KegleGame, x: float, y: float, aim: str,
          speed: float) -> tuple:
  """The shot of red put down at 'x', 'y' from the layout and struck at
  'speed' at the middle of ball 'aim': its recording and recorder."""
  balls = game.redPlaced(game.layoutBalls(), x, y)
  named = {ball.name: ball for ball in balls}
  red, target = named['red'], named[aim]
  dx, dy = target.x - red.x, target.y - red.y
  size = math.hypot(dx, dy)
  struck = Cue().sent(red, dx / size, dy / size, speed, 0.0, 0.0, RADIUS)
  shot = tuple(struck if ball.name == 'red' else ball for ball in balls)
  recorder = KegleRecorder(KegleMotion(TABLE), 1000.0, 50, 60.0,
                           TABLE.pinsPlaced(balls))
  return recorder.recorded(shot), recorder


class TestKegleGame(BilliardsTest):
  """Tests for 'KegleGame'."""

  def test_lag_and_layout(self) -> None:
    """The players lag from three-cushion's lag position; the winner
    lays out or lets the other; the layout has the whites on their
    spots, red in hand."""
    game = KegleGame(TABLE).begun()
    self.assertEqual(game.match.phase, 'lag')
    self.assertEqual(game.lagBalls(), TABLE.table.lagPosition())
    chosen = game.lagged('yellow').chosen(False)
    self.assertEqual(chosen.match.phase, 'play')
    self.assertEqual(chosen.match.starter, 0)
    self.assertTrue(chosen.match.inHand and chosen.match.layout)
    self.assertEqual(chosen.layoutBalls(), TABLE.opening())
    self.assertEqual(chosen.match.cueBall(), 'red')

  def test_distances(self) -> None:
    """The distance steps through 200 to 800 in hundreds, after the
    last the first, the game begun anew at its lag."""
    game = KegleGame(TABLE).begun()
    seen = []
    for _ in DISTANCES:
      game = game.nextDistance()
      seen.append(game.match.distance)
      self.assertEqual(game.match.phase, 'lag')
    self.assertEqual(sorted(seen), list(DISTANCES))
    self.assertEqual(KegleGame(TABLE).withDistance(800).nextDistance()
                     .match.distance, 200)

  def test_red_placed(self) -> None:
    """Red in hand goes down within a quarter of either short cushion,
    clear of the whites; not in the middle of the table, nor on a
    white."""
    game = laidOut()
    balls = game.layoutBalls()
    for x, y in ((400.0, 2600.0), (1000.0, 300.0)):
      placed = game.redPlaced(balls, x, y)
      self.assertEqual({ball.name: ball for ball in placed}['red'][1:3],
                       (x, y))
    self.assertIsNone(game.redPlaced(balls, 400.0, 1500.0))
    white = balls[0]
    self.assertIsNone(game.redPlaced(balls, white.x + 30.0, white.y))

  def test_crossed(self) -> None:
    """Red from the head end struck at yellow on the foot spot crosses
    the middle line before it strikes it: no foul. Struck at white on
    its own half, from in hand, it is a foul (9.4)."""
    game = laidOut()
    recording, recorder = redAt(game, 300.0, 2600.0, 'yellow', 3000.0)
    crossed, whiteY = game.shotOf(recording, recorder, True).firstWhite
    self.assertTrue(crossed)
    self.assertLess(whiteY, 0.5 * TABLE.table.length)
    self.assertFalse(game.called(recording, recorder).foul)
    recording, recorder = redAt(game, 300.0, 2600.0, 'white', 1500.0)
    shot = game.shotOf(recording, recorder, True)
    self.assertFalse(shot.firstWhite[0])
    call = game.called(recording, recorder)
    self.assertEqual((call.foul, call.rule), (True, '9.4'))

  def test_unparked(self) -> None:
    """After the shot a white gone into a pocket is back on the layout
    spot opposite the other white (9.1); red gone into one is in hand,
    where the layout has it."""
    game = laidOut()
    lying = (Ball('white', *TABLE.parkedAt(4)),
             Ball('yellow', 1000.0, 1800.0), Ball('red', 700.0, 1200.0))
    balls = game.unparked(lying)
    self.assertEqual(balls[0][1:3], TABLE.spots()[0])
    self.assertEqual(balls[1:], lying[1:])
    lying = (Ball('white', 300.0, 900.0), Ball('yellow', 1000.0, 1800.0),
             Ball('red', *TABLE.parkedAt(0)))
    balls = game.unparked(lying)
    self.assertEqual(balls[2][1:3], TABLE.opening()[2][1:3])
    self.assertEqual(balls[:2], lying[:2])

  def test_judged(self) -> None:
    """After a scoring shot the series goes on, the balls as they lie;
    after a ball off the table the other plays from the layout; after
    red went into a pocket the other has red in hand, put down at the
    head end, the whites as they lie."""
    game = laidOut()
    lying = (Ball('white', 300.0, 900.0), Ball('yellow', 1000.0, 1800.0),
             Ball('red', 700.0, 1200.0))
    scored = KegleCall(4, False, '3.5', 'Red: 4 points.', True, 0,
                       Streak(False, 1))
    after, balls = game.judged(scored, lying)
    self.assertEqual((after.match.current, after.match.run), (0, 4))
    self.assertEqual(balls, lying)
    off = KegleCall(0, True, '11', 'Foul.', False, 0, Streak())
    after, balls = game.judged(off, lying)
    self.assertEqual(after.match.current, 1)
    self.assertEqual(balls, TABLE.opening())
    pocketed = KegleCall(0, True, '5.7', 'Foul.', False, 0, Streak())
    after, balls = game.judged(pocketed, lying)
    self.assertTrue(after.match.inHand)
    self.assertEqual(balls[:2], lying[:2])
    self.assertEqual(balls[2][1:3], TABLE.opening()[2][1:3])
