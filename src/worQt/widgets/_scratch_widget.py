"""
ScratchWidget is an ad hoc subclass of 'PaintedWidget' used for development
and testing purposes. It is named 'ScratchWidget' rather than 'TestWidget'
so its name does not trip the 'worQt.qtest' test discovery, which collects
class names beginning with 'Test'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils.geom import Size
from . import PaintedWidget
from ..paint_ops import PaintBoxModel

if TYPE_CHECKING:  # pragma: no cover
  pass


class ScratchWidget(PaintedWidget):
  """
  ScratchWidget is an ad hoc subclass of 'PaintedWidget' used for
  development and testing purposes.

  No '__init__' is declared: the inherited 'PaintedWidget'/'AbstractWidget'
  constructor dispatcher handles construction.
  """

  paintBoxOp = PaintBoxModel()

  def _getRequiredSize(self, ) -> Size:
    return Size(200, 200)
