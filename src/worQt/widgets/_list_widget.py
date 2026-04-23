"""
ListWidget subclasses 'AbstractWidget' and provides an advanced list
widget with its own child 'LabelWidget' objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import Field, AttriBox
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

from . import AbstractWidget, LabelWidget
from ..layouts import LayoutIndex
from ..layouts import LayoutIndex as Index
from ..utils.geom import Size

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Union, Iterator

  MaybeInt: TypeAlias = Optional[int]
  IntField: TypeAlias = Union[int, Field]

  WidgetsTuple: TypeAlias = tuple[LabelWidget, ...]
  MaybeWidgets: TypeAlias = Optional[WidgetsTuple]
  WidgetsField: TypeAlias = Union[WidgetsTuple, Field]

  Strings: TypeAlias = tuple[str, ...]
  MaybeStrings: TypeAlias = Optional[Strings]
  StringsField: TypeAlias = Union[Strings, Field]


class ListWidget(AbstractWidget):
  """
  ListWidget subclasses 'AbstractWidget' and provides an advanced list
  widget with its own child 'LabelWidget' objects.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_max__: int = 10

  #  Private Variables
  __base_layout__: BaseLayout = None
  __label_widgets__: MaybeWidgets = None
  __list_items__: MaybeStrings = None
  __max_items__: MaybeInt = None

  #  Public Variables
  baseLayout: LayoutField = Field()
  labelWidgets: WidgetsField = Field()
  listItems: StringsField = Field()
  protoType: LabelBox = AttriBox[LabelWidget](THIS, )
  maxItems: IntField = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createBaseLayout(self, ) -> None:
    raise NotImplementedError

  @baseLayout.GET
  def _getBaseLayout(self, **kwargs) -> BaseLayout:
    raise NotImplementedError

  @labelWidgets.GET
  def _getLabelWidgets(self, **kwargs) -> WidgetsTuple:
    if self.__label_widgets__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createLabelWidgets()
      return self._getLabelWidgets(_recursion=True)
    if isinstance(self.__label_widgets__, tuple):
      labelWidget = None
      for labelWidget in self.__label_widgets__:
        if not isinstance(labelWidget, LabelWidget):
          break
      else:
        return self.__label_widgets__
      if labelWidget is None:  # empty tuple
        return ()
      raise TypeException('labelWidget', labelWidget, LabelWidget)
    raise TypeException('__label_widgets__', self.__label_widgets__, tuple)

  @listItems.GET
  def _getListItems(self, **kwargs, ) -> Strings:
    if self.__list_items__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__list_items__ = ()
      return self._getListItems(_recursion=True)
    if isinstance(self.__list_items__, tuple):
      item = None
      for item in self.__list_items__:
        if not isinstance(item, str):
          break
      else:
        return self.__list_items__
      if item is None:  # empty tuple
        return ()
      raise TypeException('item', item, str)
    raise TypeException('__list_items__', self.__list_items__, tuple)

  @maxItems.GET
  def _getMaxItems(self, **kwargs) -> int:
    if self.__max_items__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__max_items__ = self.__fallback_max__
      return self._getMaxItems(_recursion=True)
    if isinstance(self.__max_items__, int):
      return self.__max_items__
    raise TypeException('__max_items__', self.__max_items__, int)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _registerItem(self, item: str) -> None:
    existing = self.listItems
    if len(self) < self.maxItems:
      self.__list_items__ = (*existing, item)
    else:
      self.__list_items__ = (*existing, item)[1:]
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[str]:
    yield from self.listItems

  def __len__(self, ) -> int:
    return len(self.listItems)

  def __getitem__(self, index: int) -> str:
    if index < 0:
      return self.__getitem__(index + len(self))
    if index < len(self):
      return self.listItems[index]
    infoSpec = """Index '%d' out of range: '%d'!"""
    info = infoSpec % (index, len(self))
    raise IndexError(textFmt(info))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def append(self, item: str) -> None:
    self._registerItem(item)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def validateLabels(self, ) -> bool:
    for i, item in enumerate(self.listItems):
      labelWidget = self.labelWidgets[i]
      if labelWidget.text != item:
        break
    else:
      return True
    return False

  def updateLayout(self, **kwargs) -> None:
    if self.validateLabels():
      return None
    if kwargs.get('_recursion', False):
      raise RecursionError
    for i, item in enumerate(self.listItems):
      try:
        label = self.__label_widgets__[i]
      except IndexError:
        label = LabelWidget(self.protoType, )
        self.__label_widgets__ = (*self.__label_widgets__, label)
      except TypeError:
        label = LabelWidget(self.protoType, )
        self.__label_widgets__ = label,
      label.text = item
      index = LayoutIndex(i, 0, )
      self.baseLayout[index] = label

  def update(self, ) -> None:
    """
    Reset base layout

    Ensure existing label widgets have correct text.

    Set layout again.
    """

  def _getRequiredSize(self, ) -> Size:
    raise NotImplementedError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
