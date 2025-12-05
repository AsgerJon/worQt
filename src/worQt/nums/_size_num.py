"""
SizeNum enumerates size policies. Please note the unintuitive meaning:
'MIN' means that the size hints are taken to mean the minimum size,
whilst expanding, while 'MAX' means that the size hints are taken to mean
the maximum size, whilst contracting. In other words, 'MIN' results in a
larger size than 'MAX'. This mirrors the naming conventions used in Qt.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QSizePolicy

from worktoy.keenum import KeeNum, Kee


class SizeNum(KeeNum):
  """
  SizeNum enumerates size policies.
  """

  FIX = Kee[QSizePolicy.Policy](QSizePolicy.Policy.Fixed)
  MAX = Kee[QSizePolicy.Policy](QSizePolicy.Policy.Maximum)
  PREF = Kee[QSizePolicy.Policy](QSizePolicy.Policy.Preferred)
  MIN = Kee[QSizePolicy.Policy](QSizePolicy.Policy.MinimumExpanding)
