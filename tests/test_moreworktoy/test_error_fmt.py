"""
TestErrorFmt subclasses 'MoreWorktoyTest' and covers the 'errorFmt'
traceback formatter. It is plain Python, so no 'QApplication' is needed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import re
import sys

from worktoy.waitaminute import TypeException

from moreworktoy.utilities import errorFmt

from . import MoreWorktoyTest

_ANSI = re.compile(r'\x1b\[[0-9;]*m')


def _plain(text: str) -> str:
  """Strip ANSI colour codes so content can be asserted on."""
  return _ANSI.sub('', text)


def _boom() -> object:
  """A module-level helper that raises 'AttributeError'."""
  marker = 1
  return marker.no_such_attr


class _Sample:
  """A class whose method raises, exercising the sticky headers."""

  def method(self) -> object:
    """Raise 'AttributeError' from inside a class method."""
    value = 2
    return value.no_such_method()


def _useMissing() -> object:
  """Reference an undefined global to raise 'NameError'."""
  base = 10
  return base + undefinedName  # noqa


class TestErrorFmt(MoreWorktoyTest):
  """Tests for 'errorFmt' and its helpers."""

  def test_rejects_non_exception(self) -> None:
    """A non-exception argument is refused."""
    with self.assertRaises(TypeException):
      errorFmt('not an exception')

  def test_requires_traceback(self) -> None:
    """An exception without a traceback is refused."""
    with self.assertRaises(ValueError):
      errorFmt(ValueError('never raised'))

  def test_header_and_message(self) -> None:
    """The header names the exception type and its message."""
    try:
      _ = 1 / 0
    except Exception as exc:
      out = _plain(errorFmt(exc))
    self.assertIn('Caught ZeroDivisionError', out)
    self.assertIn('division by zero', out)

  def test_caret_marker(self) -> None:
    """The offending line carries a caret row with the 'E >' gutter."""
    try:
      _ = 1 / 0
    except Exception as exc:
      out = _plain(errorFmt(exc))
    self.assertIn('^', out)
    self.assertIn('E >', out)

  def test_source_window(self) -> None:
    """A called helper shows its own source line in the window."""
    try:
      _boom()
    except Exception as exc:
      out = _plain(errorFmt(exc))
    self.assertIn('no_such_attr', out)

  def test_sticky_headers(self) -> None:
    """A method error sticks the class and method headers on top."""
    try:
      _Sample().method()
    except Exception as exc:
      out = _plain(errorFmt(exc))
    self.assertIn('class _Sample', out)
    self.assertIn('def method', out)
    self.assertIn('from file:', out)

  def test_precise_caret_span(self) -> None:
    """On 3.11+, the caret underlines the exact failing name."""
    if sys.version_info < (3, 11):
      return
    try:
      _useMissing()
    except Exception as exc:
      out = _plain(errorFmt(exc))
    counts = [ln.count('^') for ln in str.splitlines(out) if '^' in ln]
    self.assertIn(len('undefinedName'), counts)
