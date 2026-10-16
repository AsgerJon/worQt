"""
The 'worQt.widgets' package provides the widget components of the 'worQt'
framework. It provides custom layout and widget implementations. The base
widget class implements the box model for fine control of spacing and
alignments.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._widget_mixin import WidgetMixin
from ._abstract_widget import AbstractWidget
from ._base_widget import BaseWidget

__all__ = [
  'WidgetMixin',
  'AbstractWidget',
  'BaseWidget',
]
