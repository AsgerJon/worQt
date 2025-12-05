"""
The 'worQt.res' package provides centrally managed resources used across
the 'worQt' framework. This centralizes role-specific resources such as
icons, shortcuts, and other assets without tying them to specific
implementations.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._get_icon import getIcon
from ._get_short_cut import getShortCut

__all__ = [
    'getIcon',
    'getShortCut',
]
