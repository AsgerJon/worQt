"""
BoxModel class for managing box model properties of a widget.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QMarginsF, QMargins
from worktoy.core import Object
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe
from worktoy.dispatch import overload

from . import Margins

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


class BoxModel(BaseObject):
  """
  BoxModel class for managing box model properties of a widget.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins__ = Margins(2, 2, 2, 2, )
  __fallback_borders__ = Margins(1, 1, 1, 1, )
  __fallback_paddings__ = Margins(2, 2, 2, 2, )
  __fb_margins_corners__ = 2, 2
  __fb_borders_corners__ = 1, 1
  __fb_paddings_corners__ = 2, 2

  #  Private Variables
  __margins_margin__ = None
  __borders_margin__ = None
  __paddings_margin__ = None
  __margins_corners__ = None
  __borders_corners__ = None
  __paddings_corners__ = None

  #  Public Variables
  marginsTuple = Field()
  paddingsTuple = Field()
  bordersTuple = Field()

  marginsCorners = Field()
  paddingsCorners = Field()
  bordersCorners = Field()

  #  Virtual Variables
  margins = Field()
  paddings = Field()
  borders = Field()

  marginsF = Field()
  paddingsF = Field()
  bordersF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @marginsTuple.GET
  def _getMarginsTuple(self) -> tuple[int, int, int, int]:
    return maybe(self.__margins_margin__, self.__fallback_margins__)

  @bordersTuple.GET
  def _getBordersTuple(self) -> tuple[int, int, int, int]:
    return maybe(self.__borders_margin__, self.__fallback_borders__)

  @paddingsTuple.GET
  def _getPaddingsTuple(self) -> tuple[int, int, int, int]:
    return maybe(self.__paddings_margin__, self.__fallback_paddings__)

  @margins.GET
  def _getMargins(self) -> QMargins:
    return self.marginsTuple.Q

  @borders.GET
  def _getBorders(self) -> QMargins:
    return self.bordersTuple.Q

  @paddings.GET
  def _getPaddings(self) -> QMargins:
    return self.paddingsTuple.Q

  @marginsF.GET
  def _getMarginsF(self) -> QMarginsF:
    return self.marginsTuple.QF

  @bordersF.GET
  def _getBordersF(self) -> QMarginsF:
    return self.bordersTuple.QF

  @paddingsF.GET
  def _getPaddingsF(self) -> QMarginsF:
    return self.paddingsTuple.QF

  @marginsCorners.GET
  def _getMarginsCorners(self) -> tuple[int, int]:
    return maybe(self.__margins_corners__, self.__fb_margins_corners__)

  @bordersCorners.GET
  def _getBordersCorners(self) -> tuple[int, int]:
    return maybe(self.__borders_corners__, self.__fb_borders_corners__)

  @paddingsCorners.GET
  def _getPaddingsCorners(self) -> tuple[int, int]:
    return maybe(self.__paddings_corners__, self.__fb_paddings_corners__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Margins setters
  @margins.SET
  @overload(Margins)
  def _setMargins(self, margin: Margins) -> None:
    self.__margins_margin__ = margin

  @margins.SET
  @overload(QMargins)
  def _setMargins(self, margins: QMargins) -> None:
    self.__margins_margin__ = Margins.fromQMargins(margins)

  @margins.SET
  @overload(QMarginsF)
  def _setMargins(self, margins: QMarginsF) -> None:
    self.__margins_margin__ = Margins.fromQMarginsF(margins)

  #  Borders setters
  @borders.SET
  @overload(Margins)
  def _setBorders(self, margin: Margins) -> None:
    self.__borders_margin__ = margin

  @borders.SET
  @overload(QMargins)
  def _setBorders(self, margins: QMargins) -> None:
    self.__borders_margin__ = Margins.fromQMargins(margins)

  @borders.SET
  @overload(QMarginsF)
  def _setBorders(self, margins: QMarginsF) -> None:
    self.__borders_margin__ = Margins.fromQMarginsF(margins)

  #  Paddings setters
  @paddings.SET
  @overload(Margins)
  def _setPaddings(self, margin: Margins) -> None:
    self.__paddings_margin__ = margin

  @paddings.SET
  @overload(QMargins)
  def _setPaddings(self, margins: QMargins) -> None:
    self.__paddings_margin__ = Margins.fromQMargins(margins)

  @paddings.SET
  @overload(QMarginsF)
  def _setPaddings(self, margins: QMarginsF) -> None:
    self.__paddings_margin__ = Margins.fromQMarginsF(margins)

  #  Corners setters
  @marginsCorners.SET
  def _setMarginsCorners(self, *args) -> None:
    self.__margins_corners__ = args

  @bordersCorners.SET
  def _setBordersCorners(self, *args) -> None:
    self.__borders_corners__ = args

  @paddingsCorners.SET
  def _setPaddingsCorners(self, *args) -> None:
    self.__paddings_corners__ = args
