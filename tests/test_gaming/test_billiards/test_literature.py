"""
TestLiterature plays shots drawn in the literature through the engine
and holds it to their paths. The break as a Korean three-cushion guide
draws it (japong.com, "쓰리쿠션 초구 공략법"), aimed exactly as it says,
the stick laid off the line by the squirt as a player allows for it:
from the player's right spot, 3/5 of the red on its left side, the tip
at 2 o'clock "2 tips", two thirds of the most side a tip gives on a
three tip scale, at the speed the constants were fitted with. The cue
ball runs the far left corner, the long rail on the left about 165 mm
from the foot and the foot rail about 115 mm from the corner, then the
long rail on the right about 1180 mm from the foot; the red runs the
foot rail just right of the middle, the long rail on the right, and
the head rail. Whether the cue ball then makes the yellow is a knife
edge in the engine, a graze, so it is not held to it. The player stands
at the head facing the foot, so his left is the table's 'right'
cushion.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from worQt.gaming.billiards import CaromTable, Cue, Motion, Recorder
from worQt.gaming.billiards import Recording, Referee, Shot

from . import BilliardsTest

TABLE = CaromTable()


@functools.cache
def koreanBreak() -> tuple[Recording, object]:
  """The break as the Korean guide draws it, recorded, and its call:
  white on spot 5, 3/5 of the red on its left as the player sees it,
  the tip two thirds of the miscue limit out at 2 o'clock, leaving at
  4.848 m/s, the speed the constants were fitted with."""
  balls = TABLE.openingFor('white', 5)
  white, yellow, red = balls
  radius = TABLE.radius
  dx, dy = red.x - white.x, red.y - white.y
  apart = math.hypot(dx, dy)
  across = (-dy / apart, dx / apart)
  if across[0] < 0.0:
    across = (-across[0], -across[1])
  offset = 2.0 * radius * (1.0 - 0.6)
  aimX = red.x + across[0] * offset - white.x
  aimY = red.y + across[1] * offset - white.y
  clock, cue = math.radians(60.0), Cue()
  out = 2.0 / 3.0 * 0.5
  struck = cue.sent(white, aimX, aimY, 4848.0, out * math.cos(clock),
                    out * math.sin(clock), radius)
  recording = Recorder(Motion()).recorded((struck, yellow, red))
  call = Referee().call(Shot('white', 'white', balls,
                             recording.touchesOf(), recording.last(), True,
                             aimX, aimY, False, False))
  return recording, call


def contacts(recording: Recording, name: str) -> list[tuple]:
  """The contacts of the ball 'name' in order, each what it touched,
  a cushion's name or a ball's, and where the ball was then."""
  out = []
  for time, touch in recording.touches:
    if name not in (touch.first, touch.second):
      continue
    ball = {ball.name: ball for ball in recording.ballsAt(time)}[name]
    if touch.kind == 'cushion':
      out.append((touch.second, ball.x, ball.y))
    else:
      other = touch.second if touch.first == name else touch.first
      out.append((other, ball.x, ball.y))
  return out


class TestLiterature(BilliardsTest):
  """Tests holding the engine to shots drawn in the literature."""

  def test_korean_break_cue_ball(self) -> None:
    """The cue ball takes the red, runs the far left corner, the long
    rail first, and crosses to the right long rail near where the guide
    draws it."""
    recording, _ = koreanBreak()
    route = contacts(recording, 'white')
    self.assertEqual([what for what, _, _ in route[:4]],
                     ['red', 'right', 'foot', 'left'])
    _, _, firstY = route[1]
    self.assertLess(firstY, 350.0)
    _, secondX, _ = route[2]
    self.assertGreater(secondX, TABLE.width - 250.0)
    _, _, thirdY = route[3]
    self.assertLess(abs(thirdY - 1180.0), 150.0)

  def test_korean_break_red(self) -> None:
    """The red runs the foot rail right of the middle as the player
    sees it, then the long rail on his right, then the head rail."""
    recording, _ = koreanBreak()
    route = [what for what, _, _ in contacts(recording, 'red')]
    cushions = [what for what in route if what in ('left', 'right', 'foot',
                                                    'head')]
    self.assertEqual(cushions[:3], ['foot', 'left', 'head'])
    foot = next(x for what, x, _ in contacts(recording, 'red')
                if what == 'foot')
    self.assertLess(abs(foot - 473.0), 150.0)
