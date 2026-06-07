"""
WPainterPath subclasses 'QPainterPath' and expands with direct support for
certain geometry classes used in 'worQt'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QPainterPath
from icecream import ic
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from .geom import Rect, RoundedRect
from ..mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Union


class WPainterPath(QPainterPath, MixinBase):
  """
  WPainterPath subclasses 'QPainterPath' and expands with direct support for
  certain geometry classes used in 'worQt'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addRect(self, rect: Rect, *args) -> None:
    if args:
      return QPainterPath.addRect(self, rect, *args)
    if isinstance(rect, Rect):
      return QPainterPath.addRect(self, rect.Q)
    raise TypeException('rect', rect, Rect)

  def addRoundedRect(self, rect: Rect, *args) -> None:
    hr, vr, *_ = (*args, 0, 0)
    if isinstance(rect, QRect):
      return QPainterPath.addRoundedRect(self, rect, hr, vr)
    if isinstance(rect, QRectF):
      return QPainterPath.addRoundedRect(self, QRectF.toRect(rect), hr, vr)
    if isinstance(rect, RoundedRect):
      return QPainterPath.addRoundedRect(self, rect.Q, rect.hr, rect.vr)
    if isinstance(rect, Rect):
      return QPainterPath.addRoundedRect(self, rect.Q, hr, vr)
    raise TypeException('rect', rect, Rect, QRect, QRectF, RoundedRect)
