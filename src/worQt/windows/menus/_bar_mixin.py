"""
BarMixin subclasses 'MixinBase' and provides the mixin between 'Shiboken'
and the menubar classes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ...mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type, Union, Optional


class BarMixin(MixinBase):
  """
  BarMixin subclasses 'MixinBase' and provides the mixin between 'Shiboken'
  and the menubar classes.
  """
  pass
