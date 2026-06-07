"""
GenericFamilyMeta subclasses 'FontMeta' and provides the metaclass for the
'GenericFamilyNum' enumeration.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import FontMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union


class GenericFamilyMeta(FontMeta):
  """
  GenericFamilyMeta subclasses 'FontMeta' and provides the metaclass for the
  'GenericFamilyNum' enumeration.
  """
  pass
