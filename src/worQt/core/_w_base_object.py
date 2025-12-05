"""
WBaseObject provides a subclass of 'BaseObject' from 'worktoy' with a
contrived metaclass permitting it as an additional base class for QObject
subclasses used in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

from worktoy.mcls import BaseMeta, BaseSpace

from moreworktoy.core import Object as __worktoy_Object__

from ..desQt import Etc, App

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, TypeAlias, Union, Any, Type, Optional

  Bases: TypeAlias = tuple[type, ...]
  Space: TypeAlias = Union[dict[str, Any], BaseSpace]
  Widget: TypeAlias = Optional[QWidget]
  Parent: TypeAlias = tuple[Widget, tuple[Any, ...]]


class _Shiboken(type(QObject)):
  """
  Retrieval of the Shiboken metaclass.
  """


class _CombinedMeta(_Shiboken, BaseMeta):
  """
  Combined metaclass for worQt QObject subclasses.
  """

  @classmethod
  def __prepare__(mcls, name: str, bases: Bases, **kw) -> Space:
    bases = (*[b for b in bases if b.__name__ != '_InitSub'],)
    return BaseSpace(mcls, name, bases, **kw)

  def __new__(mcls, name: str, bases: Bases, space: Space, **kw) -> Self:
    return super().__new__(mcls, name, bases, space.compile(), **kw)


class WBaseObject(__worktoy_Object__, metaclass=_CombinedMeta):
  """
  Retrieves the 'Object' class from 'worktoy', but using the combined
  metaclass. This class now has a sufficiently contrived metaclass to be
  permitted as a base class for QObject subclasses used in the worQt
  framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables

  etc = Etc()
  app = App()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  UTILITY METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def parseParent(*args, **kwargs) -> Parent:
    """
    Extracts the first 'QWidget' object from the positional arguments and
    returns it along with the remaining arguments as a tuple.

    Parameters
    ----------
    *args : Any
        Positional arguments potentially containing a 'QWidget' object.
    **kwargs : Any
        Keyword arguments (not used in this method).

    Returns
    -------
    Parent
        A tuple containing the extracted 'QWidget' (or None if not found)
        and a tuple of the remaining positional arguments.
    """
    posArgs = [*reversed([*args, ]), ]
    outArgs = []
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, QWidget):
        return arg, (*outArgs, *reversed(posArgs),)
      outArgs.append(arg)
    else:
      return None, (*outArgs,)
