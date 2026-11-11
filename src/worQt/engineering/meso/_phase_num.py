"""
PhaseNum enumerates what the springs of a lattice are made of.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.keenum import Kee, KeeNum


class PhaseNum(KeeNum):
  """
  PhaseNum enumerates what a spring of a lattice is made of: 'STONE',
  between two nodes in one stone; 'MORTAR', between two nodes clear of
  every stone; 'BOND', crossing a stone's edge, where the mortar meets
  the stone; 'PLATEN', where a cell along the top or the bottom bears on
  the platen. Each member's 'index' is the code the lattice keeps it by.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  STONE: Kee[str] = Kee[str]('stone')
  MORTAR: Kee[str] = Kee[str]('mortar')
  BOND: Kee[str] = Kee[str]('bond')
  PLATEN: Kee[str] = Kee[str]('platen')
