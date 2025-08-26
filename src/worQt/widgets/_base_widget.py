"""
BaseWidget provides the basic widget functionality for the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ..desQt import App, Etc

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


class BaseWidget(QWidget):
  """BaseWidget subclass QWidget and provides the basic widget functionality
  for the worQt framework."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  app = App()
  etc = Etc()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    for arg in args:
      if isinstance(arg, QWidget):
        QWidget.__init__(self, arg)
        break
    else:
      QWidget.__init__(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """
    Subclasses can implement this method to specify how the widget
    initializes itself. This method should initialize only visual
    components. For logic, use the 'initLogic' method.
    """

  def initLogic(self, ) -> None:
    """
    Subclasses can implement this method to specify how the widget
    initializes its logic. This method should initialize only logic
    components. For visual components, use the 'initUi' method.
    """
