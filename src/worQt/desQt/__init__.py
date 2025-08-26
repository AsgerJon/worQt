"""
The 'worQt.app.des_qt' module provides non-general descriptors specific to
the 'worQt' library.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import pens
from ._app import App
from ._etc import Etc
from ._resources import Resources
from ._sounds import Sounds
from ._state_flag import StateFlag

___all__ = [
    'pens',
    'App',
    'Etc',
    'Resources',
    'Sounds',
    'StateFlag',
]
