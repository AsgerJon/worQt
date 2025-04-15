"""StatusBar provides the status bar for the main application window."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QStatusBar

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class StatusBar(QStatusBar):
  """StatusBar provides the status bar for the main application window."""
  pass
