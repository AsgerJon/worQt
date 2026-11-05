"""
EZWordApp subclasses 'App' and is the EZWord application.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPalette, QColor

from ...app import App
from . import EZWordWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias

  RGB: TypeAlias = tuple[int, int, int]

_ROLE = QPalette.ColorRole
_DISABLED = QPalette.ColorGroup.Disabled
_DARK: dict[QPalette.ColorRole, RGB] = {
  _ROLE.Window         : (43, 45, 49),
  _ROLE.WindowText     : (212, 212, 212),
  _ROLE.Base           : (30, 31, 34),
  _ROLE.AlternateBase  : (35, 36, 40),
  _ROLE.ToolTipBase    : (43, 45, 49),
  _ROLE.ToolTipText    : (212, 212, 212),
  _ROLE.PlaceholderText: (128, 128, 128),
  _ROLE.Text           : (212, 212, 212),
  _ROLE.Button         : (43, 45, 49),
  _ROLE.ButtonText     : (212, 212, 212),
  _ROLE.BrightText     : (255, 99, 99),
  _ROLE.Highlight      : (61, 111, 180),
  _ROLE.HighlightedText: (255, 255, 255),
}
_DARK_DISABLED: RGB = (110, 110, 110)  # disabled text of every kind


class EZWordApp(App):
  """
  EZWordApp subclasses 'App' and is the EZWord application. Its window is
  an 'EZWordWindow', and its exit guard asks to save while any of its
  tabs holds unsaved changes. It is dark: Qt's Fusion style with a dark
  palette, so the window and its menus match the page.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = EZWordWindow

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args) -> None:
    App.__init__(self, *args)
    self.setStyle('Fusion')
    self.setPalette(self.darkPalette())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def darkPalette() -> QPalette:
    """The 'darkPalette' method returns the palette EZWord's window and
    menus are drawn in."""
    palette = QPalette()
    for role, rgb in _DARK.items():
      palette.setColor(role, QColor(*rgb))
    for role in (_ROLE.Text, _ROLE.ButtonText, _ROLE.WindowText):
      palette.setColor(_DISABLED, role, QColor(*_DARK_DISABLED))
    return palette

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  EXIT GUARD   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def hasUnsavedChanges(self, ) -> bool:
    """There are unsaved changes while any tab's page is modified."""
    return True if self.window.unsavedPages() else False

  def saveChanges(self, ) -> bool:
    """Saving the changes saves every modified page, asking for a file
    for one never saved; cancelling that cancels the exit."""
    for page in self.window.unsavedPages():
      self.window.selectTab(self.window.pages.index(page))
      if not self.window.saveTab(page):
        return False
    return True
