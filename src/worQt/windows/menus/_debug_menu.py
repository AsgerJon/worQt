"""
DebugMenu subclasses 'WMenu' and provides a debug menu intended for
development allowing for ad hoc testing of actions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox
from worktoy.utilities import textFmt

from . import WMenu, WAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union

  ActionBox: TypeAlias = Union[WAction, AttriBox]

DEBUG_TIP: str = textFmt(
  """Debug menu providing access to debugging actions for development.""",
  )
DEBUG_TIP_01: str = textFmt("""Never gonna give you up.""", )
DEBUG_TIP_02: str = textFmt("""Never gonna let you down.""", )
DEBUG_TIP_03: str = textFmt("""Never gonna run around and desert you.""", )
DEBUG_TIP_04: str = textFmt("""Never gonna make you cry.""", )


class DebugMenu(WMenu):
  """
  DebugMenu subclasses 'WMenu' and provides a debug menu intended for
  development allowing for ad hoc testing of actions.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  debug01: ActionBox = AttriBox[WAction](THIS, 'debug01', DEBUG_TIP_01)
  debug02: ActionBox = AttriBox[WAction](THIS, 'debug02', DEBUG_TIP_02)
  debug03: ActionBox = AttriBox[WAction](THIS, 'debug03', DEBUG_TIP_03)
  debug04: ActionBox = AttriBox[WAction](THIS, 'debug04', DEBUG_TIP_04)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    Initialize the user interface of the menu by adding the actions to the
    menu.
    """
    super().initUI()
    self.tip = DEBUG_TIP
    self.addAction(self.debug01)
    self.debug01.keyBind = 'ALT+1'
    self.addAction(self.debug02)
    self.debug02.keyBind = 'ALT+2'
    self.addAction(self.debug03)
    self.debug03.keyBind = 'ALT+3'
    self.addAction(self.debug04)
    self.debug04.keyBind = 'ALT+4'
