"""
The 'worQt.app.des_qt' module provides non-general descriptors specific to
the 'worQt' library.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import pens
from ._action_resource import ActionResource
from ._action_meta import ActionMeta
from ._action_base import ActionBase
from ._action_icons import ActionIcons
from ._action_shortcuts import ActionShortcuts
from ._app import App
from ._etc import Etc
from ._img_extensions import ImgExtensions
from ._res_image import resImage

___all__ = [
    'pens',
    'ActionResource',
    'ActionMeta',
    'ActionBase',
    'ActionIcons',
    'ActionShortcuts',
    'App',
    'Etc',
    'ImgExtensions',
    'resImage',
]
