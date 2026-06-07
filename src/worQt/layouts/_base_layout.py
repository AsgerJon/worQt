"""
BaseLayout subclasses 'QGridLayout' and 'LayoutMixin' providing the base
layout class used across the 'worQt' framework. 'PySide6' does provide
several subclasses of 'QLayout' besides 'QGridLayout', but the
recommendation is to subclass this class to remake those based on the
provided 'QGridLayout' functionality.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout
from worktoy.desc import Field

from . import LayoutMixin
from ..utils.geom import Size

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, Type, TypeAlias

  SizeField: TypeAlias = Union[Field, Size]


class BaseLayout(QGridLayout, LayoutMixin):
  """
  BaseLayout subclasses 'QGridLayout' and 'LayoutMixin' providing the base
  layout class used across the 'worQt' framework. 'PySide6' does provide
  several subclasses of 'QLayout' besides 'QGridLayout', but the
  recommendation is to subclass this class to remake those based on the
  provided 'QGridLayout' functionality.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables

  #  Virtual Variables
  assignedSize: SizeField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @assignedSize.GET
  def _getAssignedSize(self, ) -> Size:
    return self.parent().viewRect.size

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
