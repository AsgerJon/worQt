"""
A 'tab': one pane of related settings, in the VLC sense - a family such as
'Audio', 'Interface' or 'Hotkeys' that owns a handful of settings shown
together. The tab keeps its settings in definition order and reads or writes
them all at once as a plain '{name: value}' mapping, which is what the file
codec and the dialog both consume. Names and the current value live behind
worktoy 'Field's; the settings themselves are held in a private mapping.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ._setting import Setting, humanizeName

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class SettingsTab(BaseObject):
  """
  A named pane of related settings. Define settings on it with 'define' (a
  name and a typed default), reach them by name, and read or apply the whole
  pane as a '{name: value}' mapping.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __tab_name__ = ''  # backing store for 'name'
  __tab_label__ = ''  # backing store for 'label'
  __settings__ = None  # ordered mapping name -> Setting

  #  Public Variables
  name: Field[str] = Field()  # the tab key (read-only)
  label: Field[str] = Field()  # the display label for the pane

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @name.GET
  def _getName(self, ) -> str:
    return self.__tab_name__

  @label.GET
  def _getLabel(self, ) -> str:
    return self.__tab_label__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @label.SET
  def _setLabel(self, text: Any) -> None:
    self.__tab_label__ = '' if text is None else str(text)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _store(self, ) -> dict:
    """The settings mapping, created on first use."""
    if self.__settings__ is None:
      self.__settings__ = dict()
    return self.__settings__

  def add(self, setting: Setting) -> Setting:
    """Add a fully built 'Setting' and return it."""
    self._store()[setting.name] = setting
    return setting

  def define(self, name: str, default: Any) -> Setting:
    """Build a setting from a name and a typed default (its type fixes the
    'Setting[T]' type parameter), add it, and return it (so the caller can
    chain 'withLabel'/'withHelp')."""
    return self.add(Setting[type(default)](default).withName(name))

  def setting(self, name: str) -> Setting:
    """The 'Setting' object stored under 'name'."""
    return self._store()[name]

  def names(self, ) -> list:
    """The setting names, in definition order."""
    return list(self._store())

  def value(self, name: str) -> Any:
    """The current value of the named setting."""
    return self._store()[name].value

  def setValue(self, name: str, raw: Any) -> None:
    """Set the named setting's value (coerced to its declared type)."""
    self._store()[name].set(raw)

  def toDict(self, ) -> dict:
    """The pane as a plain '{name: value}' mapping."""
    return {name: s.value for name, s in self._store().items()}

  def applyDict(self, mapping: dict) -> None:
    """Apply values from 'mapping' to the settings it names; unknown keys
    are ignored and absent settings keep their current value."""
    store = self._store()
    for name, setting in store.items():
      if name in mapping:
        setting.set(mapping[name])

  def reset(self, ) -> None:
    """Restore every setting in the pane to its default."""
    for setting in self._store().values():
      setting.reset()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str, str)
  def __init__(self, name: str, label: str) -> None:
    self.__tab_name__ = name
    self.__tab_label__ = label
    self.__settings__ = dict()

  @overload(str)
  def __init__(self, name: str) -> None:
    self.__tab_name__ = name
    self.__tab_label__ = humanizeName(name)
    self.__settings__ = dict()

  @overload()
  def __init__(self, ) -> None:
    self.__settings__ = dict()

  def __iter__(self, ):
    return iter(self._store().values())

  def __len__(self, ) -> int:
    return len(self._store())

  def __contains__(self, name: str) -> bool:
    return name in self._store()

  def __getitem__(self, name: str) -> Any:
    return self._store()[name].value

  def __setitem__(self, name: str, raw: Any) -> None:
    self._store()[name].set(raw)

  def __str__(self, ) -> str:
    return 'Tab %r (%d settings)' % (self.__tab_name__, len(self._store()))

  __repr__ = __str__
