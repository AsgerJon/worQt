"""
MetaTest subclasses 'BaseMeta' and provides the metaclass from which the
'AppTest' classes are derived.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Callable

from worktoy.desc import Field
from worktoy.mcls import BaseMeta

from . import SpaceTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional

  Bases: TypeAlias = tuple[type, ...]


class MetaTest(BaseMeta):
  """
  MetaTest subclasses 'BaseMeta' and provides the metaclass from which the
  'AppTest' classes are derived.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __test_methods__: Optional[dict[str, Callable]] = None

  #  Public Variables
  testMethods: Field[dict[str, Callable]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @testMethods.GET
  def _getTestMethods(cls, ) -> dict[str, Callable]:
    return getattr(cls, '__test_methods__', )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __prepare__(mcls, name: str, bases: Bases, **kwargs) -> SpaceTest:
    """
    Prepare the namespace for the class.

    Parameters
    ----------
    name: str
      The name of the class being defined.
    bases: tuple[type, ...]
      The base classes of the class being defined.

    Returns
    -------
    SpaceTest
      An document of 'SpaceTest' to be used as the namespace for the
      class.
    """
    return SpaceTest(mcls, name, bases, **kwargs)

  def __new__(mcls, name: str, bases: Bases, space: SpaceTest, **kw) -> type:
    return super().__new__(mcls, name, bases, space, **kw)
