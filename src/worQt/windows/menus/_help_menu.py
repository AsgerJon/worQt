"""
HelpMenu subclasses 'WMenu' and provides the help menu in the main menubar
of the main application window.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QMenu, QMenuBar, QApplication
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.utilities import textFmt

from . import WMenu, WAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union

  ActionBox: TypeAlias = Union[WAction, AttriBox]

HELP_TIP: str = textFmt(
  """Help menu providing access to documentation and about dialogs.""",
  )
DOC_TIP: str = textFmt(
  """Open the documentation in the default web browser.""",
  )
ABOUT_QT_TIP: str = textFmt(
  """Open the 'About Qt' dialog providing information about the Qt 
  framework.""",
  )
ABOUT_TIP: str = textFmt(
  """Open the 'About' dialog providing information about the application.""",
  )


class HelpMenu(WMenu):
  """
  HelpMenu subclasses 'WMenu' and provides the help menu in the main menubar
  of the main application window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  docs: ActionBox = AttriBox[WAction](THIS, 'help', DOC_TIP)
  aboutQt: ActionBox = AttriBox[WAction](THIS, 'aboutQt', ABOUT_QT_TIP)
  about: ActionBox = AttriBox[WAction](THIS, 'about', ABOUT_TIP)

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    Initializes the UI by populating the menu with registered actions.
    """
    super().initUI()
    self.setToolTip(HELP_TIP)
    self.addAction(self.docs)
    self.aboutQt.triggered.connect(QApplication.aboutQt)
    self.addAction(self.aboutQt)
    self.about.keyBind = ''
    self.addAction(self.about)
