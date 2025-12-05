"""
ActionBox provides a subclass of 'AttriBox' specifically for 'WAction'
objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import Any

from worktoy.desc import AttriBox


class ActionBox(AttriBox):
  """
  ActionBox provides a subclass of 'AttriBox' specifically for 'WAction'
  objects.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getPosArgs(self, **kwargs) -> tuple[Any, ...]:
    attriArgs = AttriBox.getPosArgs(self, **kwargs)
    owner = self.getFieldOwner()
    name = self.getFieldName()
    return (owner, name, *attriArgs)  # noqa, pycharm please!
