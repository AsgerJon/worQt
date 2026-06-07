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
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException
from worktoy.work_test import BaseTest

from . import MetaTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Type

  from . import AppTest

  AppTestType: TypeAlias = Type[AppTest]


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
      raise MissingVariable(self, 'appTestType', AppTestType)
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
    cls = self.appTestType
    argv = [sys.executable, '-m', 'worQt.qtest', cls.__module__]
    env = {**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)}
    child = Popen(
        argv, env=env, start_new_session=True,
        stdout=PIPE, stderr=STDOUT, text=True
    )
    try:
      output, _ = child.communicate(timeout=cls.getTimeout())
    except TimeoutExpired:
      os.killpg(os.getpgid(child.pid), SIGKILL)
      output, _ = child.communicate()
    return child.returncode, output
