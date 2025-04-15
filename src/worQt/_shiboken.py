"""For the purposes of type checking, Shiboken should be understood as the
metaclass creating the QObject class."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QObject

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  Shiboken = type(QObject)
else:
  Shiboken = type
