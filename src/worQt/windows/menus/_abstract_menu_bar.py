"""
AbstractMenuBar subclasses 'QMenuBar' and 'MixinBase' and provides the
base for menu bars in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenuBar

from ...mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class AbstractMenuBar(QMenuBar, MixinBase):
  """
  AbstractMenuBar subclasses 'QMenuBar' and 'MixinBase' and provides the
  base for menu bars in the main window.
  """
