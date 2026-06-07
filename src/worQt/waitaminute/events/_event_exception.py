"""
EventException provides a custom exception raised by custom widgets during
event handling. Such exceptions require a specialized routing to reach
error handling on the application level. This is because the event loop
generally swallows exceptions raised during event handling. The
'AbstractWidget' class in 'worQt.widgets' package wraps 'QWidget.event' in
a try-except clause that catches 'EventException' exceptions and routes
them through a special signal to a dedicated slot on the application level.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class EventException(Exception):
  """
  EventException provides a custom exception raised by custom widgets during
  event handling. Such exceptions require a specialized routing to reach
  error handling on the application level. This is because the event loop
  generally swallows exceptions raised during event handling. The
  'AbstractWidget' class in 'worQt.widgets' package wraps 'QWidget.event' in
  a try-except clause that catches 'EventException' exceptions and routes
  them through a special signal to a dedicated slot on the application level.
  """

  __slots__ = ('event',)

  def __init__(self, event_: QEvent = None, ) -> None:
    self.event = event_
    Exception.__init__(self, )

  def __str__(self, ) -> str:
    if self.event is None:
      return Exception.__str__(self, )
    infoSpec = """<%s during '%s': %s>"""
    clsName = type(self).__name__
    eType = type(self.event).__name__
    eClsName = type(self.event).__name__
    eInfoSpec = """<%s: %s>"""
    eInfo = eInfoSpec % (eClsName, eType)
    return infoSpec % (clsName, eType, eInfo)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%s)"""
    clsName = type(self).__name__
    eInfo = repr(self.event)
    eventType = QEvent.type(self.event).name
    eClsName = type(self.event).__name__
    eInfoSpec = """<%s: %s>"""
    eInfo = eInfoSpec % (eClsName, eventType)
    return infoSpec % (clsName, eInfo)
