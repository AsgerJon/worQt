"""
HelpContentsAction subclasses 'AbstractAction' and provides the 'Help'
action in the 'Help' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class HelpContentsAction(AbstractAction):
  """
  HelpContentsAction subclasses 'AbstractAction' and provides the 'Help'
  action in the 'Help' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'help-contents'
  __action_title__: str = 'Help'
  __key_bind__: str = 'F1'
