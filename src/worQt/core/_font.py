"""
'Font' implements
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QFont
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

from ..nums import FontFamilyNum


class Font(BaseObject):
  """Font implements the font family and size."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_family__ = 'MONTSERRAT'
  __fallback_size__ = 12
  __fallback_weight__ = 400
  __fallback_italic__ = False

  #  Private Variables
  __font_family__ = None
  __font_size__ = None
  __font_weight__ = None
  __italic_flag__ = None

  #  Public Variables
  family = Field()
  size = Field()
  weight = Field()
  italic = Field()

  #  Virtual Variables
  Q = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @family.GET
  def _getFamily(self, ) -> FontFamilyNum:
    fallback = FontFamilyNum[self.__fallback_family__]
    return maybe(self.__font_family__, fallback)

  @size.GET
  def _getSize(self) -> int:
    """Returns the font size."""
    return maybe(self.__font_size__, self.__fallback_size__)

  @weight.GET
  def _getWeight(self) -> int:
    """Returns the font weight."""
    return maybe(self.__font_weight__, self.__fallback_weight__)

  @italic.GET
  def _getItalic(self) -> bool:
    """Returns the italic flag."""
    return maybe(self.__italic_flag__, self.__fallback_italic__)

  @Q.GET
  def _getQ(self) -> QFont:
    """Returns the QFont object."""
    font = QFont()
    font.setFamily(self.family)
    font.setPointSize(self.size)
    font.setWeight(self.weight)
    font.setItalic(self.italic)
    return font
