"""
UndefinedState provides a custom exception raised to indicate that a state
managing class object received events forming an undefined pattern. Please
note that exception handling is significantly more complicated in the
'worQt' framework stemming from the multithreaded nature of the general
'Qt' framework which it accesses through 'PySide6'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import AbstractException


class UndefinedState(AbstractException):
  """
  UndefinedState provides a custom exception raised to indicate that a state
  managing class object received events forming an undefined pattern. Please
  note that exception handling is significantly more complicated in the
  'worQt' framework stemming from the multithreaded nature of the general
  'Qt' framework which it accesses through 'PySide6'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getExitCode(self, ) -> int:
    """
    Returns 70, inspired by the 'EX_SOFTWARE' exit code defined in the
    'sysexits.h' header file. This code is used to indicate that the
    application encountered an internal software error, which is suitable
    for the 'UndefinedState' exception.
    """
    return 70
