"""
TextWidget subclasses 'LabelWidget' and renders multi-line, word-wrapped
body text. It changes nothing about how the text reaches the screen - that
is still the inherited 'PaintLabel' paint operation - it only declares the
box model and the wrapping/alignment the longer text needs: word wrap, a
top-left anchor and a content height derived from the wrapped layout.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from worktoy.desc import Field, AttriBox

from . import LabelWidget
from ..utils import WFont
from ..utils.font_nums import FontFamilyNum, FontWeightNum
from ..utils.geom import Size, InSets
from ..utils.qee_num import Alignum

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union

  WFontBox: TypeAlias = Union[WFont, AttriBox]
  FloatField: TypeAlias = Union[float, Field]


class TextWidget(LabelWidget):
  """
  TextWidget subclasses 'LabelWidget' and expands the text rendering of the
  label with much longer text over multiple lines. The text is painted by
  the inherited 'PaintLabel' operation; this class only supplies the box
  model, the word-wrap mode and the multi-line content size.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables - a roomier box model than the single-line label
  __fallback_margins_dims__ = InSets(4, 4, 4, 4)
  __fallback_borders_dims__ = InSets(1, 1, 1, 1)
  __fallback_paddings_dims__ = InSets(4, 4, 4, 4)
  __fallback_radius__ = 4

  #  Public Variables
  font: WFontBox = AttriBox[WFont](
    FontFamilyNum.CASCADIA_MONO,
    FontWeightNum.NORMAL,
    10,
    )

  #  Virtual Variables
  reqHeight: FloatField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getWrapMode(self, **kwargs) -> QTextOption.WrapMode:
    """Wrap the body text on word boundaries (the label does not wrap)."""
    return QTextOption.WrapMode.WordWrap

  def _getTextAlignum(self, **kwargs) -> Alignum:
    """Anchor the body text at the top-left, not centred like a label."""
    return Alignum.TOP_LEFT

  @reqHeight.GET
  def _getReqHeight(self, **kwargs) -> float:
    """The height the wrapped text occupies at the current paint width."""
    wrapFlag = Qt.TextFlag.TextWordWrap
    metrics = self.font.metricsF
    rect = metrics.boundingRect(self.paintView.Q, wrapFlag, self.text)
    return rect.height()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the available paint width less
    the box-model insets, and the wrapped-text height at that width."""
    newWidth = self.paintView.width
    newWidth -= self.marginsDims.left + self.marginsDims.right
    newWidth -= self.bordersDims.left + self.bordersDims.right
    newWidth -= self.paddingsDims.left + self.paddingsDims.right
    return Size(newWidth, self.reqHeight)
