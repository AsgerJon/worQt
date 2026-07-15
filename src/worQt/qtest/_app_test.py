"""
AppTest subclasses 'BaseTest' from 'worktoy.work_test' and provides a
special test class suitable for tests that require a running QApplication.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
import sys

from PySide6.QtCore import QCoreApplication, QTimer, QEvent
from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtWidgets import QApplication
from worktoy.desc import Field
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException
from worktoy.work_test import BaseTest

from moreworktoy.utilities import errorFmt

from . import MetaTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Type, Any

  AppType: TypeAlias = Type[QApplication]


class AppTest(BaseTest, metaclass=MetaTest):
  """
  AppTest subclasses 'BaseTest' from 'worktoy.work_test' and provides a
  special test class suitable for tests that require a running QApplication.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations from metaclass
  testMethods: Field[dict[str, Callable]]

  #  Fallback Variables
  __fallback_application__: AppType = QApplication

  #  Class Variables
  __application_type__: Optional[AppType] = None
  __time_out__: float = 30.0

  #  Private Variables
  __persistent_widgets__: Optional[set[int]] = None

  #  Public Variables
  app: Field[QApplication] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @app.GET
  def _getApp(self, ) -> QCoreApplication:
    """
    The running 'QApplication'. 'runTest' creates it before any test method
    runs, so it always exists by the time a test reads 'self.app'.
    """
    running = QApplication.instance()
    if isinstance(running, QCoreApplication):
      return running
    raise TypeException(
        'QApplication.instance()', running, QCoreApplication, QApplication
    )

  def _getPersistentWidgets(self, ) -> set[int]:
    """
    The set of top-level widgets that were open before this test started.
    'tearDown' uses it to dispose only the windows and dialogs THIS test
    opened, never any others.
    """
    return maybe(self.__persistent_widgets__, set())

  def _clearPersistentWidgets(self, ) -> None:
    """
    Clear the set of top-level widgets that were open before this test
    started. 'tearDown' uses it to dispose only the windows and dialogs THIS
    test opened, never any others.
    """
    self.__persistent_widgets__ = None

  def _freezePersistentWidgets(self, ) -> None:
    """
    Snapshot the top-level widgets that are open right now, so 'tearDown'
    disposes only the windows and dialogs THIS test opens, never any others.
    """
    self._clearPersistentWidgets()
    widgets = QApplication.topLevelWidgets()
    self.__persistent_widgets__ = {id(w) for w in widgets}

  def _disposeOpenedWidgets(self, ) -> None:
    """
    Dispose every top-level widget THIS test opened - those absent from the
    'setUp' snapshot - without firing 'closeEvent'; 'deleteLater' avoids any
    unsaved-changes prompt or geometry write that 'close' would trigger.
    Widgets already open before the test started are left alone.
    """
    preopenWidgets = self._getPersistentWidgets()
    for widget in QApplication.topLevelWidgets():
      if id(widget) not in preopenWidgets:
        widget.hide()
        widget.deleteLater()
    #  'deleteLater' only acts once a 'DeferredDelete' event is delivered,
    #  and the run loop is not re-entered between tests, so flush them now -
    #  the widgets are actually freed before the next test instead of piling
    #  up.
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QApplication.processEvents()

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
    The deadline in seconds for one run in its child process. Subclasses
    with slower suites may override.
    """
    return cls.__time_out__

  def setUp(self, ) -> None:
    """
    Snapshot the top-level widgets already open, so 'tearDown' disposes only
    the windows and dialogs THIS test opens, never any others. A test owns
    what it opens; the shared 'QApplication' lives for the whole class.
    """
    super().setUp()
    self._freezePersistentWidgets()

  def tearDown(self, ) -> None:
    """
    Dispose every top-level widget this test opened (and only those), without
    firing 'closeEvent' - 'deleteLater' avoids any unsaved-changes prompt or
    geometry write that 'close' would trigger - then let the base tear down.
    """
    super().tearDown()
    self._disposeOpenedWidgets()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _runMethod(cls, name: str) -> bool:
    """
    Runs a single collected test method on a fresh document, with
    'setUp'/'tearDown' around it. Returns True on success; on failure it
    prints the formatted exception and returns False. Only 'Exception' is
    caught, so 'KeyboardInterrupt'/'SystemExit' still abort the run.
    """
    instance = cls(name)
    try:
      instance.setUp()
      getattr(instance, name)()
    except Exception as exception:
      print('FAILED: %s.%s' % (cls.__name__, name))
      print(errorFmt(exception))
      return False
    finally:
      instance.tearDown()
    return True

  @classmethod
  def _suppressBenignQtWarnings(cls, ) -> None:
    """
    Installs a Qt message handler that drops known-benign warnings and
    forwards every other message to stderr unchanged, so real warnings stay
    visible. Each 'AppTest' runs in its own process, so this is scoped to
    the test child. The dropped tokens are:

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
  def runTest(cls, ) -> Any:
    """
    Runs every collected test method from inside a live, running event
    loop: a 'QApplication' is created, the methods are scheduled to run
    once the loop is spinning ('QTimer.singleShot'), 'app.exec' is entered,
    and the loop is quit once they finish. Returning normally counts as
    success; any failure is printed and re-raised so '__main__' reports it.
    """
    cls._suppressBenignQtWarnings()
    app = QApplication.instance() or cls.getApplicationType()(sys.argv)
    methods: dict[str, Callable[[], None]] = cls.testMethods
    failed = []

    def _runAll() -> None:
      try:
        failed.extend(n for n in methods if not cls._runMethod(n))
      finally:
        app.quit()

    QTimer.singleShot(0, _runAll)
    app.exec()
    if failed:  # pragma: no cover
      #  Only fires from a no-running-loop call against a failing class;
      #  reaching it in-suite would leak a persistent QApplication into the
      #  in-process tests. Covered indirectly by a real failing child run.
      infoSpec = '%d of %d test(s) failed: %s'
      info = infoSpec % (len(failed), len(methods), ', '.join(failed))
      raise AssertionError(info)
