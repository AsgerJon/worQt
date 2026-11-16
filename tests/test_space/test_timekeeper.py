"""
TestTimekeeper covers the solar system's time (user, 2026-11-16: "just
put in a leap step every 256 steps, where we adjust"; "we just put a
factor on each step"): the warps, a leap each 256 steps folding the
time into the sky, nothing jumping at a leap, and warping to a moment
(the spec: "warp to apogee ... stops shortly before it").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._timekeeper import LEAP, WARPS, Timekeeper

from . import FRAME, SpaceTest


class TestTimekeeper(SpaceTest):
  """Tests for 'Timekeeper'."""

  def test_warps(self) -> None:
    """Time runs at one to 100 000 times; up and down a warp at a time,
    no further; back to real time at once."""
    keeper = Timekeeper(self.systemOf())
    self.assertEqual(keeper.factor, 1)
    for warp in WARPS[1:]:
      keeper.faster()
      self.assertEqual(keeper.factor, warp)
    keeper.faster()
    self.assertEqual(keeper.factor, 100000)
    keeper.slower()
    self.assertEqual(keeper.factor, 10000)
    keeper.realtime()
    self.assertEqual(keeper.factor, 1)
    keeper.slower()
    self.assertEqual(keeper.factor, 1)
    self.assertEqual(keeper.secondsOf(FRAME), FRAME)

  def test_leap(self) -> None:
    """Every 256th step leaps: the time since the last is folded into the
    sky and starts at nought; the game's own clock goes on."""
    system = self.systemOf()
    keeper = Timekeeper(system)
    luna = system.named('Luna')
    for _ in range(LEAP - 1):
      self.assertFalse(keeper.ticked(FRAME))
    then = system.relative(luna, 0, keeper.now + FRAME)[0]
    self.assertTrue(keeper.ticked(FRAME))
    self.assertEqual(keeper.now, 0.0)
    self.assertEqual(keeper.leaps, 1)
    self.assertEqual(system.version, 1)
    self.assertAlmostEqual(keeper.elapsed, LEAP * FRAME, 9)
    self.assertClose(system.relative(luna, 0, 0.0)[0], then, 1e-3)

  def test_smooth(self) -> None:
    """Over many leaps Luna moves from step to step as fast as it goes,
    never jumping, at real time and at warp."""
    system = self.systemOf()
    keeper = Timekeeper(system)
    luna = system.named('Luna')
    last = system.relative(luna, 0, 0.0)[0]
    for factor in (1, 100000):
      keeper.realtime()
      while keeper.factor < factor:
        keeper.faster()
      for _ in range(3 * LEAP):
        seconds = keeper.secondsOf(FRAME)
        keeper.ticked(seconds)
        place, speed = system.relative(luna, 0, keeper.now)
        moved = math.dist(place, last)
        most = seconds * math.dist(speed, (0, 0, 0)) * 1.01 + 1e-3
        self.assertLessEqual(moved, most)
        last = place

  def test_aim(self) -> None:
    """Warped to a moment 5000 s on, time runs fast, eases off, stops on
    it exactly, never past it, and runs as it is after."""
    keeper = Timekeeper(self.systemOf())
    target = keeper.elapsed + 5000.0
    keeper.aim(5000.0)
    self.assertGreater(keeper.factor, 1)
    frames = 0
    while keeper.aimed is not None and frames < 10000:
      keeper.ticked(keeper.secondsOf(FRAME))
      self.assertLessEqual(keeper.elapsed, target + 1e-9)
      frames += 1
    self.assertLess(frames, 600)
    self.assertAlmostEqual(keeper.elapsed, target, 6)
    self.assertEqual(keeper.factor, 1)
    keeper.ticked(keeper.secondsOf(FRAME))
    self.assertAlmostEqual(keeper.elapsed, target + FRAME, 6)
