"""
ActionMixin subclasses 'MixinBase' from the 'worQt.mixin' package and
provides a base exposing both the 'Shiboken' metaclass and the 'BaseMeta'
metaclass from 'worktoy'. Subclasses will thus have access to the features
provided by 'worktoy' such as function overloading.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon, QKeySequence
from worktoy.desc import Field
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet
from worktoy.waitaminute.desc import WriteOnceError

from ...mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union, Any

  StrField: TypeAlias = Union[Field, str]
  IconField: TypeAlias = Union[Field, QIcon]
  KeyField: TypeAlias = Union[QKeySequence, Field]
  MaybeKey: TypeAlias = Optional[QKeySequence]
  MaybeStr: TypeAlias = Optional[str]


class ActionMixin(MixinBase):
  """
  ActionMixin subclasses 'MixinBase' from the 'worQt.mixin' package and
  provides a base exposing both the 'Shiboken' metaclass and the 'BaseMeta'
  metaclass from 'worktoy'. Subclasses will thus have access to the features
  provided by 'worktoy' such as function overloading.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __tool_tip__: MaybeStr = None

  #  Public Variables
  tip: StrField = Field()

  #  Virtual Variables
  varName: StrField = Field()
  publicName: StrField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @varName.GET
  def _getVarName(self, ) -> str:
    return self.fieldBox.getFieldName()

  @publicName.GET
  def _getPublicName(self, ) -> str:
    boxName = str.replace(self.varName, 'Action', '')
    boxName = str.replace(boxName, 'action', '')
    boxChars = [(' %s' if str.isupper(c) else '%s') % c for c in boxName]
    boxParts = str.split(str.join('', boxChars))
    boxParts = [str.capitalize(part) for part in boxParts if part]
    return ' '.join(boxParts)

  def _createToolTip(self, ) -> None:
    self.tip = str(self.publicName)

  @tip.GET
  def _getToolTip(self, **kwargs) -> str:
    if self.__tool_tip__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createToolTip()
      return self._getToolTip(_recursion=True)
    if isinstance(self.__tool_tip__, str):
      return self.__tool_tip__
    raise TypeException('__tool_tip__', self.__tool_tip__, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @tip.SET
  def _setToolTip(self, value: str, **kwargs) -> None:
    self.__tool_tip__ = str.strip(value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @tip.preSet
  def _preSetToolTip(self, value: str, **kwargs) -> None:
    value = str.strip(value)
    if isinstance(value, str):
      try:
        oldTip = self._getToolTip(_recursion=True)
      except RecursionError:
        pass
      else:
        if oldTip == value:
          raise SkipSet

  @tip.onSet
  def _onSetToolTip(self, value: Any, **kwargs) -> None:
    self.setToolTip(self.tip)
