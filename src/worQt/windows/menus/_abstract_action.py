"""
AbstractAction subclasses 'QAction' and 'MixinBase' and provides the base
for actions in the main window menus.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPixmap, QIcon, QKeySequence, QAction
from worktoy.desc import FixBox, Field
from worktoy.waitaminute import TypeException

from ...mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional


class AbstractAction(QAction, MixinBase):
  """
  AbstractAction subclasses 'QAction' and 'MixinBase' and provides the base
  for actions in the main window menus.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: Optional[str] = None
  __action_title__: Optional[str] = None
  __key_bind__: Optional[str] = None

  #  Private Variables
  __icon_cache__: Optional[QIcon] = None
  __title_cache__: Optional[str] = None
  __short_cut__: Optional[QKeySequence] = None

  #  Public Variables
  actionIcon: Field[QIcon] = Field()
  actionTitle: Field[str] = Field()
  actionShortcut: Field[QKeySequence] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createActionIcon(self, ) -> None:
    if self.__icon_reference__ is None:
      self.__icon_cache__ = QIcon()
    else:
      self.__icon_cache__ = QIcon.fromTheme(self.__icon_reference__)

  @actionIcon.GET
  def _getActionIcon(self, **kwargs) -> QIcon:
    """
    Action classes that require an icon can set the class attribute
    '__icon_reference__' to the name of a standard icon as described by the
    freedesktop icon naming specification. Alternatively, they can
    override this method entirely. The default implementation returns an
    empty icon.
    """
    if self.__icon_cache__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createActionIcon()
      return self._getActionIcon(_recursion=True)
    if isinstance(self.__icon_cache__, QIcon):
      return self.__icon_cache__
    raise TypeException('__icon_cache__', self.__icon_cache__, QIcon)

  def _createActionTitle(self, ) -> None:
    if self.__action_title__ is None:
      self.__title_cache__ = self.getFieldName()
    else:
      self.__title_cache__ = self.__action_title__

  @actionTitle.GET
  def _getActionTitle(self, **kwargs) -> str:
    """
    Action classes that require a title can set the class attribute
    '__action_title__' to the desired title. Alternatively, they can
    override this method entirely. The default implementation returns the
    name of the field.
    """
    if self.__title_cache__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createActionTitle()
      return self._getActionTitle(_recursion=True)
    if isinstance(self.__title_cache__, str):
      return self.__title_cache__
    raise TypeException('__title_cache__', self.__title_cache__, str)

  def _createActionShortcut(self, ) -> None:
    if self.__key_bind__ is None:
      self.__short_cut__ = QKeySequence()
    else:
      self.__short_cut__ = QKeySequence.fromString(self.__key_bind__)

  @actionShortcut.GET
  def _getActionShortcut(self, **kwargs) -> QKeySequence:
    """
    Action classes that require a shortcut can set the class attribute
    '__key_bind__' to the desired key bind as a string. Alternatively, they
    can override this method entirely. The default implementation returns an
    empty key sequence.
    """
    if self.__short_cut__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createActionShortcut()
      return self._getActionShortcut(_recursion=True)
    if isinstance(self.__short_cut__, QKeySequence):
      return self.__short_cut__
    raise TypeException('__short_cut__', self.__short_cut__, QKeySequence)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    It should be called by the general 'initUI' chain beginning from the
    main window class responsible for the menus. 
    """
    self.setIcon(self.actionIcon)
    self.setText(self.actionTitle)
    self.setShortcut(self.actionShortcut)
