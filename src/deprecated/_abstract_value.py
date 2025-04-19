"""AbstractValue provides a base class for non-localized geometric values
such as length. Subclasses implement the 'getValue' method to return the
value of the object. """
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


class AbstractValue(BaseObject):
  """AbstractValue provides a base class for non-localized geometric values
  such as length. Subclasses implement the 'getValue' method to return the
  value of the object. """
  value = Field()

  @abstractmethod
  @value.GET
  def _getValue(self) -> float:
    """Get the value of the object."""
    raise NotImplementedError

  def __float__(self, ) -> float:
    """Convert the object to a float."""
    value = self._getValue()
    if isinstance(value, float):
      return value
    return float(value)

  def __int__(self, ) -> int:
    """Convert the object to an int."""
    value = self._getValue()
    if isinstance(value, int):
      return value
    return int(value)

  def __str__(self, ) -> str:
    """Convert the object to a string."""
    clsName = type(self).__name__
    value = self._getValue()
    if value.is_integer():
      return '%d' % int(value)
    return str(value)
