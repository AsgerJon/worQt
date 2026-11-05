"""
ViMode enumerates the modes of a 'Vidget'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import Kee, KeeNum


class ViMode(KeeNum):
  """
  ViMode enumerates the modes of a 'Vidget', as in Vi: in 'NORMAL' the
  keys are commands, in 'INSERT' they type, and in 'COMMAND' they write
  an ex command on the status line, after ':'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  NORMAL: Kee[str] = Kee[str]('normal')
  INSERT: Kee[str] = Kee[str]('insert')
  COMMAND: Kee[str] = Kee[str]('command')
