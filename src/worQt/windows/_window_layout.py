"""
WindowLayout subclasses 'BaseLayout' and provides the widgets and layouts
for the main application window. It replaces 'LayoutWindow' as subclass in
between 'BaseWindow' and 'MainWindow' and should instead be owned by
'MainWindow'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ..layouts import BaseLayout

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Type


class WindowLayout(BaseLayout):
  """
  WindowLayout subclasses 'BaseLayout' and provides the widgets and layouts
  for the main application window. It replaces 'LayoutWindow' as subclass in
  between 'BaseWindow' and 'MainWindow' and should instead be owned by
  'MainWindow'.
  """
