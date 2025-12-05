"""
WSignal provides a vastly superior implementation of the descriptor
protocol to facilitate the creation of SignalInstance objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import SignalInstance

from worQt.core import WBaseObject


class WSignal(WBaseObject):
  """
  WSignal provides a vastly superior implementation of the descriptor
  protocol to facilitate the creation of SignalInstance objects.
  """

  def _createSignalInstance(self, ) -> SignalInstance:
    """Create a SignalInstance."""
    posArgs = self.getPosArgs()
    keyArgs = self.getKeyArgs()
    return SignalInstance(*posArgs, **keyArgs)

  def __instance_get__(self, *args, **kwargs) -> SignalInstance:
    """Create a SignalInstance when accessed from an instance."""
    pvtName = self._getPrivateName()
    try:
      signal = getattr(self.instance, self.getPrivateName())
    except AttributeError as attributeError:
      if kwargs.get('_recursion', False):
        raise RecursionError from attributeError
      signal = self._createSignalInstance()
      setattr(self.instance, pvtName, signal)
      return self.__instance_get__(*args, _recursion=True)
    else:
      return signal
