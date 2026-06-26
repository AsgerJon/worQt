"""
PaintException subclasses 'EventException' and provides a custom exception
raised during paint_ops events.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from . import EventException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class PaintException(EventException):
  """
  PaintException subclasses 'EventException' and provides a custom exception
  raised during paint_ops events.
  """

  __slots__ = ('widget', 'painter', 'event')

  def __init__(self, *args, ) -> None:
    _widget, _painter, _event, _msg = None, None, None, None
    posArgs = [*reversed(args), ]
    unusedArgs = []

    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, QWidget) and _widget is None:
        _widget = arg
        continue
      if isinstance(arg, QPainter) and _painter is None:
        _painter = arg
        continue
      if isinstance(arg, QEvent) and _event is None:
        _event = arg
        continue
      if isinstance(arg, str) and _msg is None:
        _msg = arg
        continue
      unusedArgs.append(arg)
    if _widget is not None:
      self.widget = _widget
    if _painter is not None:
      self.painter = _painter
    if _msg is None:
      EventException.__init__(self, _event, *unusedArgs)
    else:
      EventException.__init__(self, _event, _msg, *unusedArgs)
