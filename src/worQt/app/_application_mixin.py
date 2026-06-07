"""
ApplicationMixin subclasses 'QApplication' and 'MixinBase' creating the
entry point for application classes. It combines the 'QApplication' with
the 'worktoy.mcls.BaseObject' functionality.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication
from ..mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  pass


class ApplicationMixin(QApplication, MixinBase):
  """
  ApplicationMixin subclasses 'QApplication' and 'MixinBase' creating the
  entry point for application classes. It combines the 'QApplication' with
  the 'worktoy.mcls.BaseObject' functionality.
  """
