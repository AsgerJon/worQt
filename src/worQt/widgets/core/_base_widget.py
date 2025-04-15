"""BaseWidget provides the baseclass for widgets in the worQt library."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QWidget

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class _Deps:
  """_Deps provides the dependencies for the worQt library."""
  __imported_objects__ = [
      QWidget,
  ]


class BaseWidget(QWidget):
  """BaseWidget provides the baseclass for widgets in the worQt library."""

  def __init__(self, *args) -> None:
    for arg in args:
      if isinstance(arg, QWidget):
        QWidget.__init__(self, arg)
        break
    else:
      QWidget.__init__(self, )

  def initUi(self, ) -> None:
    """Hook allowing for widget initialization right before painting.
    Subclasses containing child widgets should specify how to organize the
    layout of child widgets by implementing this method. Single widget
    classes are not required to implement this method. """

  def initLogic(self, ) -> None:
    """Hook allowing for widgets to connect their internal signals and
    slots in support of their external functionality. This method is
    called immediately after the parent show method is called. """

  def show(self, ) -> None:
    """Override the show method to call the initUi and initLogic methods
    before showing the widget. """
    self.initUi()
    QWidget.show(self)
    self.initLogic()
