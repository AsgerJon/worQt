"""App class provides the base application class. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow
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

  #  Private Variables
  __window_class__ = None
  __window_instance__ = None

  #  Public Variables
  windowClass = Field()
  windowInstance = Field()

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_getitem__(cls, window: Window) -> Self:
    """Sets the window class. """
    cls.__window_class__ = window
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
    super().onStartUp()
    print('Application starting up.')
    self.windowInstance.show()

  def onExit(self, ) -> None:
    """Called when the application exits."""
    # Clean up resources
    super().onExit()
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
