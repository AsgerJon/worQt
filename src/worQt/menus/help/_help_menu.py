"""
HelpMenu provides the help menu for the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS

from . import AboutAction, AboutQtAction, DebugAction
from .. import AbstractMenu, ActionBox

if TYPE_CHECKING:  # pragma: no cover
  pass


class HelpMenu(AbstractMenu):
  """
  HelpMenu provides the help menu for the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  about = ActionBox[AboutAction](THIS)
  aboutQt = ActionBox[AboutQtAction](THIS)
  debug = ActionBox[DebugAction](THIS)
  debugLeft = ActionBox[DebugAction](THIS)
  debugRight = ActionBox[DebugAction](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    """
    Initialize the HelpMenu with common 'Help' actions.
    """
    super().__init__(*args, **kwargs)
    self.setTitle('Help')
    self.setObjectName('menus_help')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    self.addAction(self.about, )
    self.addAction(self.aboutQt, )
    self.addSeparator()
    self.addAction(self.debug, )
    self.addAction(self.debugLeft, )
    self.addAction(self.debugRight, )

  def initLogic(self) -> None:
    pass
