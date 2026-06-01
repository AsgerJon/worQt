"""
App is the concrete 'worQt' application class. It exposes a context
manager protocol: '__enter__' returns the application instance and
'__exit__' runs the Qt event loop.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING
import sys

from PySide6.QtWidgets import QSplashScreen
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException

from . import AbstractApplication
from ..window import MainWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Union, TypeAlias


class App(AbstractApplication):
  """
  Concrete 'worQt' application. Supports use as a context manager:

      with App(*sys.argv) as app:
        app.splash.show()
        app.window.show()

  '__exit__' runs the Qt event loop and blocks until the application
  quits. If the with-body raises, the event loop is not started and
  the exception propagates.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __return_code__: Optional[int] = None
  __splash_screen__: Optional[QSplashScreen] = None
  __main_window__: Optional[MainWindow] = None

  #  Public Variables
  returnCode: Field[int] = Field()
  splash: Field[QSplashScreen] = Field()
  window: Field[MainWindow] = Field()

  #  Virtual Variables

  def _createSplash(self, ) -> None:
    self.__splash_screen__ = QSplashScreen()

  @splash.GET
  def _getSplash(self, **kwargs) -> QSplashScreen:
    """Lazily construct and return the splash screen."""
    if self.__splash_screen__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createSplash()
      return self._getSplash(_recursion=True)
    if isinstance(self.__splash_screen__, QSplashScreen):
      return self.__splash_screen__
    name, value = '__splash_screen__', self.__splash_screen__
    raise TypeException(name, value, QSplashScreen)

  def _createWindow(self, ) -> None:
    self.__main_window__ = MainWindow()

  @window.GET
  def _getWindow(self, **kwargs) -> MainWindow:
    """Lazily construct and return the main window."""
    if self.__main_window__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWindow()
      return self._getWindow(_recursion=True)
    if isinstance(self.__main_window__, MainWindow):
      return self.__main_window__
    name, value = '__main_window__', self.__main_window__
    raise TypeException(name, value, MainWindow)

  @returnCode.GET
  def _getReturnCode(self) -> int:
    return maybe(self.__return_code__, 1)  # 1 indicating error

  def __init__(self, *args: str) -> None:
    """
    Construct the application. Positional arguments are forwarded to
    'QApplication' as the argv list. Typical usage is
    'App(*sys.argv)'.
    """
    super().__init__([*args, ])

  def __enter__(self) -> App:
    return self

  def __exit__(self, _, exception: Optional[BaseException], __) -> None:
    """
    Run the Qt event loop on normal exit. If the with-body raised,
    skip the event loop and let the exception propagate.
    """
    if exception is None:
      self.__return_code__ = self.exec()
