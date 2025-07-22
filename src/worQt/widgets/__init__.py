"""
The 'worQt.widgets' provides layouts and widgets used across the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._base_widget import BaseWidget
from ._layout import Layout
from ._box_widget import BoxWidget

__all__ = [
    'BaseWidget',
    'Layout',
    'BoxWidget',
]
