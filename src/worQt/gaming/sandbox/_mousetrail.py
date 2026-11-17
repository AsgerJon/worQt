"""
MouseTrail keeps the mouse's motion as it came, each report stamped
with its time, and hands it on by time (user, 2026-11-17: "when moving
the mouse to change view, it feels like it polls every t0, whilst
somethign else renders at t1"; again: "the mouse look around polling
timer ... is colliding with the refresh rate"): taken a frame at a time
as it arrived, a mouse reporting at another rate than the screen draws
gave some frames one report and some two (at 125 reports a second and
60 frames, two, two, three: the look stuttered at the two rates' beat,
whatever they were). Each report is spread over the time since the one
before it (at most a report's usual spacing), and each frame takes the
motion of its own span of time, a little in the past ('takenUntil'):
even whatever the two rates. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections import deque

#  The reports' usual spacing until it is known (s), how many spacings
#  and lags are kept to know it by, the longest spacing still counted
#  as the mouse moving on (s); how far behind the frames take the
#  motion: the usual spacing, the delivery's wobble (the lags' spread
#  up to their 'LATE' share: reports wait while a frame is worked out)
#  and 'SLACK' more (the stamps' millisecond), within 'LEAST' and 'MOST'
#  (s).
SPACING = 0.008
KEPT = 64
MOVING = 0.05
LATE = 1.0
SLACK = 0.002
LEAST, MOST = 0.002, 0.04


class MouseTrail:
  """
  MouseTrail holds the mouse's reports not yet all taken (each its span
  of time on the reader's clock and the pixels moved right and down in
  it), the spacings between reports and the lags of their delivery
  (their stamps put on the reader's clock by the least lag seen: the
  clocks' offset), and how far
  the motion has been taken ('taken', s). 'noted' adds a report,
  'takenUntil' hands on the motion up to a moment (a frame's), 'cleared'
  forgets it all.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  taken: float | None

  #  Private Variables
  __spans: list
  __spacings: deque
  __lags: deque
  __last: float | None
  __least: float | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.__spacings, self.__lags = deque(maxlen=KEPT), deque(maxlen=KEPT)
    self.__spans, self.__last, self.taken = [], None, None
    self.__least = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def spacing(self, ) -> float:
    """The 'spacing' property is the reports' usual spacing (their
    middle one lately, moving), s."""
    if not self.__spacings:
      return SPACING
    ordered = sorted(self.__spacings)
    return ordered[len(ordered) // 2]

  @property
  def behind(self, ) -> float:
    """The 'behind' property is how far behind a frame's moment the
    motion is taken, s."""
    wobble = 0.0
    if self.__lags:
      ordered = sorted(self.__lags)
      wobble = ordered[int(LATE * (len(ordered) - 1))] - self.__least
    return max(LEAST, min(MOST, self.spacing + wobble + SLACK))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def noted(self, stamp: float, arrived: float, right: float,
            down: float) -> None:
    """The 'noted' method adds a report of 'right' and 'down' pixels,
    stamped 'stamp' s (the window system's clock; nought or less: none,
    its arrival taken) and arrived 'arrived' s (the reader's clock); one
    arriving after its time was taken is handed on at the next frame."""
    if stamp <= 0.0:
      stamp = arrived
    lag = arrived - stamp
    if self.__least is None or abs(lag - self.__least) > 1.0:
      self.__lags.clear()
      self.__least = lag
    self.__least = min(self.__least, lag)
    self.__lags.append(lag)
    end = stamp + self.__least
    if self.__last is not None and 0.0 < end - self.__last < MOVING:
      self.__spacings.append(end - self.__last)
    start = end - self.spacing
    if self.__last is not None:
      start = max(start, min(self.__last, end))
    self.__last = end
    if self.taken is not None and end <= self.taken:
      start = end = self.taken + 1e-9
    elif self.taken is not None:
      start = max(start, self.taken)
    if right or down:
      self.__spans.append((start, end, float(right), float(down)))

  def takenUntil(self, now: float) -> tuple[float, float]:
    """The 'takenUntil' method returns the pixels moved right and down
    from where the motion was taken last up to 'behind' s before 'now'
    (each report's share of its span in that time), and forgets them."""
    edge = now - self.behind
    if self.taken is None:
      self.taken = min([edge] + [start for start, _, _, _ in self.__spans])
    if edge <= self.taken:
      return 0.0, 0.0
    right = down = 0.0
    kept = []
    for start, end, dx, dy in self.__spans:
      if end <= self.taken:
        continue
      if end - start <= 1e-9:
        share = 1.0 if end <= edge else 0.0
        done = 1.0 if end <= edge else 0.0
      else:
        low, high = max(start, self.taken), min(end, edge)
        share = max(0.0, high - low) / (end - start)
        done = max(0.0, edge - start) / (end - start)
      right += share * dx
      down += share * dy
      if done < 1.0:
        kept.append((start, end, dx, dy))
    self.__spans = kept
    self.taken = edge
    return right, down

  def cleared(self, ) -> None:
    """The 'cleared' method forgets the motion not yet taken (the
    pointer let go, or come back in elsewhere)."""
    self.__spans, self.__last, self.taken = [], None, None
