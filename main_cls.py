"""Tester classes"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

import shiboken6


class Meta(type(shiboken6.Shiboken.Object)):
  """Metaclass for PySide6"""
  pass


class Breh(metaclass=Meta):
  """Breh class"""
  pass
