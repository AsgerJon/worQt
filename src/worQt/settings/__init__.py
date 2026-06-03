"""
The 'worQt.settings' package is a generic, Qt-free system for managing an
application's settings. Settings are grouped into 'tabs' (VLC-style panes,
each a family of related settings); the whole set reflects to and from a
per-application config file in the OS-specific config directory, written in
a small TOML dialect. The matching 'SettingsDialog' (in 'worQt.widgets')
presents the tabs as a tabbed editor.

Layering: '_config_path' and '_toml' are leaf helpers; '_setting' defines a
single setting; '_settings_tab' groups settings into a pane; '_settings'
ties the tabs to their file.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._config_path import configDir, configFileName, configPath
from ._toml import dumpToml, loadToml
from ._setting import Setting, humanizeName
from ._settings_tab import SettingsTab
from ._settings import Settings

__all__ = [
  'configDir',
  'configFileName',
  'configPath',
  'dumpToml',
  'loadToml',
  'humanizeName',
  'Setting',
  'SettingsTab',
  'Settings',
]
