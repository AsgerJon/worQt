"""
ZoomInAction subclasses 'AbstractAction' and provides the 'Zoom In' action
in the 'View' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class ZoomInAction(AbstractAction):
  """
  ZoomInAction subclasses 'AbstractAction' and provides the 'Zoom In' action
  in the 'View' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'zoom-in'
  __action_title__: str = 'Zoom In'
  __key_bind__: str = ''
