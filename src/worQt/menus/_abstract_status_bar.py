"""
AbstractStatusBar provides a base class for status bar implementations in
the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QStatusBar

from worQt.app.desQt import App
from worQt.core import Parent

if TYPE_CHECKING:  # pragma: no cover
  pass


class AbstractStatusBar(QStatusBar):
  """
  AbstractStatusBar provides a base class for status bar implementations in
  the worQt framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables

  #  Public Variables
  app = App()
  parent = Parent()

  #  TODO: Implement some stuff lol
