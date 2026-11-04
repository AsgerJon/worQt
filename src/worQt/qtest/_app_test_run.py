"""
AppTestRun runs one test class in a fresh, expendable interpreter and
reports how that run ended. A hang, a segfault or a crashing import then
costs one reported status instead of the whole suite, and a test class can
never leak state into the next one. Every class runs this way, an 'AppTest'
inside a live event loop and a plain 'BaseTest'/'TestCase' without one.

The class holds both halves of the protocol between the suite and a child:
'run' (in the suite's process) starts and supervises the child, and
'runChild' (in the child, reached through 'python -m worQt.qtest --child
<module>') loads and runs the class. The child loads its module under a
load deadline, then reports the class's own deadline back through a pipe;
the clock for that deadline starts there. Before either deadline expires,
'faulthandler' in the child writes the stack of every thread to the output,
so a TIMEOUT shows where the test was stuck; a segfault does the same.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import faulthandler
import os
import select
import sys
import traceback
import unittest
from importlib import import_module
from inspect import getmembers, isclass
from signal import SIGKILL
from subprocess import Popen, TimeoutExpired, STDOUT
from tempfile import TemporaryFile
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt
from worktoy.waitaminute import SubclassException

from . import MetaTest, RenderMode

if TYPE_CHECKING:  # pragma: no cover
  from typing import IO, TypeAlias, Type

  TestType: TypeAlias = Type[unittest.TestCase]


class AppTestRun(BaseObject):
  """
  AppTestRun runs the test class of one module in its own child process
  and returns '(exitCode, output)'. See the module docstring for the
  protocol between the suite and the child.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __pass_code__: int = 0  # every test passed (or was skipped)
  __error_code__: int = 2  # the class could not be loaded or run
  __fail_code__: int = 3  # the class ran and a test failed
  __load_time_out__: float = 60.0  # seconds to import and resolve a class
  __default_time_out__: float = 30.0  # for a class with no '__time_out__'
  __kill_grace__: float = 2.0  # seconds for the stack dump before the kill
  __handshake_variable__: str = 'WORQT_QTEST_FD'
  __child_variable__: str = 'WORQT_QTEST_CHILD'  # set in every child
  #  What Qt prints when it cannot start a windowing platform
  __display_failure_tokens__: tuple[str, ...] = (
    'no Qt platform plugin could be initialized',
    'could not connect to display',
    'Could not load the Qt platform plugin',
  )
  __headless_note__: str = """authentic display unavailable; ran headless
  (offscreen)"""

  #  Public Variables
  testName = AttriBox[str]()
  timedOut = AttriBox[bool](False)
  deadline = AttriBox[float](0.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, testName: str) -> None:
    self.testName = testName

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT SIDE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run(self, ) -> tuple[int, str]:
    """
    The 'run' method runs the test module 'testName' in a child process
    and returns '(exitCode, output)', the output being everything the
    child printed, in order. The exit code is negative when a signal
    ended the child: -11 for a segfault, -9 when it was killed. A kill
    for overrunning a deadline also sets 'timedOut' and 'deadline'.

    The child runs on the real display first. When it dies because no
    windowing platform could be started - Qt aborts, which nothing
    in-process can catch, so the fallback lives here - it runs once more
    headless ('offscreen'), with a note heading the output. A genuine
    test failure never triggers that second run.
    """
    code, output = self._launch(RenderMode.AUTHENTIC)
    if not self._isDisplayFailure(code, output):
      return code, output
    self.timedOut, self.deadline = False, 0.0
    code, output = self._launch(RenderMode.HEADLESS)
    return code, '%s\n%s' % (textFmt(self.__headless_note__), output)

  @classmethod
  def _isDisplayFailure(cls, code: int, output: str) -> bool:
    """
    The '_isDisplayFailure' method tells whether a child died because Qt
    could not start a windowing platform. A child that exited cleanly is
    never second-guessed.
    """
    if not code:
      return False
    for token in cls.__display_failure_tokens__:
      if token in output:
        return True
    return False

  def _launch(self, mode: RenderMode) -> tuple[int, str]:
    """
    The '_launch' method runs the child once, under 'mode', and returns
    '(exitCode, output)'.
    """
    readEnd, writeEnd = os.pipe()
    try:
      with TemporaryFile() as log:
        child = self._spawn(log, writeEnd, mode)
        self._supervise(child, readEnd)
        log.seek(0)
        output = log.read().decode('utf-8', 'replace')
    finally:
      os.close(readEnd)
    return child.returncode, output

  def _childArgv(self, ) -> list[str]:
    """
    The '_childArgv' method returns the command line of the child. With
    'WORQT_COVERAGE' set, the child runs under 'coverage', which starts
    tracing before 'worQt' is imported, so import-time lines count too.
    """
    argv = [sys.executable, '-m', 'worQt.qtest', '--child', self.testName]
    if os.environ.get('WORQT_COVERAGE'):
      argv[1:1] = ['-m', 'coverage', 'run']
    return argv

  def _childEnv(self, writeEnd: int, mode: RenderMode) -> dict[str, str]:
    """
    The '_childEnv' method returns the environment of the child. Unbuffered
    output keeps the order of what the child prints and loses nothing when
    it is killed; 'faulthandler' turns a segfault into a stack trace from
    the first line of the interpreter on. The child marker tells a suite
    running inside a test (as the harness's own tests do) that it is not
    the top-level run, so it leaves 'latest.log' alone. 'mode' decides
    the Qt platform: the real one, or 'offscreen'.
    """
    env = mode.applyEnv(dict(os.environ))
    env['PYTHONPATH'] = os.pathsep.join(sys.path)
    env['PYTHONUNBUFFERED'] = '1'
    env['PYTHONFAULTHANDLER'] = '1'
    env[self.__handshake_variable__] = str(writeEnd)
    env[self.__child_variable__] = '1'
    return env

  def _spawn(self, log: IO, writeEnd: int, mode: RenderMode) -> Popen:
    """
    The '_spawn' method starts the child in a session of its own, so a
    kill takes down anything it started too. The output goes to a file
    rather than a pipe: a pipe nobody drains while waiting for the
    handshake would fill and stall a talkative child into a false TIMEOUT.
    """
    try:
      return Popen(
          self._childArgv(),
          stdout=log,
          stderr=STDOUT,
          env=self._childEnv(writeEnd, mode),
          start_new_session=True,
          pass_fds=(writeEnd,),
      )
    finally:
      os.close(writeEnd)  # the child holds its own copy

  def _supervise(self, child: Popen, readEnd: int) -> None:
    """
    The '_supervise' method waits for the child to finish, killing it when
    it overruns. Loading must finish within the load deadline; then the
    child reports the class deadline, and the clock restarts for it. If
    the pipe closes without a report, the child is already on its way out
    (it failed to load, or crashed).
    """
    grace = self.__kill_grace__
    loadLimit = self.__load_time_out__ + grace
    ready, _, _ = select.select([readEnd], [], [], loadLimit)
    if not ready:
      return self._kill(child, self.__load_time_out__)
    message = os.read(readEnd, 64)
    if not message:
      return self._await(child, loadLimit, self.__load_time_out__)
    self.deadline = float(message.decode('ascii'))
    return self._await(child, self.deadline + grace, self.deadline)

  def _await(self, child: Popen, limit: float, deadline: float) -> None:
    """
    The '_await' method waits up to 'limit' seconds for the child to exit,
    and kills it for overrunning 'deadline' if it does not.
    """
    try:
      child.wait(limit)
    except TimeoutExpired:
      self._kill(child, deadline)

  def _kill(self, child: Popen, deadline: float) -> None:
    """
    The '_kill' method kills the child's whole process group and records
    that it overran 'deadline'.
    """
    self.timedOut = True
    self.deadline = deadline
    try:
      os.killpg(os.getpgid(child.pid), SIGKILL)
    except ProcessLookupError:  # pragma: no cover  # exited just in time
      pass
    child.wait()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CHILD SIDE   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def runChild(cls, *names: str) -> int:
    """
    The 'runChild' method is the child half of the protocol: it loads the
    test class of the single module named, runs it, and returns the exit
    code the suite decodes. Every failure, including one while loading, is
    printed with its traceback before the code is returned, so the output
    always says why.
    """
    faulthandler.enable()
    faulthandler.dump_traceback_later(cls.__load_time_out__)
    try:
      return cls._loadAndRun(*names)
    finally:
      faulthandler.cancel_dump_traceback_later()

  @classmethod
  def _loadAndRun(cls, *names: str) -> int:
    """
    The '_loadAndRun' method tells a class that cannot even be loaded (an
    error code) apart from one that ran and failed (a fail code).
    """
    try:
      testClass = cls._loadClass(*names)
    except Exception:
      traceback.print_exc()
      return cls.__error_code__
    cls._handshake(cls._classTimeout(testClass))
    try:
      result = cls._execute(testClass)
    except Exception:
      traceback.print_exc()
      return cls.__error_code__
    if result.wasSuccessful():
      return cls.__pass_code__
    return cls.__fail_code__

  @classmethod
  def _loadClass(cls, *names: str) -> TestType:
    """
    The '_loadClass' method resolves the one module name given to its test
    class, refusing a class with nothing to run: a class whose methods are
    all misnamed would otherwise pass without testing anything.
    """
    if len(names) != 1:
      infoSpec = """A child runs exactly one test module, but received %d
      names: '%s'"""
      raise ValueError(textFmt(infoSpec % (len(names), ', '.join(names))))
    testClass = cls.getNamed(*names)
    if cls.testNames(testClass):
      return testClass
    infoSpec = """The test class '%s' has no test methods to run! Test
    methods are named 'test*' (or also 'run*' on an 'AppTest')."""
    raise LookupError(textFmt(infoSpec % testClass.__name__))

  @classmethod
  def getNamed(cls, name: str) -> TestType:
    """
    The 'getNamed' method imports the module 'name' and returns the single
    test class it defines: a class named 'Run*' or 'Test*' whose
    '__module__' is that module. Classes the module merely imports - such
    as 'unittest.TestCase' itself - do not count.
    """
    module = import_module(name)
    found = []
    for objName, obj in getmembers(module, isclass):
      if not objName.startswith(('Run', 'Test')):
        continue
      if obj.__module__ != module.__name__:
        continue
      if not issubclass(obj, unittest.TestCase):
        raise SubclassException(obj, unittest.TestCase)
      found.append(obj)
    if len(found) == 1:
      return found[0]
    if found:
      infoSpec = """Found multiple test classes in the module '%s': %s!"""
      clsNames = ', '.join(obj.__name__ for obj in found)
      raise RuntimeError(textFmt(infoSpec % (name, clsNames)))
    infoSpec = """Found no 'Run*' or 'Test*' class in the module '%s'!"""
    raise LookupError(textFmt(infoSpec % name))

  @staticmethod
  def testNames(testClass: TestType) -> tuple[str, ...]:
    """
    The 'testNames' method returns the names of the test methods of
    'testClass': the collected 'test*'/'run*' methods of an 'AppTest',
    inherited ones included, or the 'test*' methods unittest would load
    from a plain 'TestCase'.
    """
    if isinstance(testClass, MetaTest):
      return (*testClass.testMethods,)
    loader = unittest.defaultTestLoader
    return (*loader.getTestCaseNames(testClass),)

  @classmethod
  def _classTimeout(cls, testClass: TestType) -> float:
    """
    The '_classTimeout' method returns the deadline of 'testClass': its
    'getTimeout()' when it has one (every 'AppTest' does), else its
    '__time_out__', else the default.
    """
    getTimeout = getattr(testClass, 'getTimeout', None)
    if callable(getTimeout):
      return float(getTimeout())
    fallback = cls.__default_time_out__
    return float(getattr(testClass, '__time_out__', fallback))

  @classmethod
  def _handshake(cls, deadline: float) -> None:
    """
    The '_handshake' method arms the stack dump for 'deadline', then tells
    the supervising suite the deadline, which starts its clock. Run by
    hand there is no suite to tell, but the dump is armed all the same.
    """
    faulthandler.dump_traceback_later(deadline)
    fd = os.environ.pop(cls.__handshake_variable__, None)
    if fd is None:
      return
    os.write(int(fd), ('%r\n' % deadline).encode('ascii'))
    os.close(int(fd))

  @classmethod
  def _execute(cls, testClass: TestType) -> unittest.TestResult:
    """
    The '_execute' method runs 'testClass' with the standard unittest
    runner - an 'AppTest' inside its live event loop - and returns the
    result.
    """
    if isinstance(testClass, MetaTest):
      return testClass.runTest()
    names = cls.testNames(testClass)
    suite = unittest.TestSuite([testClass(name) for name in names])
    return unittest.TextTestRunner(sys.stderr, True, 2).run(suite)
