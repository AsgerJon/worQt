"""
KeyboardException subclasses 'EventException' and provides a custom
exception raised during keyboard events.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QKeyEvent

from worQt.waitaminute.events import EventException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class KeyboardException(EventException):
  """
  KeyboardException subclasses 'EventException' and provides a custom
  exception raised during keyboard events.
  """

  __slots__ = ('widget', 'event',)

  def __init__(self, *args, ) -> None:
    _widget, _event, _msg = None, None, None
    posArgs = [*reversed(args), ]
    unusedArgs = []

    while posArgs:
      arg = posArgs.pop()
      if hasattr(arg, 'widget') and _widget is None:
        _widget = arg.widget
        continue
      if isinstance(arg, QKeyEvent) and _event is None:
        _event = arg
        continue
      if isinstance(arg, str) and _msg is None:
        _msg = arg
        continue
      unusedArgs.append(arg)
    if _widget is not None:
      self.widget = _widget
    if _event is not None:
      self.event = _event
    if _msg is None:
      EventException.__init__(self, *unusedArgs)
    else:
      EventException.__init__(self, _msg, *unusedArgs)
