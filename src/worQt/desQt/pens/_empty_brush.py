"""
EmptyBrush creates an empty 'QBrush' object. It has color with 0 alpha and
brush style: 'Qt.BrushStyle.NoBrush'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class EmptyBrush:
  """
  EmptyBrush creates an empty 'QBrush' object. It has color with 0 alpha and
  brush style: 'Qt.BrushStyle.NoBrush'.
  """

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    brush = QBrush()
    color = QColor(0, 0, 0, 0)
    style = Qt.BrushStyle.NoBrush
    brush.setColor(color)
    brush.setStyle(style)
    return brush
