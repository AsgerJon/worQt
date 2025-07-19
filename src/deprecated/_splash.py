"""Splash provides a splash screen for the application. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QSplashScreen
from worktoy.attr import Field, AttriBox
from worktoy.core import Object
from worktoy.static.zeroton import THIS
from worktoy.waitaminute import VariableNotNone, MissingVariable, \
  TypeException, SubclassException
from worktoy.waitaminute.desc import ReadOnlyError, ProtectedError

from worQt.app import App

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Self, Any, TypeAlias, Type

  SplashClass: TypeAlias = Type[QSplashScreen]
  Splash: TypeAlias = QSplashScreen


class Splash(Object):
  """Splash provides a splash screen for the application."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __screen_class__ = None
  __splash_screen__ = None

  #  Public Variables
  instance = App()  # Replaces context with app instance
  app = App()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getSplashClass(self) -> SplashClass:
    """Getter-function for the splash screen class."""
    if self.__screen_class__ is None:
      raise MissingVariable('__screen_class__', type(QSplashScreen))
    return self.__screen_class__

  def _setSplashClass(self, cls: SplashClass) -> None:
    """Setter-function for the splash screen class."""
    if self.__screen_class__ is not None:
      raise VariableNotNone('__screen_class__', self.__screen_class__)
    if not isinstance(cls, type):
      raise TypeException('cls', cls, type(QSplashScreen))
    if not issubclass(cls, QSplashScreen):
      raise SubclassException(cls, QSplashScreen)
    self.__screen_class__ = cls

  def _createSplashScreen(self, **kwargs) -> None:
    """Create the splash screen of the application."""
    if self.__splash_screen__ is not None:
      raise VariableNotNone('__splash_screen__', self.__splash_screen__)
    cls = self._getSplashClass()
    args = self.getPosArgs(THIS=QCoreApplication.instance())
    args = [arg for arg in args if arg is not cls]
    kwargs = self.getKeyArgs(THIS=QCoreApplication.instance())
    self.__splash_screen__ = cls(*args, **kwargs)

  def _getSplashScreen(self, **kwargs) -> Splash:
    """Getter-function for the splash screen."""
    if self.__splash_screen__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createSplashScreen()
      return self._getSplashScreen(_recursion=True)
    return self.__splash_screen__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, splashClass: Any) -> None:
    self._setSplashClass(splashClass)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, *args, **kwargs) -> Splash:
    """Instance getter for the main window."""
    return self._getSplashScreen()

  def __instance_set__(self, value: Splash, *args, **kwargs) -> None:
    """Instance setter for the main window."""
    raise ReadOnlyError(self.instance(), self, value)

  def __instance_delete__(self, *args, **kwargs) -> None:
    """Instance deleter for the main window."""
    raise ProtectedError(self.instance(), self, None)

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
