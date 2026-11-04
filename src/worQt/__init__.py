"""
The 'worQt' expands the functionality of the 'worktoy' library with
utilities for development of desktop applications based on Qt for Python.

The subpackages load on first access rather than when 'worQt' itself is
imported. 'python -m worQt.qtest' imports this package before the test
runner, so a broken widget or window module must not be able to take the
runner down with it: the breakage then surfaces as a failure of the test
class that imports it.
"""
#  Apache-2.0 license
#  Copyright (c) 2025-2026 Asger Jon Vistisen
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from ._class_body_template import ClassBodyTemplate

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

  from . import mixin
  from . import qtest
  from . import layouts
  from . import widgets
  from . import windows

__all__ = (
  'ClassBodyTemplate',
  'mixin',
  'qtest',
  'layouts',
  'widgets',
  'windows',
)

_LAZY_PACKAGES = ('mixin', 'qtest', 'layouts', 'widgets', 'windows')


def __getattr__(name: str) -> Any:
  """
  The module-level '__getattr__' imports a subpackage the first time it is
  reached as an attribute, so 'worQt.widgets' and 'from worQt import
  widgets' keep working without importing every subpackage up front.
  """
  if name in _LAZY_PACKAGES:
    return import_module('%s.%s' % (__name__, name))
  infoSpec = """module '%s' has no attribute '%s'"""
  raise AttributeError(infoSpec % (__name__, name))
