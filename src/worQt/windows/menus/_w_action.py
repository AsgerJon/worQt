"""
WAction subclasses 'ActionMixin' and 'QAction' providing the action class
used by the menu implementations provided by the 'worQt.windows.menus'
package.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QKeyCombination
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMenu
from icecream import ic
from worktoy.desc import Field, SymbolicName
from worktoy.dispatch import overload
from worktoy.utilities import textFmt, maybe
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet
from worktoy.waitaminute.desc import WriteOnceError

from ...mixin import FreeDesktopIcon, KeyboardShortcuts
from . import ActionMixin

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union

  StrField: TypeAlias = Union[Field, str]
  IconField: TypeAlias = Union[Field, QIcon]
  KeyField: TypeAlias = Union[QKeySequence, Field, str]
  MaybeKey: TypeAlias = Optional[QKeySequence]
  MaybeStr: TypeAlias = Optional[str]
  StrArgs: TypeAlias = tuple[MaybeStr, tuple[Any, ...]]


class WAction(QAction, ActionMixin):
  """
  WAction subclasses 'ActionMixin' and 'QAction' providing the action class
  used by the menu implementations provided by the 'worQt.windows.menus'
  package.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  STATIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _parseAltName(*args, ) -> StrArgs:
    if not args:
      return None, ()
    posArgs = [*reversed(args), ]
    unusedArgs = []
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, str):
        if str.islower(arg) and ' ' not in arg:
          list.extend(unusedArgs, posArgs)
          return arg, (*unusedArgs,)
    else:
      return None, (*unusedArgs,)

  @staticmethod
  def _parseToolTip(*args, ) -> StrArgs:
    if not args:
      return None, ()
    posArgs = [*reversed(args), ]
    unusedArgs = []
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, str):
        if str.islower(arg):
          if ' ' not in arg:
            unusedArgs.append(arg)
            continue
          list.extend(unusedArgs, posArgs)
          return str.capitalize(arg), (*unusedArgs,)
    else:
      return None, (*unusedArgs,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __key_bind__: MaybeKey = None
  __alternative_name__: MaybeStr = None

  #  Public Variables
  altName: StrField = Field()
  keyBind: KeyField = Field()

  #  Virtual Variables
  publicIcon: IconField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @altName.GET
  def _getAltName(self, ) -> str:
    return maybe(self.__alternative_name__, self.varName)

  @publicIcon.GET
  def _getPublicIcon(self, ) -> QIcon:
    icon = FreeDesktopIcon.findIcon(self.varName)
    if icon is FreeDesktopIcon.NULL:
      return FreeDesktopIcon.findIcon(self.altName).Q
    return FreeDesktopIcon.findIcon(self.varName).Q

  def _createKeyBind(self, ) -> None:
    varBind = KeyboardShortcuts.findShortcut(self.varName)
    if QKeySequence.isEmpty(varBind.Q):
      altBind = KeyboardShortcuts.findShortcut(self.altName)
      self.keyBind = altBind.Q
    else:
      self.keyBind = varBind.Q

  @keyBind.GET
  def _getKeyBind(self, **kwargs) -> QKeySequence:
    if self.__key_bind__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createKeyBind()
      return self._getKeyBind(_recursion=True)
    if isinstance(self.__key_bind__, QKeySequence):
      return self.__key_bind__
    raise TypeException('__key_bind__', self.__key_bind__, QKeySequence)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @keyBind.SET
  @overload(str)
  def _setKeyBind(self, value: str, **kwargs) -> None:
    self.__key_bind__ = QKeySequence.fromString(value)

  @overload(QKeySequence)
  def _setKeyBind(self, value: QKeySequence, **kwargs) -> None:
    self.__key_bind__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @keyBind.preSet
  def _preSetKeyBind(self, value: Any, **kwargs) -> None:
    if isinstance(value, str):
      try:
        oldBind = self._getKeyBind(_recursion=True)
      except RecursionError:
        pass
      else:
        if QKeySequence.toString(oldBind) == value:
          raise SkipSet

  @keyBind.onSet
  def _onSetKeyBind(self, value: Any, **kwargs) -> None:
    QAction.setShortcut(self, self.keyBind)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QMenu)
  def __init__(self, menu: QMenu, **kwargs) -> None:
    super().__init__(menu)

  @overload(QMenu, str)  # Parent, tooltip
  @overload(QMenu, str, str)  # Parent, tooltip, alternative name
  def __init__(self, menu, *args) -> None:
    super().__init__(menu)
    toolTip, unusedArgs = self._parseToolTip(*args, )
    altName, unusedArgs = self._parseAltName(*unusedArgs, )
    if toolTip is not None:
      self.__tool_tip__ = toolTip
    if altName is not None:
      self.__alternative_name__ = altName

  @overload.finalize
  def __init__(self, *args, **kwargs) -> None:
    QAction.setShortcutVisibleInContextMenu(self, True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    QAction.setText(self, self.publicName)
    QAction.setIcon(self, self.publicIcon)
    QAction.setShortcut(self, self.keyBind)
    QAction.setToolTip(self, self.tip)
