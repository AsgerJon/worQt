"""
Parent provides a descriptor for the parent-child relationships between
objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QObject
from worktoy.core import Object

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Parent(Object):
  """
  Parent provides a descriptor for the parent-child relationships between
  objects.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Typehints
  instance: QObject

  def __instance_get__(self, *args, **kwargs) -> Any:
    """Returns the parent of the object, or None if no parent is set. """
    if QCoreApplication.instance() is None:
      raise NotImplementedError("""TODO: no running instance!""")
    return QObject.parent(self.instance)
