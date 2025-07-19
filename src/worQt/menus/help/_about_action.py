"""
AboutAction provides the 'About' action for the 'Help' menu in the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction
from ...nums import KeyNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  pass


class AboutAction(AbstractAction):
  """
  AboutAction provides the 'About' action for the 'Help' menu in the worQt
  framework.
  """

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('About')
    self.setObjectName('menus_help_about_action')
    self.setIcon('help-about')
    self.setShortcut(KeyNum.KEY_F1, KeyMod(0))
    self.setMenuRole(AbstractAction.MenuRole.AboutRole)
