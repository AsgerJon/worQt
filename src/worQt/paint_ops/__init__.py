"""
The 'worQt.widgets.paint_ops' package provides classes encapsulates painting
operations modularly, allowing for flexible and reusable painting logic
across different widgets. Many such operations are the same across
otherwise different widgets.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._paint_mixin import PaintMixin
from ._abstract_paint_op import AbstractPaintOp
from ._paint_rect import PaintRect
from ._paint_box_model import PaintBoxModel
from ._paint_label import PaintLabel

__all__ = [
  'PaintMixin',
  'AbstractPaintOp',
  'PaintRect',
  'PaintBoxModel',
  'PaintLabel',
  ]
