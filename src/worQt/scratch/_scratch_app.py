"""
ScratchApp provides the sample app.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ..app import App

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Type


class ScratchApp(App):
  """
  ScratchApp provides the sample app.
  """
