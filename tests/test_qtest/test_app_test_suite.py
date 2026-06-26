"""
TestAppTestSuite covers 'AppTestSuite': filesystem discovery
('_scanDir'/'_walk'/'_discover'), the 'mainDir'/'testsDir'/'verbosity'
accessors and their defensive branches, exit-code description, name
resolution ('getNamed' and its edge cases) and the run loop ('runAll',
exercised against a stubbed 'AppTestRun'). 'testMeBro' is covered against a
stubbed suite so it does not launch the real test run.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile
import types
from typing import TYPE_CHECKING

import worQt.qtest._app_test_suite as suiteModule
import worQt.qtest._test_me_bro as broModule
from worktoy.waitaminute import SubclassException, TypeException
from worktoy.work_test import BaseTest

from worQt.qtest import AppTestSuite, testMeBro

from . import QTestTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _Pass:
  """Stub test class reporting a clean run."""
  _fake = (0, '')

  @classmethod
  def getTimeout(cls) -> float:
    return 30.0


class _Fail:
  """Stub test class reporting a failing run with output."""
  _fake = (3, 'boom')

  @classmethod
  def getTimeout(cls) -> float:
    return 30.0


class _FakeRun:
  """Drop-in for 'AppTestRun' returning the class's canned result."""

  def __init__(self, cls) -> None:
    self.cls = cls

  def run(self) -> tuple:
    return self.cls._fake


class TestAppTestSuite(QTestTest):
  """Tests for the discovery-and-run suite."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HELPERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _tree() -> str:
    """Build a throwaway 'tests' tree and return its path."""
    tmp = tempfile.mkdtemp()
    td = os.path.join(tmp, 'tests')
    os.makedirs(os.path.join(td, 'sub'))
    os.makedirs(os.path.join(td, 'nopkg'))  # no __init__: not a package
    rels = ['__init__.py', 'run_a.py', 'test_b.py', 'x.py',
            'sub/__init__.py', 'sub/test_c.py', 'nopkg/run_d.py']
    for rel in rels:
      open(os.path.join(td, rel), 'w').close()
    return td

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DISCOVERY   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_discover_tree(self) -> None:
    """'_discover' finds 'run*'/'test*' modules in packages and skips a
    directory without '__init__.py'."""
    td = self._tree()
    try:
      names = set(AppTestSuite(td)._discover())
      self.assertIn('tests.run_a', names)
      self.assertIn('tests.test_b', names)
      self.assertIn('tests.sub.test_c', names)
      self.assertFalse(any('run_d' in n for n in names))  # nopkg skipped
      self.assertFalse(any(n.endswith('.x') for n in names))  # not run/test
    finally:
      shutil.rmtree(os.path.dirname(td), ignore_errors=True)

  def test_iter_uses_discovered_cache(self) -> None:
    """Iterating the suite yields the discovered (real) test modules."""
    names = [*AppTestSuite()]
    self.assertIn('tests.test_qtest.test_app_test_suite', names)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ACCESSORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_main_dir(self) -> None:
    """'mainDir' resolves lazily to an existing directory."""
    self.assertTrue(os.path.isdir(AppTestSuite().mainDir))

  def test_main_dir_not_a_directory(self) -> None:
    """A 'mainDir' pointing at a file raises 'NotADirectoryError'."""
    tmp = tempfile.mkdtemp()
    afile = os.path.join(tmp, 'afile')
    open(afile, 'w').close()
    try:
      suite = AppTestSuite()
      suite.__main_dir__ = afile
      with self.assertRaises(NotADirectoryError):
        _ = suite.mainDir
    finally:
      shutil.rmtree(tmp, ignore_errors=True)

  def test_main_dir_missing(self) -> None:
    """A 'mainDir' pointing nowhere raises 'FileNotFoundError'."""
    suite = AppTestSuite()
    suite.__main_dir__ = os.path.join(tempfile.gettempdir(), 'nope_xyz_123')
    with self.assertRaises(FileNotFoundError):
      _ = suite.mainDir

  def test_tests_dir_lazy(self) -> None:
    """A no-arg suite resolves 'testsDir' to an existing directory and adds
    its parent to 'sys.path'."""
    suite = AppTestSuite()
    testsDir = suite.testsDir
    self.assertTrue(os.path.isdir(testsDir))
    self.assertIn(os.path.dirname(testsDir), sys.path)

  def test_tests_dir_not_a_directory(self) -> None:
    """A 'testsDir' pointing at a file raises 'NotADirectoryError'."""
    tmp = tempfile.mkdtemp()
    afile = os.path.join(tmp, 'afile')
    open(afile, 'w').close()
    try:
      with self.assertRaises(NotADirectoryError):
        _ = AppTestSuite(afile).testsDir
    finally:
      shutil.rmtree(tmp, ignore_errors=True)

  def test_tests_dir_missing(self) -> None:
    """A 'testsDir' pointing nowhere raises 'FileNotFoundError'."""
    missing = os.path.join(tempfile.gettempdir(), 'nope_tests_xyz')
    with self.assertRaises(FileNotFoundError):
      _ = AppTestSuite(missing).testsDir

  def test_verbosity_round_trip(self) -> None:
    """'verbosity' is settable and readable."""
    suite = AppTestSuite()
    suite.verbosity = 0
    self.assertEqual(suite.verbosity, 0)

  def test_dir_recursion_guards(self) -> None:
    """The lazy 'mainDir'/'testsDir' getters guard against re-entry."""
    with self.assertRaises(RecursionError):
      AppTestSuite()._getMainDir(_recursion=True)
    with self.assertRaises(RecursionError):
      AppTestSuite()._getTestsDir(_recursion=True)

  def test_dir_wrong_slot_type(self) -> None:
    """A non-string 'mainDir'/'testsDir' slot raises 'TypeException'."""
    main = AppTestSuite()
    main.__main_dir__ = 123
    with self.assertRaises(TypeException):
      _ = main.mainDir
    tests = AppTestSuite()
    tests.__tests_dir__ = 123
    with self.assertRaises(TypeException):
      _ = tests.testsDir

  def test_log_below_verbosity_is_silent(self) -> None:
    """A '_log' below the suite's verbosity prints nothing and returns."""
    suite = AppTestSuite()
    suite.verbosity = 0
    with contextlib.redirect_stdout(io.StringIO()) as captured:
      suite._log(2, 'hidden')
    self.assertEqual(captured.getvalue(), '')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DESCRIBE   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_describe_codes(self) -> None:
    """'_describe' maps every exit-code family to a label."""
    cases = {
      0  : 'PASS',
      3  : 'FAIL',
      2  : 'ERROR',
      1  : 'ERROR',
      -9 : 'TIMEOUT',
      -11: 'CRASH',
      -5 : 'CRASH',  # other signal
      7  : 'FAIL',  # other positive code
    }
    for code, label in cases.items():
      self.assertEqual(AppTestSuite._describe(code, 30.0)[0], label)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GET NAMED   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_get_named_resolves(self) -> None:
    """'getNamed' resolves a discovered module to its test class."""
    cls = AppTestSuite.getNamed('tests.test_app.test_exec')
    self.assertEqual(cls.__name__, 'TestExec')

  def test_get_named_unknown_raises(self) -> None:
    """An undiscovered name raises 'ImportError'."""
    with self.assertRaises(ImportError):
      AppTestSuite.getNamed('tests.nope.nope')

  def _injectModule(self, name: str, module: types.ModuleType) -> None:
    """Register 'module' under 'name' and add it to the discovered cache,
    restoring the cache in 'tearDown' via the saved snapshot."""
    sys.modules[name] = module
    AppTestSuite.__discovered_cache__ = (*AppTestSuite._getDiscovered(), name)

  def test_get_named_multiple_classes(self) -> None:
    """A module with two test classes raises 'RuntimeError'."""
    saved = AppTestSuite._getDiscovered()
    module = types.ModuleType('tests._fake_multi')

    class TestOne(BaseTest):
      pass

    class TestTwo(BaseTest):
      pass

    module.TestOne, module.TestTwo = TestOne, TestTwo
    try:
      self._injectModule('tests._fake_multi', module)
      with self.assertRaises(RuntimeError):
        AppTestSuite.getNamed('tests._fake_multi')
    finally:
      AppTestSuite.__discovered_cache__ = saved
      sys.modules.pop('tests._fake_multi', None)

  def test_get_named_non_testcase(self) -> None:
    """A 'Test'-named class that is not a 'TestCase' raises
    'SubclassException'."""
    saved = AppTestSuite._getDiscovered()
    module = types.ModuleType('tests._fake_bad')

    class TestNope:  # not a TestCase
      pass

    module.TestNope = TestNope
    try:
      self._injectModule('tests._fake_bad', module)
      with self.assertRaises(SubclassException):
        AppTestSuite.getNamed('tests._fake_bad')
    finally:
      AppTestSuite.__discovered_cache__ = saved
      sys.modules.pop('tests._fake_bad', None)

  def test_get_named_no_class(self) -> None:
    """A module with no test class raises 'ImportError'."""
    saved = AppTestSuite._getDiscovered()
    module = types.ModuleType('tests._fake_none')
    try:
      self._injectModule('tests._fake_none', module)
      with self.assertRaises(ImportError):
        AppTestSuite.getNamed('tests._fake_none')
    finally:
      AppTestSuite.__discovered_cache__ = saved
      sys.modules.pop('tests._fake_none', None)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  RUN ALL (stubbed)  # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_run_all_counts_failures(self) -> None:
    """'runAll' runs each discovered class through 'AppTestRun', logs each
    outcome and returns the failure count. A passing, a failing and an
    unresolvable name are exercised."""

    class _Suite(AppTestSuite):
      def __iter__(self) -> Any:
        yield from ['ok', 'bad', 'err']

      def getNamed(self, name: str) -> Any:
        if name == 'err':
          raise ImportError('err')
        return {'ok': _Pass, 'bad': _Fail}[name]

    saved = suiteModule.AppTestRun
    suiteModule.AppTestRun = _FakeRun
    try:
      suite = _Suite()
      suite.verbosity = 2  # exercise the per-line logging
      #  Capture the stub suite's RUN/FAIL/ERROR logging so it does not
      #  leak into the real runner's report and look like a failure.
      with contextlib.redirect_stdout(io.StringIO()):
        failures = suite.runAll()
      self.assertEqual(failures, 2)  # 'bad' + 'err'
    finally:
      suiteModule.AppTestRun = saved

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TEST ME BRO  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_me_bro_delegates(self) -> None:
    """'testMeBro' delegates to 'AppTestSuite().runAll()'."""

    class _Stub:
      def runAll(self) -> int:
        return 0

    saved = broModule.AppTestSuite
    broModule.AppTestSuite = _Stub
    try:
      self.assertEqual(testMeBro(), 0)
    finally:
      broModule.AppTestSuite = saved
