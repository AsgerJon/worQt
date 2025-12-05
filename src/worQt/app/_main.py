"""App class provides the base application class. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow, QApplication
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException

from . import AbstractApplication

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias, Any

  Window: TypeAlias = Type[QMainWindow]


class Main(AbstractApplication):
  """App class provides the base application class."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_window__ = QMainWindow
  __fallback_name__ = 'main.py'

  #  Private Variables
  __app_name__ = None
  __window_class__ = None
  __window_instance__ = None

  #  Public Variables
  windowClass = Field()
  windowInstance = Field()
  appName = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @windowClass.GET
  def _getWindowClass(self) -> type[QMainWindow]:
    """Returns the class of the main window."""
    return maybe(self.__window_class__, self.__fallback_window__)

  @windowInstance.GET
  def _getWindowInstance(self, **kwargs) -> QMainWindow:
    """Returns the instance of the main window."""
    if self.__window_instance__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__window_instance__ = self.windowClass()
      return self._getWindowInstance(_recursion=True)
    if isinstance(self.__window_instance__, self.windowClass):
      return self.__window_instance__
    name, value = '__window_instance__', self.__window_instance__
    raise TypeException(name, value, self.windowClass, )

  @appName.GET
  def _getAppName(self, **kwargs) -> str:
    """Returns the name of the application."""
    if self.__app_name__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__app_name__ = self.__fallback_name__
      return self._getAppName(_recursion=True)
    return self.__app_name__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_getitem__(cls, argTuple: tuple[Any, ...]) -> Self:
    """
    Please note that all arguments passed are received in a tuple as the
    single positional argument.
    """
    args = [*argTuple, ]
    _windowClass, _appName = None, None
    for arg in args:
      if isinstance(arg, type) and _windowClass is None:
        if issubclass(arg, QMainWindow):
          _windowClass = arg
      elif isinstance(arg, str) and _appName is None:
        _appName = arg
    cls.__window_class__ = maybe(_windowClass, cls.__fallback_window__)
    cls.__app_name__ = maybe(_appName, cls.__fallback_name__)
    return cls

  def __call__(self, *args: Any, **kwargs: Any) -> Self:
    """Initializes the application with the given arguments."""
    self.__init__(*args, **kwargs)
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def onStartUp(self, ) -> None:
    """Called when the application starts up."""
    # Initialize the application
    QApplication.setApplicationDisplayName(self.appName)
    QApplication.setApplicationName(self.appName)
    super().onStartUp()
    print('Application starting up.')
    self.windowInstance.show()
    QMainWindow.setWindowTitle(self.windowInstance, self.appName)

  def onShutdown(self, ) -> None:
    """Called when the application exits."""
    # Clean up resources
    super().onShutdown()
    print('Application exiting.')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initializes the application."""
    super().__init__(*args, **kwargs)
    infoSpec = """Initializing app: %s from entry point: %s"""
    info = infoSpec % (type(self).__name__, args[0])
    print(info)
