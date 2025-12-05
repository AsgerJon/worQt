"""
ActionMeta provides a base class for resources associated with actions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core import Object

from . import ActionMeta

if TYPE_CHECKING:  # pragma: no cover
  from . import ActionResource


class ActionBase(Object, metaclass=ActionMeta):
  """
  ActionMeta provides a base class for resources associated with actions.
  """

  toQ = None  # Must be implemented by subclasses

  def __getattr__(self, name: str) -> ActionResource:
    cls = type(self)
    mcls = type(cls)
    try:
      value = getattr(mcls, name)
    except AttributeError:
      return object.__getattribute__(self, name)
    else:
      return value
