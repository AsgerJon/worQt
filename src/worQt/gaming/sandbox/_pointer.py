"""
Pointer is the mouse pointer taken by a surface to look round with: it
is hidden, kept near the middle, and its moves are handed on: as they
came ('moved') or by time, each frame the motion of its own span of
time ('movedBy', '_mousetrail'). Taken, the cursor is also hidden by the
X server itself ('_hiddencursor': else gamescope does not hold the
mouse in its window).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import time

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QCursor

from ._hiddencursor import HiddenCursor
from ._mousetrail import MouseTrail


class Pointer:
  """
  Pointer is the mouse pointer on 'surface' (a widget or a window):
  'taken' while it looks round, hidden; the pixels it moved right and
  down not yet handed on ('moved'), and the same stamped with their
  times ('trail': handed on by time, 'movedBy'). Put back in the middle
  when it
  strays a quarter of the surface off it, each move read from the
  nearer of where it last was and where it was put, so putting it back
  never jerks the look.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, surface: object) -> None:
    self.surface, self.taken, self.trail = surface, False, MouseTrail()
    self.hiding = HiddenCursor()
    self._frames, self._right, self._down = [], 0.0, 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def take(self, ) -> None:
    """The 'take' method takes the pointer: hidden (by the X server too,
    before it is put back: the warp locks it), put in the middle."""
    self.taken, self._frames = True, []
    self._right, self._down = 0.0, 0.0
    self.trail.cleared()
    self.surface.setCursor(QCursor(Qt.CursorShape.BlankCursor))
    self.hiding.hidden()
    self._recentred()

  def letGo(self, ) -> None:
    """The 'letGo' method lets the pointer go, shown again."""
    if self.taken:
      self.surface.unsetCursor()
    self.hiding.shown()
    self.taken, self._frames = False, []
    self.trail.cleared()

  def forget(self, ) -> None:
    """The 'forget' method forgets where the pointer was (it left the
    surface: coming back in elsewhere must turn nothing)."""
    self._frames = []
    self.trail.cleared()

  def moved(self, ) -> tuple[float, float]:
    """The 'moved' method returns the pixels moved right and down since
    last asked, and forgets them."""
    right, down = self._right, self._down
    self._right, self._down = 0.0, 0.0
    return right, down

  def movedBy(self, now: float) -> tuple[float, float]:
    """The 'movedBy' method returns the pixels moved right and down in
    the time up to the frame at 'now' ('time.perf_counter', s) since the
    frame before it (a little behind it: 'MouseTrail.takenUntil')."""
    return self.trail.takenUntil(now)

  def movedTo(self, at: QPointF, local: QPointF,
              stamp: float = 0.0) -> None:
    """The 'movedTo' method notes the pointer at 'at' on the screen,
    'local' on the surface, at 'stamp' s (the event's time: the window
    system's clock; nought: none, its arrival taken)."""
    if not self.taken:
      return
    frames = self._frames
    if not frames:
      frames.append(at)
    nearest = min(range(len(frames)), key=lambda k: abs(
      at.x() - frames[k].x()) + abs(at.y() - frames[k].y()))
    last = frames.pop(nearest)
    frames.append(at)
    right, down = at.x() - last.x(), at.y() - last.y()
    self._right += right
    self._down += down
    self.trail.noted(stamp, time.perf_counter(), right, down)
    wide, high = self.surface.width(), self.surface.height()
    if abs(local.x() - 0.5 * wide) > 0.25 * wide \
        or abs(local.y() - 0.5 * high) > 0.25 * high:
      self._recentred()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _recentred(self, ) -> None:
    """Puts the hidden pointer back in the middle, keeping two places to
    read moves from: where it last was and where it is put."""
    surface = self.surface
    target = surface.mapToGlobal(QPoint(surface.width() // 2,
                                        surface.height() // 2))
    self._frames = self._frames[-1:] + [QPointF(target)]
    QCursor.setPos(target)
