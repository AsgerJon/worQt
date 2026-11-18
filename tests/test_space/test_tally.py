"""
TestTally covers the debug view's rates (user, 2026-11-18: "implement
debug view in the top left listing fps, and phys rate"): what is
counted at a frame's end said as how many a second, anew every span;
and the view shown anew ten times a second, not every frame ("we don't
need to refresh the fps counter 1200 times pers second").
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._tally import SPAN, Tally

from . import SpaceTest


class TestTally(SpaceTest):
  """Tests for counting how often a second."""

  def test_rate(self) -> None:
    """Twenty steps a frame at sixty frames a second is 1200 a second,
    said once a span has passed; nought before; a stop (nought counted)
    brings it to nought within two spans."""
    tally, frame = Tally(), 1.0 / 60.0
    now = 10.0
    tally.counted(20, now)
    self.assertEqual(tally.rate, 0.0)
    frames = int(SPAN / frame) + 1
    for _ in range(frames):
      now += frame
      tally.counted(20, now)
    self.assertAlmostEqual(tally.rate, 1200.0, 6)
    for _ in range(2 * frames):
      now += frame
      tally.counted(0, now)
    self.assertEqual(tally.rate, 0.0)

  def test_refused(self) -> None:
    """Less than nothing cannot be counted."""
    with self.assertRaises(ValueError):
      Tally().counted(-1, 0.0)

  def test_shown(self) -> None:
    """At 144 frames a second for two seconds the window shows the
    debug view's lines 20 times, the first at once (its own method, its
    viewport stood in for)."""
    import math
    from types import SimpleNamespace
    from worQt.gaming.space._spacewindow import DEBUG_EVERY, SpaceWindow
    shown = []
    window = SimpleNamespace(
      _debugAt=-math.inf, _debugText=lambda: 'fps',
      viewport=SimpleNamespace(debugShown=shown.append))
    frames = 288
    for k in range(frames):
      SpaceWindow._debugKept(window, 5.0 + 2.0 * k / frames)
    self.assertEqual(len(shown), round(2.0 / DEBUG_EVERY))
