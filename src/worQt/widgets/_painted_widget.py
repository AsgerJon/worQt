"""
PaintedWidget subclasses 'AbstractWidget' and provides the entry point for
the 'worQt' widget family.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtGui import QPaintEvent

from . import AbstractWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Type


class PaintedWidget(AbstractWidget):
  """
  PaintedWidget subclasses 'AbstractWidget' and provides the entry point for
  the 'worQt' widget family.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintEvent(self, event: QPaintEvent) -> None:
    super().paintEvent(event)
    
