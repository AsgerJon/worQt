"""
TestLaps covers the lap timer ('LapTimer'): driven round the oval's
middle line at 25 m/s from the start-finish line, a frame at a time, its
laps take the lap's length over the speed (64.372 s), to a microsecond
(the moment it crossed found between frames); backing over the line
and on again counts no lap; a lap's time reads as minutes, seconds and
hundredths ('lapText').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys._laps import LINE, LapTimer, lapText
from worQt.phys._terrain import OVAL_LENGTH, ovalAt

from . import PhysTest

FRAME = 1.0 / 60.0


class TestLaps(PhysTest):
  """Tests for the lap timer."""

  def test_laps(self) -> None:
    """At 25 m/s round the middle line, two laps of 64.372 s each (to a
    microsecond), the running lap's time what has passed since."""
    timer = LapTimer(0.0)
    time = 0.0
    while time < 140.0:
      x, y, _ = ovalAt(LINE + 25.0 * time, 0.0)
      timer.seen(x, y, time)
      time += FRAME
    self.assertEqual(len(timer.laps), 2)
    for lap in timer.laps:
      self.assertNear(lap, OVAL_LENGTH / 25.0, 1e-6)
    self.assertNear(timer.now(time - FRAME),
                    time - FRAME - 2.0 * OVAL_LENGTH / 25.0, 1e-6)
    self.assertEqual(timer.best, min(timer.laps))
    self.assertEqual(timer.last, timer.laps[-1])

  def test_backing(self) -> None:
    """Rocked back and forth over the line, 10 m either way, many times,
    the timer counts no lap."""
    timer = LapTimer(0.0)
    for step in range(600):
      x, y, _ = ovalAt(LINE + 10.0 * math.sin(0.2 * step), 0.0)
      timer.seen(x, y, step * FRAME)
    self.assertEqual(timer.laps, [])
    self.assertIsNone(timer.best)

  def test_text(self) -> None:
    """A lap's time reads as minutes, seconds and hundredths; none, as
    dashes."""
    self.assertEqual(lapText(57.123), '0:57.12')
    self.assertEqual(lapText(125.5), '2:05.50')
    self.assertEqual(lapText(None), '-:--.--')
