"""
TestAbstractApplication subclasses 'AppTest' and provides testing for the
'AbstractApplication' class in 'worQt.app' package.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QSplashScreen
from worktoy.waitaminute import TypeException

from worQt.app import AbstractApplication, App
from worQt.mixin import MixinMeta
from worQt.qtest import AppTest
from worQt.windows import AbstractWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type


class _Window(AbstractWindow):
  """A minimal main-window type for the application to build."""


class _App(App):
  """An 'App' that fixes a window type, so 'getWindowClass'/'window'
  resolve. The harness instantiates this as the process singleton."""

  __window_class__ = _Window


class TestAbstractApplication(AppTest):
  """
  Test class for 'AbstractApplication' in 'worQt.app' package.
  """

  @classmethod
  def getApplicationType(cls) -> type:
    return _App

  def test_metaclass(self, ) -> None:
    """
    Test that 'AbstractApplication' has the correct metaclass.
    """
    self.assertIsInstance(AbstractApplication, MixinMeta)

  def test_normalize_argv(self, ) -> None:
    """'_normalizeArgv' unpacks a lone non-string iterable but passes the
    splatted form and a single string through unchanged."""
    self.assertEqual(App._normalizeArgv(('a', 'b')), ['a', 'b'])
    self.assertEqual(App._normalizeArgv(('solo',)), ['solo'])
    self.assertEqual(App._normalizeArgv(([1, 2],)), [1, 2])

  def test_recursion_peek(self, ) -> None:
    """
    This method tests the recursion peek patterns as they apply to
    'AbstractApplication'.
    """
    with self.assertRaises(RecursionError):
      app = QApplication.instance()
      AbstractApplication._getSplash(app, _recursion=True)

    with self.assertRaises(RecursionError):
      app = QApplication.instance()
      AbstractApplication._getWindow(app, _recursion=True)

  def test_bad_type(self, ) -> None:
    """
    This method tests the imaginative branches where 'splash' and 'window'
    has bad types.
    """
    susSplash = object()
    with self.assertRaises(TypeException) as context:
      app = QApplication.instance()
      setattr(app, '__splash_screen__', susSplash)
      _ = getattr(app, 'splash')
    e = context.exception
    self.assertEqual(e.varName, '__splash_screen__')
    self.assertIs(e.actualObject, susSplash)
    self.assertIs(e.actualType, object)
    self.assertIn(QSplashScreen, e.expectedTypes)

    susWindow = object()
    windowClass = QApplication.instance().getWindowClass()  # noqa
    with self.assertRaises(TypeException) as context:
      app = QApplication.instance()
      setattr(app, '__main_window__', susWindow)
      _ = getattr(app, 'window')
    e = context.exception
    self.assertEqual(e.varName, '__main_window__')
    self.assertIs(e.actualObject, susWindow)
    self.assertIs(e.actualType, object)
    self.assertIn(windowClass, e.expectedTypes)
