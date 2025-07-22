"""
AbstractWindow provides the base class for application windows in the
worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow

from ..desQt import App
from ..core import Parent

if TYPE_CHECKING:  # pragma: no cover
  pass


class AbstractWindow(QMainWindow):
  """
  AbstractWindow provides the base class for application windows in the
  worQt framework. It is a subclass of QMainWindow and serves as a
  foundation for creating application windows with common functionality.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  app = App()
  parent = Parent()
