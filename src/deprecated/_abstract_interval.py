"""AbstractInterval provides a base class for non-localized geometric
values such as sizes and vectors. Subclasses must provide the following
properties:
  - lower: float -> The lower edge of the object.
  - upper: float -> The upper edge of the object.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from abc import abstractmethod

from worktoy.attr import Field
from worktoy.mcls import BaseObject
from worktoy.text import monoSpace
from worktoy.waitaminute import ReadOnlyError, DispatchException

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Self, Never, Any, Optional, TypeAlias, Union

  _NotImplementedType = type(NotImplemented)
  _Other: TypeAlias = Union[tuple[float, float], _NotImplementedType]


class AbstractInterval(BaseObject):
  """AbstractInterval provides a base class for non-localized geometric
  values such as sizes and vectors. Subclasses must provide the following
  properties:
    - lower: float -> The lower edge of the object.
    - upper: float -> The upper edge of the object.
  """

  #  Functional variables
  __iter_contents__ = None

  lower = Field()
  upper = Field()

  @abstractmethod
  @lower.GET
  def _getLower(self) -> float:
    """Get the lower edge of the object."""
    raise NotImplementedError

  @abstractmethod
  @upper.GET
  def _getUpper(self) -> float:
    """Get the upper edge of the object."""
    raise NotImplementedError

  def __iter__(self, ) -> Self:
    """Implementation of the iterator protocol."""
    self.__iter_contents__ = [self._getLower(), self._getUpper()]
    return self

  def __next__(self, ) -> float:
    """Implementation of the iterator protocol."""
    if self.__iter_contents__:
      return self.__iter_contents__.pop(0)
    self.__iter_contents__ = None
    raise StopIteration

  @classmethod
  def _resolveIndex(cls, index: int) -> str:
    """Resolve the index to a value."""
    if index < 0:
      return cls._resolveIndex(index + 2)
    if index > 1:
      raise IndexError('Index out of range')
    return 'upper' if index else 'lower'

  @staticmethod
  def _resolveKey(key: str) -> str:
    """Resolve the key to a value."""
    if 'lower' in key.lower():
      return 'lower'
    if 'upper' in key.lower():
      return 'upper'
    infoSpec = """Received invalid key: '%s'! Expected one of: lower, 
    upper."""
    raise KeyError(monoSpace(infoSpec % key))

  @classmethod
  def _resolveIdentifier(cls, identifier: object) -> str:
    """Resolve the identifier to a value."""
    if isinstance(identifier, int):
      return cls._resolveIndex(identifier)
    if isinstance(identifier, str):
      return cls._resolveKey(identifier)
    infoSpec = """Unable to resolve member from identifier: '%s'!"""
    raise TypeError(monoSpace(infoSpec % identifier))

  def __getitem__(self, *identifiers) -> float:
    """Implementation of the getitem protocol."""
    for identifier in identifiers:
      try:
        identifier = self._resolveIdentifier(identifier)
        break
      except TypeError as typeError:
        if 'resolve' in str(typeError):
          continue
        raise typeError
    else:
      infoSpec = """Unable to resolve member from identifier: '%s'!"""
      raise TypeError(monoSpace(infoSpec % identifiers))
    if identifier == 'lower':
      return self._getLower()
    if identifier == 'upper':
      return self._getUpper()
    infoSpec = """Unable to resolve member from identifier: '%s'!"""
    raise TypeError(monoSpace(infoSpec % identifier))

  def __setitem__(self, identifier: object, value: object) -> Never:
    """Instances are immutable"""
    cls = type(self)
    identifier = cls._resolveIdentifier(identifier)
    desc = getattr(cls, identifier)
    raise ReadOnlyError(self, desc, value)

  @classmethod
  def _resolveOther(cls, other: Any) -> _Other:  # tuple[float, float]:
    """Resolve the other object to an interval."""
    if isinstance(other, cls):
      return other._getLower(), other._getUpper()
    if isinstance(other, (float, int)):
      return other, other
    try:
      other = cls(other.real, other.imag)
      return other._getLower(), other._getUpper()
    except DispatchException:
      return NotImplemented

  def __contains__(self, other: Any) -> bool:
    """Implementation of the contains protocol."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if TYPE_CHECKING:
      assert isinstance(self.lower, float)
      assert isinstance(self.upper, float)
    if other.lower < self.lower or other.upper > self.upper:
      return False
    return True

  def __eq__(self, other: Any) -> bool:
    """Implementation of the equality protocol."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return False
    if TYPE_CHECKING:
      assert isinstance(self.lower, float)
      assert isinstance(self.upper, float)
    if self.lower - other.lower:
      return False
    if self.upper - other.upper:
      return False
    return True
