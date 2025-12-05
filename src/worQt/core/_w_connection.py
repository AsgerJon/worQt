"""
WConnection attempts to subclass the type of the object returned by
connecting signals to slots.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QMetaObject


class WConnection(QMetaObject.Connection):
  """
  WConnection attempts to subclass the type of the object returned by
  connecting signals to slots.
  """
