"""
TypeSignature encapsulates type signatures in hashable objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core.sentinels import FALLBACK
from worktoy.dispatch import TypeSignature as __TypeSignature__

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class TypeSignature(__TypeSignature__):
  """
  TypeSignature encapsulates type signatures in hashable objects.
  """

  @classmethod
  def fallback(cls) -> Self:
    """Returns a fallback type signature."""
    return cls(FALLBACK)
