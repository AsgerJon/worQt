"""
_Overloader provides a class of which 'overload' is an instance extending
the functionality to include 'flex' and 'fallback' on dot notation.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import Dispatcher, TypeSignature
from ..core import perm

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable, TypeAlias

  Method: TypeAlias = Callable[..., Any]
  Decorator: TypeAlias = Callable[[Method], Dispatcher]


class _Overloader:
  """
  _Overloader provides a class of which 'overload' is an instance extending
  the functionality to include 'flex' and 'fallback' on dot notation.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __call__(self, *types) -> Decorator:
    """Returns a Dispatcher instance for the given type signatures. """
    return self._decoratorFactory(*types)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _decoratorFactory(*types) -> Decorator:
    """
    Returns a Dispatcher instance for the given type signatures.
    This is a domain-specific method to apply the overload decorator.
    """
    sig = TypeSignature(*types)

    def decorator(arg: Any) -> Dispatcher:
      if isinstance(arg, Dispatcher):  # allows stacking overloads
        func = ([f for _, f in arg.__sig_funcs__] or []).pop()
        arg.__sig_funcs__.append((sig, func))
        return arg
      return Dispatcher([(sig, arg)])

    return decorator

  @classmethod
  def flex(cls, *types) -> Decorator:
    """
    Returns a Dispatcher instance for the given type signatures.
    This is a domain-specific method to apply the flex decorator.
    """

    decorators = []
    for sigs in perm(*types):
      decorators.append(cls._decoratorFactory(*sigs))

    def decorator(arg: Any) -> Dispatcher:
      dispatcher = Dispatcher()
      for sig in perm(*types):
        dispatcher.__sig_funcs__.append((TypeSignature(*sig), arg))
      return dispatcher

    return decorator

  @classmethod
  def fallback(cls, fallbackFunction: Callable) -> Decorator:
    """
    Returns a Dispatcher instance for the given type signatures.
    This is a domain-specific method to apply the fallback decorator.
    """
    return Dispatcher(fallbackFunction)


overload = _Overloader()

__all__ = ['overload', ]
