"""
Tally counts what happens and says how often a second (user, 2026-11-18:
"implement debug view in the top left listing fps, and phys rate"): the
physics' steps, as the frames are counted for 'fps'. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  How long it counts before it says the rate anew, s (as the frames).
SPAN = 0.5


class Tally:
  """
  Tally holds how many have happened since it last said ('_count') and
  since when ('_since', s); 'counted' adds some at a time, and every
  'SPAN' s 'rate' is said anew: how many a second over that span.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  rate: float

  #  Private Variables
  _count: int
  _since: float | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.rate, self._count, self._since = 0.0, 0, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def counted(self, count: int, now: float) -> None:
    """The 'counted' method adds 'count' happened by 'now' (real s,
    'time.perf_counter'); 'SPAN' s on from when it began counting,
    'rate' is said anew and it counts afresh."""
    if count < 0:
      raise ValueError('cannot count %d' % count)
    if self._since is None:
      self._since = now
      return
    self._count += int(count)
    if now - self._since >= SPAN:
      self.rate = self._count / (now - self._since)
      self._count, self._since = 0, now
