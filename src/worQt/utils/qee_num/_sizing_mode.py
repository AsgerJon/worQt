"""
SizingMode subclasses 'KeeNum' and enumerates the sizing modes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QSizePolicy
from worktoy.desc import Field
from worktoy.keenum import KeeNum, Kee

Q_EXT = QSizePolicy.Policy.Maximum
Q_INT = QSizePolicy.Policy.MinimumExpanding
POL = QSizePolicy.Policy

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias

  from . import SizingMode as SELF

  KeePolicy: TypeAlias = Union[SELF, POL, Kee]
  PolicyField: TypeAlias = Union[POL, Field]


class SizingMode(KeeNum):
  """
  SizingMode subclasses 'KeeNum' and enumerates the sizing modes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  EXTRINSIC: KeePolicy = Kee[POL](Q_EXT)
  INTRINSIC: KeePolicy = Kee[POL](Q_INT)

  #  Virtual Variables
  Q: PolicyField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQPolicy(self, ) -> POL:
    return self.value
