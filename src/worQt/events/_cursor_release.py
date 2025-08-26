"""
CursorRelease subclasses CursorEvent and encapsulates the event where the
mouse button is released in the custom event system. Instances respect the
'getMouseArea' method of the owning widget.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import CursorEvent

if TYPE_CHECKING:  # pragma: no cover
  pass


class CursorRelease(CursorEvent):
  """
  CursorRelease subclasses CursorEvent and encapsulates the event where the
  mouse button is released in the custom event system. Instances respect the
  'getMouseArea' method of the owning widget.
  """
