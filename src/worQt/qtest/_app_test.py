"""
AppTest subclasses 'BaseTest' from 'worktoy.work_test' and provides a
special test class suitable for tests that require a running QApplication.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING
import sys
import unittest

from PySide6.QtCore import QCoreApplication, QTimer, QEvent
from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtWidgets import QApplication
from worktoy.desc import Field
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import TypeException
from worktoy.work_test import BaseTest

from . import MetaTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Type, Any, Callable

  AppType: TypeAlias = Type[QApplication]
  Outcome: TypeAlias = list[tuple[bool, Any]]


class AppTest(BaseTest, metaclass=MetaTest):
  """
  AppTest subclasses 'BaseTest' from 'worktoy.work_test' and provides a
  special test class suitable for tests that require a running QApplication.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_application__: AppType = QApplication

  #  Class Variables
  __application_type__: Optional[AppType] = None
  __time_out__: float = 30.0

  #  Private Variables
  __preopen__ = None  # top-level widgets already open when this test began

  #  Public Variables
  app: Field[QApplication] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @app.GET
  def _getApp(self, ) -> QCoreApplication:
    """
    The 'app' getter returns the running 'QApplication'. 'runTest' creates
    it before any test method runs, so it always exists by the time a test
    reads 'self.app'.
    """
    running = QApplication.instance()
    if isinstance(running, QCoreApplication):
      return running
    raise TypeException(
        'QApplication.instance()', running, QCoreApplication, QApplication
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def getApplicationType(cls, ) -> AppType:
    """
    Subclasses can implement this method if they require a different
    application type than the default 'QApplication'.
    """
    fb = cls.__fallback_application__
    appType: Type[QApplication] = maybe(cls.__application_type__, fb)
    return appType

  @classmethod
  def getTimeout(cls, ) -> float:
    """
    The 'getTimeout' method returns the deadline in seconds for running
    this class in its child process, counted from when the class has
    loaded. Subclasses with slower suites may override it, or simply set
    '__time_out__'.
    """
    return cls.__time_out__

  def setUp(self, ) -> None:
    """
    The 'setUp' method snapshots the top-level widgets already open, so
    'tearDown' disposes only the windows and dialogs THIS test opens, never
    any others. A test owns what it opens; the shared 'QApplication' lives
    for the whole class. The snapshot holds the widgets themselves rather
    than their ids: a widget Qt created on its own side (a popup, a
    tooltip) may get a fresh Python wrapper on every lookup, so only a held
    reference keeps its identity stable until 'tearDown' compares against
    it.
    """
    super().setUp()
    self.__preopen__ = (*QApplication.topLevelWidgets(),)

  def tearDown(self, ) -> None:
    """
    The 'tearDown' method lets the base tear down, then disposes every
    top-level widget this test opened - even when the base fails the test,
    for instance over a failed 'subTest' block - so a failing test never
    leaves windows behind for the next one.
    """
    try:
      super().tearDown()
    finally:
      self._disposeOpened()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _disposeOpened(self, ) -> None:
    """
    The '_disposeOpened' method hides and deletes every top-level widget
    opened since 'setUp', without firing 'closeEvent' - 'deleteLater'
    avoids any unsaved-changes prompt or geometry write that 'close' would
    trigger. 'deleteLater' alone only acts once the event loop gets control
    back, which it does not between tests, so the deferred deletes are
    flushed here and the widgets are actually freed before the next test.
    """
    preopen = maybe(self.__preopen__, ())
    self.__preopen__ = None
    for widget in QApplication.topLevelWidgets():
      if widget in preopen:
        continue
      widget.hide()
      widget.deleteLater()
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QApplication.processEvents()

  @classmethod
  def _suppressBenignQtWarnings(cls, ) -> None:
    """
    The '_suppressBenignQtWarnings' method installs a Qt message handler
    that drops known-benign warnings and forwards every other message to
    stderr unchanged, so real warnings stay visible. Each 'AppTest' runs
    in its own process, so this is scoped to the test child. The dropped
    tokens are:

    - 'propagateSizeHints' - emitted by the 'offscreen' QPA plugin when a
      top-level window is shown.
    - 'event loop is already running' - emitted when a test drives an
      exec-based path (such as 'App.__exit__') while the harness already
      owns the running loop; the nested 'exec' returns at once by design.
    """
    benign = ('propagateSizeHints', 'event loop is already running',)

    def handler(msgType: Any, context: Any, message: str) -> None:
      for token in benign:
        if token in message:
          return
      sys.stderr.write('%s\n' % message)

    qInstallMessageHandler(handler)

  @classmethod
  def _callInLoop(cls, app: Any, call: Callable, outcome: Outcome) -> None:
    """
    The '_callInLoop' method is what the event loop runs once it spins: it
    records what 'call' returned, or whatever it raised, and quits the
    loop either way. An exception must not escape from here - Qt would
    print it and carry on, 'exec' would return normally, and a broken run
    would be reported as a pass.
    """
    try:
      outcome.append((True, call()))
    except BaseException as exception:
      outcome.append((False, exception))
    finally:
      app.quit()

  @classmethod
  def runInLoop(cls, call: Callable) -> Any:
    """
    The 'runInLoop' method calls 'call' from inside a live, running event
    loop and returns its value, which is what lets test methods rely on
    queued signals, timers and 'QTest.qWait' exactly as the application
    would. Whatever 'call' raised is raised again here, after the loop has
    stopped. It creates the 'QApplication' if none exists yet; it must not
    be called while a loop is already running.
    """
    cls._suppressBenignQtWarnings()
    app = QApplication.instance() or cls.getApplicationType()(sys.argv)
    outcome = []
    QTimer.singleShot(0, partial(cls._callInLoop, app, call, outcome))
    app.exec()
    if not outcome:
      infoSpec = """The event loop of '%s' stopped before its tests ran!"""
      raise RuntimeError(textFmt(infoSpec % cls.__name__))
    returned, value = outcome[0]
    if returned:
      return value
    raise value

  @classmethod
  def runTest(cls, ) -> unittest.TestResult:
    """
    The 'runTest' method runs every collected test method of the class
    inside a live event loop through the standard unittest machinery, and
    returns the 'TestResult'. Being standard is the point: 'setUpClass',
    'addCleanup', 'skipTest', 'expectedFailure' and a failing 'tearDown'
    all behave exactly as they do in any other unittest suite.
    """
    suite = unittest.TestSuite([cls(name) for name in cls.testMethods])
    runner = unittest.TextTestRunner(sys.stderr, True, 2)
    return cls.runInLoop(partial(runner.run, suite))
