"""
EmptyPen provides an empty 'QPen' object with the descriptor protocol.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class EmptyPen:
  """
  EmptyPen provides an empty 'QPen' object with the descriptor protocol.
  """

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    pen = QPen()
    pen.setStyle(Qt.PenStyle.NoPen)
    color = QColor()
    color.setAlpha(0)
    pen.setColor(color)
    return pen
