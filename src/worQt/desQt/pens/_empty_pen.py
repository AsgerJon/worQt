"""
EmptyPen creates an empty 'QPen' object. It has color with 0 alpha and pen
style: 'Qt.PenStyle.NoPen'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class EmptyPen:
  """
  EmptyPen creates an empty 'QPen' object. It has color with 0 alpha and pen
  style: 'Qt.PenStyle.NoPen'.
  """

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    pen = QPen()
    color = QColor(0, 0, 0, 0, )
    style = Qt.PenStyle.NoPen
    pen.setColor(color)
    pen.setStyle(style)
    pen.setWidth(0)
    return pen
