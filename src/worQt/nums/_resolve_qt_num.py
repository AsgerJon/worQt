"""
The 'resolveQtNum' function resolves the Qt Enum from an 'int'. Why does
this exist? Because .... ?
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from enum import EnumMeta
  from typing import Any


def _resolveIndex(enumType: EnumMeta, index: int) -> str:
  """Resolve the Qt Enum from an 'int'."""
  for name, value in enumType.__members__.items():
    if value.value == index:
      return name
  infoSpec = """No member of '%s' with value '%d' found!"""
  info = infoSpec % (enumType.__name__, index)
  raise IndexError(info)


def _resolveName(enumType: EnumMeta, name: str) -> str:
  """Resolve the Qt Enum from a 'str'."""
  for key, value in enumType.__members__.items():
    if key == name:
      return key
  infoSpec = """No member of '%s' with name '%s' found!"""
  info = infoSpec % (enumType.__name__, name)
  raise KeyError(info)


def resolveQtNum(enumType: EnumMeta, identifier: Any) -> str:
  """Resolve the Qt Enum from an 'int'.

  Args:
      enumType (EnumMeta): The Qt Enum type.
      identifier (Any): The integer value to resolve.

  Returns:
      str: The name of the enum member, or 'Unknown' if not found.
  """
  if isinstance(identifier, int):
    return _resolveIndex(enumType, identifier)
  if isinstance(identifier, str):
    return _resolveName(enumType, identifier)
  raise TypeException('identifier', identifier, int, str)
