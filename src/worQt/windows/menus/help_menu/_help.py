"""
Help subclasses 'AbstractMenu' and provides the 'Help' menu in the main
window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractMenu, ActionBox
from . import AboutAction, AboutQtAction, HelpContentsAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Help(AbstractMenu):
  """
  Help subclasses 'AbstractMenu' and provides the 'Help' menu in the main
  window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __menu_title__ = 'Help'

  #  Actions
  about = ActionBox[AboutAction]()
  aboutQt = ActionBox[AboutQtAction]()
  helpContents = ActionBox[HelpContentsAction]()

