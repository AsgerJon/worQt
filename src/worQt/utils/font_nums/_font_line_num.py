"""
FontLineNum enumerates the line augmentations for text lines: 'underline',
'overline' and 'strikeout' (or 'strikethrough').
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from types import FunctionType

from PySide6.QtGui import QFont
from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable, Type, TypeAlias, Any

  FontSetter: TypeAlias = Callable[[QFont, Any], None]
  FontGetter: TypeAlias = Callable[[QFont], Any]


class FontLineNum(KeeNum):
  """
  FontLineNum enumerates the line augmentations for text lines: 'underline',
  'overline' and 'strikeout' (or 'strikethrough').
  """

  UNDERLINE = Kee[str]('UnderLine')
  OVERLINE = Kee[str]('OverLine')
  STRIKEOUT = Kee[str]('StrikeOut')
