"""
FullScreenAction subclasses 'AbstractAction' and provides the 'Full Screen'
action in the 'View' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class FullScreenAction(AbstractAction):
  """
  FullScreenAction subclasses 'AbstractAction' and provides the 'Full
  Screen' action in the 'View' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'view-fullscreen'
  __action_title__: str = 'Full Screen'
  __key_bind__: str = ''
