"""
EmptyBrush provides an empty brush object for use in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class EmptyBrush:
  """
  EmptyBrush provides an empty brush object for use in the worQt framework.
  """

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    brush = QBrush()
    brush.setStyle(Qt.BrushStyle.NoBrush)
    color = QColor()
    color.setAlpha(0)
    brush.setColor(color)
    return brush
