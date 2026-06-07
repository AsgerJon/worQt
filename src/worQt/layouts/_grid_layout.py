"""
GridLayout subclasses BaseLayout and implements a grid layout manager for
widgets. It is used by both windows and compound widgets to manage the
layout of the widgets.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout
from worktoy.desc import Field
from worktoy.waitaminute import TypeException

from . import BaseLayout, LayoutIndex
from ..widgets import AbstractWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union

  IndexDict: TypeAlias = dict[LayoutIndex, AbstractWidget]
  MaybeIndexDict: TypeAlias = Optional[IndexDict]
  IndexDictField: TypeAlias = Union[Field, IndexDict]
  MaybeInt: TypeAlias = Optional[int]
  MaybeWidget: TypeAlias = Optional[AbstractWidget]


class GridLayout(BaseLayout):
  """
  GridLayout subclasses BaseLayout and implements a grid layout manager for
  widgets. It is used by both windows and compound widgets to manage the
  layout of the widgets.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __widget_dict__: MaybeIndexDict = None

  #  Public Variables
  widgetDict: IndexDictField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createWidgetDict(self, ) -> None:
    self.__widget_dict__ = dict()

  @widgetDict.GET
  def _getWidgetDict(self, **kwargs) -> IndexDict:
    if self.__widget_dict__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createWidgetDict()
      return self._getWidgetDict(_recursion=True)
    if isinstance(self.__widget_dict__, dict):
      if not self.__widget_dict__:
        return self.__widget_dict__
      index, widget = None, None
      for index, widget in self.__widget_dict__.items():
        if isinstance(index, LayoutIndex):
          if isinstance(widget, AbstractWidget):
            continue
        break
      else:
        return self.__widget_dict__
      if isinstance(index, LayoutIndex):
        raise TypeException('widget', widget, AbstractWidget)
      raise TypeException('index', index, LayoutIndex)
    raise TypeException('__widget_dict__', self.__widget_dict__, dict)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    Initializes the UI of the layout. This method should be called after
    all widgets have been added to the layout.
    """
    self.reset()
    for index, widget in self.widgetDict.items():
      widget.initUI()
      QGridLayout.addWidget(self, widget, *index, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  REQUIRED METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def reset(self, ) -> None:
    """
    Resets the layout by clearing all widgets from the QGridLayout manager.
    """
    while QGridLayout.count(self, ):
      oldCount = QGridLayout.count(self, )
      _ = QGridLayout.takeAt(self, 0)
      newCount = QGridLayout.count(self, )
      if newCount:
        if newCount == oldCount:
          raise RecursionError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __getitem__(self, index: LayoutIndex) -> AbstractWidget:
    return self.widgetDict[index]

  def __setitem__(self, index: LayoutIndex, widget: AbstractWidget) -> None:
    self.widgetDict[index] = widget
