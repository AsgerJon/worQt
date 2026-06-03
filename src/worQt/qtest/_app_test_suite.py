"""
The 'run' function provides the main entry point for running the tests.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
import inspect
import unittest
from typing import TYPE_CHECKING
from types import ModuleType
from importlib import import_module

from worktoy.dispatch import overload
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException, SubclassException
from worktoy.work_test import BaseTest
from worktoy.utilities import wordWrap

from . import MetaTest, AppTestRun

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Iterator, Type

  MaybeStr: TypeAlias = Optional[str]
  Test: TypeAlias = Type[BaseTest]


class AppTestSuite(BaseObject):
  """
  This private class is responsible for discovering the tests in the
  'tests.test_app' that require unconventional testing. These are
  characterized by way of naming. While 'unittest' rely on module and method
  names beginning with 'test' and class names with 'Test', to recognize test
  cases, this class relies on 'run' and 'Run' respectively.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __main_dir__: MaybeStr = None
  __tests_dir__: MaybeStr = None
  __root_dir__: MaybeStr = None
  __discovered_cache__: Optional[tuple[str, ...]] = None
  __verbosity__: int = 2

  #  Public Variables
  mainDir: Field[str] = Field()
  testsDir: Field[str] = Field()
  verbosity: Field[int] = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createMainDir(self, ) -> None:
    mainModule: ModuleType = sys.modules['__main__']
    mainFile: str = getattr(mainModule, '__file__', os.getcwd())
    self.__main_dir__ = os.path.dirname(os.path.abspath(mainFile))

  @mainDir.GET
  def _getMainDir(self, **kwargs, ) -> str:
    if self.__main_dir__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMainDir()
      return self._getMainDir(_recursion=True)
    if isinstance(self.__main_dir__, str):
      if os.path.exists(self.__main_dir__):
        if os.path.isdir(self.__main_dir__):
          return self.__main_dir__
        raise NotADirectoryError(self.__main_dir__)
      raise FileNotFoundError(self.__main_dir__)
    raise TypeException('__main_dir__', self.__main_dir__, str)

  def _createTestsDir(self, ) -> None:
    self.__tests_dir__ = os.path.join(self._getSrcDir(), 'tests')

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
    yielded as names.
    """
    names = []
    packageDirs = []
    for item in os.listdir(dirPath):
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
    The dotted names of every 'run*'/'test*' module and 'run*'/'test*'
    package found recursively under 'self.testsDir', WITHOUT importing
    them. Reads 'self.testsDir', computes the 'sys.path' root once, and
    hands both to the static '_walk'.
    """
    basePath: str = os.path.dirname(self.testsDir.rstrip(os.sep))
    return self._walk(self.testsDir, basePath)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[str]:
    """
    Yields the dotted name of every discovered 'run*'/'test*' test module.
    Each name resolves to its test class through 'getNamed'.
    """
    yield from self._getDiscovered()

  @staticmethod
  def _describe(code: int, timeout: float) -> tuple[str, str]:
    """
    Maps a child exit code (as returned by 'AppTest.start') to a
    '(label, reason)' pair for reporting. A negative code is death by
    signal: -9 is the deadline kill, -11 a segfault.
    """
    if not code:
      return 'PASS', ''
    if code == 3:
      return 'FAIL', 'the test raised'
    if code == 2:
      return 'ERROR', 'malformed suite'
    if code == 1:
      return 'ERROR', 'no test class found'
    if code == -9:
      return 'TIMEOUT', 'killed after %gs deadline' % (timeout,)
    if code == -11:
      return 'CRASH', 'segmentation fault (signal 11)'
    if code < 0:
      return 'CRASH', 'killed by signal %d' % (-code,)
    return 'FAIL', 'exit code %d' % (code,)

  def _log(self, level: int, *parts: str) -> None:
    """
    Reflows 'parts' to at most 77 columns via 'wordWrap' and prints the
    result, but only when 'verbosity' is at least 'level'. Verbosity 0 is
    silent, 1 prints only the final summary, 2 (the default) prints every
    per-test outcome.
    """
    if self.verbosity < level:
      return
    print(wordWrap(77, *parts))

  def runAll(self, ) -> int:
    """
    Runs every discovered test class, each in its own expendable child
    process via 'AppTest.start', reporting each outcome at verbosity 2 and
    a summary at verbosity 1. Returns the count of classes that did not
    pass, suitable as a process exit code.
    """
    rule = '-' * 60
    failures = 0
    names = [*self]
    for name in names:
      try:
        cls = self.getNamed(name)
      except Exception as error:
        self._log(2, 'ERROR: %s (%s: %s)' % (
            name, type(error).__name__, error))
        self._log(2, rule)
        failures += 1
        continue
      self._log(2, 'RUN: %s' % (cls.__name__,))
      code, output = AppTestRun(cls).run()
      if output.strip():
        self._log(2, output)
      #  Plain (non-AppTest) classes run in-process and have no deadline.
      timeout = cls.getTimeout() if hasattr(cls, 'getTimeout') else 0.0
      label, reason = self._describe(code, timeout)
      if reason:
        self._log(2, '%s: %s (%s)' % (label, cls.__name__, reason))
      else:
        self._log(2, '%s: %s' % (label, cls.__name__))
      self._log(2, rule)
      if label != 'PASS':
        failures += 1
    passed = len(names) - failures
    self._log(1, '%d passed, %d failed of %d tests' % (
        passed, failures, len(names)))
    return failures

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _getSrcDir() -> str:
    here: str = os.path.dirname(os.path.abspath(__file__))
    while 'tests' not in os.listdir(here) and len(here) > 1:
      here = os.path.dirname(here)
    if 'tests' not in os.listdir(here):
      raise FileNotFoundError
    return here

  @classmethod
  def __class_init__(cls, name, bases, space, **kwargs) -> None:
    """
    Caches the absolute path to the root directory containing 'tests'.
    Discovery is deferred until the first 'getNamed' call. If no such root
    can be found, '_getSrcDir' raises 'FileNotFoundError' here, at class
    creation.
    """
    cls.__root_dir__ = cls._getSrcDir()

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

  @classmethod
  def getNamed(cls, name: str) -> MetaTest:
    if name not in cls._getDiscovered():
      raise ImportError(name)
    namedModule = import_module(name)
    out = None
    for objName, obj in inspect.getmembers(namedModule, inspect.isclass):
      if not objName.startswith(('Run', 'Test')):
        continue
      if not issubclass(obj, unittest.TestCase):
        raise SubclassException(obj, unittest.TestCase)
      if out is None:
        out = obj
        continue
      infoSpec = """Found multiple test classes in the same module: %s!"""
      info = infoSpec % (name,)
      raise RuntimeError(info)
    if out is None:
      raise ImportError(name)
    return out
