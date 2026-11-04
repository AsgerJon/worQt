"""
The 'worQt.widgets' package provides the widget components of the 'worQt'
framework. It provides custom layout and widget implementations. The base
widget class implements the box model for fine control of spacing and
alignments.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._widget_mixin import WidgetMixin
from ._abstract_widget import AbstractWidget
from ._painted_widget import PaintedWidget
from ._label_widget import LabelWidget
from ._text_widget import TextWidget
from ._paint_button import PaintButton
from ._click_button import ClickButton
from ._push_button import PushButton
from ._scratch_widget import ScratchWidget

__all__ = [
  'WidgetMixin',
  'AbstractWidget',
  'PaintedWidget',
  'LabelWidget',
  'TextWidget',
  'PaintButton',
  'ClickButton',
  'PushButton',
  'ScratchWidget',
  ]
