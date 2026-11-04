"""
TestAppTestRun holds the harness to its promises. Each fixture module in
'tests.test_qtest.fixtures' ends a different way - passing, failing,
segfaulting, hanging, failing to load - and runs here in a real child
process, as the suite would run it; the test then checks that the ending
is reported for what it is, with the output that explains it. The
resolution of a module to its test class is tested in-process.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys
import unittest
from types import ModuleType
from typing import TYPE_CHECKING
from unittest import mock

from worktoy.waitaminute import SubclassException
from worktoy.work_test import BaseTest

import worQt.qtest
from worQt.qtest import AppTest, AppTestRun, AppTestSuite, RenderMode

from . import QTestTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

_FIXTURES = 'tests.test_qtest.fixtures.'
_SCRATCH_MODULE = 'tests.test_qtest._scratch_module'


class TestAppTestRun(QTestTest):
  """Tests for 'AppTestRun': real child runs and class resolution."""

  #  Ten or so children, one of them hanging past its deadline.
  __time_out__ = 180.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HELPERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _run(fixture: str) -> tuple[str, str]:
    """Runs a fixture module in a child; returns '(label, output)'."""
    testRun = AppTestRun(_FIXTURES + fixture)
    code, output = testRun.run()
    timedOut, deadline = testRun.timedOut, testRun.deadline
    label, _ = AppTestSuite._describe(code, timedOut, deadline)
    return label, output

  @staticmethod
  def _scratchModule(*classes: type) -> ModuleType:
    """A throwaway module defining 'classes', registered for import."""
    module = ModuleType(_SCRATCH_MODULE)
    for cls in classes:
      cls.__module__ = _SCRATCH_MODULE
      setattr(module, cls.__name__, cls)
    sys.modules[_SCRATCH_MODULE] = module
    return module

  def tearDown(self, ) -> None:
    sys.modules.pop(_SCRATCH_MODULE, None)
    super().tearDown()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CHILD RUNS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_pass(self) -> None:
    """A passing class passes, its inherited test and its skip included."""
    label, output = self._run('_pass')
    self.assertEqual(label, 'PASS', output)
    self.assertIn('run_inherited', output)
    self.assertIn('skipped', output)

  def test_fail(self) -> None:
    """A failing test fails the class, and the tests after it still run."""
    label, output = self._run('_fail')
    self.assertEqual(label, 'FAIL', output)
    self.assertIn('run_after_failure', output)

  def test_sub_test_failure_fails(self) -> None:
    """A failure raised from 'tearDown' fails the class (it used to pass)."""
    label, output = self._run('_sub_test_fail')
    self.assertEqual(label, 'FAIL', output)
    self.assertIn('run_after_sub_test', output)

  def test_crash(self) -> None:
    """A segfault is a CRASH, with the stack of the crashing test."""
    label, output = self._run('_crash')
    self.assertEqual(label, 'CRASH', output)
    self.assertIn('Segmentation fault', output)
    self.assertIn('run_crash', output)

  def test_hang(self) -> None:
    """Overrunning the deadline is a TIMEOUT, with the stack it hung in."""
    label, output = self._run('_hang')
    self.assertEqual(label, 'TIMEOUT', output)
    self.assertIn('Timeout', output)
    self.assertIn('run_hang', output)

  def test_empty_is_error(self) -> None:
    """A class without test methods is an ERROR, not a silent pass."""
    label, output = self._run('_empty')
    self.assertEqual(label, 'ERROR', output)
    self.assertIn('no test methods', output)

  def test_plain_class(self) -> None:
    """A plain 'BaseTest' class runs in a child too, without an app."""
    label, output = self._run('_plain')
    self.assertEqual(label, 'PASS', output)

  def test_load_error(self) -> None:
    """A module failing to import is an ERROR showing why."""
    label, output = self._run('_load_error')
    self.assertEqual(label, 'ERROR', output)
    self.assertIn('the fixture module fails to import', output)

  def test_missing_module(self) -> None:
    """A module that does not exist is an ERROR showing why."""
    label, output = self._run('_no_such_module')
    self.assertEqual(label, 'ERROR', output)
    self.assertIn('No module named', output)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CLASS RESOLUTION   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_get_named_ignores_imported_classes(self) -> None:
    """Only a class the module defines counts, not one it imports."""

    class TestDefined(BaseTest):
      def test_x(self) -> None:
        pass

    module = self._scratchModule(TestDefined)
    module.TestCase = unittest.TestCase
    self.assertIs(AppTestRun.getNamed(_SCRATCH_MODULE), TestDefined)

  def test_get_named_multiple_raises(self) -> None:
    """Two test classes in one module are refused."""

    class TestOne(BaseTest):
      pass

    class TestTwo(BaseTest):
      pass

    self._scratchModule(TestOne, TestTwo)
    with self.assertRaises(RuntimeError):
      AppTestRun.getNamed(_SCRATCH_MODULE)

  def test_get_named_none_raises(self) -> None:
    """A module without a test class is refused."""
    self._scratchModule()
    with self.assertRaises(LookupError):
      AppTestRun.getNamed(_SCRATCH_MODULE)

  def test_get_named_not_a_test_case_raises(self) -> None:
    """A 'Run*'/'Test*' class that is no 'TestCase' is refused."""

    class RunNothing:
      pass

    self._scratchModule(RunNothing)
    with self.assertRaises(SubclassException):
      AppTestRun.getNamed(_SCRATCH_MODULE)

  def test_load_class_needs_one_name(self) -> None:
    """A child runs exactly one module."""
    with self.assertRaises(ValueError):
      AppTestRun._loadClass()
    with self.assertRaises(ValueError):
      AppTestRun._loadClass('a', 'b')

  def test_test_names(self) -> None:
    """Plain classes yield 'test*' methods; an 'AppTest' its collection."""

    class TestPlainNames(BaseTest):
      def test_a(self) -> None:
        pass

      def run_b(self) -> None:
        pass

    class RunAppNames(AppTest):
      def run_c(self) -> None:
        pass

    self.assertEqual(AppTestRun.testNames(TestPlainNames), ('test_a',))
    self.assertEqual(AppTestRun.testNames(RunAppNames), ('run_c',))

  def test_class_timeout(self) -> None:
    """The deadline comes from 'getTimeout', '__time_out__' or default."""

    class RunSlow(AppTest):
      __time_out__ = 99.0

    class TestPlainSlow(BaseTest):
      __time_out__ = 42.0

    class TestPlainDefault(BaseTest):
      pass

    self.assertEqual(AppTestRun._classTimeout(RunSlow), 99.0)
    self.assertEqual(AppTestRun._classTimeout(TestPlainSlow), 42.0)
    default = AppTestRun.__default_time_out__
    self.assertEqual(AppTestRun._classTimeout(TestPlainDefault), default)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DISPLAY FALLBACK   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_render_mode_env(self) -> None:
    """The authentic mode keeps the platform; headless forces offscreen."""
    env = {'QT_QPA_PLATFORM': 'xcb', 'OTHER': '1'}
    self.assertEqual(RenderMode.AUTHENTIC.applyEnv(env), env)
    headless = RenderMode.HEADLESS.applyEnv(env)
    self.assertEqual(headless['QT_QPA_PLATFORM'], 'offscreen')
    self.assertEqual(headless['OTHER'], '1')
    self.assertEqual(env['QT_QPA_PLATFORM'], 'xcb')

  def test_is_display_failure(self) -> None:
    """Only a failed child that says it had no display is one."""
    noDisplay = 'qt.qpa.xcb: could not connect to display'
    self.assertTrue(AppTestRun._isDisplayFailure(-6, noDisplay))
    self.assertFalse(AppTestRun._isDisplayFailure(0, noDisplay))
    self.assertFalse(AppTestRun._isDisplayFailure(3, 'AssertionError'))

  def test_falls_back_to_headless(self) -> None:
    """A child that had no display runs once more, headless."""
    modes = []
    noDisplay = 'qt.qpa.xcb: could not connect to display'

    def fakeLaunch(self, mode: RenderMode) -> tuple[int, str]:
      modes.append(mode)
      if mode is RenderMode.AUTHENTIC:
        return -6, noDisplay
      return 0, 'ran offscreen'

    with mock.patch.object(AppTestRun, '_launch', fakeLaunch):
      code, output = AppTestRun('any.module').run()
    self.assertEqual(modes, [RenderMode.AUTHENTIC, RenderMode.HEADLESS])
    self.assertEqual(code, 0)
    self.assertIn('ran headless', output)
    self.assertIn('ran offscreen', output)

  def test_genuine_failure_is_not_rerun(self) -> None:
    """A real test failure runs once, on the real display only."""
    modes = []

    def fakeLaunch(self, mode: RenderMode) -> tuple[int, str]:
      modes.append(mode)
      return 3, 'AssertionError: 1 != 2'

    with mock.patch.object(AppTestRun, '_launch', fakeLaunch):
      code, output = AppTestRun('any.module').run()
    self.assertEqual(modes, [RenderMode.AUTHENTIC])
    self.assertEqual(code, 3)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LAZY EXPORT  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_widget_test_is_lazy(self) -> None:
    """'WidgetTest' loads on access; an unknown name still raises."""
    self.assertTrue(issubclass(worQt.qtest.WidgetTest, AppTest))
    with self.assertRaises(AttributeError):
      _ = worQt.qtest.NoSuchThing
