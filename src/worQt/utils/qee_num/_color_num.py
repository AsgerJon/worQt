"""
ColorNum enumerates a collection of named instances of 'Color' objects.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeNum, Kee

from .. import Color

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, TypeAlias, Any


class ColorNum(KeeNum):
  """
  ColorNum enumerates a collection of named instances of 'Color' objects.
  """

  WHITE = Kee[Color](255, 255, 255)
  EGG_SHELL = Kee[Color](252, 230, 201)
  SILVER = Kee[Color](192, 192, 192)
  CHARCOAL = Kee[Color](54, 69, 79)
  
  BLACK = Kee[Color](0, 0, 0)

  RED = Kee[Color](255, 0, 0)
  GREEN = Kee[Color](0, 255, 0)
  BLUE = Kee[Color](0, 0, 255)

  YELLOW = Kee[Color](255, 255, 0)
  CYAN = Kee[Color](0, 255, 255)
  MAGENTA = Kee[Color](255, 0, 255)

  ORANGE = Kee[Color](255, 165, 0)
  AQUA_MARINE = Kee[Color](0, 255, 165)
  PURPLE = Kee[Color](165, 0, 255, )

  LIME = Kee[Color](165, 255, 0)
  ROYAL_BLUE = Kee[Color](0, 165, 255)
  HOT_PINK = Kee[Color](255, 0, 165)
