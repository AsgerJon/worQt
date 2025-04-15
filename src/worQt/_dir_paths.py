"""This file provides functions returning paths to the etc directory."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os

from worktoy.text import monoSpace

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


def _validatePath(dirPath: str) -> None:
  """Validate the path to the directory."""
  if not os.path.exists(dirPath):
    raise FileNotFoundError
  if not os.path.isdir(dirPath):
    raise NotADirectoryError
  if not os.access(dirPath, os.W_OK | os.X_OK):
    e = """Access to directory: '%s' denied!"""
    raise PermissionError(monoSpace(e % dirPath))


def getSrc() -> str:
  """Return the path to the source directory."""
  here = os.path.abspath(os.path.dirname(__file__))
  return os.path.normpath(os.path.join(here, '..'))


def getEtc(**kwargs) -> str:
  """Return the path to the etc-directory."""
  src = getSrc()
  etc = os.path.join(src, 'etc')
  try:
    _validatePath(etc)
  except FileNotFoundError as fileNotFoundError:
    if kwargs.get('_recursion', False):
      raise RecursionError from fileNotFoundError
    os.makedirs(etc)
    return getEtc(_recursion=True)
  except NotADirectoryError as notADirectoryError:
    raise notADirectoryError
  except PermissionError as permissionError:
    raise permissionError
  return etc


def getResourcePath(**kwargs) -> str:
  """Return the path to the resource directory."""
  etc = getEtc()
  resourcePath = os.path.join(etc, 'resources')
  try:
    _validatePath(resourcePath)
  except FileNotFoundError as fileNotFoundError:
    if kwargs.get('_recursion', False):
      raise RecursionError from fileNotFoundError
    os.makedirs(resourcePath)
    return getResourcePath(_recursion=True)
  except NotADirectoryError as notADirectoryError:
    raise notADirectoryError
  except PermissionError as permissionError:
    raise permissionError
  return resourcePath


def getIconPath(**kwargs) -> str:
  """Return the path to the icon directory."""
  resourcePath = getResourcePath()
  iconPath = os.path.join(resourcePath, 'icons')
  try:
    _validatePath(iconPath)
  except FileNotFoundError as fileNotFoundError:
    if kwargs.get('_recursion', False):
      raise RecursionError from fileNotFoundError
    os.makedirs(iconPath)
    return getIconPath(_recursion=True)
  except NotADirectoryError as notADirectoryError:
    raise notADirectoryError
  except PermissionError as permissionError:
    raise permissionError
  return iconPath
