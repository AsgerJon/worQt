"""
DemoButton is a 'PushButton' whose content clearly shades on hover and
darkens on press, so the demo shows the button's state at a glance. It
changes only the per-state content colour; it inherits the recogniser and
the rest of the box-model behaviour from 'PushButton'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.utils import ButtonStateFlags as BSFlags, Color
from worQt.widgets import PushButton

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class DemoButton(PushButton):
  """A 'PushButton' with pronounced hover/press content shading."""

  __state_content_color__ = {
    BSFlags.NULL                      : Color(212, 212, 214),
    BSFlags.HOVERED                   : Color(184, 190, 202),  # shaded
    BSFlags.PRESSED                   : Color(138, 146, 162),  # depressed
    BSFlags.DISABLED                  : Color(212, 212, 214),
    BSFlags.DISABLED | BSFlags.HOVERED: Color(212, 212, 214),
    BSFlags.DISABLED | BSFlags.PRESSED: Color(212, 212, 214),
  }
