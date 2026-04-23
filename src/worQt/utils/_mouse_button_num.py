"""
MouseButtonNum subclasses 'KeeNum' and enumerates the typical five mouse
buttons: left, right, middle, back and forward.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication
from worktoy.keenum import KeeNum
from moreworktoy.keenum import Kee
from worktoy.utilities import textFmt

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Union, Optional, Self

  MaybeApp: TypeAlias = Optional[QApplication]


class MouseButtonNum(KeeNum):
  """
  MouseButtonNum subclasses 'KeeNum' and enumerates the typical five mouse
  buttons: left, right, middle, back and forward.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  NULL = Kee[Qt.MouseButton](Qt.MouseButton.NoButton)
  LEFT = Kee[Qt.MouseButton](Qt.MouseButton.LeftButton)
  RIGHT = Kee[Qt.MouseButton](Qt.MouseButton.RightButton)
  MIDDLE = Kee[Qt.MouseButton](Qt.MouseButton.MiddleButton)
  BACK = Kee[Qt.MouseButton](Qt.MouseButton.BackButton)
  FORWARD = Kee[Qt.MouseButton](Qt.MouseButton.ForwardButton)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def fromApp(cls, app: MaybeApp = None) -> Self:
    """
    This method resolves an enumeration from the given app. If no app is
    passed, the currently running app is retrieved.
    """
    if app is None:
      return cls.fromApp(QApplication.instance())
    return cls(app.mouseButtons())

  @classmethod
  def fromEvent(cls, e: QMouseEvent) -> Self:
    eventValue = QMouseEvent.buttons(e)
    for self in cls:
      if self.value == eventValue:
        return self
    infoSpec = """Unable to resolve mouse button from event: '%s'!"""
    info = infoSpec % (str(e),)
    raise ValueError(textFmt(info))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __bool__(self, ) -> bool:
    return False if self is self.NULL else True
