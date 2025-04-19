"""Plane provides a baseclass for two component classes. These include:
- Point -> Denoting a position in the plane
- Size -> Denoting a size in the plane
- Vector -> Denoting a vector in the plane
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import AttriBox
from worktoy.mcls import BaseObject
from worktoy.static import overload, THIS
from worktoy.text import monoSpace, typeMsg
from worktoy.waitaminute import DispatchException

from . import AbstractGeometry

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Self, Any


class Plane(BaseObject):
  """Plane provides a baseclass for two component classes. These include:
  - Point -> Denoting a position in the plane
  - Size -> Denoting a size in the plane
  - Vector -> Denoting a vector in the plane
  """

  __iter_contents__ = None

  __r0_keys__ = ['x', 'r0']
  __r1_keys__ = ['y', 'r1']

  r0 = AttriBox[float](0.0)
  r1 = AttriBox[float](0.0)

  @classmethod
  def _getR0Keys(cls) -> list[str]:
    """Return the r0 keys."""
    return cls.__r0_keys__

  @classmethod
  def _getR1Keys(cls) -> list[str]:
    """Return the r1 keys."""
    return cls.__r1_keys__

  #  num, num

  @overload(int, int)
  @overload(float, float)
  @overload(float, int)
  @overload(int, float)
  def __init__(self, *args, **kwargs) -> None:
    try:
      self.r0, self.r1 = [float(arg) for arg in args]
    except Exception as exception:
      raise DispatchException from exception
    else:
      if kwargs.get('verbose', False):
        infoSpec = """Instantiating '%s' object: '%s'"""
        clsName = type(self).__name__
        selfStr = str(self)
        print(infoSpec % (clsName, selfStr))
    finally:
      if kwargs.get('verbose', False):
        exception = locals().get('exception', None)
        if exception is not None:
          infoSpec = """Encountered: %s during instantiation of %s"""
          clsName = type(self).__name__
          eStr = str(exception)
          print(infoSpec % (clsName, eStr))

  @overload(complex)
  def __init__(self, z: complex, **kwargs) -> None:
    self.r0, self.r1 = [float(z.real), float(z.imag)]

  @overload(THIS)
  def __init__(self, other: Self, **kwargs) -> None:
    self.r0, self.r1 = [float(other.r0), float(other.r1)]

  @overload(THIS, THIS)
  def __init__(self, p: Self, q: Self, **kwargs) -> None:
    d0 = q.r0 - p.r0
    d1 = q.r1 - p.r1
    self.r0, self.r1 = [float(d0), float(d1)]

  @overload(tuple)
  @overload(list)
  def __init__(self, vals: Any, **kwargs) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(*vals)

  @overload()
  def __init__(self, ) -> None:
    pass

  def __abs__(self, ) -> float:
    """Return the length of the vector."""
    return (self.r0 ** 2 + self.r1 ** 2) ** 0.5

  def __len__(self, ) -> int:
    """Returns 2"""
    return 2

  def __bool__(self, ) -> bool:
    """Return True if the vector is not zero."""
    return True if self.r0 ** 2 + self.r1 ** 2 else False

  def __str__(self, ) -> str:
    """Return the string representation of the vector."""
    infoSpec = """%s[%s: float, %s: float]"""
    rStr0 = '%d' % int(self.r0) if self.r0.is_integer() else '%.3f' % self.r0
    rStr1 = '%d' % int(self.r1) if self.r1.is_integer() else '%.3f' % self.r1
    name = type(self).__name__
    return monoSpace(infoSpec % (name, rStr0, rStr1))

  def __repr__(self, ) -> str:
    """Return the string representation of the vector."""
    infoSpec = """%s(%s, %s)"""
    rStr0 = '%d' % int(self.r0) if self.r0.is_integer() else '%.3f' % self.r0
    rStr1 = '%d' % int(self.r1) if self.r1.is_integer() else '%.3f' % self.r1
    name = type(self).__name__
    return monoSpace(infoSpec % (name, rStr0, rStr1))

  def __iter__(self, ) -> Self:
    """Return an iterator for the vector."""
    self.__iter_contents__ = [self.r0, self.r1]
    return self

  def __next__(self) -> Any:
    """Return the next item in the iterator."""
    if self.__iter_contents__:
      return self.__iter_contents__.pop(0)
    self.__iter_contents__ = None
    raise StopIteration

  def _parseIndex(self, index: int) -> str:
    """Return the indexed item in the vector."""
    if index < 0:
      return self._parseIndex(len(self) + index)
    if index >= len(self):
      raise IndexError('Index out of range')
    return 'r1' if index else 'r0'

  def _parseKey(self, key: str) -> str:
    """Return the keyed item in the vector."""
    if key.lower() in self._getR0Keys():
      return 'r0'
    if key.lower() in self._getR1Keys():
      return 'r1'
    raise KeyError("""Key: '%s' not found!""" % key)

  def __getitem__(self, item: Any) -> float:
    """Return the indexed item in the vector."""
    key = None
    if isinstance(item, int):
      key = self._parseIndex(item)
    elif isinstance(item, str):
      key = self._parseKey(item)
    else:
      raise TypeError(typeMsg('item', item, int))
    return getattr(self, key)

  def _resolveOther(self, other: Any) -> Self:
    """Resolve the other object to a vector."""
    cls = type(self)
    if isinstance(other, cls):
      return other
    if isinstance(other, (tuple, list)):
      try:
        return cls(other[0], other[1])
      except IndexError:
        return NotImplemented
    if isinstance(other, (float, int)):
      return cls(other, other)
    if isinstance(other, complex):
      return cls(other.real, other.imag)
    try:
      out = cls(other)
    except DispatchException:
      return NotImplemented
    else:
      return out
    finally:
      pass

  def __neg__(self, ) -> Self:
    """Return the negation of the vector."""
    cls = type(self)
    return cls(-self.r0, -self.r1)

  def __add__(self, other: Self) -> Self:
    """Return the sum of the vector and another vector."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    cls = type(self)
    return cls(self.r0 + other.r0, self.r1 + other.r1)

  def __iadd__(self, other: Self) -> Self:
    """Return the sum of the vector and another vector."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    self.r0 += other.r0
    self.r1 += other.r1
    return self

  def __radd__(self, other: Self) -> Self:
    """Return the sum of the vector and another vector."""
    return self + other

  def __sub__(self, other: Self) -> Self:
    """Return the difference of the vector and another vector."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    cls = type(self)
    return self + (-other)

  def __isub__(self, other: Self) -> Self:
    """Return the difference of the vector and another vector."""
    other = self._resolveOther(other)
    self.r0 -= other.r0
    self.r1 -= other.r1
    return self

  def __rsub__(self, other: Self) -> Self:
    """Return the difference of the vector and another vector."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    cls = type(self)
    return cls(other.r0 - self.r0, other.r1 - self.r1)

  def __mul__(self, other: Self) -> Self:
    """Return the product of the vector and another vector."""
    if isinstance(other, (int, float)):
      cls = type(self)
      return cls(self.r0 * other, self.r1 * other)
    return NotImplemented

  def __imul__(self, other: Self) -> Self:
    """Return the product of the vector and another vector."""
    if isinstance(other, (int, float)):
      self.r0 *= other
      self.r1 *= other
      return self
    return NotImplemented

  def __rmul__(self, other: Self) -> Self:
    """Return the product of the vector and another vector."""
    if isinstance(other, (int, float)):
      cls = type(self)
      return cls(self.r0 * other, self.r1 * other)
    return NotImplemented

  def __truediv__(self, other: Self) -> Self:
    """Return the division of the vector and another vector."""
    if isinstance(other, (int, float)):
      if not other:
        raise ZeroDivisionError
      cls = type(self)
      return cls(self.r0 / other, self.r1 / other)
    return NotImplemented

  def __itruediv__(self, other: Self) -> Self:
    """Return the division of the vector and another vector."""
    if isinstance(other, (int, float)):
      if not other:
        raise ZeroDivisionError
      self.r0 /= other
      self.r1 /= other
      return self
    return NotImplemented

  def __rtruediv__(self, other: Self) -> Self:
    """Return the division of the vector and another vector."""
    if isinstance(other, (int, float)):
      if not other:
        raise ZeroDivisionError
      cls = type(self)
      return cls(other / self.r0, other / self.r1)
    return NotImplemented

  def __mod__(self, other: Self) -> Self:
    """Return the modulus of the vector and another vector."""
    if isinstance(other, (int, float)):
      cls = type(self)
      return cls(self.r0 % other, self.r1 % other)
    return NotImplemented

  def __imod__(self, other: Self) -> Self:
    """Return the modulus of the vector and another vector."""
    if isinstance(other, (int, float)):
      self.r0 %= other
      self.r1 %= other
      return self
    return NotImplemented

  def __rmod__(self, other: Self) -> Self:
    """Return the modulus of the vector and another vector."""
    if isinstance(other, (int, float)):
      cls = type(self)
      return cls(other % self.r0, other % self.r1)
    return NotImplemented

  def __pow__(self, other: Self) -> Self:
    return NotImplemented

  def __ipow__(self, other: Self) -> Self:
    return NotImplemented

  def __rpow__(self, other: Self) -> Self:
    return NotImplemented

  def __matmul__(self, other: Self) -> Self:
    return NotImplemented

  def __imatmul__(self, other: Self) -> Self:
    return NotImplemented

  def __rmatmul__(self, other: Self) -> Self:
    return NotImplemented

  def __complex__(self, ) -> complex:
    """Return the complex representation of the vector."""
    return self.r0 + self.r1 * 1j

  def __xor__(self, other: Self) -> Self:
    """Return the bitwise XOR of the vector and another vector."""
    return NotImplemented
