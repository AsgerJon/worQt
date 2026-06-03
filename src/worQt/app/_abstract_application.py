"""
AbstractApplication is the abstract base class for worQt applications.
It is a QApplication subclass built with MixinMeta so that worktoy
descriptor and overload machinery are available alongside Qt.

It also owns the lazily-built, app-scoped handles every worQt app shares:
the return code, the splash screen, the main window, and the application
settings. The window and settings *types* are app-specific, so a concrete
subclass declares them with '__window_class__' / '__settings_class__'; the
lazy construction, type-checking and access all live here. Because the
'QApplication' instance is reachable from any 'MixinBase' via 'self.app',
'self.app.settings' / 'self.app.window' reach these from anywhere in the
object graph.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QSplashScreen
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import MissingVariable, TypeException

from . import ApplicationMixin
from ..settings import Settings

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtCore import QObject, QEvent
  from PySide6.QtWidgets import QMainWindow


class AbstractApplication(ApplicationMixin):
  """
  Abstract base for 'worQt' applications. Owns the shared, lazily-built app
  handles ('returnCode', 'splash', 'window', 'settings'); a concrete app
  sets '__window_class__' (and optionally '__settings_class__') and adds
  behaviour by overriding 'handleException'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = None  # the QMainWindow subclass built for 'window'
  __settings_class__ = None  # the Settings subclass built for 'settings'

  #  Private Variables
  __return_code__ = None  # the exec() exit code, set on a clean __exit__
  __splash_screen__ = None  # the lazily-built splash screen
  __main_window__ = None  # the lazily-built main window
  __app_settings__ = None  # the lazily-built application settings

  #  Public Variables
  returnCode: Field[int] = Field()
  splash: Field[QSplashScreen] = Field()
  window: Field[QMainWindow] = Field()
  settings: Field[Settings] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getWindowClass(self, ) -> type:
    """The 'QMainWindow' subclass this app builds for 'window'. A concrete
    app sets '__window_class__'; reading 'window' without it raises."""
    if self.__window_class__ is None:
      raise MissingVariable(self, '__window_class__', type)
    return self.__window_class__

  def getSettingsClass(self, ) -> type:
    """The 'Settings' subclass this app builds for 'settings', defaulting
    to the generic 'Settings'."""
    return maybe(self.__settings_class__, Settings)

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
    self.__main_window__ = self.getWindowClass()()

  @window.GET
  def _getWindow(self, **kwargs) -> QMainWindow:
    """Lazily construct and return the app's main window."""
    windowClass = self.getWindowClass()
    if self.__main_window__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWindow()
      return self._getWindow(_recursion=True)
    if isinstance(self.__main_window__, windowClass):
      return self.__main_window__
    name, value = '__main_window__', self.__main_window__
    raise TypeException(name, value, windowClass)

  def _createSettings(self, ) -> None:
    self.__app_settings__ = self.getSettingsClass()()

  @settings.GET
  def _getSettings(self, **kwargs) -> Settings:
    """Lazily construct and return the application settings (the app's
    settings class, the generic 'Settings' by default)."""
    settingsClass = self.getSettingsClass()
    if self.__app_settings__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createSettings()
      return self._getSettings(_recursion=True)
    if isinstance(self.__app_settings__, settingsClass):
      return self.__app_settings__
    name, value = '__app_settings__', self.__app_settings__
    raise TypeException(name, value, settingsClass)

  @returnCode.GET
  def _getReturnCode(self, ) -> int:
    return maybe(self.__return_code__, 1)  # 1 indicating error

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def notify(self, receiver: QObject, event: QEvent) -> bool:
    """
    Wrap Qt event delivery so exceptions raised inside slots and
    event filters are routed to 'handleException'. Only 'Exception'
    subclasses are intercepted; 'BaseException' subclasses such as
    'KeyboardInterrupt' and 'SystemExit' propagate unchanged.
    """
    try:
      out = super().notify(receiver, event)
    except Exception as exception:
      handled = self.handleException(exception, receiver, event)
      if handled is None:
        return False
      return True if handled else False
    else:
      return True if out else False

  def handleException(
      self,
      exc: Exception,
      receiver: QObject = None,
      event: QEvent = None,
  ) -> bool | None:
    """
    Hook for exceptions raised during event delivery. The default
    implementation is a no-op; concrete subclasses override to log,
    swallow, exit, or re-raise.
    """
