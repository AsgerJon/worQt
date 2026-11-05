"""
The 'worQt.vidget' package provides the 'Vidget', worQt's own text
editing widget, made of its painted widgets and paint operations instead
of Qt's text edits, and editing the way Vi does: 'NORMAL', 'INSERT' and
'COMMAND' modes, counts, motions, the register, undo and ex commands.
Vi as it is, but no trap: the mouse puts the cursor where it clicks and
moves the focus away as it would anywhere else.

- ViMode: the modes.
- viMotions: the Vi motions, as plain functions of a text.
- PaintStatusLine, PaintLineNumbers, PaintViText: the paint operations
  behind it.
- VidgetBase: the text, cursor, history and register, with the editing
  primitives the commands are made of.
- Vidget: the Vi commands.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._vi_mode import ViMode
from . import _vi_motions as viMotions
from ._paint_status_line import PaintStatusLine
from ._paint_line_numbers import PaintLineNumbers
from ._paint_vi_text import PaintViText
from ._vidget_base import VidgetBase
from ._vidget import Vidget

__all__ = (
  'ViMode',
  'viMotions',
  'PaintStatusLine',
  'PaintLineNumbers',
  'PaintViText',
  'VidgetBase',
  'Vidget',
)
