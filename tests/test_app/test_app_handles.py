"""
TestApp drives the shared application handles on 'AbstractApplication' and
the context-manager protocol on 'App'. The harness instantiates the class's
'__application_type__' as the process singleton, so '_App' (an 'App'
subclass that fixes a window type) becomes 'self.app', making 'splash',
'window', 'getWindowClass', 'returnCode', 'notify' and the
'__enter__'/'__exit__' loop reachable.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget, QSplashScreen
from worktoy.waitaminute import MissingVariable

from worQt.app import App
from worQt.qtest import AppTest
from worQt.windows import AbstractWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _Win(AbstractWindow):
  """A minimal main-window type for the app to build."""


class _App(App):
  """An 'App' that fixes a window type and a configurable exception
  result. 'AbstractApplication.__init__' already accepts the harness's
  single-argv-list call, so no constructor override is needed."""

  __window_class__ = _Win
  __handler_result__ = None

  def handleException(self, exc, receiver=None, event=None) -> Any:
    return self.__handler_result__


class _Boom(QWidget):
  """A widget whose 'event' always raises, to drive 'notify's except
  path."""

  def event(self, event: QEvent) -> bool:
    raise RuntimeError('boom')


class TestApp(AppTest):
  """Covers the 'AbstractApplication' handles and 'App' lifecycle."""

  __application_type__ = _App

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HANDLES   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_return_code_default(self) -> None:
    """Before any clean exit, 'returnCode' is the error default '1'."""
    self.assertEqual(self.app.returnCode, 1)

  def test_splash_lazy_and_cached(self) -> None:
    """'splash' builds a 'QSplashScreen' once and caches it."""
    self.assertIsInstance(self.app.splash, QSplashScreen)
    self.assertIs(self.app.splash, self.app.splash)

  def test_window_lazy_and_cached(self) -> None:
    """'window' builds the configured window type once and caches it."""
    self.assertIsInstance(self.app.window, _Win)
    self.assertIs(self.app.window, self.app.window)

  def test_window_class(self) -> None:
    """'getWindowClass' returns the configured window type."""
    self.assertIs(self.app.getWindowClass(), _Win)

  def test_window_class_missing(self) -> None:
    """With no window type set, 'getWindowClass' raises."""
    type(self.app).__window_class__ = None
    try:
      with self.assertRaises(MissingVariable):
        self.app.getWindowClass()
    finally:
      type(self.app).__window_class__ = _Win

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFY   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_notify_normal(self) -> None:
    """Delivering an event to a well-behaved receiver returns a bool."""
    result = self.app.notify(QWidget(), QEvent(QEvent.Type.User))
    self.assertIsInstance(result, bool)

  def test_notify_exception_unhandled(self) -> None:
    """A raising receiver with a 'None' handler result yields 'False'."""
    self.app.__handler_result__ = None
    out = self.app.notify(_Boom(), QEvent(QEvent.Type.User))
    self.assertFalse(out)

  def test_notify_exception_handled(self) -> None:
    """A non-'None' handler result drives the truthy/falsy branch."""
    self.app.__handler_result__ = True
    self.assertTrue(self.app.notify(_Boom(), QEvent(QEvent.Type.User)))
    self.app.__handler_result__ = False
    self.assertFalse(self.app.notify(_Boom(), QEvent(QEvent.Type.User)))
    self.app.__handler_result__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONTEXT MANAGER  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_enter_returns_self(self) -> None:
    """'__enter__' returns the application."""
    self.assertIs(self.app.__enter__(), self.app)

  def test_exit_skips_loop_on_exception(self) -> None:
    """An exception in the with-body skips the event loop."""
    before = self.app.returnCode
    self.app.__exit__(None, RuntimeError('boom'), None)
    self.assertEqual(self.app.returnCode, before)

  def test_exit_runs_loop_on_clean_exit(self) -> None:
    """A clean exit runs 'self.exec()' and records its return code. Inside
    the harness's already-running loop 'exec()' returns immediately, so
    this neither blocks nor schedules a quit. Defined last so the code it
    records does not disturb 'test_return_code_default'."""
    self.app.__exit__(None, None, None)
    self.assertIsInstance(self.app.returnCode, int)
