"""
The 'worQt.widgets' provides layouts and widgets used across the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._base_widget import BaseWidget
from ._v_spacer import VSpacer
from ._h_spacer import HSpacer
from ._tensor_widget import TensorWidget
from ._image_widget import ImageWidget
from ._dynamic_image import DynamicImage
from ._label_widget import LabelWidget

__all__ = [
    'BaseWidget',
    'VSpacer',
    'HSpacer',
    'TensorWidget',
    'ImageWidget',
    'DynamicImage',
    'LabelWidget',
]
