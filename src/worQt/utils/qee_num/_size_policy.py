"""
SizePolicy subclasses 'BaseObject' and provides an object specifying
vertical and horizontal sizing modes, convertible to a 'QSizePolicy'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QSizePolicy
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException

from worQt.utils.qee_num import SizingMode

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias

  MaybeSizingMode: TypeAlias = Optional[SizingMode]


class SizePolicy(BaseObject):
  """
  SizePolicy subclasses 'BaseObject' and provides an object specifying
  vertical and horizontal sizing modes, convertible to a 'QSizePolicy'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __horizontal_fallback__ = SizingMode.INTRINSIC
  __vertical_fallback__ = SizingMode.INTRINSIC

  #  Private Variables
  __horizontal_mode__: MaybeSizingMode = None
  __vertical_mode__: MaybeSizingMode = None

  #  Public Variables
  horizontal: Field[SizingMode] = Field()
  vertical: Field[SizingMode] = Field()

  #  Virtual Variables
  Q: Field[QSizePolicy] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createHorizontalMode(self) -> None:
    self.__horizontal_mode__ = self.__horizontal_fallback__

  @horizontal.GET
  def _getHorizontalMode(self, **kwargs) -> SizingMode:
    if self.__horizontal_mode__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createHorizontalMode()
      return self._getHorizontalMode(_recursion=True)
    if isinstance(self.__horizontal_mode__, SizingMode):
      return self.__horizontal_mode__
    name, value = '__horizontal_mode__', self.__horizontal_mode__
    raise TypeException(name, value, SizingMode)

  def _createVerticalMode(self) -> None:
    self.__vertical_mode__ = self.__vertical_fallback__

  @vertical.GET
  def _getVerticalMode(self, **kwargs) -> SizingMode:
    if self.__vertical_mode__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createVerticalMode()
      return self._getVerticalMode(_recursion=True)
    if isinstance(self.__vertical_mode__, SizingMode):
      return self.__vertical_mode__
    name, value = '__vertical_mode__', self.__vertical_mode__
    raise TypeException(name, value, SizingMode)

  @Q.GET
  def _getQ(self) -> QSizePolicy:
    """
    The 'Q' getter returns the 'QSizePolicy' with this policy's modes.
    """
    h = self.horizontal.value
    v = self.vertical.value
    return QSizePolicy(h, v)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @horizontal.SET
  def _setHorizontalMode(self, value: SizingMode) -> None:
    if not isinstance(value, SizingMode):
      raise TypeException('horizontal', value, SizingMode)
    self.__horizontal_mode__ = value

  @vertical.SET
  def _setVerticalMode(self, value: SizingMode) -> None:
    if not isinstance(value, SizingMode):
      raise TypeException('vertical', value, SizingMode)
    self.__vertical_mode__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __hash__(self, ) -> int:
    return hash((hash(self.horizontal), hash(self.vertical),))
