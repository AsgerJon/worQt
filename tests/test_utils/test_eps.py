"""
TestEps subclasses 'UtilsTest' and tests the 'worQt.utils.Eps' descriptor,
which exposes 'sys.float_info.epsilon' read-only. It is plain Python, so no
'QApplication' is needed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from worktoy.waitaminute.desc import ReadOnlyError, ProtectedError

from worQt.utils import Eps

from . import UtilsTest


class _EpsHost:
  """A throwaway owner carrying an 'Eps' descriptor."""

  eps = Eps()


class TestEps(UtilsTest):
  """Tests for the 'Eps' descriptor."""

  def test_value(self) -> None:
    """Reading through an instance yields the machine epsilon."""
    self.assertEqual(_EpsHost().eps, sys.float_info.epsilon)

  def test_class_access_returns_descriptor(self) -> None:
    """Reading through the class returns the descriptor itself."""
    self.assertIsInstance(_EpsHost.eps, Eps)

  def test_read_only(self) -> None:
    """Assignment is refused."""
    with self.assertRaises(ReadOnlyError):
      _EpsHost().eps = 1.0

  def test_protected(self) -> None:
    """Deletion is refused."""
    with self.assertRaises(ProtectedError):
      del _EpsHost().eps

  def test_str_and_repr(self) -> None:
    """The string forms name the field and the source expression."""
    self.assertIn('eps', str(_EpsHost.eps))
    self.assertEqual(repr(_EpsHost.eps), 'sys.float_info.epsilon')

  def test_str_unowned(self) -> None:
    """An 'Eps' not assigned to a class names the source expression."""
    self.assertIn('epsilon', str(Eps()))
