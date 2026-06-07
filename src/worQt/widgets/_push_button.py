"""
PushButton subclasses the 'AbstractButton' and provides a push-button
widget.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import PaintButton, ClickButton
from ..utils import ButtonStateFlags as BSFlags, Color
from ..utils.geom import InSets

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Union, Optional, Type

  StateDims: TypeAlias = dict[BSFlags, InSets]
  StateColor: TypeAlias = dict[BSFlags, Color]


class PushButton(ClickButton):
  """
  PushButton subclasses the 'AbstractButton' and provides a push-button
  widget.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  # --- States
  __base_state__: BSFlags = BSFlags.NULL
  __hovered_state__: BSFlags = BSFlags.HOVERED
  __pressed_state__: BSFlags = BSFlags.PRESSED
  __disabled_state__: BSFlags = BSFlags.DISABLED
  __disabled_hovered__: BSFlags = BSFlags.DISABLED | BSFlags.HOVERED
  __disabled_pressed__: BSFlags = BSFlags.DISABLED | BSFlags.PRESSED

  # --- Margins
  __state_margins_dims__: StateDims = {
    __base_state__      : InSets(2, 2, 2, 2, ),
    __hovered_state__   : InSets(1, 1, 1, 1, ),
    __pressed_state__   : InSets(1, 1, 1, 1, ),
    __disabled_state__  : InSets(2, 2, 2, 2, ),
    __disabled_hovered__: InSets(1, 1, 1, 1, ),
    __disabled_pressed__: InSets(1, 1, 1, 1, ),
    }
  __state_margins_color__: StateColor = {
    __base_state__      : Color(255, 255, 255),
    __hovered_state__   : Color(255, 255, 255),
    __pressed_state__   : Color(255, 255, 255),
    __disabled_state__  : Color(255, 255, 255),
    __disabled_hovered__: Color(255, 255, 255),
    __disabled_pressed__: Color(255, 255, 255),
    }
  __state_borders_dims__: StateDims = {
    __base_state__      : InSets(1, 1, 1, 1, ),
    __hovered_state__   : InSets(2, 2, 2, 2, ),
    __pressed_state__   : InSets(2, 2, 2, 2, ),
    __disabled_state__  : InSets(1, 1, 1, 1, ),
    __disabled_hovered__: InSets(2, 2, 2, 2, ),
    __disabled_pressed__: InSets(2, 2, 2, 2, ),
    }
  __state_borders_color__: StateColor = {
    __base_state__      : Color(0, 0, 0),
    __hovered_state__   : Color(0, 0, 0),
    __pressed_state__   : Color(0, 0, 0),
    __disabled_state__  : Color(0, 0, 0),
    __disabled_hovered__: Color(0, 0, 0),
    __disabled_pressed__: Color(0, 0, 0),
    }
  __state_content_dims__: StateDims = {
    __base_state__      : InSets(2, 2, 2, 2, ),
    __hovered_state__   : InSets(2, 2, 2, 2, ),
    __pressed_state__   : InSets(2, 2, 2, 2, ),
    __disabled_state__  : InSets(2, 2, 2, 2, ),
    __disabled_hovered__: InSets(2, 2, 2, 2, ),
    __disabled_pressed__: InSets(2, 2, 2, 2, ),
    }
  __state_content_color__: StateColor = {
    __base_state__      : Color(223, 223, 223),
    __hovered_state__   : Color(223, 223, 223),
    __pressed_state__   : Color(191, 191, 191),
    __disabled_state__  : Color(223, 223, 223),
    __disabled_hovered__: Color(255, 255, 255),
    __disabled_pressed__: Color(255, 255, 255),
    }

  #  Private Variables

  #  Public Variables

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getMarginsDims(self, **kwargs) -> InSets:
    """
    _getMarginsDims returns the dimensions of the margins of the widget.
    """
    return self.__state_margins_dims__[self.state]

  def _getBordersDims(self, **kwargs) -> InSets:
    """
    _getBordersDims returns the dimensions of the borders of the widget.
    """
    return self.__state_borders_dims__[self.state]

  def _getPaddingsDims(self, **kwargs) -> InSets:
    """
    _getContentDims returns the dimensions of the content of the widget.
    """
    return self.__state_content_dims__[self.state]

  def _getMarginsColor(self, **kwargs) -> Color:
    """
    _getMarginsColor returns the color of the margins of the widget.
    """
    return self.__state_margins_color__[self.state]

  def _getBordersColor(self, **kwargs) -> Color:
    """
    _getBordersColor returns the color of the borders of the widget.
    """
    return self.__state_borders_color__[self.state]

  def _getPaddingsColor(self, **kwargs) -> Color:
    """
    _getContentColor returns the color of the content of the widget.
    """
    return self.__state_content_color__[self.state]
