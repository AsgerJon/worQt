"""
View subclasses 'AbstractMenu' and provides the 'View' menu in the main
window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractMenu, ActionBox
from . import FullScreenAction, ZoomInAction, ZoomOutAction, ZoomResetAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class View(AbstractMenu):
  """
  View subclasses 'AbstractMenu' and provides the 'View' menu in the main
  window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Actions
  fullScreen = ActionBox[FullScreenAction]()
  zoomIn = ActionBox[ZoomInAction]()
  zoomOut = ActionBox[ZoomOutAction]()
  zoomReset = ActionBox[ZoomResetAction]()
