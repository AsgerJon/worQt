"""
BaseWidget subclasses 'AbstractWidget' and provides the base class for
standard widgets. It is more restrictive than 'AbstractWidget' requiring
implementation of sizing and alignment policies.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractWidget


class BaseWidget(AbstractWidget):
  """
  BaseWidget subclasses 'AbstractWidget' and provides the base class for
  standard widgets. It is more restrictive than 'AbstractWidget' requiring
  implementation of sizing and alignment policies.
  """

