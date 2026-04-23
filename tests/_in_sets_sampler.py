"""
InSetsSampler subclasses 'BaseSampler' from 'worktoy.work_test.samplers'
and provides a sampler class for 'InSets' objects from 'worQt.utils.geom'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException
from worktoy.work_test.samplers import BaseSampler, IntSampler
from worQt.utils.geom import InSets

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias, Type

  MaybeInt: TypeAlias = Optional[int]
  IntField: TypeAlias = Union[int, Field]
  MaybeIntSampler: TypeAlias = Optional[IntSampler]
  IntSamplerField: TypeAlias = Union[IntSampler, Field]


class InSetsSampler(BaseSampler):
  """
  InSetsSampler subclasses 'BaseSampler' from 'worktoy.work_test.samplers'
  and provides a sampler class for 'InSets' objects from 'worQt.utils.geom'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_min_left__: int = 0
  __fallback_max_left__: int = 15
  __fallback_min_top__: int = 0
  __fallback_max_top__: int = 15
  __fallback_min_right__: int = 0
  __fallback_max_right__: int = 15
  __fallback_min_bottom__: int = 0
  __fallback_max_bottom__: int = 15

  #  Private Variables
  # ---#  Limit Values
  __min_left__: MaybeInt = None
  __max_left__: MaybeInt = None
  __min_top__: MaybeInt = None
  __max_top__: MaybeInt = None
  __min_right__: MaybeInt = None
  __max_right__: MaybeInt = None
  __min_bottom__: MaybeInt = None
  __max_bottom__: MaybeInt = None
  # ---#  Samplers
  __left_sampler__: MaybeIntSampler = None
  __top_sampler__: MaybeIntSampler = None
  __right_sampler__: MaybeIntSampler = None
  __bottom_sampler__: MaybeIntSampler = None

  #  Public Variables
  # ---#  Limit Values
  minLeft: IntField = Field()
  maxLeft: IntField = Field()
  minTop: IntField = Field()
  maxTop: IntField = Field()
  minRight: IntField = Field()
  maxRight: IntField = Field()
  minBottom: IntField = Field()
  maxBottom: IntField = Field()
  # ---#  Samplers
  left: IntSamplerField = Field()
  top: IntSamplerField = Field()
  right: IntSamplerField = Field()
  bottom: IntSamplerField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @minLeft.GET
  def _getMinLeft(self, **kwargs) -> int:
    if self.__min_left__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__min_left__ = self.__fallback_min_left__
      return self._getMinLeft(_recursion=True)
    return self.__min_left__

  @maxLeft.GET
  def _getMaxLeft(self, **kwargs) -> int:
    if self.__max_left__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__max_left__ = self.__fallback_max_left__
      return self._getMaxLeft(_recursion=True)
    return self.__max_left__

  @minTop.GET
  def _getMinTop(self, **kwargs) -> int:
    if self.__min_top__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__min_top__ = self.__fallback_min_top__
      return self._getMinTop(_recursion=True)
    return self.__min_top__

  @maxTop.GET
  def _getMaxTop(self, **kwargs) -> int:
    if self.__max_top__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__max_top__ = self.__fallback_max_top__
      return self._getMaxTop(_recursion=True)
    return self.__max_top__

  @minRight.GET
  def _getMinRight(self, **kwargs) -> int:
    if self.__min_right__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__min_right__ = self.__fallback_min_right__
      return self._getMinRight(_recursion=True)
    return self.__min_right__

  @maxRight.GET
  def _getMaxRight(self, **kwargs) -> int:
    if self.__max_right__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__max_right__ = self.__fallback_max_right__
      return self._getMaxRight(_recursion=True)
    return self.__max_right__

  @minBottom.GET
  def _getMinBottom(self, **kwargs) -> int:
    if self.__min_bottom__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__min_bottom__ = self.__fallback_min_bottom__
      return self._getMinBottom(_recursion=True)
    return self.__min_bottom__

  @maxBottom.GET
  def _getMaxBottom(self, **kwargs) -> int:
    if self.__max_bottom__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self.__max_bottom__ = self.__fallback_max_bottom__
      return self._getMaxBottom(_recursion=True)
    return self.__max_bottom__

  def _createLeftSampler(self, ) -> None:
    self.__left_sampler__ = IntSampler(self.minLeft, self.maxLeft)

  @left.GET
  def _getLeftSampler(self, **kwargs) -> IntSampler:
    if self.__left_sampler__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self._createLeftSampler()
      return self._getLeftSampler(_recursion=True)
    if isinstance(self.__left_sampler__, IntSampler):
      return self.__left_sampler__
    name, value = '__left_sampler__', self.__left_sampler__
    raise TypeException(name, value, IntSampler)

  def _createTopSampler(self, ) -> None:
    self.__top_sampler__ = IntSampler(self.minTop, self.maxTop)

  @top.GET
  def _getTopSampler(self, **kwargs) -> IntSampler:
    if self.__top_sampler__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self._createTopSampler()
      return self._getTopSampler(_recursion=True)
    if isinstance(self.__top_sampler__, IntSampler):
      return self.__top_sampler__
    name, value = '__top_sampler__', self.__top_sampler__
    raise TypeException(name, value, IntSampler)

  def _createRightSampler(self, ) -> None:
    self.__right_sampler__ = IntSampler(self.minRight, self.maxRight)

  @right.GET
  def _getRightSampler(self, **kwargs) -> IntSampler:
    if self.__right_sampler__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self._createRightSampler()
      return self._getRightSampler(_recursion=True)
    if isinstance(self.__right_sampler__, IntSampler):
      return self.__right_sampler__
    name, value = '__right_sampler__', self.__right_sampler__
    raise TypeException(name, value, IntSampler)

  def _createBottomSampler(self, ) -> None:
    self.__bottom_sampler__ = IntSampler(self.minBottom, self.maxBottom)

  @bottom.GET
  def _getBottomSampler(self, **kwargs) -> IntSampler:
    if self.__bottom_sampler__ is None:
      if kwargs.get('_recursion', False): raise RecursionError
      self._createBottomSampler()
      return self._getBottomSampler(_recursion=True)
    if isinstance(self.__bottom_sampler__, IntSampler):
      return self.__bottom_sampler__
    name, value = '__bottom_sampler__', self.__bottom_sampler__
    raise TypeException(name, value, IntSampler)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @minLeft.SET
  def _setMinLeft(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('minLeft', value, int)
    self.__min_left__ = value

  @maxLeft.SET
  def _setMaxLeft(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('maxLeft', value, int)
    self.__max_left__ = value

  @minTop.SET
  def _setMinTop(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('minTop', value, int)
    self.__min_top__ = value

  @maxTop.SET
  def _setMaxTop(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('maxTop', value, int)
    self.__max_top__ = value

  @minRight.SET
  def _setMinRight(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('minRight', value, int)
    self.__min_right__ = value

  @maxRight.SET
  def _setMaxRight(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('maxRight', value, int)
    self.__max_right__ = value

  @minBottom.SET
  def _setMinBottom(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('minBottom', value, int)
    self.__min_bottom__ = value

  @maxBottom.SET
  def _setMaxBottom(self, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('maxBottom', value, int)
    self.__max_bottom__ = value

  @left.SET
  def _setLeftSampler(self, value: IntSampler) -> None:
    if not isinstance(value, IntSampler):
      raise TypeException('leftSampler', value, IntSampler)
    self.__left_sampler__ = value

  @top.SET
  def _setTopSampler(self, value: IntSampler) -> None:
    if not isinstance(value, IntSampler):
      raise TypeException('topSampler', value, IntSampler)
    self.__top_sampler__ = value

  @right.SET
  def _setRightSampler(self, value: IntSampler) -> None:
    if not isinstance(value, IntSampler):
      raise TypeException('rightSampler', value, IntSampler)
    self.__right_sampler__ = value

  @bottom.SET
  def _setBottomSampler(self, value: IntSampler) -> None:
    if not isinstance(value, IntSampler):
      raise TypeException('bottomSampler', value, IntSampler)
    self.__bottom_sampler__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getValueType(self, **kwargs) -> type:
    return InSets

  def _getItem(self, ) -> InSets:
    return InSets(
      self.left.item,
      self.top.item,
      self.right.item,
      self.bottom.item,
      )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int, int, int, int, int)
  def __init__(self, *args, ) -> None:
    self.__min_left__ = args[0]
    self.__max_left__ = args[1]
    self.__min_top__ = args[2]
    self.__max_top__ = args[3]
    self.__min_right__ = args[4]
    self.__max_right__ = args[5]
    self.__min_bottom__ = args[6]
    self.__max_bottom__ = args[7]

  @overload(int, int, int, int)
  def __init__(self, *args, ) -> None:
    self.__min_left__ = 0
    self.__max_left__ = args[0]
    self.__min_top__ = 0
    self.__max_top__ = args[1]
    self.__min_right__ = 0
    self.__max_right__ = args[2]
    self.__min_bottom__ = 0
    self.__max_bottom__ = args[3]

  @overload(int, int)
  def __init__(self, *args, ) -> None:
    self.__min_left__, self.__max_left__ = args
    self.__min_top__, self.__max_top__ = args
    self.__min_right__, self.__max_right__ = args
    self.__min_bottom__, self.__max_bottom__ = args
