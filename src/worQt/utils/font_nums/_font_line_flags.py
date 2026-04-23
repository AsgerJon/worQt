"""
FontLineFlags enumerates the combinations of line augmentations for
'QFont' objects. 'Line augmentation' refers to: 'underline', 'overline'
and 'strikeout' (or 'strikethrough').
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from types import FunctionType
from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from worktoy.desc import Field
from worktoy.keenum import KeeFlags, KeeFlag
from worktoy.waitaminute import TypeException

# from ...paint_ops import TextPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Callable, Union

  QFontMethod: TypeAlias = Callable[[QFont, ], QFont]
  MethodField: TypeAlias = Union[QFontMethod, Field]


class FontLineFlags(KeeFlags):
  """
  FontLineFlags enumerates the combinations of line augmentations for
  'QFont' objects. 'Line augmentation' refers to: 'underline', 'overline'
  and 'strikeout' (or 'strikethrough').
  """

  UNDERLINE = KeeFlag()
  STRIKEOUT = KeeFlag()
  OVERLINE = KeeFlag()

  def apply(self, font: QFont, ) -> QFont:
    QFont.setUnderline(font, True if self.name == 'UNDERLINE' else False)
    QFont.setStrikeOut(font, True if self.name == 'STRIKEOUT' else False)
    QFont.setOverline(font, True if self.name == 'OVERLINE' else False)
    return font
