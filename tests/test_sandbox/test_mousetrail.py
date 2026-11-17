"""
TestMouseTrail covers the mouse's motion handed on by time (user,
2026-11-17: "when moving the mouse to change view, it feels like it
polls every t0, whilst somethign else renders at t1"; "the mouse look
around polling timer ... is colliding with the refresh rate"): a mouse
moving evenly at 125 reports a second turns the look evenly frame by
frame at 60 and at 144 frames a second (taken as the reports came,
frames got two or three, nought or one); the reports delivered late in
batches, as an event loop busy drawing delivers them, still even by
their stamps; nothing is lost when the mouse stops; a first move after
a rest is not smeared over the rest.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox._mousetrail import MouseTrail

from . import SandboxTest

#  The mouse's reports' spacing (125 a second, a common mouse's), s; how
#  far a report moves, pixels; the stamps' clock against the reader's.
REPORT = 0.008
STEP = 1.0
CLOCKS = 1000.0


class TestMouseTrail(SandboxTest):
  """Tests for the mouse's motion handed on by time."""

  def _moved(self, trail: MouseTrail, frame: float, seconds: float,
             batched: bool) -> list:
    """Returns the motion each frame takes ('frame' s apart) while the
    mouse moves evenly for 'seconds' s and then rests a while, its
    reports delivered at once ('batched': each frame's at its start)."""
    reports = [k * REPORT for k in range(1, int(seconds / REPORT) + 1)]
    out, next_ = [], 0
    frames = int((seconds + 0.2) / frame)
    for k in range(1, frames + 1):
      now = k * frame
      while next_ < len(reports) and reports[next_] <= now:
        at = reports[next_]
        arrived = now if batched else at
        trail.noted(at + CLOCKS, arrived + 0.0005, STEP, 0.0)
        next_ += 1
      out.append(trail.takenUntil(now)[0])
    return out

  def _raw(self, frame: float, seconds: float) -> list:
    """Returns the motion each frame took as the reports came (the old
    way: all that arrived since the frame before)."""
    reports = [k * REPORT for k in range(1, int(seconds / REPORT) + 1)]
    out = []
    for k in range(1, int(seconds / frame) + 1):
      out.append(sum(STEP for r in reports if (k - 1) * frame < r <= (
        k * frame)))
    return out

  def test_even(self) -> None:
    """At 60 and 144 frames a second, the look turns as evenly as the
    mouse moves, within 3 % of its rate a frame once going (as the
    reports came: 2 or 3, 0 or 1 a frame)."""
    for frame in (1.0 / 60.0, 1.0 / 144.0):
      want = STEP * frame / REPORT
      raw = self._raw(frame, 1.0)[10:]
      self.assertGreater(max(raw) - min(raw), 0.9, frame)
      moved = self._moved(MouseTrail(), frame, 1.0, False)
      going = moved[int(0.1 / frame):int(0.9 / frame)]
      for amount in going:
        self.assertLess(abs(amount - want), 0.03 * want, (frame, amount))

  def test_batched(self) -> None:
    """Delivered in batches at each frame's start, the reports' stamps
    still turn the look evenly once the clocks' offset is found (the
    least lag seen: in the first moments it shifts by a fraction of a
    millisecond): within 5 % (as the reports came: 2 or 3, 50 %)."""
    frame = 1.0 / 60.0
    want = STEP * frame / REPORT
    moved = self._moved(MouseTrail(), frame, 1.0, True)
    for amount in moved[int(0.3 / frame):int(0.9 / frame)]:
      self.assertLess(abs(amount - want), 0.05 * want, amount)

  def test_whole(self) -> None:
    """When the mouse stops, every pixel it moved has been handed on."""
    for frame in (1.0 / 60.0, 1.0 / 144.0):
      for batched in (False, True):
        moved = self._moved(MouseTrail(), frame, 0.5, batched)
        self.assertAlmostEqual(sum(moved), STEP * int(0.5 / REPORT), 6)

  def test_after_rest(self) -> None:
    """A move after a second's rest is handed on within two frames, not
    spread over the rest; a report arriving after its time was taken is
    handed on at the next frame."""
    trail, frame = MouseTrail(), 1.0 / 60.0
    trail.takenUntil(0.5)
    trail.noted(1.5 + CLOCKS, 1.5005, 5.0, 2.0)
    first = trail.takenUntil(1.5 + frame)
    second = trail.takenUntil(1.5 + 2.0 * frame)
    self.assertAlmostEqual(first[0] + second[0], 5.0, 9)
    self.assertAlmostEqual(first[1] + second[1], 2.0, 9)
    trail.noted(1.0 + CLOCKS, 1.6, 3.0, 0.0)
    self.assertAlmostEqual(trail.takenUntil(1.6 + frame)[0], 3.0, 9)
