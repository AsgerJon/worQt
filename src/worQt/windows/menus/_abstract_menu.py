"""
AbstractMenu subclasses 'QMenu' and 'MixinBase' and provides the base for
menus in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException, SubclassException

from ...mixin import MixinBase
from . import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias, Optional

  Actions: TypeAlias = dict[str, AbstractAction]
  MaybeActions: TypeAlias = Optional[Actions]
  ActionType: TypeAlias = type[AbstractAction]
  ActionTypes: TypeAlias = dict[str, ActionType]
  MaybeActionTypes: TypeAlias = Optional[ActionTypes]


class AbstractMenu(QMenu, MixinBase):
  """
  AbstractMenu subclasses 'QMenu' and 'MixinBase' and provides the base for
  menus in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: Optional[str] = None
  __menu_title__: Optional[str] = None
  __registered_action_types__: MaybeActionTypes = None

  #  Private Variables
  __icon_cache__: Optional[QIcon] = None
  __title_cache__: Optional[str] = None
  __action_cache__: MaybeActions = None

  #  Public Variables
  menuIcon: Field[QIcon] = Field()
  menuTitle: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _classCreateRegisteredActionTypes(cls, ) -> None:
    regs = maybe(cls.__registered_action_types__, dict())
    cls.__registered_action_types__ = {**regs, }

  @classmethod
  def _classGetRegisteredActionTypes(cls, **kwargs) -> ActionTypes:
    """
    This method returns the registered action types for the menu.
    """
    if cls.__registered_action_types__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      cls._classCreateRegisteredActionTypes()
      return cls._classGetRegisteredActionTypes(_recursion=True)
    if isinstance(cls.__registered_action_types__, dict):
      for name, actionType in cls.__registered_action_types__.items():
        if not isinstance(actionType, type):
          raise TypeException(f'actionType for {name}', actionType, type)
        if not issubclass(actionType, AbstractAction):
          raise SubclassException(actionType, AbstractAction)
      return cls.__registered_action_types__
    name = '__registered_action_types__'
    value = cls.__registered_action_types__
    raise TypeException(name, value, dict)

  @classmethod
  def registerActionType(cls, name: str, actionType: ActionType) -> None:
    """
    This method registers an action type on the menu. The action type must be
    a subclass of 'AbstractAction'. Registered action types are used by the
    menu to determine which actions to initialize and display.
    """
    existing = cls._classGetRegisteredActionTypes()
    if name in existing:
      raise NotImplementedError("""lol we need a custom exception!""")
    if not isinstance(actionType, type):
      raise TypeException('actionType', actionType, type)
    if not issubclass(actionType, AbstractAction):
      raise SubclassException(actionType, AbstractAction)
    existing[name] = actionType
    cls.__registered_action_types__ = existing

  def _createMenuIcon(self, ) -> None:
    if self.__icon_reference__ is None:
      self.__icon_cache__ = QIcon()
    else:
      self.__icon_cache__ = QIcon.fromTheme(self.__icon_reference__)

  @menuIcon.GET
  def _getMenuIcon(self, **kwargs) -> QIcon:
    """
    Menu classes that require an icon can set the class attribute
    '__icon_reference__' to the name of a standard icon as described by the
    freedesktop icon naming specification. Alternatively, they can
    override this method to provide a custom icon. The default
    implementation returns an empty icon.
    """
    if self.__icon_cache__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMenuIcon()
      return self._getMenuIcon(_recursion=True)
    if isinstance(self.__icon_cache__, QIcon):
      return self.__icon_cache__
    raise TypeException('__icon_cache__', self.__icon_cache__, QIcon)

  def _createMenuTitle(self, ) -> None:
    if self.__menu_title__ is None:
      self.__title_cache__ = self.getFieldName()
    else:
      self.__title_cache__ = self.__menu_title__

  @menuTitle.GET
  def _getMenuTitle(self, **kwargs) -> str:
    """
    Menu classes that require a title can set the class attribute
    '__menu_title__' to the desired title. Alternatively, they can
    override this method to provide a custom title. The default
    implementation returns the name of the field.
    """
    if self.__title_cache__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMenuTitle()
      return self._getMenuTitle(_recursion=True)
    if isinstance(self.__title_cache__, str):
      return self.__title_cache__
    raise TypeException('__title_cache__', self.__title_cache__, str)

  def _createActions(self, ) -> None:
    actions = dict()
    for name, actionType in self._classGetRegisteredActionTypes().items():
      action = actionType(self, )
      setattr(action, '__field_name__', name)
      setattr(self, name, action)
      actions[name] = action
    self.__action_cache__ = {**actions, }

  def getActions(self, **kwargs) -> Actions:
    """
    This method returns the actions to be displayed in the menu. By default,
    it initializes and returns an action for each registered action type.
    """
    if self.__action_cache__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createActions()
      return self.getActions(_recursion=True)
    if isinstance(self.__action_cache__, dict):
      for name, action in self.__action_cache__.items():
        if not isinstance(action, AbstractAction):
          raise TypeException(f'action for {name}', action, AbstractAction)
      return self.__action_cache__
    name = '__action_cache__'
    value = self.__action_cache__
    raise TypeException(name, value, dict)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    This method initializes the menu visually - applying its own title and
    icon - and calls the 'initUI' method of the owned actions. It should be
    called by the general 'initUI' chain beginning from the main window
    class responsible for the menus.
    """
    self.setTitle(self.menuTitle)
    self.setIcon(self.menuIcon)
    for name, action in self.getActions().items():
      self.addAction(action)
      action.initUI()
