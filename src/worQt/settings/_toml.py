"""
A deliberately small TOML reader and writer, covering exactly the shape the
settings system produces: a document of '[section]' tables, each a flat set
of 'key = value' pairs whose values are strings, integers, floats or
booleans. Comments ('#' to end of line, outside strings) are honoured on
read. This is not a general TOML implementation - nested tables, arrays,
dates and multi-line strings are out of scope - but it round-trips every
file this package writes, with no third-party dependency.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

_ESCAPES = {'\\': '\\\\', '"': '\\"', '\n': '\\n', '\t': '\\t', '\r': '\\r'}
_UNESCAPES = {'\\': '\\', '"': '"', 'n': '\n', 't': '\t', 'r': '\r'}


def _encodeString(text: str) -> str:
  """Render 'text' as a quoted, escaped TOML basic string."""
  return '"%s"' % (''.join(_ESCAPES.get(ch, ch) for ch in text),)


def _encodeValue(value: Any) -> str:
  """Render a scalar as TOML. 'bool' is checked before 'int' (a subclass)."""
  if isinstance(value, bool):
    return 'true' if value else 'false'
  if isinstance(value, int):
    return str(value)
  if isinstance(value, float):
    return repr(value)  # keeps the decimal point and any exponent
  if value is None:
    return '""'
  return _encodeString(str(value))


def dumpToml(data: dict) -> str:
  """
  Serialise 'data' (a mapping whose values are scalars or flat sub-tables)
  to TOML text. Scalar top-level keys come first, then one '[name]' table
  per sub-mapping. Returns the empty string for empty input.
  """
  lines = []
  scalars = [(k, v) for k, v in data.items() if not isinstance(v, dict)]
  tables = [(k, v) for k, v in data.items() if isinstance(v, dict)]
  for key, value in scalars:
    lines.append('%s = %s' % (key, _encodeValue(value)))
  for name, table in tables:
    if lines:
      lines.append('')
    lines.append('[%s]' % (name,))
    for key, value in table.items():
      lines.append('%s = %s' % (key, _encodeValue(value)))
  if not lines:
    return ''
  return '\n'.join(lines) + '\n'


def _stripComment(line: str) -> str:
  """Drop an unquoted '#' comment, leaving any '#' inside a string alone."""
  inString = False
  escaped = False
  for index, ch in enumerate(line):
    if inString:
      if escaped:
        escaped = False
      elif ch == '\\':
        escaped = True
      elif ch == '"':
        inString = False
      continue
    if ch == '"':
      inString = True
    elif ch == '#':
      return line[:index]
  return line


def _decodeString(body: str) -> str:
  """Undo the escaping done by '_encodeString' on a string's inner text."""
  out = []
  index = 0
  length = len(body)
  while index < length:
    ch = body[index]
    if ch == '\\' and index + 1 < length:
      out.append(_UNESCAPES.get(body[index + 1], body[index + 1]))
      index += 2
      continue
    out.append(ch)
    index += 1
  return ''.join(out)


def _decodeValue(text: str) -> Any:
  """Parse a single TOML scalar: string, bool, int or float (else bare)."""
  if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
    return _decodeString(text[1:-1])
  if text == 'true':
    return True
  if text == 'false':
    return False
  try:
    return int(text)
  except ValueError:
    pass
  try:
    return float(text)
  except ValueError:
    pass
  return text  # an unquoted, non-numeric bareword: keep it as a string


def loadToml(text: str) -> dict:
  """
  Parse TOML 'text' produced by 'dumpToml' (or a compatible hand edit) into
  a mapping of '{section: {key: value}}'. Keys before any '[section]' land
  at the top level. Raises 'ValueError' on a non-blank line that is neither
  a section header nor a 'key = value' pair.
  """
  data = {}
  current = data
  for rawLine in text.splitlines():
    line = _stripComment(rawLine).strip()
    if not line:
      continue
    if line[0] == '[' and line[-1] == ']':
      name = line[1:-1].strip()
      current = {}
      data[name] = current
      continue
    if '=' not in line:
      raise ValueError('Malformed settings line: %r' % (rawLine,))
    key, _, valueText = line.partition('=')
    current[key.strip()] = _decodeValue(valueText.strip())
  return data
