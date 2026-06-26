"""
TestSpaceTest covers 'SpaceTest' (the 'AppTest' namespace) and its
'DuplicateException': collecting test methods, the type guards on
'getTestMethods'/'addTestMethod', and the duplicate-name rejection.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException

from worQt.qtest import MetaTest
from worQt.qtest._space_test import SpaceTest, DuplicateException

from . import QTestTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


def _noop() -> None:
  """A trivial callable used as a stand-in test method."""


class TestSpaceTest(QTestTest):
  """Tests for the test-collecting namespace."""

  @staticmethod
  def _space(name: str = 'X') -> SpaceTest:
    return SpaceTest(MetaTest, name, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DUPLICATE EXCEPTION  # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_duplicate_exception_message(self) -> None:
    """'DuplicateException' renders the offending key."""
    self.assertIn('k', str(DuplicateException('k')))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GET TEST METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_get_none_is_empty(self) -> None:
    """An uncollected namespace yields an empty mapping."""
    self.assertEqual(self._space().getTestMethods(), {})

  def test_get_empty_is_empty(self) -> None:
    """An explicitly empty collection yields an empty mapping."""
    space = self._space()
    space.__test_methods__ = {}
    self.assertEqual(space.getTestMethods(), {})

  def test_get_valid(self) -> None:
    """A well-formed collection is returned unchanged."""
    space = self._space()
    space.__test_methods__ = {'test_x': _noop}
    self.assertEqual(space.getTestMethods(), {'test_x': _noop})

  def test_get_bad_value_raises(self) -> None:
    """A non-callable value raises 'TypeException'."""
    space = self._space()
    space.__test_methods__ = {'test_x': 123}
    with self.assertRaises(TypeException):
      space.getTestMethods()

  def test_get_bad_key_raises(self) -> None:
    """A non-string key raises 'TypeException'."""
    space = self._space()
    space.__test_methods__ = {123: _noop}
    with self.assertRaises(TypeException):
      space.getTestMethods()

  def test_get_bad_container_raises(self) -> None:
    """A non-dict collection raises 'TypeException'."""
    space = self._space()
    space.__test_methods__ = 'oops'
    with self.assertRaises(TypeException):
      space.getTestMethods()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ADD TEST METHOD  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_add_and_collect(self) -> None:
    """'addTestMethod' stores a method, readable via 'getTestMethods'."""
    space = self._space()
    space.addTestMethod('test_x', _noop)
    self.assertEqual(space.getTestMethods(), {'test_x': _noop})

  def test_add_bad_key_raises(self) -> None:
    """A non-string key raises 'TypeException'."""
    with self.assertRaises(TypeException):
      self._space().addTestMethod(123, _noop)

  def test_add_bad_method_raises(self) -> None:
    """A non-callable method raises 'TypeException'."""
    with self.assertRaises(TypeException):
      self._space().addTestMethod('test_x', 123)

  def test_add_duplicate_raises(self) -> None:
    """Re-adding the same key raises 'DuplicateException'."""
    space = self._space()
    space.addTestMethod('test_x', _noop)
    with self.assertRaises(DuplicateException):
      space.addTestMethod('test_x', _noop)
