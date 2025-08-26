"""
The 'worQt.waitaminute' module provides custom exceptions specific to the
'worQt' framework. It follows the pattern set forth by
'worktoy.waitaminute'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._abstract_exception import AbstractException
from ._undefined_state import UndefinedState

__all__ = [
    'AbstractException',
    'UndefinedState',
]
