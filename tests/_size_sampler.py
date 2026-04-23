"""
SizeSampler subclasses 'Point2DSampler' from the 'tests' package for the
'worQt' library. It shares the same structure as 'Point2DSampler' having
two components.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.work_test.samplers import IntSampler

from worQt.utils.geom import Size

from . import Point2DSampler

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias, Type

  IntField: TypeAlias = Union[int, Field]
  IntSamplerField: TypeAlias = Union[IntSampler, Field]


class SizeSampler(Point2DSampler):
  """
  SizeSampler subclasses 'Point2DSampler' from the 'tests' package for the
  'worQt' library. It shares the same structure as 'Point2DSampler' having
  two components.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  widthSampler: IntSamplerField = Field(Point2DSampler.xSampler)
  heightSampler: IntSamplerField = Field(Point2DSampler.ySampler)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getValueType(self, **kwargs) -> type:
    return Size

  def _getItem(self, ) -> Size:
    return Size(self.widthSampler.item, self.heightSampler.item)
