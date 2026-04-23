"""
RectSampler subclasses BaseSampler from 'worktoy.work_test.samplers'
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.lorem_ipsum import StochasticWord
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException
from worktoy.work_test.samplers import BaseSampler, IntSampler

from worQt.utils.geom import Rect
from . import Point2DSampler, SizeSampler

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias, Type

  Ints: TypeAlias = tuple[int, int]
  MaybeInts: TypeAlias = Optional[Ints]
  IntsField: TypeAlias = Union[Ints, Field]

  MaybePoint2DSampler: TypeAlias = Optional[Point2DSampler]
  Point2DField: TypeAlias = Union[Point2DSampler, Field]
  MaybeSizeSampler: TypeAlias = Optional[SizeSampler]
  SizeField: TypeAlias = Union[SizeSampler, Field]


class RectSampler(IntSampler):
  """
  RectSampler subclasses BaseSampler from 'worktoy.work_test.samplers'
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_top_left__ = 0, 255, 0, 255
  __fallback_size__ = 32, 255, 32, 255

  #  Private Variables
  __top_left_args__: MaybeInts = None
  __size_args__: MaybeInts = None
  __top_left_sampler__: MaybePoint2DSampler = None
  __size_sampler__: MaybeSizeSampler = None

  #  Public Variables
  topLeft: Point2DField = Field()
  size: SizeField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createTopLeft(self, ) -> None:
    args = maybe(self.__top_left_args__, self.__fallback_top_left__)
    self.__top_left_sampler__ = Point2DSampler(*args)

  @topLeft.GET
  def _getTopLeft(self, **kwargs) -> Point2DSampler:
    if self.__top_left_sampler__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createTopLeft()
      return self._getTopLeft(_recursion=True)
    if isinstance(self.__top_left_sampler__, Point2DSampler):
      return self.__top_left_sampler__
    name, value = '__top_left_sampler__', self.__top_left_sampler__
    raise TypeException(name, value, Point2DSampler)

  def _createSize(self, ) -> None:
    args = maybe(self.__size_args__, self.__fallback_size__)
    self.__size_sampler__ = SizeSampler(*args)

  @size.GET
  def _getSize(self, **kwargs) -> SizeSampler:
    if self.__size_sampler__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createSize()
      return self._getSize(_recursion=True)
    if isinstance(self.__size_sampler__, SizeSampler):
      return self.__size_sampler__
    name, value = '__size_sampler__', self.__size_sampler__
    raise TypeException(name, value, SizeSampler)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getValueType(self, **kwargs) -> type:
    return Rect

  def _getItem(self, ) -> Rect:
    return Rect(self.topLeft.item, self.size.item)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int, int, int, int, int)
  @overload(int, int, int, int, int, int)
  def __init__(self, *args, ) -> None:
    self.__top_left_args__ = args[:4]
    self.__size_args__ = args[4:]

  @overload(int, int, int, int)
  def __init__(self, *args, ) -> None:
    self.__top_left_args__ = (*args[:2], *args[:2])
    self.__size_args__ = (*args[2:], *args[2:])

  @overload()
  def __init__(self, **kwargs) -> None:
    pass
