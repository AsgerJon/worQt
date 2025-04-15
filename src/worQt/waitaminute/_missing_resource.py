"""MissingResource should be raised when a named resource in the
'worQt.resources' module is not found."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.text import monoSpace

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class MissingResource(Exception):
  """MissingResource should be raised when a named resource in the
  'worQt.resources' module is not found."""

  __resource_name__ = None
  __resource_type__ = None
  __resource_path__ = None

  def __init__(self, name: str, cls: type, resPath: str) -> None:
    """Initialize the MissingResource with a name and a class."""
    self.__resource_name__ = name
    self.__resource_type__ = cls
    self.__resource_path__ = resPath

    infoSpec = """Unable to find resource named: '%s' to create resource of 
    type: '%s' in path: '%s'"""
    info = monoSpace(infoSpec % (name, cls.__name__, resPath))
    Exception.__init__(self, info)
