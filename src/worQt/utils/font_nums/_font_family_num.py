"""
FontFamilyNum enumerates the currently available font families in the
system. The members of this enumeration depend entirely on the system,
requiring dynamic creation. The customized metaclass system provides this
functionality.

Regardless of what fonts are available, font families generally belong to
on of the following: Serif, Sans, and Mono. Below is a brief explanation
of each:

- Serif
  Serif fonts are characterized by small lines or strokes attached to the
  ends of the characters. They are often considered more traditional and
  are commonly used in printed materials. Examples of serif fonts include:
  - Times New Roman
  - Georgia
  - Garamond

- Sans (Sans Serif)
  Sans serif fonts do not have the small lines or strokes at the ends of
  the characters. They are often considered more modern and are commonly
  used in digital media. Examples of sans serif fonts include:
  - Arial
  - Helvetica
  - Verdana

- Mono (Monospaced)
  Monospaced fonts have characters that occupy the same amount of
  horizontal space. They are often used in programming and coding
  environments because they make it easier to align code and
  distinguish between similar characters. Examples of monospaced fonts
  include:
  - Courier New
  - Consolas
  - Monaco

For convenience, the metaclass system provides class attributes for each
category returning an enumeration matching a family of that category that
is available on the system:
- FontFamilyNum.defaultSerif
- FontFamilyNum.defaultSans
- FontFamilyNum.defaultMono

To require a particular font family, rather than just a category,
the running system must provide it. The 'worQt' provides no facilities for
font installation, it merely exposes what is available.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from worktoy.dispatch import overload
from worktoy.keenum import KeeNum

from . import FontFamilyMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias


class FontFamilyNum(KeeNum, metaclass=FontFamilyMeta):
  """
  FontFamilyNum enumerates the currently available font families in the
  system. The members of this enumeration depend entirely on the system,
  requiring dynamic creation. The customized metaclass system provides this
  functionality.
  """

  def apply(self, font: QFont) -> QFont:
    """
    Applies the font family to the given 'QFont' instance and returns it.
    """
    font.setFamily(self.value)
    return font
