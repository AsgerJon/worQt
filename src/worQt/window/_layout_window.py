"""LayoutWindow subclasses BaseWindow and adds widget and layout
management. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import BaseWindow

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class LayoutWindow(BaseWindow):
  """LayoutWindow subclasses BaseWindow and adds widget and layout
  management. """
