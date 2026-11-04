"""
InvalidSizePolicy is a custom exception inheriting from 'EventException'
raised when an invalid size policy is encountered during event handling in
the 'worQt' framework.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from . import EventException


class InvalidSizePolicy(EventException):
  """
  InvalidSizePolicy is a custom exception inheriting from 'EventException'
  raised when an invalid size policy is encountered during event handling in
  the 'worQt' framework.
  """

  __slots__ = ('sizePolicy', 'event')

  def __init__(self, *args, ) -> None:
    _sizePolicy, _event, *_ = (*args, None, None)
    self.sizePolicy = _sizePolicy
    EventException.__init__(self, _event)

  def __str__(self, ) -> str:
    if self.sizePolicy is None:
      return EventException.__str__(self, )
    infoSpec = """<%s: Received: '%s': '%s'>"""
    clsName = type(self).__name__
    polType = type(self.sizePolicy).__name__
    polInfo = str(self.sizePolicy)
    return infoSpec % (clsName, polType, polInfo)
