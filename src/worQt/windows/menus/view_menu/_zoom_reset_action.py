"""
ZoomResetAction subclasses 'AbstractAction' and provides the 'Reset Zoom'
action in the 'View' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class ZoomResetAction(AbstractAction):
  """
  ZoomResetAction subclasses 'AbstractAction' and provides the 'Reset Zoom'
  action in the 'View' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'zoom-original'
  __action_title__: str = 'Reset Zoom'
  __key_bind__: str = ''
