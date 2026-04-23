"""
Insets encapsulates four directional inset values describing distances
from the left, top, right, and bottom edges of a rectangular region.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMargins, QMarginsF, QRect, QRectF
from worktoy.core.sentinels import THIS
from worktoy.desc import Field, FixBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import stringList
from worktoy.waitaminute import TypeException, attributeErrorFactory
from worktoy.waitaminute.desc import ProtectedError

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Type, TypeAlias, Any, Union, Never, Self

  GotItem: TypeAlias = Union[int, Iterator[int]]


class Insets(BaseObject):
  """
  Insets encapsulates four directional inset values describing distances
  from the left, top, right, and bottom edges of a rectangular region.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __top_keys__ = stringList("""top, t""")
  __left_keys__ = stringList("""left, l""")
  __bottom_keys__ = stringList("""bottom, b""")
  __right_keys__ = stringList("""right, r""")
  __key_groups__ = (
    __top_keys__,
    __left_keys__,
    __bottom_keys__,
    __right_keys__,
  )

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  top = FixBox[int](0)
  left = FixBox[int](0)
  bottom = FixBox[int](0)
  right = FixBox[int](0)

  #  Virtual Variables
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQ(self) -> QMargins:
    return QMargins(*self, )

  @QF.GET
  def _getQF(self) -> QMarginsF:
    return QMargins.toMarginsF(self.Q)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self) -> Iterator[int]:
    yield self.left
    yield self.top
    yield self.right
    yield self.bottom

  def __len__(self) -> int:
    return 4

  def _rollIndex(self, index: int) -> int:
    if index < 0:
      return self._rollIndex(index + len(self))
    if index < len(self):
      return index
    infoSpec = """Index '%d' is out of bounds for '%s' objects having 
    length: %d."""
    clsName = type(self).__name__
    info = infoSpec % (index, clsName, len(self),)
    raise IndexError(info)

  def _parseKey(self, identifier: Any, **kwargs) -> str:
    if isinstance(identifier, int):
      return self.__key_groups__[self._rollIndex(identifier)][0]
    if not isinstance(identifier, str):
      raise TypeException('identifier', identifier, int, str)
    for group in self.__key_groups__:
      for key_ in group:
        if kwargs.get('case_sensitive', True):
          if identifier == key_:
            return group[0]
        else:
          if identifier.lower() == key_.lower():
            return group[0]
    if kwargs.get('case_sensitive', True) and isinstance(identifier, str):
      return self._parseKey(identifier, case_sensitive=False)
    raise KeyError(identifier)

  def _resolveIndex(self, index: int) -> int:
    rolled = self._rollIndex(index)
    return (*self,)[rolled]

  def _resolveKey(self, key: str) -> int:
    return getattr(self, self._parseKey(key))

  def _resolveSlice(self, slice_: slice) -> Iterator[int]:
    yield from (*self,)[slice_]

  def __getitem__(self, identifier: Any) -> GotItem:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    if isinstance(identifier, slice):
      return self._resolveSlice(identifier)
    raise TypeException('identifier', identifier, int, str, slice)

  def __setitem__(self, identifier: Any, value: int) -> None:
    if not isinstance(value, int):
      raise TypeException('value', value, int)
    if isinstance(identifier, (int, str)):
      key = self._parseKey(identifier)
      return setattr(self, key, value)
    if isinstance(identifier, slice):
      infoSpec = """Cannot set multiple values at once on '%s' objects."""
      clsName = type(self).__name__
      info = infoSpec % (clsName,)
      raise TypeError(info)
    raise TypeException('identifier', identifier, int, str)

  def __delitem__(self, identifier: Any) -> Never:
    try:
      key = self._parseKey(identifier)
    except (KeyError, IndexError) as exception:
      attributeError = attributeErrorFactory(self, identifier)
      raise attributeError from exception
    else:
      cls = type(self)
      desc = getattr(cls, key)
      oldValue = getattr(self, key)
      raise ProtectedError(self, desc, oldValue)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int)
  def __init__(self, *args, **kwargs) -> None:
    self.left, self.top, self.right, self.bottom = args
    if kwargs:
      self.__init__(**kwargs)

  @overload(int, int)
  def __init__(self, vertical: int, horizontal: int, **kwargs) -> None:
    self.__init__(horizontal, vertical, horizontal, vertical)
    if kwargs:
      self.__init__(**kwargs)

  @overload(int)
  def __init__(self, allSides: int, **kwargs) -> None:
    self.__init__(allSides, allSides, allSides, allSides)
    if kwargs:
      self.__init__(**kwargs)

  @overload(THIS)
  def __init__(self, other: Self, **kwargs) -> None:
    self.__init__(*other, **kwargs)

  @overload(QMargins)
  def __init__(self, qMargins: QMargins, **kwargs) -> None:
    self.__init__(
      qMargins.left(),
      qMargins.top(),
      qMargins.right(),
      qMargins.bottom(),
      **kwargs,
    )

  @overload(QMarginsF)
  def __init__(self, qMarginsF: QMarginsF, **kwargs) -> None:
    self.__init__(QMarginsF.toMargins(qMarginsF), **kwargs)

  @overload(QRect, QRect)
  def __init__(self, outer: QRect, inner: QRect, **kwargs) -> None:
    self.__init__(
      inner.left() - outer.left(),
      inner.top() - outer.top(),
      outer.right() - inner.right(),
      outer.bottom() - inner.bottom(),
      **kwargs,
    )

  @overload(QRectF, QRectF)
  def __init__(self, outer: QRectF, inner: QRectF, **kwargs) -> None:
    self.__init__(QRectF.toRect(outer, ), QRectF.toRect(inner, ), **kwargs)

  @overload(QRectF, QRect)
  @overload(QRect, QRectF)
  def __init__(self, *args, **kwargs) -> None:
    outer, inner = args
    if isinstance(outer, QRectF):
      outer = QRectF.toRect(outer, )
    if isinstance(inner, QRectF):
      inner = QRectF.toRect(inner, )
    self.__init__(outer, inner, **kwargs)

  @overload()
  def __init__(self, **kwargs) -> None:
    for group in self.__key_groups__:
      for key in group:
        if key in kwargs:
          value = kwargs[key]
          if not isinstance(value, int):
            raise TypeException(key, value, int)
          setattr(self, group[0], value)
          break

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
