"""
TestMetaTest covers how an 'AppTest' class collects its test methods: by
name prefix, plain functions only, and inherited from base test classes so
a test written once on a base runs on every subclass.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox

from worQt.qtest import AppTest

from . import QTestTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestMetaTest(QTestTest):
  """Tests for the test-method collection of 'MetaTest'."""

  def test_prefixes(self) -> None:
    """'run*' and 'test*' functions are collected; others are not."""

    class RunPrefixes(AppTest):
      def run_a(self) -> None:
        pass

      def test_b(self) -> None:
        pass

      def check_c(self) -> None:
        pass

    self.assertEqual([*RunPrefixes.testMethods], ['run_a', 'test_b'])

  def test_only_plain_functions(self) -> None:
    """A classmethod, staticmethod or callable field is never a test."""

    class RunHelpers(AppTest):
      testBox = AttriBox[int](0)

      @classmethod
      def runHelper(cls) -> None:
        pass

      @staticmethod
      def testStatic() -> None:
        pass

    self.assertEqual(RunHelpers.testMethods, {})
    self.assertNotIn('runTest', AppTest.testMethods)

  def test_inherited(self) -> None:
    """Tests on a base class are collected on the subclass, base first."""

    class RunBase(AppTest):
      def run_base(self) -> None:
        pass

    class RunDerived(RunBase):
      def run_derived(self) -> None:
        pass

    self.assertEqual([*RunDerived.testMethods], ['run_base', 'run_derived'])

  def test_override_replaces(self) -> None:
    """A subclass redefining a test replaces it, keeping one entry."""

    class RunBase(AppTest):
      def run_shared(self) -> None:
        pass

    class RunDerived(RunBase):
      def run_shared(self) -> None:
        pass

    methods = RunDerived.testMethods
    self.assertEqual([*methods], ['run_shared'])
    self.assertEqual(methods['run_shared'].__qualname__.split('.')[-2],
                     'RunDerived')
