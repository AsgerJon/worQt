"""
TextWidget subclasses 'LabelWidget' and expands the text rendering of the
label with much longer text over multiple lines.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from icecream import ic
from worktoy.desc import Field, AttriBox
from worktoy.waitaminute import TypeException

from . import LabelWidget
from ..utils import WFont, Color
from ..utils.font_nums import FontFamilyNum, FontWeightNum
from ..utils.geom import Size, InSets
from ..utils.geom.euclid import Dimension
from ..utils.qee_num import Alignum, SizePolicy, SizingMode

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union

  WFontBox: TypeAlias = Union[WFont, AttriBox]
  FloatField: TypeAlias = Union[float, Field]
  MaybeFloat: TypeAlias = Optional[float]
  InSetsField: TypeAlias = Union[InSets, Field]


class TextWidget(LabelWidget):
  """
  TextWidget subclasses 'LabelWidget' and expands the text rendering of the
  label with much longer text over multiple lines.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_horizontal_mode__ = SizingMode.INTRINSIC
  __fallback_vertical_mode__ = SizingMode.INTRINSIC

  #  Private Variables

  #  Public Variables
  font: WFontBox = AttriBox[WFont](
    FontFamilyNum.CASCADIA_MONO,
    FontWeightNum.NORMAL,
    10,
    )
  paddingsDims: InSetsField = Field(LabelWidget.paddingsDims)
  bordersDims: InSetsField = Field(LabelWidget.bordersDims)
  marginsDims: InSetsField = Field(LabelWidget.marginsDims)

  #  Virtual Variables
  reqHeight: FloatField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getText(self, **kwargs) -> str:
    """
    This method formats the text with line breaks to match the available
    width. This method also determines the necessary height. This height
    is then available at the 'reqHeight' public variable.
    """
    superText = LabelWidget._getText(self, **kwargs)
    metrics = self.font.metricsF
    textRect = metrics.boundingRect(superText, self.textOption, )
    return superText

  def _getWrapMode(self, **kwargs) -> QTextOption.WrapMode:
    return QTextOption.WrapMode.WordWrap

  def _getTextAlignum(self, **kwargs) -> Alignum:
    return Alignum.TOP_LEFT

  @reqHeight.GET
  def _getReqHeight(self, **kwargs) -> float:
    wrapFlag = Qt.TextFlag.TextWordWrap
    metrics = self.font.metricsF
    rect = metrics.boundingRect(self.paintView.Q, wrapFlag, self.text)
    return rect.height()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getRequiredSize(self, ) -> Size:
    """
    This method computest the size required to bound the label text.
    """
    newWidth = self.paintView.width
    newWidth -= self.marginsDims.left + self.marginsDims.right
    newWidth -= self.bordersDims.left + self.bordersDims.right
    newWidth -= self.paddingsDims.left + self.paddingsDims.right
    return Size(newWidth, self.reqHeight)

  def initUI(self, ) -> None:
    """
    Initializes the UI of the widget. This method should be called after
    all properties have been set.
    """
    self.marginsDims.left = 4
    self.marginsDims.top = 4
    self.marginsDims.right = 4
    self.marginsDims.bottom = 4
    self.bordersDims.left = 1
    self.bordersDims.top = 1
    self.bordersDims.right = 1
    self.bordersDims.bottom = 1
    self.paddingsDims.left = 4
    self.paddingsDims.top = 4
    self.paddingsDims.right = 4
    self.paddingsDims.bottom = 4
    #  Colours:
    self.marginsColor = Color(169, 255, 0)
    self.bordersColor = Color(255, 0, 0)
    self.paddingsColor = Color(255, 255, 0)
    self.cornerXRadius = 4
    self.cornerYRadius = 4
    super().initUI()
