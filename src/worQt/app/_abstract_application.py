"""
AbstractApplication is the abstract base class for worQt applications.
It is a QApplication subclass built with MixinMeta so that worktoy
descriptor and overload machinery are available alongside Qt.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import ApplicationMixin

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtCore import QObject, QEvent


class AbstractApplication(ApplicationMixin):
  """
  Abstract base for 'worQt' applications. Concrete subclasses fill in
  application-specific behaviour; abstract methods may be declared here
  as the framework matures.
  """

  def notify(self, receiver: QObject, event: QEvent) -> bool:
    """
    Wrap Qt event delivery so exceptions raised inside slots and
    event filters are routed to 'handleException'. Only 'Exception'
    subclasses are intercepted; 'BaseException' subclasses such as
    'KeyboardInterrupt' and 'SystemExit' propagate unchanged.
    """
    try:
      out = super().notify(receiver, event)
    except Exception as exception:
      handled = self.handleException(exception, receiver, event)
      if handled is None:
        return False
      return True if handled else False
    else:
      return True if out else False

  def handleException(
      self,
      exc: Exception,
      receiver: QObject = None,
      event: QEvent = None,
  ) -> bool | None:
    """
    Hook for exceptions raised during event delivery. The default
    implementation is a no-op; concrete subclasses override to log,
    swallow, exit, or re-raise.
    """
