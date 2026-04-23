"""
Point2DSampler subclasses 'IntSampler' from 'worktoy.work_test.samplers' and
provides a sampler class for 'Point2D' objects from 'worQt.utils.geom'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException
from worktoy.work_test.samplers import BaseSampler, IntSampler

from worQt.utils.geom import Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias, Type

  MaybeSampler: TypeAlias = Optional[IntSampler]
  SamplerField: TypeAlias = Union[IntSampler, Field]

  Ints: TypeAlias = tuple[int, int]
  MaybeInts: TypeAlias = Optional[Ints]
  IntsField: TypeAlias = Union[Ints, Field]


class Point2DSampler(BaseSampler):
  """
  Point2DSampler subclasses 'IntSampler' from 'worktoy.work_test.samplers'
  and provides a sampler class for 'Point2D' objects from 'worQt.utils.geom'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_args_x__ = 0, 255
  __fallback_args_y__ = 0, 255

  #  Private Variables
  __x_args__: MaybeInts = None
  __y_args__: MaybeInts = None
  __x_sampler__: MaybeSampler = None
  __y_sampler__: MaybeSampler = None

  #  Public Variables
  xSampler: SamplerField = Field()
  ySampler: SamplerField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createXSampler(self, **kwargs) -> None:
    args = maybe(self.__x_args__, self.__fallback_args_x__)
    self.__x_sampler__ = IntSampler(*args)

  @xSampler.GET
  def _getXSampler(self, **kwargs) -> IntSampler:
    if self.__x_sampler__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createXSampler(**kwargs)
      return self._getXSampler(_recursion=True)
    if isinstance(self.__x_sampler__, IntSampler):
      return self.__x_sampler__
    raise TypeException('__x_sampler__', self.__x_sampler__, IntSampler)

  def _createYSampler(self, **kwargs) -> None:
    args = maybe(self.__y_args__, self.__fallback_args_y__)
    self.__y_sampler__ = IntSampler(*args)

  @ySampler.GET
  def _getYSampler(self, **kwargs) -> IntSampler:
    if self.__y_sampler__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createYSampler(**kwargs)
      return self._getYSampler(_recursion=True)
    if isinstance(self.__y_sampler__, IntSampler):
      return self.__y_sampler__
    raise TypeException('__y_sampler__', self.__y_sampler__, IntSampler)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getValueType(self, **kwargs) -> type:
    return Point2D

  def _getItem(self, ) -> Point2D:
    return Point2D(self.xSampler.item, self.ySampler.item)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int)
  def __init__(self, *args, ) -> None:
    x0, x1, y0, y1 = args
    self.__x_args__ = x0, x1
    self.__y_args__ = y0, y1

  @overload(int, int)
  def __init__(self, *args, ) -> None:
    x1, y1 = args
    self.__x_args__ = 0, x1
    self.__y_args__ = 0, y1

  @overload()
  def __init__(self, **kwargs) -> None:
    pass
