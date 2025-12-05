"""
Object provides the base for 'worktoy'. The expansion here adds the
'_resolveOther' method which tries to cast another object as an instance
of the same class as self. This has both general use and general
implementation making it suitable for inclusion in the base Object class.

Example:

  class ComplexNumber(Object):

    __slots__ = ('realPart', 'imagPart')

    #  Constructors omitted for brevity.

    def __add__(self, other: Any) -> Self:
      other = self._resolveOther(other)
      if other is NotImplemented:
        return NotImplemented
      x = self.realPart + other.realPart
      y = self.imagPart + other.imagPart
      return type(self)(x, y)

    def __neg__(self) -> Self:
      return type(self)(-self.realPart, -self.imagPart)

    def __sub__(self, other: Any) -> Self:
      other = self._resolveOther(other)
      if other is NotImplemented:
        return NotImplemented
      return self + (-other)  # 'other' is an instance of ComplexNumber now.

    ...

    #  Remaining methods left as an exercise for the try-hard reader.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core import Object as __worktoy_object__

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self


class Object(__worktoy_object__):
  """
  Expansion with '_resolveOther' method.
  """

  def _resolveOther(self, other: Any) -> Self:
    """
    If 'other' is an instance of the exact same class as 'self',
    it is just returned. If not, the method attempts to cast 'other' to
    the type of self. If the constructor raises TypeError or ValueError,
    the method returns 'NotImplemented', otherwise the method returns the
    cast object.

    Please note that this method assumes that the subclass of Object
    raises either TypeError or ValueError if unable to instantiate from
    'other' and that the resulting object reasonably collects values from
    'other' as appropriate.

    The 'Object' base itself makes no use of '_resolveOther'. Subclasses
    making uses of it are responsible for adhering to the assumptions
    described above.

    If the subclass is also a subclass of 'BaseObject', the function
    overload system it provides will raise 'DispatchException' if unable
    to parse arguments received. This custom exception subclasses
    'TypeError' allowing '_resolveOther' to catch it.
    """
    cls = type(self)
    if type(other) is cls:  # Only if the types are exactly the same.
      return other
    try:
      castObject = cls(other)
    except (TypeError, ValueError):
      return NotImplemented
    return castObject
