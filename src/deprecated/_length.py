"""Length subclasses AbstractInterval and provides. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import Field
from worktoy.parse import maybe

from worQt.tools.geometry import AbstractValue

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class Length(AbstractValue):
  """Length subclasses AbstractInterval and provides a length in 2D
  space. """

  __fallback_value__ = 0
  __pvt_value__ = None
