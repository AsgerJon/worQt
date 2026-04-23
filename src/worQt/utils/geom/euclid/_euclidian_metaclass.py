"""
EuclidianMetaclass provides the metaclass for the metaclass system used by
the 'worQt.utils.geom.euclid' package.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseMeta

from . import EuclidianSpace as ESpace

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias

  Bases: TypeAlias = tuple[type, ...]


class EuclidianMetaclass(BaseMeta):
  """
  EuclidianMetaclass provides the metaclass for the metaclass system used
  by the 'worQt.utils.geom.euclid' package.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getNamespace(cls) -> ESpace:
    eSpace = BaseMeta.getNamespace(cls, )
    if TYPE_CHECKING:  # pragma: no cover
      assert isinstance(cls, EuclidianMetaclass)
      assert isinstance(eSpace, ESpace)
    return eSpace

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __prepare__(mcls, name: str, bases: Bases, **kwargs) -> ESpace:
    """
    The '__prepare__' method is overridden to provide a custom namespace for
    class body execution. This namespace is an instance of 'EuclidianSpace',
    which allows for the tracking of 'Dimension' objects encountered during
    class body execution.
    """
    return ESpace(mcls, name, bases, **kwargs)
