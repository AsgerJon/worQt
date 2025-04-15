"""LayoutSpan class for managing layout spans in a grid layout."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import LayoutIndex

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class LayoutSpan(LayoutIndex):
  """LayoutSpan class for managing layout spans in a grid layout."""
  pass
