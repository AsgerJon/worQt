"""
The 'errorFmt' function provides a well styled error message for
exceptions.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING
from traceback import StackSummary, FrameSummary, walk_tb

from worktoy.waitaminute import TypeException

from . import textFmt, wordWrap

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional

fillWidth = 77
redSym = '\x1b[31m'
blueSym = '\x1b[38;2;65;105;225m'  # royal blue
resetSym = '\x1b[0m'
_spaceToken = re.compile(r'\{\{(\d+)Spaces\}\}')


def _freeze(n: int) -> str:
  """
  The '_freeze' function encodes 'n' verbatim spaces as a token that
  survives 'textFmt' whitespace collapsing, expanded back by '_thaw'.
  """
  return '{{%dSpaces}}' % n if n > 0 else ''


def _thaw(text: str) -> str:
  """
  The '_thaw' function restores frozen space tokens to literal spaces.
  """

  def expand(match) -> str:
    return ' ' * int(match.group(1))

  return _spaceToken.sub(expand, text)


def _fillBorder(label: str, fill: str) -> str:
  """
  The '_fillBorder' function centers 'label' on the full fill width,
  padding out to both edges with the 'fill' character.
  """
  pad = fillWidth - len(label)
  if pad < 2:
    return label
  left = pad // 2
  return '%s%s%s' % (fill * left, label, fill * (pad - left))


def _gutter(numStr: str, numWidth: int) -> str:
  """
  The '_gutter' function builds the right-aligned line-number column
  followed by the ' | ' separator, all frozen to survive 'textFmt'.
  """
  pad = numWidth - len(numStr)
  return '%s%s%s|%s' % (_freeze(pad), numStr, _freeze(1), _freeze(1))


def _wrap(text: str, width: int) -> list[str]:
  """
  The '_wrap' function reflows 'text' to 'width' via worktoy 'wordWrap'
  and returns the resulting lines.
  """
  if not text:
    return ['', ]
  return str.split(wordWrap(max(1, width), text), os.linesep)


def _wrapPath(text: str, width: int) -> list[str]:
  """
  The '_wrapPath' function breaks 'text' onto lines of at most 'width',
  splitting only after a '/' or '.' separator (kept at the end of the
  continued line).
  """
  lines: list[str] = []
  cur = ''
  chunk = ''
  for ch in text:
    chunk += ch
    if ch == '/' or ch == '.':
      if cur and len(cur) + len(chunk) > width:
        lines.append(cur)
        cur = chunk
      else:
        cur += chunk
      chunk = ''
  cur += chunk
  lines.append(cur)
  return lines


def _elide(text: str, width: int) -> str:
  """
  The '_elide' function trims 'text' from the left to fit 'width',
  marking the dropped prefix with a leading ellipsis so the trailing
  part - the useful end - always survives.
  """
  if len(text) <= width:
    return text
  if width < 2:
    return text[len(text) - width:] if width > 0 else ''
  return '…%s' % text[len(text) - width + 1:]


def _publicQualName(qualName: str) -> str:
  """
  The '_publicQualName' function drops closure noise: each '<locals>'
  marker and the enclosing local function it belongs to, e.g.
  'Dispatcher._createCachedFunction.<locals>.dispatch' ->
  'Dispatcher.dispatch'.
  """
  out: list[str] = []
  for part in str.split(qualName, '.'):
    if part == '<locals>':
      if out:
        out.pop()
      continue
    out.append(part)
  return str.join('.', out) if out else qualName


def _readSource(fileName: str) -> list[str]:
  """
  The '_readSource' function returns the newline-stripped lines of the
  source file at 'fileName'.
  """
  handle = None
  try:
    handle = open(fileName, 'r', encoding='utf-8')
    rawLines: list[str] = handle.readlines()
  finally:
    if handle is not None:
      handle.close()
  return [str.rstrip(line, '\n') for line in rawLines]


def _colSpan(frameObj, lasti: int):
  """
  The '_colSpan' function returns the exact '(startCol, endCol,
  endLine)' of the failing instruction from 'co_positions' (Python
  3.11+), or '(None, None, None)' when positions are unavailable.
  """
  positioner = getattr(frameObj.f_code, 'co_positions', None)
  if positioner is None:  #  pre-3.11
    return None, None, None
  try:
    startLine, endLine, col, endCol = tuple(positioner())[lasti // 2]
  except Exception:
    return None, None, None
  return col, endCol, endLine


def _stickyHeaders(lines: list[str], idx: int) -> list[int]:
  """
  The '_stickyHeaders' function returns the line indices of the
  enclosing 'def'/'class' headers above line 'idx', outermost first,
  as PyCharm shows them stuck to the top of the editor.
  """
  positions: list[int] = []
  minIndent = len(lines[idx]) - len(str.lstrip(lines[idx]))
  for pos in range(idx - 1, -1, -1):
    stripped = str.lstrip(lines[pos])
    if not stripped:
      continue
    indent = len(lines[pos]) - len(stripped)
    if indent >= minIndent:
      continue
    minIndent = indent
    if (str.startswith(stripped, 'def ')
        or str.startswith(stripped, 'class ')
        or str.startswith(stripped, 'async def ')):
      positions.append(pos)
  return positions[::-1]


def _codeRows(lines: list[str], pos: int, numWidth: int,
              contentW: int) -> list[str]:
  """
  The '_codeRows' function renders one source line as gutter-prefixed
  rows, wrapping to 'contentW' with double-indented continuations.
  """
  srcLine = lines[pos]
  indentN = len(srcLine) - len(str.lstrip(srcLine))
  segments = _wrap(str.strip(srcLine), contentW - indentN - 4)
  out: list[str] = []
  for segIdx, seg in enumerate(segments):
    numStr = str(pos + 1) if not segIdx else ''
    indent = indentN if not segIdx else indentN + 4
    out.append('%s%s%s' % (
        _gutter(numStr, numWidth), _freeze(indent), seg))
  return out


def _dottedRow(numWidth: int, contentW: int, firstNo: int,
               lastNo: int) -> str:
  """
  The '_dottedRow' function renders the blue dotted separator standing
  in for the source lines omitted below a sticky header, with a '~' in
  the line-number column.
  """
  if lastNo > firstNo:
    label = ' %d - %d ' % (firstNo, lastNo)
  elif lastNo == firstNo:
    label = ' %d ' % firstNo
  else:
    label = ''
  pad = max(0, contentW - len(label))
  left = pad // 2
  content = '%s%s%s' % ('.' * left, label, '.' * (pad - left))
  gutter = '%s%s~%s%s%s:%s%s' % (
      _freeze(numWidth - 1), blueSym, resetSym, _freeze(1), blueSym,
      resetSym, _freeze(1))
  return '%s%s%s%s' % (gutter, blueSym, content, resetSym)


def _caretRow(numWidth: int, contentW: int, startCol: int,
              endCol: int) -> str:
  """
  The '_caretRow' function builds the red caret row pointing at the
  offending column span of the line above it, with a red 'E' in the
  line-number column and red dots bridging out to the carets.
  """
  caretWidth = max(1, endCol - startCol)
  offset = startCol if startCol < contentW else 0
  if offset + caretWidth > contentW:
    caretWidth = max(1, contentW - offset)
  errGutter = '%s%sE%s%s%s>%s%s' % (
      _freeze(numWidth - 1), redSym, resetSym, _freeze(1), redSym,
      resetSym, _freeze(1))
  return '%s%s%s%s%s' % (
      errGutter, redSym, '.' * offset, '^' * caretWidth, resetSym)


def _renderFrame(frame: FrameSummary, frameObj, excType: str,
                 span) -> list[str]:
  """
  The '_renderFrame' function renders one traceback frame as a box: the
  exception type on the top border, the enclosing scope stuck above the
  source window (omitted lines dotted out) with a red caret on the
  offending line, and the dotted 'module.qualname' on the bottom border.
  """
  fileName: str = frame.filename
  topRow = '_' * fillWidth
  botRow = '¨' * fillWidth
  try:
    lines: list[str] = _readSource(fileName)
  except Exception:
    lines = []
  lineNo: int = frame.lineno or 0
  idx: int = lineNo - 1
  if not lines or idx < 0 or idx >= len(lines):
    return [topRow, botRow, ]
  start: int = max(0, idx - 3)
  stop: int = min(len(lines), idx + 4)
  numWidth: int = len(str(stop))
  contentW: int = fillWidth - (numWidth + 3)
  #  Exact columns on 3.11+; whole-line fallback on older / unknown.
  startCol, endCol, endLine = span
  if startCol is None or endCol is None:
    startCol = len(lines[idx]) - len(str.lstrip(lines[idx]))
    endCol = len(lines[idx])
  elif endLine != lineNo:  #  span crosses lines; stop at this line's end
    endCol = len(lines[idx])
  rows: list[str] = [topRow, _gutter('', numWidth), ]
  headers = _stickyHeaders(lines, idx)
  winStart = start
  if headers:
    winStart = max(start, headers[-1] + 1)
    for i, pos in enumerate(headers):
      rows.extend(_codeRows(lines, pos, numWidth, contentW))
      nextPos = headers[i + 1] if i + 1 < len(headers) else winStart
      if nextPos > pos + 1:  #  only when lines were actually omitted
        rows.append(_dottedRow(numWidth, contentW, pos + 2, nextPos))
  for pos in range(winStart, stop):
    rows.extend(_codeRows(lines, pos, numWidth, contentW))
    if pos == idx:
      rows.append(_caretRow(numWidth, contentW, startCol, endCol))
  rows.append(botRow)
  return rows


def errorFmt(exception: Exception, ) -> str:
  """
  The 'errorFmt' function provides a well styled error message for
  exceptions.

  :param exception: The exception to format.
  """
  if not isinstance(exception, Exception):
    raise TypeException('exception', exception, Exception)
  excType: str = type(exception).__name__
  excMsg: str = str(exception)
  excTraceback = exception.__traceback__
  if excTraceback is None:
    raise ValueError('No traceback found in exception.')
  #  Raw traceback keeps frame objects and 'tb_lasti' for exact
  #  columns; summaries carry the source line and names.
  rawFrames = []
  tb = excTraceback
  while tb is not None:
    rawFrames.append((tb.tb_frame, tb.tb_lasti))
    tb = tb.tb_next
  rawFrames = rawFrames[::-1]
  summaries = [*StackSummary.extract(walk_tb(excTraceback))][::-1]
  rows: list[str] = []
  #  Exception summary first, so it sits with the error site: the frames
  #  are rendered deepest-first, so the frame that raised comes next.
  rows.append('_' * fillWidth)
  rows.append('Caught %s' % excType)
  rows.append('¨' * fillWidth)
  if excMsg:
    for msgLine in _wrap(excMsg, fillWidth - 2):
      rows.append('%s%s' % (_freeze(2), msgLine))
  for i, frame in enumerate(summaries):
    fileName = frame.filename
    #  Synthetic frames (frozen imports, '<string>', ...) have no readable
    #  source and would render as empty boxes, so they are skipped.
    if str.startswith(fileName, '<') and str.endswith(fileName, '>'):
      continue
    frameObj, lasti = rawFrames[i]
    rows.append('')  #  blank line before each frame
    rows.append('from file:')
    for pathLine in _wrapPath(frame.filename, fillWidth - 2):
      rows.append('%s%s' % (_freeze(2), pathLine))
    rows.extend(_renderFrame(frame, frameObj, excType,
                             _colSpan(frameObj, lasti)))
  return _thaw(textFmt(str.join('<br>', rows)))
