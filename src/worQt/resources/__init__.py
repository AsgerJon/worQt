"""The 'worQt.resources' provides enumerations for resources such as
icons. A particular application should point an environment variable to a
folder containing each resource type. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._res_num import ResNum, ResNumEntry, MetaResNum
from ._icon_res import IconRes
from ._shortcut_res import ShortcutRes

__all__ = [
    "ResNum",
    "ResNumEntry",
    "MetaResNum",
    "IconRes",
    "ShortcutRes",
]
