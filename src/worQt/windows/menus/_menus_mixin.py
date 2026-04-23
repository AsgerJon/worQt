"""
MenusMixin subclasses MixinBase and provides the mixin between 'Shiboken'
and the menu classes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QKeyCombination
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import QMenu
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import WriteOnceError

from moreworktoy.waitaminute import MissingImplementation
from ...mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Type
  from ...mixin import BoxBase

  from . import AbstractMenu

  WMenu: TypeAlias = Type[AbstractMenu]
  WMenus: TypeAlias = tuple[BoxBase, ...]
  WActions: TypeAlias = tuple[BoxBase, ...]


class MenusMixin(MixinBase):
  """
  MenusMixin subclasses MixinBase and provides certain common functionalities
  shared by actions and menus in the worQt framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  # --#  Definition of accepted keys and types for various properties
  __icon_keys__ = ('icon', 'iconId', 'icon_id',)
  __icon_types__ = (str, QIcon,)
  __keybind_keys__ = ('keyBind', 'key_bind', 'shortcut',)
  __keybind_types__ = (str, QKeySequence,)
  __tooltip_keys__ = ('toolTip', 'tool_tip', 'tooltip', 'tip',)
  __tooltip_types__ = (str,)
  __text_keys__ = ('text', 'label', 'name',)
  __text_types__ = (str,)
  # --#  Registration of Menus and Actions
  __registered_actions__ = None
  __registered_menus__ = None

  #  Fallback Variables
  __fallback_icon__ = 'application-x-executable'
  __fallback_keybind__ = ''
  __fallback_tooltip__ = ''

  #  Private Variables
  __public_name__ = None
  __action_icon__ = None
  __key_bind__ = None
  __tool_tip__ = None

  #  Public Variables
  publicName = Field()
  actionIcon = Field()
  keyBind = Field()
  actionTip = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createPublicName(self, ) -> None:
    """Creator-function for the public name"""
    name = str.replace(self.fieldName, 'Action', '')
    name = str.replace(name, 'Menu', '').strip()
    chars = []
    for i, c in enumerate([cc for cc in name]):
      if c.isupper():
        chars.append(' %s' % c.upper())
      else:
        chars.append(c if i else c.upper())
    self.__public_name__ = ''.join(chars)

  @publicName.GET
  def _getPublicName(self, **kwargs) -> str:
    if self.__public_name__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPublicName()
      return self._getPublicName(_recursion=True)
    if isinstance(self.__public_name__, str):
      return self.__public_name__
    name, value = '__public_name__', self.__public_name__
    raise TypeException(name, value, str)

  def _createIcon(self, ) -> None:
    """Creator-function for the icon"""
    self.__action_icon__ = QIcon.fromTheme(self.__fallback_icon__)

  @actionIcon.GET
  def _getIcon(self, **kwargs) -> QIcon:
    if self.__action_icon__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createIcon()
      return self._getIcon(_recursion=True)
    if isinstance(self.__action_icon__, QIcon):
      return self.__action_icon__
    name, value = '__action_icon__', self.__action_icon__
    raise TypeException(name, value, QIcon)

  def _createKeybind(self, ) -> None:
    """Creator-function for the keybind"""
    kb = self.__fallback_keybind__
    flag = QKeySequence.SequenceFormat.PortableText
    self.__key_bind__ = QKeySequence.fromString(kb, flag)

  @keyBind.GET
  def _getKeyBind(self, **kwargs) -> QKeySequence:
    if self.__key_bind__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createKeybind()
      return self._getKeyBind(_recursion=True)
    if isinstance(self.__key_bind__, QKeySequence):
      return self.__key_bind__
    name, value = '__key_bind__', self.__key_bind__
    raise TypeException(name, value, QKeySequence)

  def _createToolTip(self, ) -> None:
    """Creator-function for the tooltip"""
    self.__tool_tip__ = self.__fallback_tooltip__

  @actionTip.GET
  def _getToolTip(self, **kwargs) -> str:
    if self.__tool_tip__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createToolTip()
      return self._getToolTip(_recursion=True)
    if isinstance(self.__tool_tip__, str):
      return self.__tool_tip__
    name, value = '__tool_tip__', self.__tool_tip__
    raise TypeException(name, value, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @publicName.SET
  def _setPublicName(self, value: str, **kwargs) -> None:
    if not isinstance(value, str):
      raise TypeException('value', value, str)
    if self.__public_name__ is not None:
      raise WriteOnceError(self, self.__public_name__, value)
    self.__public_name__ = str.strip(value)

  @keyBind.SET
  @overload(QKeySequence)
  def _setKeyBind(self, value: QKeySequence, ) -> None:
    """
    This overload permits empty sequences.
    """
    if self.__key_bind__ is not None:
      raise WriteOnceError(self, self.__key_bind__, value)
    self.__key_bind__ = value

  @overload(QKeyCombination)
  def _setKeyBind(self, value: QKeyCombination, ) -> None:
    """
    This is allowed to result in an empty sequence.
    """
    if self.__key_bind__ is not None:
      raise WriteOnceError(self, self.__key_bind__, value)
    self.__key_bind__ = QKeySequence(value)

  @overload(str)
  def _setKeyBind(self, value: str, ) -> None:
    """
    Only the empty string may result in an empty sequence.
    """
    if self.__key_bind__ is not None:
      raise WriteOnceError(self, self.__key_bind__, value)
    if value:
      fmt = QKeySequence.SequenceFormat.PortableText
      shortcut = QKeySequence.fromString(value, fmt)
      if QKeySequence.isEmpty(shortcut):
        infoSpec = """Unable to create valid keybind for '%s'!"""
        raise ValueError(textFmt(infoSpec % value))
      self.__key_bind__ = shortcut
    else:
      self.__key_bind__ = QKeySequence()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self) -> None:
    """
    Subclasses must implement this method. It is run only right before it
    is needed. It should ensure that actions are ready and added to the
    menu.
    """
    raise MissingImplementation(self, 'initUI')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
