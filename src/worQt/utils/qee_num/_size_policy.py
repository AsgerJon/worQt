"""
SizePolicy subclasses 'BaseObject' and provides an object specifying
vertical and horizontal sizing modes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QSizePolicy
from worktoy.desc import Field, Alias
from worktoy.keenum import KeeNum, Kee
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet

from worQt.utils.qee_num import SizingMode

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias

  from ...widgets import PaintedWidget as Widget

  MaybeSizingMode: TypeAlias = Optional[SizingMode]
  SizingModeField: TypeAlias = Union[SizingMode, Field]
  QField: TypeAlias = Union[QSizePolicy, Field]

  MaybeBool: TypeAlias = Optional[bool]
  BoolField: TypeAlias = Union[bool, Field]

  WidgetField: TypeAlias = Union[Widget, Field, Alias]


class SizePolicy(BaseObject):
  """
  SizePolicy subclasses 'BaseObject' and provides an object specifying
  vertical and horizontal sizing modes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __horizontal_fallback__ = SizingMode.INTRINSIC
  __vertical_fallback__ = SizingMode.INTRINSIC
  __fallback_frozen__ = True

  #  Private Variables
  __horizontal_mode__: MaybeSizingMode = None
  __vertical_mode__: MaybeSizingMode = None
  __is_frozen__: MaybeBool = None

  #  Public Variables
  horizontal: SizingModeField = Field()
  vertical: SizingModeField = Field()
  frozen: BoolField = Field()

  #  Virtual Variables
  Q: QField = Field()
  widget: WidgetField = Alias('instance')

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

  def _createFrozenFlag(self, ) -> None:
    self.__is_frozen__ = True if self.__fallback_frozen__ else False

  @frozen.GET
  def _getFrozenFlag(self, **kwargs) -> bool:
    if self.__is_frozen__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createFrozenFlag()
      return self._getFrozenFlag(_recursion=True)
    if isinstance(self.__is_frozen__, bool):
      return self.__is_frozen__
    raise TypeException('__is_frozen__', self.__is_frozen__, bool)

  @Q.GET
  def _getQ(self) -> QSizePolicy:
    """Returns the QSizePolicy representation."""
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

  @frozen.SET
  def _setFrozenFlag(self, value: bool) -> None:
    raise NotImplementedError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @horizontal.preSet
  def _preSetHorizontalMode(self, value: SizingMode) -> None:
    try:
      oldValue = self._getHorizontalMode(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldValue == value:
        raise SkipSet

  @horizontal.onSet
  def _onSetHorizontalMode(self, value: SizingMode) -> None:
    if self.hasContext():
      self.widget.update()

  @vertical.preSet
  def _preSetVerticalMode(self, value: SizingMode) -> None:
    try:
      oldValue = self._getVerticalMode(_recursion=True)
    except RecursionError:
      pass
    else:
      if oldValue == value:
        raise SkipSet

  @vertical.onSet
  def _onSetVerticalMode(self, value: SizingMode) -> None:
    if self.hasContext():
      self.widget.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __hash__(self, ) -> int:
    return hash((hash(self.horizontal), hash(self.vertical),))
