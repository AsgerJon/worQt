"""
AbstractMenu provides a base class for menus in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import TypeException

from ..app.desQt import App

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, TypeAlias, Union
  from ..menus import AbstractAction

  Action: TypeAlias = Union[AbstractAction, QAction]
  Actions: TypeAlias = Union[Action, tuple[Action, ...]]

  from . import ActionBox as Box

  Boxes: TypeAlias = Union[Box, tuple[Box, ...]]


class AbstractMenu(QMenu):
  """
  AbstractMenu provides a base class for menus in the worQt framework.
  It extends QMenu and can be used to create custom menus with additional
  functionality.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __owned_actions__ = None
  __boxed_actions__ = None

  #  Public Variables
  app = App()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def getBoxedActions(cls) -> Boxes:
    """Returns the boxed actions."""
    return maybe(cls.__boxed_actions__, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def boxAction(cls, box: Box) -> None:
    """
    Boxes the action in the menu. This allows for easy access to the action
    by its name.
    """
    existing = cls.getBoxedActions()
    cls.__boxed_actions__ = [*existing, box]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """
    Subclasses must implement this method. Here, it should add actions
    that are defined in LabelBox descriptors in the class body. Actions
    should be given as descriptors in a LabelBox. Then this method should
    add each to the menu using self.addAction(self.actionName). This
    method runs before the 'initLogic' method defined below.
    """

  def initLogic(self) -> None:
    """
    Subclasses may implement this method to connect any particular action
    to a specific logic. By default, actions are already added by the
    'initUi' defined above making them available externally.
    """

  def resolveKey(self, key: str) -> Action:
    for action in self:
      if action.objectName().lower() == key.lower():
        return action
      if action.text().lower() == key.lower():
        return action
      if action.iconText().lower() == key.lower():
        return action
    infoSpec = """No action with key '%s' found in '%s' object having 
    actions: <br><tab>%s"""
    clsName = type(self).__name__
    actionStr = '<br><tab>'.join([a.__field_name__ for a in self])
    info = infoSpec % (key, clsName, actionStr)
    raise KeyError(info)

  def resolveIndex(self, index: int) -> Action:
    if index < 0:
      return self.resolveIndex(len(self) + index)
    if index < len(self):
      return maybe(self.__owned_actions__, [])[index]
    infoSpec = """Index '%d' is out of range for '%s' object having '%d' 
    actions. """
    info = infoSpec % (index, type(self).__name__, len(self))
    raise IndexError(textFmt(info))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addAction(self, *args, **kwargs) -> Action:
    """
    Adds an action to the menu. This method is overridden to ensure that
    actions are added to the __owned_actions__ list for proper management.
    """
    existing = maybe(self.__owned_actions__, [])
    action = QMenu.addAction(self, *args, **kwargs)
    self.__owned_actions__ = [*existing, action]
    return action

  def addActions(self, *args, **kwargs) -> None:
    """
    Adds multiple actions to the menu. This method is overridden to ensure
    that all actions are added to the __owned_actions__ list for proper
    management.
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
      return self.addActions(*args[0], **kwargs)
    for action in args:
      self.addAction(action, **kwargs)

  def show(self, ) -> None:
    """
    Shows the menu. This method is overridden to ensure that the menu
    is initialized before showing it.
    """
    self.initUi()
    self.initLogic()
    QMenu.show(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Action]:
    """
    Returns an iterator over the actions in the menu. This allows for easy
    iteration over the actions in the menu.
    """
    yield from maybe(self.__owned_actions__, [])

  def __len__(self, ) -> int:
    return len(maybe(self.__owned_actions__, []))

  def __getitem__(self, identifier: Any) -> Actions:
    """
    Returns the action with the given name. This allows for easy access to
    actions by their name.
    """
    if isinstance(identifier, str):
      return self.resolveKey(identifier)
    if isinstance(identifier, int):
      return self.resolveIndex(identifier)
    if isinstance(identifier, slice):
      indices = range(*identifier.indices(len(self)))
      return (*[self.resolveIndex(i) for i in indices],)
    raise TypeException('identifier', identifier, str, int)
