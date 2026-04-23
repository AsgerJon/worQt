"""
LayoutEntry encapsulates a layout entry in a grid layout. Each entry maps
a 'LayoutIndex' to a 'LayoutItem' and is owned by a 'LayoutManager'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from worQt.layouts import LayoutIndex, LayoutItem
from worQt.mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, Self


class LayoutEntry(MixinBase):
  """
  LayoutEntry encapsulates a layout entry in a grid layout. Each entry maps
  a 'LayoutIndex' to a 'LayoutItem' and is owned by a 'LayoutManager'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __index_keys__ = ('index', 'idx', 'layout_index', 'layoutIdx',)
  __item_keys__ = ('item', 'layout_item', 'layoutItem',)

  #  Fallback Variables

  #  Private Variables
  __layout_index__ = None
  __layout_item__ = None

  #  Public Variables
  index = Field()
  item = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @index.GET
  def _getIndex(self, ) -> LayoutIndex:
    if self.__layout_index__ is None:
      raise MissingVariable(self, '__layout_index__', LayoutIndex)
    if isinstance(self.__layout_index__, LayoutIndex):
      return self.__layout_index__
    name, value = '__layout_index__', self.__layout_index__
    raise TypeException(name, value, LayoutIndex)

  @item.GET
  def _getItem(self, ) -> LayoutItem:
    if self.__layout_item__ is None:
      raise MissingVariable(self, '__layout_item__', LayoutItem)
    if isinstance(self.__layout_item__, LayoutItem):
      return self.__layout_item__
    name, value = '__layout_item__', self.__layout_item__
    raise TypeException(name, value, LayoutItem)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator:
    yield self.index
    yield self.item

  def __len__(self, ) -> int:  # 2
    return 2

  def _resolveIndex(self, index_: int) -> Any:
    return self.item if self._rollIndex(index_) % 2 else self.index

  def _resolveKey(self, key: str) -> Any:
    key = key.lower()
    if key in self.__index_keys__:
      return self.index
    if key in self.__item_keys__:
      return self.item
    raise KeyError(key)

  def __getitem__(self, identifier: Any) -> Any:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    raise TypeException('identifier', identifier, int, str, )

  def __contains__(self, other: Any) -> bool:
    if isinstance(other, LayoutIndex):
      return True if other == self.index else False
    if isinstance(other, LayoutItem):
      return True if other == self.item else False
    return False

  def __eq__(self, other: Self) -> bool:
    cls = type(self)
    if not isinstance(other, cls):
      return NotImplemented
    if self.index != other.index:
      return False
    if self.item != other.item:
      return False
    return True

  def __ne__(self, other: Self) -> bool:
    if self.__eq__(other) is NotImplemented:
      return NotImplemented
    return False if self == other else True

  def __bool__(self, ) -> bool:
    return True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(LayoutIndex, LayoutItem)
  def __init__(self, index: LayoutIndex, item: LayoutItem, ) -> None:
    self.__layout_index__ = index
    self.__layout_item__ = item

  @overload(LayoutItem, LayoutIndex)
  def __init__(self, item: LayoutItem, index: LayoutIndex, ) -> None:
    self.__layout_index__ = index
    self.__layout_item__ = item
    
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
