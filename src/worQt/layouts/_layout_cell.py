"""
LayoutCell provides a dataclass for cells in a layout manager. It has
attributes 'row' and 'column' specifying position.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import WriteOnceError

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Self, Type, Iterator

  MaybeInt: TypeAlias = Optional[int]
  IntField: TypeAlias = Union[int, Field]
  NotImplementedType: TypeAlias = Type[NotImplemented]
  MaybeSelf: TypeAlias = Union[Self, NotImplementedType]
  IntIter: TypeAlias = Iterator[int]
  StrTuple: TypeAlias = tuple[str, ...]
  KeyGroups: TypeAlias = dict[str, StrTuple]
  KeyTypes: TypeAlias = dict[str, type]
  KeyDefaults: TypeAlias = dict[str, int]


class LayoutCell(BaseObject):
  """
  LayoutCell provides a dataclass for cells in a layout manager. It has
  attributes 'row' and 'column' specifying position.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __row_keys__: StrTuple = 'row', 'r', 'y', 'vertical', 'v',
  __col_keys__: StrTuple = 'col', 'c', 'x', 'horizontal', 'h',
  __key_groups__: KeyGroups = dict(row=__row_keys__, col=__col_keys__, )
  __key_types__: KeyTypes = dict(row=int, col=int, )

  #  Fallback Variables
  __fallback_row__: int = 0
  __fallback_col__: int = 0
  __key_fallbacks__: KeyDefaults = dict(
    row=__fallback_row__,
    col=__fallback_col__,
    )

  #  Private Variables
  __row_value__: MaybeInt = None
  __col_value__: MaybeInt = None

  #  Public Variables
  row: IntField = Field()
  col: IntField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @row.GET
  def _getRow(self, **kwargs) -> int:
    if self.__row_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.row = self.__fallback_row__
    return self.__row_value__

  @col.GET
  def _getCol(self, **kwargs) -> int:
    if self.__col_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.col = self.__fallback_col__
    return self.__col_value__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @row.SET
  def _setRow(self, value: int, **kwargs) -> None:
    if self.__row_value__ is not None:
      raise WriteOnceError(self, self.__row_value__, value)
    if not isinstance(value, int):
      raise TypeException('value', value, int)
    self.__row_value__ = value

  @col.SET
  def _setCol(self, value: int, **kwargs) -> None:
    if self.__col_value__ is not None:
      raise WriteOnceError(self, self.__col_value__, value)
    if not isinstance(value, int):
      raise TypeException('value', value, int)
    self.__col_value__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> IntIter:
    yield self.row
    yield self.col

  def __len__(self, ) -> int:
    return 2

  def _resolveIndex(self, identifier: int) -> int:
    if isinstance(identifier, int):
      return self.col if identifier % 2 else self.row
    raise TypeException('identifier', identifier, int)

  def _resolveKey(self, identifier: str) -> int:
    if not isinstance(identifier, str):
      raise TypeException('identifier', identifier, str)
    if identifier in self.__row_keys__:
      return self.row
    if identifier in self.__col_keys__:
      return self.col
    if str.lower(identifier) in self.__row_keys__:
      return self.row
    if str.lower(identifier) in self.__col_keys__:
      return self.col
    raise KeyError(identifier)

  def __getitem__(self, identifier: Any) -> int:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    raise TypeException('identifier', identifier, int, str)

  def __str__(self, ) -> str:
    infoSpec = """<%s: row=%d, col=%d>"""
    clsName = type(self).__name__
    return infoSpec % (clsName, self.row, self.col)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d, %d)"""
    clsName = type(self).__name__
    return infoSpec % (clsName, self.row, self.col)

  @classmethod
  def _resolveOther(cls, other: Any) -> MaybeSelf:
    if isinstance(other, cls):
      return other
    try:
      resolved = cls(other)
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return resolved

  def __eq__(self, other: Any) -> bool:
    resolved = self._resolveOther(other)
    if resolved is NotImplemented:
      return NotImplemented
    if self.row != resolved.row:
      return False
    if self.col != resolved.col:
      return False
    return True

  def __hash__(self, ) -> int:
    return hash((self.row, self.col,))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, row: int, col: int, **kwargs) -> None:
    self.row = row
    self.col = col
    if kwargs:
      self.__init__(**kwargs)

  @overload()
  def __init__(self, **kwargs) -> None:
    cls = type(self)
    for name, defVal in self.__key_fallbacks__.items():
      keys = self.__key_groups__[name]
      type_ = self.__key_types__[name]
      desc = getattr(cls, name)
      getKey = getattr(desc, '__get_key__')
      getter = getattr(desc, getKey)
      try:
        oldValue = getter(self, _recursion=True)
      except RecursionError:
        oldValue = None
      for key in keys:
        if key in kwargs:
          value = kwargs[key]
          if oldValue is not None:
            raise WriteOnceError(desc, oldValue, value)
          if not isinstance(value, type_):
            raise TypeException(key, value, type_)
          setattr(self, name, value)
          break
      else:
        if oldValue is None:
          setattr(self, name, defVal)
