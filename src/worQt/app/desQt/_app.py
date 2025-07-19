"""
App provides a descriptor returning the QCoreApplication instance
currently running.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication
from worktoy.core import Object

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class App(Object):
  """
  App provides a descriptor returning the QCoreApplication instance
  currently running.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, *args, **kwargs) -> Any:
    """Returns the running application instance."""
    return QCoreApplication.instance()
