"""
TestAppTestSuite covers 'AppTestSuite': discovery (sorted, and blind to
the harness fixtures), the mapping of how a child ended to the reported
label, the run-and-report path with its exit status, and the guards on
'testsDir'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import contextlib
import io
import os
import tempfile
from typing import TYPE_CHECKING
from unittest import mock

from worktoy.waitaminute import TypeException

from worQt.qtest import AppTestRun, AppTestSuite

from . import QTestTest

if TYPE_CHECKING:  # pragma: no cover
  pass

_FIXTURES = 'tests.test_qtest.fixtures.'
_HERE = os.path.dirname(os.path.abspath(__file__))
_CHILD_VARIABLE = AppTestRun.__child_variable__


def _raisingRun(self) -> tuple[int, str]:
  """Stands in for 'AppTestRun.run' when the harness itself fails."""
  raise OSError('the harness broke')


def _quietRun(self) -> tuple[int, str]:
  """Stands in for 'AppTestRun.run' with a passing, chatty child."""
  return 0, 'child output'


class TestAppTestSuite(QTestTest):
  """Tests for 'AppTestSuite'."""

  #  Spawns two children.
  __time_out__ = 90.0

  @staticmethod
  def _capture(suite: AppTestSuite, *names: str) -> tuple[int, str]:
    """Runs 'names' through 'suite'; returns '(status, printed)'."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
      status = suite.runNames(*names)
    return status, buffer.getvalue()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DISCOVERY  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_scan_dir_is_sorted(self) -> None:
    """A directory scan lists modules in sorted, stable order."""
    root = os.path.dirname(os.path.dirname(_HERE))
    names, packageDirs = AppTestSuite._scanDir(_HERE, root)
    self.assertTrue(names)
    self.assertEqual([*names], sorted(names))
    self.assertIn(os.path.join(_HERE, 'fixtures'), packageDirs)

  def test_fixtures_are_not_discovered(self) -> None:
    """The deliberately failing fixtures are never part of the suite."""
    names = [*AppTestSuite()]
    self.assertIn('tests.test_qtest.test_app_test_suite', names)
    self.assertFalse([name for name in names if '.fixtures.' in name])

  def test_find_root_dir(self) -> None:
    """The root directory is the one holding 'tests'."""
    root = AppTestSuite._findRootDir()
    self.assertTrue(os.path.isdir(os.path.join(root, 'tests')))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DESCRIBE   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_describe(self) -> None:
    """Each way a child can end maps to its label."""
    describe = AppTestSuite._describe
    passCode = AppTestRun.__pass_code__
    failCode = AppTestRun.__fail_code__
    errorCode = AppTestRun.__error_code__
    self.assertEqual(describe(passCode, False, 0.0)[0], 'PASS')
    self.assertEqual(describe(failCode, False, 0.0)[0], 'FAIL')
    self.assertEqual(describe(errorCode, False, 0.0)[0], 'ERROR')
    self.assertEqual(describe(-11, False, 0.0)[0], 'CRASH')
    self.assertEqual(describe(-6, False, 0.0)[0], 'CRASH')
    self.assertEqual(describe(1, False, 0.0)[0], 'ERROR')

  def test_describe_timeout_comes_from_the_supervisor(self) -> None:
    """Only a kill by the supervisor is a TIMEOUT; any other -9 is not."""
    describe = AppTestSuite._describe
    self.assertEqual(describe(-9, True, 5.0)[0], 'TIMEOUT')
    self.assertIn('5s', describe(-9, True, 5.0)[1])
    self.assertEqual(describe(-9, False, 0.0)[0], 'CRASH')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  RUN AND REPORT   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_run_names_pass(self) -> None:
    """A passing module gives status 0; verbosity 3 shows its output."""
    suite = AppTestSuite()
    suite.verbosity = 3
    status, printed = self._capture(suite, _FIXTURES + '_plain')
    self.assertEqual(status, 0, printed)
    self.assertIn('PASS: %s_plain' % _FIXTURES, printed)
    self.assertIn('test_no_application', printed)

  def test_run_names_fail(self) -> None:
    """A failing module gives status 1 and shows the child's output."""
    suite = AppTestSuite()
    status, printed = self._capture(suite, _FIXTURES + '_fail')
    self.assertEqual(status, 1, printed)
    self.assertIn('FAIL: %s_fail' % _FIXTURES, printed)
    self.assertIn('run_fails', printed)
    self.assertIn('0 passed, 1 failed of 1 test classes', printed)

  def test_run_names_harness_failure(self) -> None:
    """A failure of the harness is an ERROR of that module, not a crash."""
    suite = AppTestSuite()
    with mock.patch.object(AppTestRun, 'run', _raisingRun):
      status, printed = self._capture(suite, 'any.module')
    self.assertEqual(status, 1)
    self.assertIn('the harness failed', printed)
    self.assertIn('the harness broke', printed)

  def test_verbosity_zero_is_silent(self) -> None:
    """At verbosity 0 nothing is printed."""
    suite = AppTestSuite()
    suite.verbosity = 0
    with mock.patch.object(AppTestRun, 'run', _quietRun):
      status, printed = self._capture(suite, 'any.module')
    self.assertEqual(status, 0)
    self.assertEqual(printed, '')

  def test_passing_output_hidden_at_verbosity_two(self) -> None:
    """At the default verbosity a passing class shows its status only."""
    suite = AppTestSuite()
    with mock.patch.object(AppTestRun, 'run', _quietRun):
      status, printed = self._capture(suite, 'any.module')
    self.assertEqual(status, 0)
    self.assertIn('PASS: any.module', printed)
    self.assertNotIn('child output', printed)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LATEST LOG   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_log_path_default(self) -> None:
    """By default the log is 'latest.log' in the project root."""
    logPath = AppTestSuite().logPath
    self.assertEqual(os.path.basename(logPath), 'latest.log')
    self.assertTrue(os.path.isdir(os.path.join(os.path.dirname(logPath),
                                               'tests')))

  def test_log_records_the_whole_run(self) -> None:
    """A top-level run logs everything, whatever the console verbosity."""
    suite = AppTestSuite()
    suite.verbosity = 0
    with tempfile.TemporaryDirectory() as tmp:
      suite.__log_path__ = os.path.join(tmp, 'latest.log')
      with mock.patch.dict(os.environ):
        os.environ.pop(_CHILD_VARIABLE, None)
        with mock.patch.object(AppTestRun, 'run', _quietRun):
          status, printed = self._capture(suite, 'any.module')
      with open(suite.__log_path__) as log:
        logged = log.read()
    self.assertEqual(status, 0)
    self.assertEqual(printed, '')
    self.assertIn('worQt.qtest run started', logged)
    self.assertIn('child output', logged)
    self.assertIn('PASS: any.module', logged)
    self.assertIn('1 passed, 0 failed of 1 test classes', logged)

  def test_log_left_alone_inside_a_test_child(self) -> None:
    """A suite running inside a test child never writes the log."""
    suite = AppTestSuite()
    suite.verbosity = 0
    with tempfile.TemporaryDirectory() as tmp:
      suite.__log_path__ = os.path.join(tmp, 'latest.log')
      with mock.patch.dict(os.environ, {_CHILD_VARIABLE: '1'}):
        with mock.patch.object(AppTestRun, 'run', _quietRun):
          self._capture(suite, 'any.module')
      self.assertFalse(os.path.exists(suite.__log_path__))

  def test_log_unwritable_is_not_fatal(self) -> None:
    """A log that cannot be written is reported, and the run goes on."""
    suite = AppTestSuite()
    with tempfile.TemporaryDirectory() as tmp:
      suite.__log_path__ = os.path.join(tmp, 'missing', 'latest.log')
      with mock.patch.dict(os.environ):
        os.environ.pop(_CHILD_VARIABLE, None)
        with mock.patch.object(AppTestRun, 'run', _quietRun):
          status, printed = self._capture(suite, 'any.module')
    self.assertEqual(status, 0)
    self.assertIn('Could not write the log', printed)
    self.assertIn('PASS: any.module', printed)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TESTS DIR  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_tests_dir_guards(self) -> None:
    """'testsDir' refuses a missing path, a file, and a non-string."""
    with self.assertRaises(FileNotFoundError):
      _ = AppTestSuite(os.path.join(_HERE, 'no_such_dir')).testsDir
    with self.assertRaises(NotADirectoryError):
      _ = AppTestSuite(os.path.abspath(__file__)).testsDir
    suite = AppTestSuite()
    suite.__tests_dir__ = 123
    with self.assertRaises(TypeException):
      _ = suite.testsDir

  def test_tests_dir_recursion_guard(self) -> None:
    """The lazy 'testsDir' getter refuses to recurse on a failed build."""
    with self.assertRaises(RecursionError):
      AppTestSuite()._getTestsDir(_recursion=True)

  def test_tests_dir_default(self) -> None:
    """By default 'testsDir' is the 'tests' directory under the root."""
    testsDir = AppTestSuite().testsDir
    self.assertEqual(os.path.basename(testsDir), 'tests')
