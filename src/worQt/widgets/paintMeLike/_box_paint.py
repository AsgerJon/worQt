"""
BoxPaint provides a paint operation drawing the box model of a widget.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.utilities import maybe

from . import AbstractPaintMeLike
from ._abstract_paint_me_like import WidgetObject, PaintOp
from ...core import BoxModel

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any


class BoxPaint(AbstractPaintMeLike):
  """
  BoxPaint provides a paint operation drawing the box model of a widget.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __box_fallback__ = BoxModel()
  __margins_color__ = None

  #  Private Variables
  __box_model__ = None

  #  Public Variables
  boxModel = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @boxModel.GET
  def _getBoxModel(self) -> BoxModel:
    """
    Get the box model of the widget.
    """
    return maybe(self.__box_model__, self.__box_fallback__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintMeLike(self, widget: WidgetObject) -> PaintOp:
    """
    Factory creating the paint operation for the widget. This method
    returns a callable that paints the box model of the widget.
    """
    raise NotImplementedError("""TODO: the thing""")  # TODO: the thing
