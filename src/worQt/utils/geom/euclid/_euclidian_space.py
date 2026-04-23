"""
EuclidianSpace provides the custom namespace class used by the metaclass
system.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseSpace
from worktoy.utilities import maybe

from . import DimHook

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias
  from .. import Dimension
  from . import EuclidianMetaclass

  Dimensions: TypeAlias = tuple[Dimension, ...]
  Bases: TypeAlias = tuple[type, ...]
  Meta: TypeAlias = Type[EuclidianMetaclass]


class EuclidianSpace(BaseSpace):
  """
  EuclidianSpace provides the custom namespace class used by the metaclass
  system.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __dimension_objects__ = None

  #  Public Variables
  dimHook = DimHook()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getDimensionObjects(self, ) -> Dimensions:
    return maybe(self.__dimension_objects__, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def registerDimensionObject(self, key: str, dim: Dimension) -> None:
    """
    Registers the 'Dimension' object 'dim' under the name 'key' in the
    namespace. Invoked by the 'DimHook' object to track 'Dimension' objects
    encountered during class body execution.
    """
    existing = self.getDimensionObjects()
    unique = (*(dim for dim in existing if dim.__field_name__ != key),)
    dim.__field_name__ = key
    existingGroup = (*dim.keyGroup,)
    setattr(dim, '__key_group__', (key, *existingGroup,))
    self.__dimension_objects__ = (*unique, dim)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, mcls: Meta, name: str, bases: Bases, **kw) -> None:
    BaseSpace.__init__(self, mcls, name, bases, **kw)
    for base in bases:
      if isinstance(base, mcls):
        space = base.getNamespace()
        dimObjects = space.getDimensionObjects()
        for dim in dimObjects:
          self.registerDimensionObject(dim.fieldName, dim)
