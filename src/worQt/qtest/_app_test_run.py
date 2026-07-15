"""
AppTestRun runs a single test class and reports its outcome: an 'AppTest' in
a fresh, expendable interpreter under a deadline, a plain 'TestCase'
in-process with the standard unittest runner.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from io import StringIO
from signal import SIGKILL
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT
from typing import TYPE_CHECKING
import unittest

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException
from worktoy.work_test import BaseTest

from . import MetaTest, RenderMode

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Type

  from . import AppTest

  AppTestType: TypeAlias = Type[AppTest]

#  Stderr fragments the Qt platform plugin prints when it cannot start,
#  the signal the runner uses to fall back from authentic to headless.
_DISPLAY_FAILURE_TOKENS: tuple[str, ...] = (
  'no Qt platform plugin could be initialized',
  'could not connect to display',
  'Could not load the Qt platform plugin',
)


class AppTestRun(BaseObject):
  """Runs a single test class and returns '(exitCode, output)': an 'AppTest'
  in its own child process under a deadline, a plain 'BaseTest'/'TestCase'
  in-process with the standard unittest runner."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __app_test_type__: Optional[AppTestType] = None

  #  Public Variables
  appTestType: Field[AppTestType] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @appTestType.GET
  def _getAppTestType(self, ) -> AppTestType:
    value = self.__app_test_type__
    if value is None:
      raise MissingVariable(self, 'appTestType', BaseTest)
    if isinstance(value, type) and issubclass(value, BaseTest):
      return value
    raise TypeException('__app_test_type__', value, BaseTest)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, appTestType: Optional[AppTestType] = None) -> None:
    if appTestType is None:
      return
    if isinstance(appTestType, type) and issubclass(appTestType, BaseTest):
      self.__app_test_type__ = appTestType
      return
    name, value = 'appTestType', appTestType
    raise TypeException(name, value, BaseTest)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run(self, ) -> tuple[int, str]:
    """
    Launches the test class in a fresh, expendable interpreter via
    'python -m worQt.qtest' and returns '(exitCode, output)', where
    'output' is the child's combined stdout and stderr captured as text. A
    hang or a crash is contained: on timeout the child's process group is
    killed and its negative signal code is returned (-9), and a segfault
    surfaces as its own negative signal (e.g. -11).
    """
    cls = self.appTestType
    if isinstance(cls, MetaTest):
      return self._runPopen()  # an AppTest: isolate it in a child process
    return self._runPlain()  # a plain TestCase (e.g. TestTruss): run it here

  def _runPlain(self, ) -> tuple[int, str]:
    """
    Run a plain 'BaseTest'/'unittest.TestCase' subclass - one without the Qt
    'runTest' event-loop machinery - with the standard unittest runner,
    in-process. Returns '(code, output)' just like '_runPopen' so the suite
    reports it identically: '0' when every test passed, '3' otherwise.
    """
    cls = self.appTestType
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
    stream = StringIO()
    result = unittest.TextTestRunner(stream, False, 2).run(suite)
    #  Stay quiet on success like the subprocess path; the suite already
    #  prints 'RUN'/'PASS'. Only surface the runner output when it failed.
    if result.wasSuccessful():
      return 0, ''
    return 3, stream.getvalue()

  def _runPopen(self, ) -> tuple[int, str]:
    """
    Runs the class in a child process, authentic first. When the child
    dies because no windowing platform could be initialised - which Qt
    reports by aborting, uncatchable in-process, so the fallback lives
    here at the process layer - it is relaunched once in the headless
    'offscreen' mode, and the note is prepended to the captured output.
    A genuine test failure never triggers the relaunch: it is gated on
    the display-init signature and a non-zero exit.
    """
    code, output = self._launch(RenderMode.AUTHENTIC)
    if self._isDisplayFailure(code, output):
      code, output = self._launch(RenderMode.HEADLESS)
      note = 'authentic display unavailable; ran headless (offscreen)'
      output = '%s\n%s' % (note, output) if output.strip() else note
    return code, output

  def _launch(self, mode: RenderMode) -> tuple[int, str]:
    """
    Launches the class in a fresh interpreter under the given 'RenderMode'
    and returns '(exitCode, combinedOutput)'. The mode sets the child's
    'QT_QPA_PLATFORM': authentic inherits the environment's real platform,
    headless forces 'offscreen'.
    """
    cls = self.appTestType
    argv = [sys.executable, '-m', 'worQt.qtest', cls.__module__]
    if os.environ.get('WORQT_COVERAGE'):
      #  Run the child under 'coverage' when measuring. Tracing starts
      #  before 'worQt' is imported, so import-time lines (class bodies,
      #  descriptor registration) are counted; 'parallel = True' in
      #  '.coveragerc' makes each child write its own data file. A child
      #  killed on timeout or segfault flushes nothing - coverage of a
      #  failed run is neither produced nor needed.
      argv[1:1] = ['-m', 'coverage', 'run']
    baseEnv = {**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)}
    env = mode.applyEnv(baseEnv)
    child = Popen(
        argv, env=env, start_new_session=True,
        stdout=PIPE, stderr=STDOUT, text=True
    )
    try:
      output, _ = child.communicate(timeout=cls.getTimeout())
    except TimeoutExpired:  # pragma: no cover
      #  Exercising this requires a child that hangs past its deadline,
      #  which is slow and would itself break the suite under test.
      os.killpg(os.getpgid(child.pid), SIGKILL)
      output, _ = child.communicate()
    return child.returncode, output

  @staticmethod
  def _isDisplayFailure(code: int, output: str) -> bool:
    """
    Reports whether the child died because no windowing platform could be
    initialised, the signal to fall back to headless. It is gated on a
    non-zero exit so a passing authentic run is never second-guessed.
    """
    if not code:
      return False
    for token in _DISPLAY_FAILURE_TOKENS:
      if token in output:
        return True
    return False
