"""
Margin provides a dataclass for margins
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMargins, QMarginsF
from worktoy.desc import Field, AttriBox
from worktoy.dispatch import overload
from worktoy.core.sentinels import THIS
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Iterator


class Margins(BaseObject):
  """Margin provides a dataclass for margins."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  left = AttriBox[float](0.0)
  top = AttriBox[float](0.0)
  right = AttriBox[float](0.0)
  bottom = AttriBox[float](0.0)

  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQMargins(self) -> QMargins:
    """Get the QMargins object."""
    return QMargins(self.left, self.top, self.right, self.bottom)

  @QF.GET
  def _getQMarginsF(self) -> QMarginsF:
    """Get the QMarginsF object."""
    return QMarginsF(self.left, self.top, self.right, self.bottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def fromQMargins(cls, margins: QMargins) -> Margins:
    """Create a Margin from QMargins."""
    return cls(
        margins.left(),
        margins.top(),
        margins.right(),
        margins.bottom()
    )

  @classmethod
  def fromQMarginsF(cls, margins: QMarginsF) -> Margins:
    """Create a Margin from QMarginsF."""
    return cls(
        margins.left(),
        margins.top(),
        margins.right(),
        margins.bottom()
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __add__(self, other: Any) -> Self:
    cls = type(self)
    if isinstance(other, cls):
      return cls(
          self.left + other.left,
          self.top + other.top,
          self.right + other.right,
          self.bottom + other.bottom
      )
    return NotImplemented

  def __iter__(self, ) -> Iterator[float]:
    """Iterate over the margins."""
    yield self.left
    yield self.top
    yield self.right
    yield self.bottom

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.left = other.left
    self.top = other.top
    self.right = other.right
    self.bottom = other.bottom

  @overload(float, float, float, float)
  @overload(int, int, int, int)
  def __init__(self, *args, ) -> None:
    self.left, self.top, self.right, self.bottom = args

  @overload(QMargins)
  def __init__(self, other: QMargins) -> None:
    self.left = other.left()
    self.top = other.top()
    self.right = other.right()
    self.bottom = other.bottom()

  @overload(QMarginsF)
  def __init__(self, other: QMarginsF) -> None:
    self.__init__(QMarginsF.toMargins(other))

  @overload(float, float)
  @overload(int, int)
  def __init__(self, left: float, top: float) -> None:
    self.left = left
    self.top = top
    self.right = left
    self.bottom = top

  @overload(float)
  @overload(int)
  def __init__(self, value: float) -> None:
    self.left = value
    self.top = value
    self.right = value
    self.bottom = value
