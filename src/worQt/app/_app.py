"""App class provides the base application class. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from warnings import warn

from PySide6.QtCore import QObject, QThread, QCoreApplication
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow
from worktoy.attr import Field
from worktoy.parse import maybe
from worktoy.text import typeMsg

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from .. import Shiboken


class _Deps:
  """Private class listing objects for import. """
  __imported_objects__ = [
      QObject,
      QCoreApplication,
      QApplication,
      QAction,
      QWidget,
      QMainWindow,
      QThread,
      maybe,
      typeMsg,
      Field,
  ]


class App(QApplication):
  """The 'App' class is a subclass of QApplication that provides
  additional functionality for creating and managing a Qt application.
  """

  __main_fallback__ = QMainWindow
  __main_cls__ = None
  __main_window__ = None

  __shutdown_level__ = None
  __registered_threads__ = None

  hasRegisteredThreads = Field()
  hasRunningThreads = Field()

  @classmethod
  def _getMainWindowClass(cls, **kwargs) -> Shiboken:
    """Returns the main window class for the application."""
    return maybe(cls.__main_cls__, cls.__main_fallback__)

  def _createMainWindow(self, ) -> None:
    """Creator function for the main window instance. """
    if self.__main_window__ is not None:
      e = """Main window instance already created!"""
      raise RuntimeError(e)
    cls = self._getMainWindowClass()
    self.__main_window__ = cls()

  def _getMainWindow(self, **kwargs) -> QMainWindow:
    """Returns the main window instance for the application."""
    if self.__main_window__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMainWindow()
      return self._getMainWindow(_recursion=True)
    if isinstance(self.__main_window__, QMainWindow):
      return self.__main_window__
    name, expType = '__main_window__', QMainWindow
    raise TypeError(typeMsg(name, self.__main_window__, expType))

  def _getShutdownLevel(self, ) -> int:
    """Returns the shutdown level for the application."""
    return maybe(self.__shutdown_level__, 0)

  def _incrementShutdownLevel(self, ) -> None:
    """Increments the shutdown level for the application."""
    self.__shutdown_level__ = self._getShutdownLevel() + 1

  @hasRegisteredThreads.GET
  def hasRegisteredThreads(self, ) -> bool:
    """Returns True if there are registered threads."""
    return True if self._getRegisteredThreads() else False

  @hasRunningThreads.GET
  def hasRunningThreads(self, ) -> bool:
    """Returns True if there are running threads."""
    return True if self._getRunningThreads() else False

  def __init__(self, *args, **kwargs) -> None:
    """Constructor for the App class."""
    posArgs = []
    allArgs = [*args, ]
    while allArgs:
      arg = allArgs.pop(0)
      if isinstance(arg, type):
        self.__main_cls__ = arg
        posArgs = [*posArgs, *allArgs]
        break
      posArgs.append(arg)
    else:
      w = """No main window class provided, falling back at QMainWindow!"""
      warn(w)
    QApplication.__init__(self, *posArgs, **kwargs)

  def _getRegisteredThreads(self, ) -> list[QThread]:
    """Returns the list of registered threads."""
    return maybe(self.__registered_threads__, [])

  def _getRunningThreads(self, ) -> list[QThread]:
    """Returns the list of running threads."""
    out = []
    for thread in self._getRegisteredThreads():
      if thread.isRunning():
        out.append(thread)
    return out

  def _registerThread(self, thread: QThread) -> None:
    """Adds a thread to the list of running threads."""
    existing = self._getRegisteredThreads()
    self.__registered_threads__ = [*existing, thread, ]

  def _requestStopThreads(self, ) -> None:
    """This method requests all threads to stop. When this method is
    called, threads are allowed to be running, but should stop upon
    receiving notification. """
    raise NotImplementedError

  def _stopRunningThreads(self, ) -> None:
    """Stops all running threads. Any thread running at this point will
    result in a RuntimeError. """
    raise NotImplementedError

  def _killRunningThreads(self, ) -> None:
    """Kills all running threads. All threads running at this point will
    receive SIGKILL. If this method is called it indicates that a thread
    is failing to respond to both normal and to stop requests. """
    raise NotImplementedError

  def quit(self, ) -> None:
    """Overrides the quit method to stop all running threads."""
    e = None
    if self.hasRunningThreads:
      level = self._getShutdownLevel()
      try:
        if not level:
          self._requestStopThreads()
        elif level == 1:
          self._stopRunningThreads()
        elif level == 2:
          self._killRunningThreads()
      except NotImplementedError as notImplementedError:
        e = notImplementedError
        return QCoreApplication.quit()
      else:
        self._incrementShutdownLevel()
      finally:
        if e is None:
          self.quit()
    else:
      return QCoreApplication.quit()

  def exec_(self, ) -> int:
    """Overrides the exec_ method to start the application."""
    self._getMainWindow().show()
    return int(QCoreApplication.exec_(self))
