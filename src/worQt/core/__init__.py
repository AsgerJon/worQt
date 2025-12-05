"""
The 'worQt.core' package provides core functionality for the worQt library.
These are used throughout the library without relying on other packages.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._rouge_vert_bleu import RougeVertBleu
from ._rgba import RGBA
from ._font import Font
from ._w_connection import WConnection
from ._w_base_object import WBaseObject
from ._ws_instance import WSInstance
from ._w_signal import WSignal

from . import geometry, images

__all__ = [
    'RougeVertBleu',
    'RGBA',
    'Font',
    'WConnection',
    'WSInstance',
    'WSignal',
    'geometry',
    'images',
    'WBaseObject',
]
