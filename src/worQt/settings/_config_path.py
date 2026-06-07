"""
Resolve where an application's settings file lives on disk. The file is
named '.<appName>.config' and sits in the platform's conventional
user-config directory: '~/Library/Application Support' on macOS, the
'%APPDATA%' roaming directory on Windows, and the XDG directory
('$XDG_CONFIG_HOME', or '~/.config') everywhere else. That last layout, the
Arch/XDG one, is also the fallback when the platform is not recognised.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


def configDir() -> str:
  """
  The user-config directory for the current platform. macOS and Windows get
  their native locations; every other platform (and any unrecognised one)
  gets the XDG/Arch layout: '$XDG_CONFIG_HOME' when set, else '~/.config'.
  """
  home = os.path.expanduser('~')
  platform = sys.platform
  if platform == 'darwin':
    return os.path.join(home, 'Library', 'Application Support')
  if platform.startswith('win') or os.name == 'nt':
    roaming = os.environ.get('APPDATA')
    if roaming:
      return roaming
    return os.path.join(home, 'AppData', 'Roaming')
  xdg = os.environ.get('XDG_CONFIG_HOME')
  if xdg:
    return xdg
  return os.path.join(home, '.config')


def configFileName(appName: str) -> str:
  """The settings file name for 'appName', namely '.<appName>.config'."""
  return '.%s.config' % (appName.strip(),)


def configPath(appName: str) -> str:
  """The full path to 'appName's settings file in the config directory."""
  return os.path.join(configDir(), configFileName(appName))
