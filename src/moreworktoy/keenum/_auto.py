"""The auto function creates an enumeration member."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import auto as __auto__
from worktoy.keenum import NUM as __NUM__

try:
  from typing import TYPE_CHECKING, Any, Self
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class NUM(__NUM__):
  """The NUM class provides a temporary dataclass for enumeration
  entries."""

  @classmethod
  def fromValue(cls, *args) -> Self:
    """Create an enumeration member from a value."""
    self = cls()
    if len(args) == 1:
      self.val = args[0]
    else:
      self.val = args


def auto(*args, ) -> NUM:
  """The auto function creates an enumeration member."""
  return NUM.fromValue(*args, )
