"""
TestAppTestRun covers 'AppTestRun': the 'appTestType' accessor and its
guards, the in-process 'TestCase' path ('_runPlain') for a passing and a
failing class, and the subprocess path ('_runPopen') driven once against a
real, fast 'AppTest' with the coverage env unset so its env-conditional
branch is taken.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.waitaminute import MissingVariable, TypeException
from worktoy.work_test import BaseTest

from worQt.qtest import AppTestRun, AppTestSuite

from . import QTestTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _PassingPlain(BaseTest):
  """A plain passing 'TestCase' for the in-process runner."""

  def test_ok(self) -> None:
    self.assertTrue(True)


class _FailingPlain(BaseTest):
  """A plain failing 'TestCase' for the in-process runner."""

  def test_bad(self) -> None:
    self.assertTrue(False)


class TestAppTestRun(QTestTest):
  """Tests for the per-class runner."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ACCESSOR   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_missing_app_test_type(self) -> None:
    """Reading 'appTestType' before it is set raises 'MissingVariable'."""
    with self.assertRaises(MissingVariable):
      _ = AppTestRun().appTestType

  def test_bad_ctor_type(self) -> None:
    """Constructing with a non-'BaseTest' type raises 'TypeException'."""
    with self.assertRaises(TypeException):
      AppTestRun(int)

  def test_bad_stored_type(self) -> None:
    """A non-'BaseTest' value in the slot raises on read."""
    runner = AppTestRun()
    runner.__app_test_type__ = int
    with self.assertRaises(TypeException):
      _ = runner.appTestType

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  IN-PROCESS RUN  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_run_plain_pass(self) -> None:
    """A passing plain 'TestCase' yields exit code 0 and no output."""
    self.assertEqual(AppTestRun(_PassingPlain).run(), (0, ''))

  def test_run_plain_fail(self) -> None:
    """A failing plain 'TestCase' yields exit code 3 and runner output."""
    code, output = AppTestRun(_FailingPlain).run()
    self.assertEqual(code, 3)
    self.assertTrue(output.strip())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SUBPROCESS RUN  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_run_popen_without_coverage(self) -> None:
    """An 'AppTest' class runs in its own process; with the coverage env
    unset the non-coverage argv branch is taken."""
    cls = AppTestSuite.getNamed('tests.test_app.test_exec')
    saved = os.environ.pop('WORQT_COVERAGE', None)
    try:
      code, _ = AppTestRun(cls).run()
    finally:
      if saved is not None:
        os.environ['WORQT_COVERAGE'] = saved
    self.assertEqual(code, 0)
