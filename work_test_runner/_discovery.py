"""
Discovery locates the test classes under a project's tests folder and
reports them by name.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING
from types import ModuleType
from unittest import TestLoader, TestSuite

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Optional
  from unittest import TestCase

  StrTuple = tuple[str, ...]


class Discovery(BaseObject):
  """
  Discovery locates every 'unittest.TestCase' subclass under a project's
  tests folder and reports them as dotted 'module:ClassName' names. The
  names are plain strings, so a caller may hand each one to a fresh
  interpreter that imports and runs that single class on its own. Naming
  the classes rather than returning live class objects is the whole
  point, since a live object would drag the very interpreter state the
  per-class isolation is meant to escape.

  By default the tests folder is the directory named 'tests' beside the
  '__main__' module, so invoking the runner from a project whose entry
  point sits next to its 'tests' package needs no configuration. A
  different root or glob pattern may be passed to the constructor.

  Attributes
  ----------
  testRoot : str
      The folder searched for test classes. Defaults to the 'tests'
      directory beside the '__main__' module.
  pattern : str
      The glob matching the test files under the root. Defaults to
      'test_*.py'.
  topLevel : str
      The parent of the tests folder, placed on 'sys.path' so the
      discovered modules import under their full dotted names. Read only.
  errors : tuple of str
      The import errors collected by the most recent 'discover' call, one
      per test module that failed to import. Read only.

  Notes
  -----
  Finding the test classes means importing the test modules, so a
  'Discovery' run pollutes its interpreter with every test module and
  whatever those modules pull in. That is deliberate and harmless when
  'Discovery' runs in its own short-lived subprocess, which is how
  'FullRunner' drives it: the process prints the names and exits,
  discarding the imports before any test class is actually run. A module
  that fails to import is not fatal; its error is captured on 'errors'
  for the caller to report.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_pattern__: str = 'test_*.py'

  #  Private Variables
  __test_root__: Optional[str] = None
  __glob_pattern__: Optional[str] = None
  __discover_errors__: Optional[StrTuple] = None

  #  Public Variables
  testRoot: Field[str] = Field()
  pattern: Field[str] = Field()
  topLevel: Field[str] = Field()
  errors: Field[StrTuple] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createTestRoot(self) -> None:
    """
    This method sets the 'testRoot' to the path of the 'tests' folder
    beside the '__main__' module.

    Returns
    -------
    str
        The path of the 'tests' folder beside the '__main__' module.
    """
    self.__test_root__ = os.path.join(self._mainDir(), 'tests')

  @testRoot.GET
  def _getTestRoot(self, **kwargs) -> str:
    """
    This getter-method returns the path of the tests root, which is the
    folder searched for test classes.

    Parameters
    ----------
    _recursion : bool, Optional, private
      This keyword-only argument is used internally to detect recursion.
      It can be used to peek at the current value of 'testRoot' without
      triggering side effects.

    Returns
    -------
    str
      The path of the tests root.
    """
    if self.__test_root__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createTestRoot()
      return self._getTestRoot(_recursion=True)
    if isinstance(self.__test_root__, str):
      return self.__test_root__
    raise TypeException('__test_root__', self.__test_root__, str)

  def _createPattern(self, ) -> None:
    """
    This method sets the 'pattern' to the fallback glob 'test_*.py'.
    """
    self.__glob_pattern__ = self.__fallback_pattern__

  @pattern.GET
  def _getPattern(self, **kwargs) -> str:
    """
    This getter-method returns the glob pattern for test files under the
    tests root.

    Parameters
    ----------
    _recursion : bool, Optional, private
      This keyword-only argument is used internally to detect recursion.
      It can be used to peek at the current value of 'pattern' without
      triggering side effects.

    Returns
    -------
    str
      The glob pattern for test files under the tests root.
    """
    if self.__glob_pattern__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPattern()
      return self._getPattern(_recursion=True)
    if isinstance(self.__glob_pattern__, str):
      return self.__glob_pattern__
    raise TypeException('__glob_pattern__', self.__glob_pattern__, str)

  @topLevel.GET
  def _getTopLevel(self) -> str:
    """
    This getter-method returns the parent directory of the 'testRoot'.

    Returns
    -------
    str
      The absolute path of the parent of the tests folder.
    """
    return os.path.dirname(os.path.abspath(self.testRoot))

  @errors.GET
  def _getErrors(self) -> StrTuple:
    """
    The import-error messages collected during the most recent 'discover'
    call, one per test module that failed to import. Empty before the
    first call and whenever every module imported cleanly.

    Returns
    -------
    StrTuple
      A tuple of strings, one formatted import-error message per test
      module that failed to import.
    """
    return maybe(self.__discover_errors__, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @testRoot.SET
  def _setTestRoot(self, value: str) -> None:
    if not isinstance(value, str):
      raise TypeException('testRoot', value, str)
    self.__test_root__ = value

  @pattern.SET
  def _setPattern(self, value: str) -> None:
    if not isinstance(value, str):
      raise TypeException('value', value, str)
    self.__glob_pattern__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _mainDir() -> str:
    """
    The directory of the running '__main__' module, falling back to the
    current working directory when '__main__' has no file, as happens in
    an interactive session.

    Returns
    -------
    str
        The absolute directory of the '__main__' module, or the current
        working directory as the fallback.
    """
    mainModule: ModuleType = sys.modules['__main__']
    mainFile: str = getattr(mainModule, '__file__', os.getcwd())
    return os.path.dirname(os.path.abspath(mainFile))

  @classmethod
  def _iterCases(cls, suite: TestSuite) -> Iterator[TestCase]:
    """
    Flattens a nested 'TestSuite' into the individual test cases it
    holds, descending into sub-suites.

    Parameters
    ----------
    suite : TestSuite
        The suite to flatten, possibly holding nested sub-suites.

    Yields
    ------
    TestCase
        Each individual test case in the suite, in order.
    """
    for item in suite:
      if isinstance(item, TestSuite):
        yield from cls._iterCases(item)
      else:
        yield item

  def discover(self) -> StrTuple:
    """
    Imports the test modules under the tests root and returns the dotted
    'module:ClassName' name of every 'TestCase' subclass found there, in
    discovery order with duplicates removed. Two kinds of class are left
    out: one reached only through an import in some test module (a
    framework base, for instance), so the result is exactly the classes
    that physically live under the tests root; and one whose name does
    not start with 'Test', which is taken to be an abstract base rather
    than a runnable case, matching the convention that concrete test
    classes are named 'Test...'. Import errors are recorded on 'errors'
    rather than raised.

    Returns
    -------
    StrTuple
        A tuple of strings, each a 'module:ClassName' name, where
        'module' is the dotted import path and 'ClassName' is the test
        class qualified name.
    """
    root: str = os.path.abspath(self.testRoot)
    if not os.path.isdir(root):
      infoSpec = """No tests directory was found at: '%s'."""
      raise FileNotFoundError(infoSpec % root)
    loader = TestLoader()
    suite = loader.discover(root, self.pattern, self.topLevel)
    self.__discover_errors__ = (*maybe(loader.errors, ()),)
    rootPkg = os.path.basename(root)
    prefix = '%s.' % rootPkg
    names = []
    seen = set()
    for case in self._iterCases(suite):
      caseType = type(case)
      if not caseType.__name__.startswith('Test'):
        continue
      moduleName = caseType.__module__
      if moduleName != rootPkg and not moduleName.startswith(prefix):
        continue
      dottedName = '%s:%s' % (moduleName, caseType.__qualname__)
      if dottedName in seen:
        continue
      seen.add(dottedName)
      names.append(dottedName)
    return (*names,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str, str)
  def __init__(self, testRoot: str, pattern: str) -> None:
    self.testRoot = testRoot
    self.pattern = pattern

  @overload(str)
  def __init__(self, testRoot: str) -> None:
    self.testRoot = testRoot

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self) -> Iterator[str]:
    yield from self.discover()

  def __str__(self) -> str:
    infoSpec = """<%s: '%s' (%s)>"""
    clsName = type(self).__name__
    return infoSpec % (clsName, self.testRoot, self.pattern)

  def __repr__(self) -> str:
    infoSpec = """%s('%s', '%s')"""
    return infoSpec % (type(self).__name__, self.testRoot, self.pattern)
