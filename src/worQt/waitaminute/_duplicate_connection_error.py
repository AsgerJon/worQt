"""
DuplicateConnectionError provides a custom exception raised to indicate
that an attempt were made to create a connection between a signal and a slot
already connected.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import SignalInstance

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable


class DuplicateConnectionError(RuntimeError):
  """
  DuplicateConnectionError provides a custom exception raised to indicate
  that an attempt were made to create a connection between a signal and a
  slot
  already connected.
  """

  __slots__ = ('sig', 'slt')

  def __init__(self, sig: SignalInstance, slt: Callable) -> None:
    self.sig = sig
    self.slt = slt

  def __str__(self, ) -> str:
    infoSpec = """Attempted to connect signal '%s' to slot '%s' when 
    already connected!"""
    return object.__str__(self, )

  __repr__ = __str__
