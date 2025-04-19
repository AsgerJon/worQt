"""AbstractMap provides a callable mapping between two geometries. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from abc import abstractmethod

from worktoy.mcls import BaseObject


class AbstractMap(BaseObject):
  """AbstractMap provides a callable mapping between two geometries.

  This is an abstract class that should be subclassed to create specific
  mapping implementations. The `__call__` method should be implemented to
  provide the actual mapping logic.
  """

  @abstractmethod
  def __call__(self, *args, **kwargs):
    """Call the mapping with the given arguments."""
