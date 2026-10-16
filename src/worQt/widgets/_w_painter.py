"""
WPainter subclasses 'QPainter'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractWidget

from PySide6.QtGui import QPainter, QPaintDevice

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias

  Device: TypeAlias = Union[AbstractWidget, QPaintDevice]


class WPainter(QPainter):
  """
  WPainter subclasses 'QPainter'.
  """

  def drawBoxModel(self, box: Box, *args: Any, **kwargs: Any) -> None:
    device: Device = QPainter.device(self)
