"""The 'worQt.widgets.core' module provides the core widgets for the
'worQt' library. These widgets provide the core functionalities such as
printing text, displaying images, reacting to user inputs and layout
management. Single function button widgets are also provided here, but
more complicated widgets such as sliders and widgets containing multiple
child widgets are provided in the 'worQt.widgets' module. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._layout_index import LayoutIndex
from ._layout_span import LayoutSpan
from ._layout_rect import LayoutRect
from ._base_widget import BaseWidget
from ._w_layout import WLayout
