"""
MainWindow provides a descriptor for the main window of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QMainWindow
from worktoy.core import Object
from worktoy.waitaminute import VariableNotNone, MissingVariable
from worktoy.waitaminute import TypeException, SubclassException
from worktoy.waitaminute.desc import ProtectedError, ReadOnlyError

from worQt.app import App

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, TypeAlias, Any, Type

  WindowClass: TypeAlias = Type[QMainWindow]
  Window: TypeAlias = QMainWindow


class Window(Object):
  """
  MainWindow provides a descriptor for the main window of the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __window_class__ = None
  __main_window__ = None

  #  Public Variables
  instance = App()  # Replaces context with app instance
  app = App()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getMainWindowClass(self) -> WindowClass:
    """Getter-function for the main window class."""
    if self.__window_class__ is None:
      raise MissingVariable('__window_class__', type(QMainWindow))
    return self.__window_class__

  def _setMainWindowClass(self, cls: WindowClass) -> None:
    """Setter-function for the main window class."""
    if self.__window_class__ is not None:
      raise VariableNotNone('__window_class__', self.__window_class__)
    if not isinstance(cls, type):
      raise TypeException('cls', cls, type(QMainWindow))
    if not issubclass(cls, QMainWindow):
      raise SubclassException(cls, QMainWindow)
    self.__window_class__ = cls

  def _createMainWindow(self, **kwargs) -> None:
    """Create the main window of the application. """
    if self.__main_window__ is not None:
      raise VariableNotNone('__main_window__', self.__main_window__)
    cls = self._getMainWindowClass()
    args = self.getPosArgs(THIS=QCoreApplication.instance())
    args = [arg for arg in args if arg is not cls]
    kwargs = self.getKeyArgs(THIS=QCoreApplication.instance())
    self.__main_window__ = cls(*args, **kwargs)

  def _getMainWindow(self, **kwargs) -> Window:
    """Getter-function for the main window."""
    if self.__main_window__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMainWindow()
      return self._getMainWindow(_recursion=True)
    return self.__main_window__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, windowClass: Any) -> None:
    self._setMainWindowClass(windowClass)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, *args, **kwargs) -> Window:
    """Instance getter for the main window."""
    return self._getMainWindow()

  def __instance_set__(self, value: Window, *args, **kwargs) -> None:
    """Instance setter for the main window."""
    raise ReadOnlyError(QCoreApplication.instance(), self, value)

  def __instance_delete__(self, *args, **kwargs) -> None:
    """Instance deleter for the main window."""
    raise ProtectedError(QCoreApplication.instance(), self, None)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __class_getitem__(cls, windowClass: Any) -> Any:
    """Class getter for the main window."""
    return cls(windowClass)

  def __call__(self, *args, **kwargs) -> Self:
    """Implements the __init__ method allowing the AttriBox like syntax."""
    Object.__init__(self, *args, **kwargs)
    return self
