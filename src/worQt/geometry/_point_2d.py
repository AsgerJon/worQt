"""Point encapsulates plane points. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF
from worktoy.desc import AttriBox, Field
from worktoy.mcls import BaseObject
from worktoy.dispatch import overload
from worktoy.core.sentinels import THIS

from typing import TYPE_CHECKING, Iterator

from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException, VariableNotNone

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Iterator


class Point2D(BaseObject):
  """Point encapsulates plane points. """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_x__ = 0.0
  __fallback_y__ = 0.0

  #  Private Variables
  __private_x__ = None
  __private_y__ = None

  #  Public Variables
  x = Field()
  y = Field()

  #  Virtual Variables
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @x.GET
  def _getX(self, **kwargs) -> float:
    """Get the x coordinate of the Point."""
    if self.__private_x__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__private_x__ = self.__fallback_x__
      return self._getX(_recursion=True)
    return self.__private_x__

  @y.GET
  def _getY(self, **kwargs) -> float:
    """Get the y coordinate of the Point."""
    if self.__private_y__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__private_y__ = self.__fallback_y__
      return self._getY(_recursion=True)
    return self.__private_y__

  @Q.GET
  def _getQ(self) -> QPoint:
    """Get the QPoint representation of the Point."""
    return QPoint(int(self.x), int(self.y))

  @QF.GET
  def _getQF(self) -> QPointF:
    """Get the QPointF representation of the Point."""
    return QPointF(self.x, self.y)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @x.SET
  def _setX(self, value: float) -> None:
    """Set the x coordinate of the Point."""
    if self.__private_x__ is not None:
      raise VariableNotNone('x', self.__private_x__, )
    if isinstance(value, (float, int)):
      self.__private_x__ = float(value)
    elif isinstance(value, complex):
      if value.imag ** 2 < 1e-12:
        self.__private_x__ = value.real
    else:
      raise TypeException('value', value, float, int, complex, )

  @y.SET
  def _setY(self, value: float) -> None:
    """Set the y coordinate of the Point."""
    if self.__private_y__ is not None:
      raise VariableNotNone('y', self.__private_y__, )
    if isinstance(value, (float, int)):
      self.__private_y__ = float(value)
    elif isinstance(value, complex):
      if value.real ** 2 < 1e-12:
        self.__private_y__ = value.imag
    else:
      raise TypeException('value', value, float, int, complex, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _resolveOther(self, other: Any) -> Self:
    cls = type(self)
    if isinstance(other, cls):
      return other
    elif isinstance(other, (tuple, list)):
      if len(other) == 2:
        return cls(other[0], other[1])
    try:
      other = cls(other)
    except (ValueError, TypeError):
      return NotImplemented
    else:
      return other

  @overload(float, float)
  def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
    """Initialize a Point with x and y coordinates."""
    self.x = x
    self.y = y

  @overload(complex)
  def __init__(self, z: complex) -> None:
    """Initialize a Point with a complex number."""
    self.x = z.real
    self.y = z.imag

  @overload(QPoint)
  def __init__(self, point: QPoint) -> None:
    """Initialize a Point from a QPoint."""
    self.x = point.x()
    self.y = point.y()

  @overload(QPointF)
  def __init__(self, point: QPointF) -> None:
    """Initialize a Point from a QPointF."""
    self.x = point.x()
    self.y = point.y()

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    """Initialize a Point from another Point."""
    self.x = other.x
    self.y = other.y

  @overload(float)
  def __init__(self, value: float) -> None:
    """Initialize a Point with a single float value."""
    self.x = value

  @overload()
  def __init__(self, ) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __bool__(self, ) -> bool:
    return True if self.x ** 2 + self.y ** 2 > 1e-12 else False

  def __len__(self, ) -> int:
    """Return the number of dimensions of the point."""
    return 2

  def __iter__(self, ) -> Iterator[float]:
    """Return an iterator over the x and y coordinates."""
    yield self.x
    yield self.y

  def __getitem__(self, identifier: Any) -> Any:
    """Get the x or y coordinate by index."""
    if isinstance(identifier, str):
      if identifier.lower() == 'x':
        return self.x
      if identifier.lower() == 'y':
        return self.y
      infoSpec = """Received key: '%s', but expected 'x' or 'y'!"""
      info = infoSpec % identifier
      raise KeyError(info)
    if isinstance(identifier, int):
      if identifier > 1:
        infoSpec = """Index '%d' is out of range!"""
        info = infoSpec % identifier
        raise IndexError(info)
      if identifier < 0:
        return self[identifier + 2]
      return self.y if identifier else self.x
    if isinstance(identifier, slice):
      if identifier.start is None:
        start = 0
      else:
        start = identifier.start
      if identifier.stop is None:
        stop = 2
      else:
        stop = identifier.stop
      if start < 0 or stop > 2:
        infoSpec = """Slice '%s' is out of range!"""
        info = infoSpec % identifier
        raise IndexError(info)
      return (*self,)[start:stop]
    raise TypeException('identifier', identifier, str, int, slice, )

  def __reversed__(self) -> Iterator[float]:
    """Return an iterator over the x and y coordinates in reverse order."""
    yield self.y
    yield self.x

  def __str__(self, ) -> str:
    """Return a string representation of the point."""
    infoSpec = """%s(%.1f, %.1f)"""
    clsName = type(self).__name__
    info = infoSpec % (clsName, self.x, self.y)
    return info

  __repr__ = __str__

  def __eq__(self, other: Any) -> bool:
    """Check if this Point is equal to another Point or a tuple/list of
    coordinates."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    dx = (self.x - other.x) ** 2
    dy = (self.y - other.y) ** 2
    return True if dx + dy < 1e-12 else False

  def __ne__(self, other: Any) -> bool:
    """Check if this Point is not equal to another Point or a tuple/list of
    coordinates."""
    loss = self - other
    if loss is NotImplemented:
      return NotImplemented
    dx = (self.x - other.x) ** 2
    dy = (self.y - other.y) ** 2
    return False if dx + dy < 1e-12 else True

  def __hash__(self, ) -> int:
    """Return a hash of the Point based on its coordinates."""
    return hash((self.x, self.y))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def dist(self, other: Any) -> float:
    """Calculate the distance to another Point or a tuple/list of
    coordinates."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    dx = self.x - other.x
    dy = self.y - other.y
    return (dx ** 2 + dy ** 2) ** 0.5

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
