"""
Alias provides a descriptor allowing renaming of a descriptor, typically
one inherited from a parent.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Alias as __old_Alias__

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable, TypeAlias

  CallMeMaybe: TypeAlias = Callable[..., Any]


class Alias(__old_Alias__):
  #  For linters who won't chill out
  if TYPE_CHECKING:  # pragma: no cover
    __add__: CallMeMaybe
    __sub__: CallMeMaybe
    __mul__: CallMeMaybe
    __truediv__: CallMeMaybe
    __floordiv__: CallMeMaybe
    __mod__: CallMeMaybe
    __divmod__: CallMeMaybe
    __pow__: CallMeMaybe
    __lshift__: CallMeMaybe
    __rshift__: CallMeMaybe
    __and__: CallMeMaybe
    __xor__: CallMeMaybe
    __or__: CallMeMaybe
    __lt__: CallMeMaybe
    __le__: CallMeMaybe
    __eq__: CallMeMaybe
    __ne__: CallMeMaybe
    __gt__: CallMeMaybe
    __ge__: CallMeMaybe
    __hash__: CallMeMaybe
    __bool__: CallMeMaybe
    __str__: CallMeMaybe
    __repr__: CallMeMaybe
