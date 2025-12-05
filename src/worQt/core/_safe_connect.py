"""
The 'safeConnect' function safely disconnects any existing connection
before establishing it. The purpose of this is to prevent duplicate
connections in the signal-slot architecture of Qt.

Arguments:
  signal: The signal to connect.
  slot: The slot to connect to the signal.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING
from warnings import simplefilter
import _warnings

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtCore import Signal, Slot


def safeConnect(signal: Signal, slot: Slot) -> None:
  """
  The 'safeConnect' function safely disconnects any existing connection
  before establishing it. The purpose of this is to prevent duplicate
  connections in the signal-slot architecture of Qt.

  Arguments:
    signal: The signal to connect.
    slot: The slot to connect to the signal.
  """
  __old_filters__ = _warnings.filters[:]
  try:
    simplefilter('ignore', RuntimeWarning, )
    signal.disconnect(slot)
    signal.connect(slot)
  finally:
    _warnings.filters[:] = __old_filters__
