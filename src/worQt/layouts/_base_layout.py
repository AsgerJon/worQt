"""
BaseLayout subclasses 'QGridLayout' and 'LayoutMixin' providing the base
layout class used across the 'worQt' framework. 'PySide6' does provide
several subclasses of 'QLayout' besides 'QGridLayout', but the
recommendation is to subclass this class to remake those based on the
provided 'QGridLayout' functionality.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout

from . import LayoutMixin

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class BaseLayout(QGridLayout, LayoutMixin):
  """
  BaseLayout subclasses 'QGridLayout' and 'LayoutMixin' providing the base
  layout class used across the 'worQt' framework. 'PySide6' does provide
  several subclasses of 'QLayout' besides 'QGridLayout', but the
  recommendation is to subclass this class to remake those based on the
  provided 'QGridLayout' functionality.
  """
