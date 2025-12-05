"""
HelpMenu subclasses QMenu to provide the help menu for the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QIntList, QApplication, QMenuBar
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..core import WBaseObject
from . import WAction, MenuSeparator
from ..core.images import BaseImage


class HelpMenu(QMenu):
  """
  HelpMenu subclasses QMenu to provide the help menu for the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  aboutAction = AttriBox[WAction](THIS, 'about')
  aboutQtAction = AttriBox[WAction](THIS, 'aboutQt')
  helpAction = AttriBox[WAction](THIS, 'help')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, bar: QMenuBar) -> None:
    QMenu.__init__(self, '&Help', bar)
    self.setTitle('&Help')
    self.addAction(self.aboutAction)
    aboutQtImage = BaseImage('about_qt')
    aboutQtIcon = QIcon(aboutQtImage.qPixmap)
    self.aboutQtAction.setIcon(aboutQtIcon)
    self.addAction(self.aboutQtAction)
    self.addSeparator()
    self.addAction(self.helpAction)
