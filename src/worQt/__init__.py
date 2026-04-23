"""The 'worQt' expands the functionality of the 'worktoy' library with
utilities for development of desktop applications based on Qt for Python. """
#  AGPL-3.0 license
#  Copyright (c) 2025-2026 Asger Jon Vistisen
from __future__ import annotations

from ._class_body_template import ClassBodyTemplate

from . import waitaminute
from . import utils
from . import mixin
from . import app
from . import layouts
from . import paint_ops
from . import widgets
from . import windows

__all__ = [
  'ClassBodyTemplate',
  'waitaminute',
  'utils',
  'mixin',
  'app',
  'layouts',
  'paint_ops',
  'widgets',
  'windows',
  ]
