"""
The settings for one application: a set of named tabs (panes), plus the file
they persist to. The file lives at the OS-specific config path derived from
the app name - '~/.config/.<name>.config' on the Arch/XDG fallback - and is
written in the small TOML dialect from '_toml': one '[tab]' table per pane,
'key = value' per setting. 'save' reflects the current values into that file
and 'load' reads them back, leaving any unknown or absent keys alone so the
schema (defined in code) always wins.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ._config_path import configPath
from ._settings_tab import SettingsTab
from ._toml import dumpToml, loadToml

if TYPE_CHECKING:  # pragma: no cover
  pass


class Settings(BaseObject):
  """
  An application's settings: its tabs and the file they live in. Add tabs
  with 'addTab', define settings on each, then 'load' the saved file over
  the defaults at startup and 'save' to write changes back.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __app_name__ = 'app'  # backing store for 'appName'
  __settings_tabs__ = None  # ordered mapping name -> SettingsTab
  __path_override__ = None  # an explicit file path, set by 'setPath'

  #  Public Variables
  appName: Field[str] = Field()  # the application name (read-only)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @appName.GET
  def _getAppName(self, ) -> str:
    return self.__app_name__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _tabMap(self, ) -> dict:
    """The tab mapping, created on first use."""
    if self.__settings_tabs__ is None:
      self.__settings_tabs__ = dict()
    return self.__settings_tabs__

  def addTab(self, name: str, label: str = None) -> SettingsTab:
    """Add a tab (pane) by name, with an optional display label, returning
    it so settings can be defined on it."""
    tab = SettingsTab(name) if label is None else SettingsTab(name, label)
    self._tabMap()[name] = tab
    return tab

  def tab(self, name: str) -> SettingsTab:
    """The tab stored under 'name'."""
    return self._tabMap()[name]

  def tabs(self, ) -> list:
    """Every tab, in definition order."""
    return list(self._tabMap().values())

  def names(self, ) -> list:
    """The tab names, in definition order."""
    return list(self._tabMap())

  def toData(self, ) -> dict:
    """Every tab as nested '{tab: {name: value}}' data."""
    return {name: tab.toDict() for name, tab in self._tabMap().items()}

  def applyData(self, data: dict) -> None:
    """Apply nested '{tab: {name: value}}' data over the current values."""
    for name, tab in self._tabMap().items():
      section = data.get(name)
      if isinstance(section, dict):
        tab.applyDict(section)

  def reset(self, ) -> None:
    """Restore every setting in every tab to its default."""
    for tab in self._tabMap().values():
      tab.reset()

  def setPath(self, path: str) -> None:
    """Pin an explicit file path, overriding the OS-derived default."""
    self.__path_override__ = path

  def path(self, ) -> str:
    """The settings file path: the pinned override, or the OS default."""
    if self.__path_override__:
      return self.__path_override__
    return configPath(self.__app_name__)

  def save(self, path: str = None) -> str:
    """
    Write the current values to the settings file (the given 'path', or the
    default), creating the parent directory if needed, and return the path
    written. The values are reflected as TOML.
    """
    target = self.path() if path is None else path
    directory = os.path.dirname(target)
    if directory and not os.path.isdir(directory):
      os.makedirs(directory)
    with open(target, 'w', encoding='utf-8') as handle:
      handle.write(dumpToml(self.toData()))
    return target

  def load(self, path: str = None) -> Settings:
    """
    Read the settings file (the given 'path', or the default) over the
    current values and return self. A missing file is not an error - the
    in-code defaults simply stand - so first launch needs no special case.
    """
    target = self.path() if path is None else path
    if not os.path.isfile(target):
      return self
    with open(target, 'r', encoding='utf-8') as handle:
      text = handle.read()
    self.applyData(loadToml(text))
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __init__(self, appName: str) -> None:
    self.__app_name__ = appName
    self.__settings_tabs__ = dict()

  @overload()
  def __init__(self, ) -> None:
    self.__settings_tabs__ = dict()

  def __iter__(self, ):
    return iter(self._tabMap().values())

  def __len__(self, ) -> int:
    return len(self._tabMap())

  def __contains__(self, name: str) -> bool:
    return name in self._tabMap()

  def __getitem__(self, name: str) -> SettingsTab:
    return self._tabMap()[name]

  def __str__(self, ) -> str:
    return 'Settings %r (%d tabs)' % (self.__app_name__, len(self._tabMap()))

  __repr__ = __str__
