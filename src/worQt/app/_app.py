"""
App is the worQt application: a 'QApplication' fused with worktoy (via
'ApplicationMixin') so descriptor and overload machinery are available
alongside Qt. It owns the lazily-built, app-scoped handles every worQt app
shares - the return code, the splash screen and the main window - routes
slot/event-filter exceptions to 'handleException', guards exit on unsaved
changes, keeps the window title's unsaved marker current, and runs the Qt
event loop as a context manager.

The window *type* is app-specific, so a concrete subclass declares it with
'__window_class__'. Because the 'QApplication' is reachable from any
'MixinBase' via 'self.app', 'self.app.window' reaches these from anywhere in
the object graph. Usage:

    with MyApp(*sys.argv) as app:
      app.window.show()
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QSplashScreen, QMessageBox
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import MissingVariable, TypeException

from . import ApplicationMixin

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional

  from PySide6.QtCore import QObject, QEvent
  from PySide6.QtWidgets import QMainWindow


class App(ApplicationMixin):
  """
  The worQt application. Owns the shared lazily-built handles ('returnCode',
  'splash', 'window'), the exception hook ('handleException'), the exit guard
  ('hasUnsavedChanges'/'saveChanges'/'confirmExit') and the title star, and
  runs the Qt event loop on a clean exit as a context manager:

      with MyApp(*sys.argv) as app:
        app.window.show()

  A concrete app subclasses this, sets '__window_class__', and overrides the
  hooks it needs.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = None  # the QMainWindow subclass built for 'window'
  __fallback_title_interval__ = 500  # ms; poll interval for the title star
  __unsaved_marker__ = ' *'  # appended to the window title when dirty

  #  Private Variables
  __return_code__ = None  # the exec() exit code, set on a clean __exit__
  __splash_screen__ = None  # the lazily-built splash screen
  __main_window__ = None  # the lazily-built main window
  __title_timer__ = None  # polls 'hasUnsavedChanges' to drive the title star

  #  Public Variables
  returnCode: Field[int] = Field()
  splash: Field[QSplashScreen] = Field()
  window: Field[QMainWindow] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getWindowClass(self, ) -> type:
    """The 'QMainWindow' subclass this app builds for 'window'. A concrete
    app sets '__window_class__'; reading 'window' without it raises."""
    if self.__window_class__ is None:
      raise MissingVariable(self, '__window_class__', type)
    return self.__window_class__

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
    self._startTitleWatch()

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

  @returnCode.GET
  def _getReturnCode(self, ) -> int:
    return maybe(self.__return_code__, 1)  # 1 indicating error

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _normalizeArgv(args: tuple) -> list:
    """Normalise the argv into the single 'list[str]' 'QApplication' wants.
    Both the splatted form ('App(*sys.argv)') and a single iterable
    ('App(sys.argv)', as the 'qtest' harness builds an
    '__application_type__') are accepted: a lone non-string iterable is
    unpacked into the argv list."""
    if len(args) == 1 and isinstance(args[0], Iterable):
      if not isinstance(args[0], str):
        return [*args[0], ]
    return [*args, ]

  def __init__(self, *args) -> None:
    """Normalise the constructor args (see '_normalizeArgv') before handing
    them to 'QApplication'."""
    super().__init__(self._normalizeArgv(args))

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  EXIT GUARD   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def hasUnsavedChanges(self) -> bool:
    """Hook: does the application hold unsaved changes? The default 'False'
    means a plain app never blocks exit. A concrete app overrides this to
    report its document state, e.g. 'return self.window.document.isDirty()'."""
    return False

  def saveChanges(self) -> bool:
    """Hook: persist the unsaved changes and report whether it succeeded. The
    default is a no-op success. A concrete app overrides this to actually
    save; returning 'False' - the user cancelled a Save dialog, say - aborts
    the exit."""
    return True

  def confirmExit(self) -> bool:
    """Consulted before the application exits, by the main window's
    'closeEvent'. With no unsaved changes it returns 'True' at once;
    otherwise it offers Save / Discard / Cancel and returns 'True' to proceed
    (saved or discarded) or 'False' to abort the exit. This is the single
    place the exit guard lives, so no window or action reimplements it."""
    if not self.hasUnsavedChanges():
      return True
    answer = QMessageBox.warning(
        self.window, 'Unsaved changes',
        'There are unsaved changes. Save before exiting?',
        QMessageBox.StandardButton.Save
        | QMessageBox.StandardButton.Discard
        | QMessageBox.StandardButton.Cancel)
    if answer == QMessageBox.StandardButton.Save:
      return self.saveChanges()
    if answer == QMessageBox.StandardButton.Discard:
      return True
    return False  # Cancel

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TITLE STAR   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _startTitleWatch(self) -> None:
    """Begin keeping the window title's unsaved-changes marker current.
    There is no generic 'dirty changed' signal, so the base app falls back
    to polling 'hasUnsavedChanges' on a timer at '__fallback_title_interval__'
    milliseconds. Started once, when the window is built."""
    if self.__title_timer__ is not None:
      return
    self.__title_timer__ = QTimer(self)
    self.__title_timer__.setInterval(self.__fallback_title_interval__)
    self.__title_timer__.timeout.connect(self._refreshTitle)
    self.__title_timer__.start()

  def _refreshTitle(self) -> None:
    """Append '__unsaved_marker__' to the window title when there are unsaved
    changes and strip it when there are none. Idempotent: it always rebuilds
    from the marker-free base title, so the marker never accumulates."""
    window = self.__main_window__
    if window is None:
      return
    marker = self.__unsaved_marker__
    base = window.windowTitle()
    if base.endswith(marker):
      base = base[:-len(marker)]
    target = '%s%s' % (base, marker) if self.hasUnsavedChanges() else base
    if target != window.windowTitle():
      window.setWindowTitle(target)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __enter__(self) -> App:
    return self

  def __exit__(self, _, exception: Optional[BaseException], __) -> None:
    """Run the Qt event loop on a clean exit. If the with-body raised, skip
    the loop and let the exception propagate."""
    if exception is None:
      self.__return_code__ = self.exec()
