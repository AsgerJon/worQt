"""
PaintMixin subclasses 'MixinBase' allowing for 'WPainterPath' to subclass
both 'QPainterPath' and 'MixinBase'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Union


class PaintMixin(MixinBase):
  """
  PaintMixin subclasses 'MixinBase' allowing for 'WPainterPath' to subclass
  both 'QPainterPath' and 'MixinBase'.
  """
  pass
