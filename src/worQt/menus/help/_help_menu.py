"""
HelpMenu provides the help menu for the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import LabelBox

from . import AboutAction, AboutQtAction, DebugAction
from .. import AbstractMenu

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
  about = LabelBox[AboutAction](THIS)
  aboutQt = LabelBox[AboutQtAction](THIS)
  debug = LabelBox[DebugAction](THIS)

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

  def initLogic(self) -> None:
    pass
