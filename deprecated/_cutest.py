"""
Cutest is the worQt-native test base. Subclass it and add methods whose
names start with 'test'. Assertions just raise 'AssertionError', so a
failure prints a normal traceback you can read.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Cutest(BaseObject):
  """Base class for worQt tests. Add 'test*' methods and pass the class
  to 'runTests'."""

  def setUp(self) -> None:
    """Hook run before each test method. Override as needed."""

  def tearDown(self) -> None:
    """Hook run after each test method. Override as needed."""

  def fail(self, message: str) -> None:
    """Fails the current test with 'message'."""
    raise AssertionError(message)

  def assertTrue(self, value: Any) -> None:
    """Fails unless 'value' is truthy."""
    if not value:
      self.fail('expected truthy, got: %r' % (value,))

  def assertFalse(self, value: Any) -> None:
    """Fails unless 'value' is falsy."""
    if value:
      self.fail('expected falsy, got: %r' % (value,))

  def assertEqual(self, left: Any, right: Any) -> None:
    """Fails unless 'left' equals 'right'."""
    if left != right:
      self.fail('%r != %r' % (left, right))
