"""
LapTimer times laps of the oval (user, 2026-11-12: "implement a
laptimer fr fr!"). The start-finish line runs across the front straight
at its middle ('LINE' m round the middle line from where the straight
begins: where the car is set down). Told where the car is each frame
('seen'), it adds up how far round the oval the car has come, forward
counted up, and a lap is done each time that passes another lap's
length: the moment it crossed the line found between the two frames.
The first lap runs from the start (standing), the rest are flying;
backing over the line takes the distance back, so the line must be
crossed forward again. 'laps' holds each lap's time, s; 'now' is the
running lap's, 'last' and 'best' the finished ones'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._terrain import OVAL_STRAIGHT

#  Where the start-finish line is, m round the middle line from the
#  front straight's start: the straight's middle.
LINE = 0.5 * OVAL_STRAIGHT


class LapTimer:
  """
  LapTimer times a car's laps, started at 'start' s: 'laps' the times
  done, 'gone' how far round it has come since, m.
  """

  def __init__(self, start: float = 0.0, course: object = None) -> None:
    from ._course import OVAL
    self.started, self.laps, self.gone = start, [], 0.0
    self._round, self._when = None, start
    self.course = OVAL if course is None else course

  def seen(self, x: float, y: float, time: float) -> None:
    """The 'seen' method notes the car at 'x', 'y' at 'time' s: how far
    it has come since last seen, and a lap done should it have crossed
    the line forward once more."""
    course = self.course
    length = course.length
    round_ = (course.placeOf(x, y)[1] - course.start) % length
    if self._round is not None:
      moved = round_ - self._round
      moved -= length * round(moved / length)
      line = (len(self.laps) + 1) * length
      if self.gone < line <= self.gone + moved:
        crossed = self._when + (time - self._when) * (
          line - self.gone) / moved
        self.laps.append(crossed - self.started)
        self.started = crossed
      self.gone += moved
    self._round, self._when = round_, time

  def now(self, time: float) -> float:
    """The 'now' method returns how long the running lap has run at
    'time', s."""
    return time - self.started

  @property
  def last(self, ) -> float | None:
    """The last lap's time, s (None before one is done)."""
    return self.laps[-1] if self.laps else None

  @property
  def best(self, ) -> float | None:
    """The best lap's time, s (None before one is done)."""
    return min(self.laps) if self.laps else None


def lapText(seconds: float | None) -> str:
  """The 'lapText' function returns a lap's time as minutes, seconds and
  hundredths ('0:57.12'), or dashes for none."""
  if seconds is None:
    return '-:--.--'
  minutes = int(seconds // 60.0)
  return '%d:%05.2f' % (minutes, seconds - 60.0 * minutes)
