"""
App provides a basic application inheriting from AbstractApplication.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QMainWindow
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute import SubclassException, TypeException
from worktoy.waitaminute.dispatch import DispatchException

from . import AbstractApplication

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type


class App(AbstractApplication):
  """
  App provides a basic application inheriting from AbstractApplication.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_window__ = QMainWindow
  __fallback_name__ = '| worQt Application |'
  __fallback_icon__ = 'breh.png'

  #  Private Variables
  __window_icon__ = None
  __window_class__ = None
  __window_instance__ = None
  __app_name__ = None

  #  Public Variables
  windowClass = Field()
  window = Field()
  appIcon = Field()
  appName = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @windowClass.GET
  def _getWindowClass(self, **kwargs) -> Type[QMainWindow]:
    if self.__window_class__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__window_class__ = self.__fallback_window__
      return self._getWindowClass(_recursion=True)
    return self.__window_class__

  def _createWindow(self, ) -> None:
    self.__window_instance__ = self.windowClass()

  @window.GET
  def _getWindowInstance(self, **kwargs) -> QMainWindow:
    if self.__window_instance__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWindow()
      return self._getWindowInstance(_recursion=True)
    if isinstance(self.__window_instance__, self.windowClass):
      return self.__window_instance__
    raise TypeException('window', self.__window_instance__, self.windowClass)

  @appIcon.GET
  def _getAppIcon(self, **kwargs) -> QIcon:
    if self.__window_icon__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      iconDir = os.path.join(self.etc, 'resources', 'icons')
      iconFid = os.path.join(iconDir, self.__fallback_icon__)
      pix = QPixmap(iconFid)
      self.__window_icon__ = QIcon(pix)
      return self._getAppIcon(_recursion=True)
    if isinstance(self.__window_icon__, QIcon):
      if QIcon.isNull(self.__window_icon__):
        raise RuntimeError("The application icon is null!")
      return self.__window_icon__
    raise TypeException('appIcon', self.__window_icon__, QIcon)

  @appName.GET
  def _getAppName(self, **kwargs) -> str:
    if self.__app_name__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__app_name__ = self.__fallback_name__
      return self._getAppName(_recursion=True)
    if isinstance(self.__app_name__, str):
      return self.__app_name__
    raise TypeException('appName', self.__app_name__, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  @appIcon.SET
  def _setAppIcon(self, iconFid: str, ) -> None:
    if os.path.isabs(iconFid):
      if os.path.exists(iconFid):
        if os.path.isfile(iconFid):
          pix = QPixmap(iconFid)
          self.__window_icon__ = QIcon(pix)
          return self.setWindowIcon(self.appIcon)
    dispatcher = getattr(type(self), '_setAppIcon')
    args = ()
    raise DispatchException(dispatcher, args)

  @overload(QIcon)
  @appIcon.SET
  def _setAppIcon(self, icon: QIcon, ) -> None:
    self.__window_icon__ = icon
    self.setWindowIcon(self.appIcon)

  @overload(QPixmap)
  @appIcon.SET
  def _setAppIcon(self, pixmap: QPixmap, ) -> None:
    icon = QIcon(pixmap)
    self.__window_icon__ = icon
    self.setWindowIcon(self.appIcon)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    AbstractApplication.__init__(self, )
    for arg in args:
      if isinstance(arg, type) and self.__window_class__ is None:
        if issubclass(arg, QMainWindow):
          self.__window_class__ = arg
          continue
        raise SubclassException(arg, QMainWindow)
      if isinstance(arg, str) and self.__app_name__ is None:
        self.__app_name__ = arg
    self.setApplicationName(self.__app_name__)
    self.setWindowIcon(self.appIcon)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def enterHook(self, *args, **kwargs) -> None:
    """Updates the window icon. """
    self.setWindowIcon(self.appIcon, )
    self.setApplicationName(self.appName, )
