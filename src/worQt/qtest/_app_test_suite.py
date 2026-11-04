"""
AppTestSuite discovers the test modules under the project's 'tests' tree
and runs each in its own child process through 'AppTestRun', reporting one
status per test class.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
import time
import traceback
from typing import TYPE_CHECKING

from worktoy.dispatch import overload
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException
from worktoy.utilities import wordWrap

from . import AppTestRun

if TYPE_CHECKING:  # pragma: no cover
  from typing import IO, TypeAlias, Optional, Iterator

  MaybeStr: TypeAlias = Optional[str]


class AppTestSuite(BaseObject):
  """
  AppTestSuite discovers and runs every test class under the project's
  'tests' tree, each in its own child process through 'AppTestRun', and
  reports the outcomes. Discovery is by naming: a module file is a
  candidate when its name begins with 'run' or 'test', and the single test
  class it defines is recognised when its name begins with 'Run' or 'Test'.
  The suite itself never imports a test module - only the child does - so
  nothing a test module does at import time can reach the suite or the
  modules after it.

  Every top-level run also writes its complete record - each status line
  and the full output of every child, whatever the console verbosity - to
  'latest.log' in the project root, replacing the previous run's. A suite
  running inside a test child, as the harness's own tests do, leaves the
  log alone.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __tests_dir__: MaybeStr = None
  __root_dir__: MaybeStr = None
  __discovered_cache__: Optional[tuple[str, ...]] = None
  __verbosity__: int = 2
  __log_name__: str = 'latest.log'
  __log_path__: MaybeStr = None  # overrides '<root>/latest.log' when set
  __log_file__ = None  # the open log while a run is going

  #  Public Variables
  testsDir: Field[str] = Field()
  verbosity: Field[int] = Field()
  logPath: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createTestsDir(self, ) -> None:
    self.__tests_dir__ = os.path.join(self._findRootDir(), 'tests')

  @testsDir.GET
  def _getTestsDir(self, **kwargs) -> str:
    if self.__tests_dir__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createTestsDir()
      return self._getTestsDir(_recursion=True)
    if isinstance(self.__tests_dir__, str):
      if os.path.exists(self.__tests_dir__):
        if os.path.isdir(self.__tests_dir__):
          return self.__tests_dir__
        raise NotADirectoryError(self.__tests_dir__)
      raise FileNotFoundError(self.__tests_dir__)
    raise TypeException('__tests_dir__', self.__tests_dir__, str)

  @verbosity.GET
  def _getVerbosity(self, ) -> int:
    return self.__verbosity__

  @verbosity.SET
  def _setVerbosity(self, value: int) -> None:
    self.__verbosity__ = int(value)

  @logPath.GET
  def _getLogPath(self, ) -> str:
    """
    The 'logPath' getter returns where a run writes its log: 'latest.log'
    in the project root, unless '__log_path__' says otherwise.
    """
    if self.__log_path__ is not None:
      return self.__log_path__
    return os.path.join(self.__root_dir__, self.__log_name__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @testsDir.onGet
  def _onGetTestsDir(self, testsDir: str, **kwargs) -> None:
    parentDir = os.path.dirname(testsDir)
    if parentDir not in sys.path:
      sys.path.append(parentDir)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __init__(self, testsDir: str, ) -> None:
    self.__tests_dir__ = testsDir

  @overload()
  def __init__(self, ) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _scanDir(dirPath: str, basePath: str) -> tuple:
    """
    Discovers from a single directory. Returns a 2-tuple of
    '(names, packageDirs)': the dotted names of the 'run*'/'test*' modules
    directly in 'dirPath' (relative to 'basePath'), and the absolute paths
    of the package subdirectories worth recursing into. Packages are
    containers, not runnable units, so they are recursed into but never
    yielded as names. Entries are sorted, so the run order is the same on
    every machine rather than whatever order the filesystem lists them in.
    """
    names = []
    packageDirs = []
    for item in sorted(os.listdir(dirPath)):
      full = os.path.join(dirPath, item)
      if item.startswith(('run', 'test')) and item.endswith('.py'):
        rel = os.path.relpath(full[:-3], basePath)
        names.append(rel.replace(os.sep, '.'))  # tests.sub.run_app
      elif os.path.isdir(full):
        if not os.path.exists(os.path.join(full, '__init__.py')):
          continue  # not a package: cannot import, do not recurse
        packageDirs.append(full)
    return (*names,), (*packageDirs,)

  @classmethod
  def _walk(cls, dirPath: str, basePath: str) -> tuple[str, ...]:
    """
    Recursive worker: '_scanDir' applied at 'dirPath' and then down each
    package subdirectory it returns, all relative to 'basePath'. Only real
    packages are descended into, so every name is importable.
    """
    names, packageDirs = cls._scanDir(dirPath, basePath)
    out = [*names]
    for packageDir in packageDirs:
      out.extend(cls._walk(packageDir, basePath))
    return (*out,)

  def _discover(self, ) -> tuple[str, ...]:
    """
    The dotted names of every 'run*'/'test*' module found recursively under
    'self.testsDir', WITHOUT importing them. Reads 'self.testsDir',
    computes the 'sys.path' root once, and hands both to the static
    '_walk'.
    """
    basePath: str = os.path.dirname(self.testsDir.rstrip(os.sep))
    return self._walk(self.testsDir, basePath)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[str]:
    """
    Yields the dotted name of every discovered 'run*'/'test*' test module.
    """
    yield from self._getDiscovered()

  @staticmethod
  def _describe(code: int, timedOut: bool, deadline: float) -> tuple:
    """
    The '_describe' method turns how a child ended into the
    '(label, reason)' pair the report shows. A timeout is known from the
    supervisor having killed the child, never guessed from the exit code,
    so a child killed by anything else is not mistaken for one.
    """
    if timedOut:
      return 'TIMEOUT', 'killed after its %gs deadline' % (deadline,)
    if code == AppTestRun.__pass_code__:
      return 'PASS', ''
    if code == AppTestRun.__fail_code__:
      return 'FAIL', 'a test failed'
    if code == AppTestRun.__error_code__:
      return 'ERROR', 'the test class could not be loaded or run'
    if code == -11:
      return 'CRASH', 'segmentation fault (signal 11)'
    if code < 0:
      return 'CRASH', 'killed by signal %d' % (-code,)
    return 'ERROR', 'the child exited with code %d' % (code,)

  @staticmethod
  def _isNested() -> bool:
    """
    The '_isNested' method tells whether this suite runs inside a test
    child, where it must not touch the log of the run it is part of.
    """
    variable = AppTestRun.__child_variable__
    return True if os.environ.get(variable) else False

  def _openLog(self, ) -> Optional[IO]:
    """
    The '_openLog' method opens the log for a new run, replacing the last
    run's, and returns it - or 'None' inside a test child, or when the log
    cannot be written, which is reported but never stops the run. The log
    is line-buffered, so even a run that gets killed leaves what it had.
    """
    if self._isNested():
      return None
    try:
      return open(self.logPath, 'w', 1, 'utf-8')
    except OSError as error:
      self._log(1, 'Could not write the log %s: %s' % (self.logPath, error))
      return None

  def _closeLog(self, ) -> None:
    """The '_closeLog' method closes the log of the run that just ended."""
    if self.__log_file__ is not None:
      self.__log_file__.close()
    self.__log_file__ = None

  def _write(self, text: str) -> None:
    """
    The '_write' method appends 'text' to the log of the current run, if
    there is one.
    """
    if self.__log_file__ is not None:
      self.__log_file__.write('%s\n' % (text,))

  def _log(self, level: int, *parts: str) -> None:
    """
    Reflows 'parts' to at most 77 columns via 'wordWrap', writes the result
    to the log, and prints it when 'verbosity' is at least 'level'. Meant
    for the suite's own status lines; child output goes through '_echo'.
    """
    text = wordWrap(77, *parts)
    self._write(text)
    if self.verbosity >= level:
      print(text)

  def _echo(self, level: int, output: str) -> None:
    """
    The '_echo' method writes child output to the log, and prints it when
    'verbosity' is at least 'level', exactly as the child wrote it.
    Reflowing it would flatten every traceback into an unreadable
    paragraph.
    """
    if not output.strip():
      return
    text = output.rstrip()
    self._write(text)
    if self.verbosity >= level:
      print(text)

  def _report(self, name: str, label: str, reason: str, output: str) -> None:
    """
    The '_report' method prints the outcome of one test module. The
    child's output is shown whenever the class did not pass, and for a
    passing class only at verbosity 3.
    """
    self._echo(3 if label == 'PASS' else 2, output)
    if reason:
      self._log(2, '%s: %s (%s)' % (label, name, reason))
    else:
      self._log(2, '%s: %s' % (label, name))
    self._log(2, '-' * 60)

  def _runOne(self, name: str) -> bool:
    """
    The '_runOne' method runs the test module 'name' in its child, reports
    the outcome and returns whether it passed. A failure of the harness
    itself while supervising is reported as an error of that module rather
    than ending the whole suite.
    """
    self._log(2, 'RUN: %s' % (name,))
    testRun = AppTestRun(name)
    try:
      code, output = testRun.run()
    except Exception:
      output = traceback.format_exc()
      self._report(name, 'ERROR', 'the harness failed', output)
      return False
    label, reason = self._describe(code, testRun.timedOut, testRun.deadline)
    self._report(name, label, reason, output)
    return True if label == 'PASS' else False

  def runNames(self, *names: str) -> int:
    """
    The 'runNames' method runs the named test modules, each in its own
    child, reporting each outcome at verbosity 2 and a summary at
    verbosity 1, and recording all of it in 'latest.log'. It returns 0
    when every module passed and 1 otherwise, ready to be a process exit
    status.
    """
    self.__log_file__ = self._openLog()
    try:
      return self._runLogged(*names)
    finally:
      self._closeLog()

  def _runLogged(self, *names: str) -> int:
    """
    The '_runLogged' method is the body of 'runNames', run while the log
    is open; the timestamp heading the log says which run it records.
    """
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    self._write('worQt.qtest run started %s' % (stamp,))
    failures = 0
    for name in names:
      if not self._runOne(name):
        failures += 1
    passed = len(names) - failures
    self._log(1, '%d passed, %d failed of %d test classes' % (
        passed, failures, len(names)))
    return 1 if failures else 0

  def runAll(self, ) -> int:
    """
    The 'runAll' method runs every discovered test module through
    'runNames' and returns its status: 0 when everything passed, 1
    otherwise.
    """
    return self.runNames(*self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _findRootDir() -> str:
    """
    The '_findRootDir' method returns the project root: the directory
    holding 'tests'. The working directory comes first, being the project
    the user runs the suite from; otherwise the search walks up from this
    package, which finds the repository when 'worQt' runs from its source
    tree.
    """
    here: str = os.getcwd()
    if os.path.isdir(os.path.join(here, 'tests')):
      return here
    here = os.path.dirname(os.path.abspath(__file__))
    while not os.path.isdir(os.path.join(here, 'tests')):
      parent = os.path.dirname(here)
      if parent == here:  # pragma: no cover  # reached the filesystem root
        return os.getcwd()
      here = parent
    return here

  @classmethod
  def __class_init__(cls, name, bases, space, **kwargs) -> None:
    """
    Caches the absolute path to the root directory containing 'tests'.
    Discovery is deferred until the suite is first iterated.
    """
    cls.__root_dir__ = cls._findRootDir()

  @classmethod
  def _getDiscovered(cls, ) -> tuple[str, ...]:
    """
    The dotted names of every discovered test module, rooted at the cached
    '__root_dir__' and memoised on first use.
    """
    if cls.__discovered_cache__ is None:
      testsDir = os.path.join(cls.__root_dir__, 'tests')
      cls.__discovered_cache__ = cls(testsDir)._discover()
    return cls.__discovered_cache__
