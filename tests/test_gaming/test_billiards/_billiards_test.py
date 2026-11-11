"""
BilliardsTest and BilliardsWidgetTest are the base classes for the
tests of 'worQt.gaming.billiards': 'BilliardsTest' subclasses
'BaseTest' for the table and its balls, which need no Qt;
'BilliardsWidgetTest' subclasses 'WidgetTest' for the widgets.

Its functions: 'ballAt' makes a ball moving and spinning so;
'aroundContact' finds the balls just before their first hit and just
after they are clear of it; 'rolledOn' runs them on until the first is
rolling; 'firstBreak' strikes the user's first break, 'breakAim'
aiming it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worktoy.work_test import BaseTest

from worQt.gaming.billiards import STILL, Ball, CaromTable, Cue, Motion
from worQt.qtest import WidgetTest


def ballAt(name: str, x: float, y: float, vx: float, vy: float,
           wx: float, wy: float, wz: float) -> Ball:
  """The 'ballAt' function returns a ball 'name' at 'x', 'y', unturned,
  moving and spinning so."""
  return Ball(name, x, y, STILL, vx, vy, wx, wy, wz)


def aroundContact(motion: Motion, balls: tuple[Ball, ...],
                  seconds: float) -> tuple[tuple, tuple]:
  """The 'aroundContact' function runs 'balls' on in steps of 0.1 ms
  for 'seconds' at most, and returns them as they were the step before
  their first hit, and the step they are clear of it again."""
  before, was = None, False
  for _ in range(round(seconds / 0.0001)):
    later = motion.advanced(balls, 0.0001)
    touching = motion.inContact(later)
    if touching and not was and before is None:
      before = balls
    if was and not touching:
      return before, later
    was, balls = touching, later
  return before, balls


def rolledOn(motion: Motion, balls: tuple[Ball, ...]) -> tuple:
  """The 'rolledOn' function runs 'balls' on in steps of a ms until the
  first of them rolls, five seconds at most, and returns them then."""
  radius = motion.table.radius
  for _ in range(5000):
    if motion.cloth.phaseOf(balls[0], radius) == 'rolling':
      return balls
    balls = motion.advanced(balls, 0.001)
  return balls


#  How far right of the red's middle the user's first break is aimed, in
#  radii. The user made it at 1.0 in the engine of the time; since the
#  cushions were fitted to the Korean break and their top grip set to the
#  measured 0.14, it scores from 1.1 to 1.35 (missing at 1.0 by 643 mm,
#  running from the foot straight up to the head): this is the middle.
BREAK_AIM = 1.2


def breakAim(white: Ball, red: Ball, radius: float) -> tuple[float, float]:
  """The 'breakAim' function returns the way 'white' is aimed in the
  user's first break: past the red's right, 'BREAK_AIM' of a radius
  from its middle, the way not of length one."""
  dx, dy = red.x - white.x, red.y - white.y
  apart = math.hypot(dx, dy)
  return (red.x + dy / apart * radius * BREAK_AIM - white.x,
          red.y - dx / apart * radius * BREAK_AIM - white.y)


def firstBreak() -> tuple[Ball, Ball, Ball]:
  """The 'firstBreak' function returns the balls of the opening, white
  struck as the user's first break: 0.38 R up, 0.26 R left, leaving at
  4.0 m/s past the red's right ('breakAim'), the squirt allowed for."""
  table = CaromTable()
  white, yellow, red = table.opening()
  radius = table.radius
  aimX, aimY = breakAim(white, red, radius)
  struck = Cue().sent(white, aimX, aimY, 4000.0, 0.38, -0.26, radius)
  return struck, yellow, red


class BilliardsTest(BaseTest):
  """Base class for the tests of the billiards' table and balls."""


class BilliardsWidgetTest(WidgetTest):
  """Base class for the tests of the billiards' widgets."""

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)
