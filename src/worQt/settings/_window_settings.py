"""
WindowSettings exposes the settings for the main window of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field

from . import AbstractSettings

if TYPE_CHECKING:  # pragma: no cover
  pass


class WindowSettings(AbstractSettings):
  """
  WindowSettings exposes the settings for the main window of the application.

  The settings file is at `etc/window_settings.json`. The settings
  available are only the minimum width and height of the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __file_name__ = 'window_settings.json'

  #  Public Variables
  minWidth = Field()
  minHeight = Field()
