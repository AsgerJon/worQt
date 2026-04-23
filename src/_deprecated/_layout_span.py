"""
LayoutSpan encapsulates a span of cells in a grid layout similar to a size
in a widget. It specifies how many rows and columns an item should occupy
in the layout.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class LayoutSpan(BaseObject):
  """
  LayoutSpan encapsulates a span of cells in a grid layout similar to a size
  in a widget. It specifies how many rows and columns an item should occupy
  in the layout.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __row_keys__ = ('rowSpan', 'rows', 'rspan', 'rSpan', 'verticalSpan',)
  __col_keys__ = ('colSpan', 'cols', 'cspan', 'cSpan', 'horizontalSpan',)

  #  Fallback Variables
  __fallback_rows__ = 1
  __fallback_cols__ = 1

  #  Private Variables
  __row_span__ = None
  __col_span__ = None

  #  Public Variables
  rowSpan = Field()
  colSpan = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @rowSpan.GET
  def _getRowSpan(self, **kwargs) -> int:
    if self.__row_span__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__row_span__ = self.__fallback_rows__
      return self._getRowSpan(_recursion=True, )
    if isinstance(self.__row_span__, int):
      return self.__row_span__
    raise TypeException('__row_span__', self.__row_span__, int)

  @colSpan.GET
  def _getColSpan(self, **kwargs) -> int:
    if self.__col_span__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__col_span__ = self.__fallback_cols__
      return self._getColSpan(_recursion=True, )
    if isinstance(self.__col_span__, int):
      return self.__col_span__
    raise TypeException('__col_span__', self.__col_span__, int)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, *args, **kwargs) -> None:
    """
    This method initializes from two integers specifying row and column
    spans respectively.
    """
    self.__row_span__, self.__col_span__ = args
    if kwargs:
      self.__init__(**kwargs)

  @overload()
  def __init__(self, **kwargs, ) -> None:
    """
    This method initializes from keyword arguments.
    """
    KEYS = [self.__row_keys__, self.__col_keys__, ]
    NAMES = ['rowSpan', 'colSpan', ]
    spans = dict()
    for keys, name in zip(KEYS, NAMES):
      for key in keys:
        if key in kwargs:
          value = kwargs[key]
          if not isinstance(value, int):
            raise TypeException(key, value, int)
          spans[name] = value
          break
    if 'rowSpan' in spans:
      self.__row_span__ = spans['rowSpan']
    if 'colSpan' in spans:
      self.__col_span__ = spans['colSpan']

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
