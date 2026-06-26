"""
MouseException subclasses 'EventException' and provides a custom exception
raised during mouse events.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from . import EventException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MouseException(EventException):
  """
  MouseException subclasses 'EventException' and provides a custom exception
  raised during mouse events.
  """

  __slots__ = ('widget', 'event')

  def __init__(self, *args, ) -> None:
    _widget, _event, _msg = None, None, None
    posArgs = [*reversed(args), ]
    unusedArgs = []

    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, QWidget) and _widget is None:
        _widget = arg
        continue
      if isinstance(arg, QMouseEvent) and _event is None:
        _event = arg
        continue
      if isinstance(arg, str) and _msg is None:
        _msg = arg
        continue
      unusedArgs.append(arg)
    if _widget is not None:
      self.widget = _widget
    if _msg is None:
      EventException.__init__(self, _event, *unusedArgs)
    else:
      EventException.__init__(self, _event, _msg, *unusedArgs)
