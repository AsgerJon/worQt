"""
BaseWidget creates the entry point that combines 'QWidget' with 'MixinBase'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from ..mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  pass


class BaseWidget(QWidget, MixinBase):
  """
  BaseWidget creates the entry point that combines 'QWidget' with
  'MixinBase'.
  """
