"""
WidgetRegistry provides a 'dict' like mapping from 'LayoutIndex' objects
to 'QWidget' objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.utilities import maybe

from . import LayoutIndex, LayoutEntry

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Iterator, TypeAlias, Type, Optional, Union

  from PySide6.QtWidgets import QWidget
  from . import LayoutEntry as Entry

  Entries: TypeAlias = tuple[Entry, ...]


class WidgetRegistry(dict):
  """
  WidgetRegistry provides a 'dict' like mapping from 'LayoutIndex' objects
  to 'QWidget' objects.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __registered_entries__ = None

  #  Public Variables
  entries = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @entries.GET
  def _getEntries(self, **kwargs) -> Entries:
    return maybe(self.__registered_entries__, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    dict.__init__(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __getitem__(self, identifier: LayoutIndex) -> QWidget:
    for entry in self.entries:
      if entry[0] == identifier:
        return entry[1]
    raise KeyError(identifier)

  def __setitem__(self, identifier: LayoutIndex, entry: Entry) -> None:
    raise NotImplementedError

  def __delitem__(self, identifier: LayoutIndex) -> None:
    raise NotImplementedError
