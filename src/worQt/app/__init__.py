"""The 'worQt.app' module provides the App class inheriting from
QApplication. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._abstract_application import AbstractApplication
from ._main import Main

__all__ = [
    'AbstractApplication',
    'Main'
]
