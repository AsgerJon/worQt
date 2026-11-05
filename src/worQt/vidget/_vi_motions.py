"""
The Vi motions as plain functions of a text and a position in it: each
returns where the motion lands, or 'None' where it finds nothing to go
to. They know nothing of Qt or of the widget, so the 'Vidget' commands
and the tests share them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional

_BLANKS = ' \t\n'


def charKind(char: str, big: bool) -> int:
  """
  The 'charKind' function returns the kind of 'char' for word motions: 0
  for whitespace, 1 for a letter, a digit or '_', 2 for anything else. A
  'big' word, Vi's WORD, is any run of non-whitespace, so then all of
  that is kind 1.
  """
  if char in _BLANKS:
    return 0
  if big or str.isalnum(char) or char == '_':
    return 1
  return 2


def lineStart(text: str, index: int) -> int:
  """The start of the line holding 'index'."""
  return str.rfind(text, '\n', 0, index) + 1


def lineEnd(text: str, index: int) -> int:
  """The end of the line holding 'index': its line break, or the end of
  the text."""
  end = str.find(text, '\n', index)
  return len(text) if end < 0 else end


def firstNonBlank(text: str, index: int) -> int:
  """The first character on the line holding 'index' that is not a space
  or a tab, or the line's end."""
  at, end = lineStart(text, index), lineEnd(text, index)
  while at < end and text[at] in ' \t':
    at += 1
  return at


def wordForward(text: str, index: int, count: int, big: bool) -> int:
  """'w' and 'W': the start of the 'count'th word after 'index'."""
  for _ in range(count):
    kind = charKind(text[index], big) if index < len(text) else 0
    while kind and index < len(text) and charKind(text[index], big) == kind:
      index += 1
    while index < len(text) and not charKind(text[index], big):
      index += 1
  return index


def wordBackward(text: str, index: int, count: int, big: bool) -> int:
  """'b' and 'B': the start of the 'count'th word before 'index'."""
  for _ in range(count):
    index -= 1
    while index > 0 and not charKind(text[index], big):
      index -= 1
    if index <= 0:
      return 0
    kind = charKind(text[index], big)
    while index > 0 and charKind(text[index - 1], big) == kind:
      index -= 1
  return index


def wordEnd(text: str, index: int, count: int, big: bool) -> int:
  """'e' and 'E': the last character of the 'count'th word ending after
  'index'."""
  for _ in range(count):
    index += 1
    while index < len(text) and not charKind(text[index], big):
      index += 1
    if index >= len(text):
      return max(len(text) - 1, 0)
    kind = charKind(text[index], big)
    while index + 1 < len(text) and charKind(text[index + 1], big) == kind:
      index += 1
  return index


def _isBlankLine(text: str, start: int) -> bool:
  return False if str.strip(text[start:lineEnd(text, start)]) else True


def paragraphForward(text: str, index: int, count: int) -> int:
  """'}': the blank line after the 'count'th paragraph from 'index', or
  the end of the text. A blank line holds nothing but whitespace."""
  at = lineStart(text, index)
  for _ in range(count):
    while at < len(text) and _isBlankLine(text, at):
      at = lineEnd(text, at) + 1
    while not _isBlankLine(text, at):
      end = lineEnd(text, at)
      if end >= len(text):
        return len(text)
      at = end + 1
  return min(at, len(text))


def paragraphBackward(text: str, index: int, count: int) -> int:
  """'{': the blank line before the 'count'th paragraph back from
  'index', or the start of the text."""
  at = lineStart(text, index)
  for _ in range(count):
    while at > 0 and _isBlankLine(text, at):
      at = lineStart(text, at - 1)
    while at > 0 and not _isBlankLine(text, at):
      at = lineStart(text, at - 1)
  return at


def findInLine(
    text: str,
    index: int,
    char: str,
    count: int,
    forward: bool,
    till: bool,
) -> Optional[int]:
  """
  'f', 't', 'F' and 'T': the 'count'th 'char' after 'index' on the same
  line, or before it when not 'forward'; with 'till', the character
  just short of it. 'None' if the line holds not so many.
  """
  start, end = lineStart(text, index), lineEnd(text, index)
  step, at = 1 if forward else -1, index
  for _ in range(count):
    at += step
    while start <= at < end and text[at] != char:
      at += step
    if not start <= at < end:
      return None
  return at - step if till else at


def search(
    text: str,
    index: int,
    pattern: str,
    forward: bool,
) -> Optional[int]:
  """
  '/', '?', 'n' and 'N': where 'pattern' next occurs after 'index', or
  before it when not 'forward', wrapping around the end of the text as
  Vi does. 'None' if it occurs nowhere.
  """
  if not pattern:
    return None
  if forward:
    found = str.find(text, pattern, index + 1)
    found = str.find(text, pattern) if found < 0 else found
  else:
    #  An occurrence starting before 'index' may reach past it.
    found = str.rfind(text, pattern, 0, max(index + len(pattern) - 1, 0))
    found = str.rfind(text, pattern) if found < 0 else found
  return None if found < 0 else found
