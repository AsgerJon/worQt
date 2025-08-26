"""
MouseTimer provides a shared base class for mouse button timers.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Qt
from worktoy.core import Object
from worktoy.desc import Field

from worQt.desQt import Etc
from worQt.settings import MouseClickSettings

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, TypeAlias

  from .. import BaseWidget as Widget

  from ...nums import MouseButtonNum as BtnNum

  WidgetType: TypeAlias = Type[Widget]


class MouseTimer(Object):
  """
  MouseTimer provides a shared base class for mouse button timers.
  It is used to manage the timing of mouse button events in widgets.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()
  settings = MouseClickSettings()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createTimer(self, ) -> QTimer:
    """
    Subclasses must implement this method to specify how to instantiate
    QTimer.
    """
    raise NotImplementedError

  def __instance_get__(self, *args, **kwargs) -> QTimer:
    pvtName = self.getPrivateName()
    if hasattr(self.instance, pvtName):
      return getattr(self.instance, pvtName)
    if kwargs.get('_recursion', False):
      raise RecursionError
    setattr(self.instance, pvtName, self._createTimer())
    return self.__instance_get__(*args, _recursion=True, )
