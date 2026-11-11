"""
GripNum enumerates what can be selected or taken hold of on a
'DiskWidget'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import Kee, KeeNum


class GripNum(KeeNum):
  """
  GripNum enumerates what can be selected or taken hold of on a
  'DiskWidget': the disk, a support, a load or reinforcement, each
  selected by a click and all but the disk dragged; the handles of the
  selected disk on its
  right edge, on its top edge and at its top right corner, which resize
  it; and the handles at the ends of the selected support's plate, which
  widen it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  DISK: Kee[str] = Kee[str]('disk')
  SUPPORT: Kee[str] = Kee[str]('support')
  LOAD: Kee[str] = Kee[str]('load')
  REBAR: Kee[str] = Kee[str]('rebar')
  LENGTH: Kee[str] = Kee[str]('length')
  HEIGHT: Kee[str] = Kee[str]('height')
  CORNER: Kee[str] = Kee[str]('corner')
  SUPPORT_START: Kee[str] = Kee[str]('support start')
  SUPPORT_END: Kee[str] = Kee[str]('support end')
