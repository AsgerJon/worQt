"""
Trails is the way each ball of a shot went, as far as the shot is
shown, and 'ribbonMesh' the triangles a way is drawn with, as a broadcast
draws it on the cloth seen from above.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple, TYPE_CHECKING

import numpy

from ._carom_table import isParked

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._recorder import Recording

_DUE = 1e-9  # s: a sample due this little after now is shown now
_TURNED = 1e-6  # a way turning back on itself: its sides cancel so far
_SHARPEST = 0.25  # a mitre reaches four half widths out at most


class Trails(NamedTuple):
  """
  Trails is the way each ball of a shot went, as far as the shot is
  shown: of each ball, its middle at the first sample and then at each
  sample at least 'spacing' mm on from the last one kept, 'kept'; the
  samples taken in so far, 'taken'. It never changes: 'followed' returns
  it with the samples up to a moment taken in; 'paths' gives each ball's
  way, ending where the ball is at that moment.

  Kept so, a way bends where the ball turned, at a cushion or another
  ball, within 'spacing'; a ball standing still adds nothing.
  """

  spacing: float = 3.0
  taken: int = 0
  kept: tuple = ()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def followed(self, recording: Recording, seconds: float) -> Trails:
    """The 'followed' method returns the trails with the samples of
    'recording' up to 'seconds' after the balls were struck taken in,
    those not taken in before."""
    count = recording.count()
    if not count:
      return self
    shown = int(math.floor(seconds * recording.rate + _DUE)) + 1
    shown = min(max(shown, 1), count)
    if shown <= self.taken:
      return self
    rows = recording.placesOf(self.taken, shown)
    kept = [list(points) for points in self.kept]
    if not kept:
      kept = [[] for _ in recording.names]
    for points, places in zip(kept, numpy.swapaxes(rows, 0, 1)):
      self._keep(points, places)
    return Trails(self.spacing, shown,
                  tuple(tuple(points) for points in kept))

  def paths(self, recording: Recording,
            seconds: float) -> tuple[numpy.ndarray, ...]:
    """The 'paths' method returns each ball's way, in the order of the
    balls of 'recording', as an array of its places, 'x' and 'y' in mm:
    the places kept, then where it is 'seconds' after the balls were
    struck. A ball whose way was not taken in has no places."""
    now = recording.ballsAt(seconds)
    out = []
    for k, ball in enumerate(now):
      points = list(self.kept[k]) if k < len(self.kept) else []
      parked = isParked(ball.x, ball.y)
      if points and not parked and points[-1] != (ball.x, ball.y):
        points.append((ball.x, ball.y))
      out.append(numpy.array(points, float).reshape(-1, 2))
    return tuple(out)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _keep(self, points: list, places: numpy.ndarray) -> None:
    """Adds to 'points' each of 'places' at least 'spacing' on from the
    last of them, the first of all whatever; none gone into a pocket."""
    spacing = self.spacing
    for x, y in places.tolist():
      if isParked(x, y):
        continue
      if points:
        lastX, lastY = points[-1]
        if math.hypot(x - lastX, y - lastY) < spacing:
          continue
      points.append((x, y))


def ribbonMesh(points: numpy.ndarray, halfWidth: float,
               lift: float) -> numpy.ndarray:
  """The 'ribbonMesh' function returns the triangles of a flat ribbon
  'halfWidth' either side of the way through 'points', each its 'x' and
  'z' in the plane 'lift' above nought, as 'prismMesh' returns triangles:
  a row a corner, its place then its normal, up. At each bend the ribbon
  is mitred, four half widths out at most; where the way turns straight
  back, it is cut square. A way of fewer than two places has none."""
  points = numpy.asarray(points, float).reshape(-1, 2)
  if len(points) > 1:
    steps = numpy.diff(points, axis=0)
    moved = numpy.hypot(steps[:, 0], steps[:, 1]) > 1e-9
    points = points[numpy.concatenate(([True], moved))]
  if len(points) < 2:
    return numpy.zeros((0, 6))
  steps = numpy.diff(points, axis=0)
  lengths = numpy.hypot(steps[:, 0], steps[:, 1])
  ways = steps / lengths[:, None]
  sides = numpy.stack((-ways[:, 1], ways[:, 0]), 1)
  before = numpy.vstack((sides[:1], sides))
  after = numpy.vstack((sides, sides[-1:]))
  mitre = before + after
  size = numpy.hypot(mitre[:, 0], mitre[:, 1])
  turned = size < _TURNED
  mitre = numpy.where(turned[:, None], after,
                      mitre / numpy.maximum(size, _TURNED)[:, None])
  reach = 1.0 / numpy.maximum((mitre * after).sum(1), _SHARPEST)
  offsets = mitre * (halfWidth * reach)[:, None]
  left, right = points + offsets, points - offsets
  corners = numpy.stack((left[:-1], right[:-1], left[1:],
                         right[:-1], right[1:], left[1:]), 1)
  corners = corners.reshape(-1, 2)
  rows = numpy.zeros((len(corners), 6))
  rows[:, 0] = corners[:, 0]
  rows[:, 1] = lift
  rows[:, 2] = corners[:, 1]
  rows[:, 4] = 1.0
  return rows
