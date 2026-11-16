"""
Pointer is the mouse pointer taken by a surface to look round with: it
is hidden, kept near the middle, and its moves are handed on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QCursor


class Pointer:
  """
  Pointer is the mouse pointer on 'surface' (a widget or a window):
  'taken' while it looks round, hidden; the pixels it moved right and
  down not yet handed on ('moved'). Put back in the middle when it
  strays a quarter of the surface off it, each move read from the
  nearer of where it last was and where it was put, so putting it back
  never jerks the look.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, surface: object) -> None:
    self.surface, self.taken = surface, False
    self._frames, self._right, self._down = [], 0.0, 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def take(self, ) -> None:
    """The 'take' method takes the pointer: hidden, put in the middle."""
    self.taken, self._frames = True, []
    self._right, self._down = 0.0, 0.0
    self.surface.setCursor(QCursor(Qt.CursorShape.BlankCursor))
    self._recentred()

  def letGo(self, ) -> None:
    """The 'letGo' method lets the pointer go, shown again."""
    if self.taken:
      self.surface.unsetCursor()
    self.taken, self._frames = False, []

  def forget(self, ) -> None:
    """The 'forget' method forgets where the pointer was (it left the
    surface: coming back in elsewhere must turn nothing)."""
    self._frames = []

  def moved(self, ) -> tuple[float, float]:
    """The 'moved' method returns the pixels moved right and down since
    last asked, and forgets them."""
    right, down = self._right, self._down
    self._right, self._down = 0.0, 0.0
    return right, down

  def movedTo(self, at: QPointF, local: QPointF) -> None:
    """The 'movedTo' method notes the pointer at 'at' on the screen,
    'local' on the surface."""
    if not self.taken:
      return
    frames = self._frames
    if not frames:
      frames.append(at)
    nearest = min(range(len(frames)), key=lambda k: abs(
      at.x() - frames[k].x()) + abs(at.y() - frames[k].y()))
    last = frames.pop(nearest)
    frames.append(at)
    self._right += at.x() - last.x()
    self._down += at.y() - last.y()
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
