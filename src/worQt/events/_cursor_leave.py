"""
CursorLeave subclasses AbstractEvent and encapsulates the event where the
cursor leaves the mouse area in the custom event system. Instances respect
the 'getMouseArea' method of the owning widget.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import CursorEvent

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


class CursorLeave(CursorEvent):
  """
  CursorLeave subclasses AbstractEvent and encapsulates the event where the
  cursor leaves the mouse area in the custom event system. Instances respect
  the 'getMouseArea' method of the owning widget.
  """
