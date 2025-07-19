"""
Dispatcher encapsulates the mapping from type signature to function
objects and thus provides the core overloading functionality.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.dispatch import Dispatcher as __Dispatcher__

from . import TypeSignature
from ..core import perm

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Callable


class Dispatcher(__Dispatcher__):
  """
  Dispatcher encapsulates the mapping from type signature to function
  objects and thus provides the core overloading functionality.
  """

  def __init__(self, *args, **kwargs) -> None:
    self.__sig_funcs__ = []
    if len(args) == 1:
      if callable(args[0]):
        self.__sig_funcs__ = [(TypeSignature.fallback(), args[0])]

  def flex(self, *types) -> Self:
    """
    Returns a Dispatcher instance for the given type signatures.
    This is a domain-specific method to apply the flex decorator.
    """

    def decorator(callMeMaybe: Callable) -> Self:
      for sig in perm(types):
        self.__sig_funcs__.append((TypeSignature(*sig), callMeMaybe))
      return self

    return decorator

  def fallback(self, func: Callable) -> Self:
    """
    Returns a Dispatcher instance with the given function as the fallback.
    This is a domain-specific method to apply the fallback decorator.
    """

    def decorator(callMeMaybe: Callable) -> Self:
      self.__sig_funcs__.append((TypeSignature.fallback(), func))
      return self

    return decorator
