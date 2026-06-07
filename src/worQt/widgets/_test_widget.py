"""
TestWidget is an ad hoc subclass of 'PaintedWidget' used for development
and testing purposes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils.geom import Size
from . import PaintedWidget
from ..paint_ops import PaintBoxModel

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestWidget(PaintedWidget):
  """
  TestWidget is an ad hoc subclass of 'PaintedWidget' used for development
  and testing purposes.
  """

  paintBoxOp = PaintBoxModel()

  def __init__(self, *args: Any, **kwargs: Any) -> None:
    super().__init__(*args, **kwargs)

  def _getRequiredSize(self, ) -> Size:
    return Size(200, 200)
