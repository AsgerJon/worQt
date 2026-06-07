"""
SingleRunner runs one test class and reports its raw outcome.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import gc
import sys
from importlib import import_module
from time import perf_counter
from typing import TYPE_CHECKING
from unittest import TestLoader, TestResult

from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import FrozenSet


class SingleRunner(BaseObject):
  """
  SingleRunner imports one test class by its dotted 'module:ClassName'
  name, runs every test method on it, and returns the raw outcome as a
  plain dict: the class name, the number of methods run, the failure,
  error, and skip records as '(testId, message)' pairs, and the
  wall-clock duration. The dict is exactly the shape 'SingleResult'
  consumes, so 'FullRunner' turns each returned dict into a typed
  'SingleResult'. SingleRunner itself never builds one, and never imports
  the result type.

  The run happens in the current interpreter. Afterwards the test modules
  that the run pulled in are popped from 'sys.modules' and the garbage
  collector is run, so the next class imported through a fresh
  SingleRunner gets fresh module and class objects rather than inheriting
  the previous class's metaclass context. Only modules under the tests
  package are evicted; the framework and standard library stay cached.

  Attributes
  ----------
  name : str
      The dotted 'module:ClassName' name of the test class to run.
  topLevel : str
      The directory put on 'sys.path' so the named module imports under
      its full dotted name. Empty when the module is already importable.

  Notes
  -----
  The scrub reclaims Python state only. C++ state, the kind a PySide6
  test leaves behind, does not live in 'sys.modules' and is untouched
  here. A test base that creates such objects is responsible for
  disposing of them in its own teardown before the next class runs. When
  even that is not enough, 'FullRunner' may instead drive each
  SingleRunner in its own subprocess, where the interpreter exit reclaims
  everything; the body below is identical either way.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  name = AttriBox[str]()
  topLevel = AttriBox[str]()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _ensurePath(self) -> None:
    """
    Puts the top-level directory on 'sys.path' so the named module
    imports under its full dotted name. Does nothing when no top level
    was given or it is already present.
    """
    top = self.topLevel
    if top and top not in sys.path:
      sys.path.insert(0, top)

  def _resolve(self) -> type:
    """
    Imports the module half of the name and walks the qualified name to
    the test class it points at.

    Returns
    -------
    type
        The test class the name points at.
    """
    moduleName, _, qualName = self.name.partition(':')
    obj = import_module(moduleName)
    for part in qualName.split('.'):
      obj = getattr(obj, part)
    return obj

  def _yeet(self, snapshot: FrozenSet) -> None:
    """
    Evicts every module imported since 'snapshot' that lives under the
    tests package, then runs the garbage collector. The tests package is
    the first segment of the class name, so the framework and standard
    library, present before the snapshot, are left cached.

    Parameters
    ----------
    snapshot : FrozenSet
        The 'sys.modules' keys captured before the run, against which the
        newly imported modules are measured.
    """
    rootPkg = self.name.partition(':')[0].partition('.')[0]
    prefix = '%s.' % rootPkg
    fresh = [name for name in sys.modules if name not in snapshot]
    for moduleName in fresh:
      if moduleName == rootPkg or moduleName.startswith(prefix):
        sys.modules.pop(moduleName, None)
    gc.collect()

  def _outcome(self, result: TestResult, duration: float) -> dict:
    """
    Packs a finished 'unittest.TestResult' into the plain dict that
    'SingleResult.fromDict' consumes, taking the test method id and
    message from each recorded failure, error, and skip.

    Parameters
    ----------
    result : TestResult
        The finished result of running the class.
    duration : float
        The wall-clock seconds the run took.

    Returns
    -------
    dict
        The raw outcome, in the shape 'SingleResult.fromDict' consumes.
    """
    return dict(
        name=self.name,
        testsRun=result.testsRun,
        failures=[[t.id(), tb] for t, tb in result.failures],
        errors=[[t.id(), tb] for t, tb in result.errors],
        skipped=[[t.id(), reason] for t, reason in result.skipped],
        duration=duration,
    )

  def run(self) -> dict:
    """
    Imports and runs the named test class and returns its raw outcome
    dict. The tests-package modules pulled in by the run are scrubbed
    afterwards whether the run succeeds or raises, so a class that fails
    to import does not leave its half-loaded modules behind for the next
    run.

    Returns
    -------
    dict
        The raw outcome, in the shape 'SingleResult.fromDict' consumes.
    """
    self._ensurePath()
    snapshot = frozenset(sys.modules)
    try:
      testClass = self._resolve()
      suite = TestLoader().loadTestsFromTestCase(testClass)
      result = TestResult()
      start = perf_counter()
      suite.run(result)
      duration = perf_counter() - start
      return self._outcome(result, duration)
    finally:
      self._yeet(snapshot)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str, str)
  def __init__(self, name: str, topLevel: str) -> None:
    self.name = name
    self.topLevel = topLevel

  @overload(str)
  def __init__(self, name: str) -> None:
    self.name = name

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __call__(self) -> dict:
    return self.run()

  def __str__(self) -> str:
    infoSpec = """<%s: %s>"""
    return infoSpec % (type(self).__name__, self.name)

  def __repr__(self) -> str:
    infoSpec = """%s('%s', '%s')"""
    return infoSpec % (type(self).__name__, self.name, self.topLevel)
