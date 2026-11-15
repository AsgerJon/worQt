"""
Courses a robot drives round (user, 2026-11-15: the real car round a lap
of central Copenhagen, after the oval): where a point lies on one ('out'
m to the right of its middle line, 'along' m round it from its start)
and back, how wide and banked it is along it, how far over its inside
edge a point is. 'OvalCourse' is the oval ('_terrain.oval''s formulas,
to the digit); 'CrgCourse' a road laid along a line ('_crg.CrgTrack':
its rows' middles, a lap closed on itself, level for the plan).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._terrain import OVAL_LENGTH, ovalAcross, ovalAt, ovalPlaceOf
from ._terrain import ovalShapeAt


class OvalCourse:
  """
  OvalCourse is the oval as a course: 'length' round its middle line,
  m, its 'start' (the start line, m round from the front straight's
  start), and its places ('placeOf', 'at'), shape ('shapeAt') and inside
  edge ('inside') as the oval's own functions have them.
  """

  def __init__(self, ) -> None:
    from ._laps import LINE
    self.length, self.start = OVAL_LENGTH, LINE

  def placeOf(self, x: float, y: float) -> tuple[float, float]:
    """The 'placeOf' method returns how far out from the middle line
    'x', 'y' is (to the right as driven) and how far round, m."""
    return ovalPlaceOf(x, y)

  def at(self, along: float, out: float) -> tuple[float, float, float]:
    """The 'at' method returns the point 'along' m round and 'out' m
    out (right) of the middle line, and the line's heading there."""
    return ovalAt(along, out)

  def shapeAt(self, along: float) -> tuple[float, float, float]:
    """The 'shapeAt' method returns how wide the racing surface is
    'along' m round, how banked, rad, and how wide its apron, m."""
    return ovalShapeAt(along)

  def inside(self, x: float, y: float) -> float:
    """The 'inside' method returns how far 'x', 'y' is over the racing
    surface's inside edge, m (below nought: on the apron or in)."""
    return float(ovalAcross(x, y)[0])


OVAL = OvalCourse()


class CrgCourse:
  """
  CrgCourse is a road laid along a line ('track', a closed lap) as a
  course: 'length' its rows' steps all round, m, starting at its first
  row; a point's place by the row nearest it (looked for about the one
  found last, all of them should it be far: 'placeOf'); its shape level,
  'width' m wide (the file says nothing of its kerbs), no apron, no
  inside edge to cross.
  """

  #  How many rows either side of the last found are looked at, and how
  #  far from the middle a point may be before every row is.
  WINDOW, LOST = 80, 30.0

  def __init__(self, track: object, width: float) -> None:
    self.track, self.width = track, width
    self.rows = len(track.x) - 1
    self.length, self.start = self.rows * track.step, 0.0
    self.hint = 0

  def _rowOf(self, x: float, y: float) -> int:
    """Returns the row nearest 'x', 'y': about the last found, else
    (the nearest there at the window's end, or far) among all."""
    track, rows = self.track, self.rows
    near = (self.hint + numpy.arange(-self.WINDOW, self.WINDOW + 1)) % rows
    far = (track.x[near] - x) ** 2 + (track.y[near] - y) ** 2
    best = int(numpy.argmin(far))
    if best in (0, len(near) - 1) or far[best] > self.LOST ** 2:
      every = (track.x[:rows] - x) ** 2 + (track.y[:rows] - y) ** 2
      return int(numpy.argmin(every))
    return int(near[best])

  def placeOf(self, x: float, y: float) -> tuple[float, float]:
    """The 'placeOf' method returns how far right of the middle line
    'x', 'y' is and how far round from the start, m (along the step it
    lies on: its share of the gap between the rows where it is across,
    as 'at' lays them; uncannyball's 'groundAt')."""
    track, rows = self.track, self.rows
    row = self._rowOf(x, y)
    dx, dy = x - track.x[row], y - track.y[row]
    along = dx * track.leftY[row] - dy * track.leftX[row]
    if along < 0.0:
      row = (row - 1) % rows
      dx, dy = x - track.x[row], y - track.y[row]
      along = dx * track.leftY[row] - dy * track.leftX[row]
    self.hint = row
    across = dx * track.leftX[row] + dy * track.leftY[row]
    gapX = track.x[row + 1] - track.x[row] + across * (
      track.leftX[row + 1] - track.leftX[row])
    gapY = track.y[row + 1] - track.y[row] + across * (
      track.leftY[row + 1] - track.leftY[row])
    share = max(0.0, min(float(along) / math.hypot(gapX, gapY), 1.0))
    return -float(across), (row + share) * track.step

  def at(self, along: float, out: float) -> tuple[float, float, float]:
    """The 'at' method returns the point 'along' m round (any number of
    laps) and 'out' m right of the middle line, and the line's heading
    there (from the way to the left, as it turns from row to row: the
    file's one heading a step held it still, then jumped, and a robot
    steering by it jerked the wheel at each row, 37 times a second at
    15 m/s)."""
    track = self.track
    s = along % self.length
    row = min(int(s / track.step), self.rows - 1)
    f = s / track.step - row
    x = track.x[row] + f * (track.x[row + 1] - track.x[row])
    y = track.y[row] + f * (track.y[row + 1] - track.y[row])
    leftX = track.leftX[row] + f * (track.leftX[row + 1] - track.leftX[row])
    leftY = track.leftY[row] + f * (track.leftY[row + 1] - track.leftY[row])
    size = math.hypot(leftX, leftY)
    return (float(x - out * leftX / size), float(y - out * leftY / size),
            math.atan2(-leftX, leftY))

  def shapeAt(self, along: float) -> tuple[float, float, float]:
    """The 'shapeAt' method returns the road's width, its banking (none:
    level for the plan) and its apron (none)."""
    return self.width, 0.0, 0.0

  def inside(self, x: float, y: float) -> float:
    """The 'inside' method returns how far over an inside edge 'x', 'y'
    is: a road has none to cross (the infinite)."""
    return math.inf
