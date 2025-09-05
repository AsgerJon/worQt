"""
AbstractMenu provides the base class for menus in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import TypeException

from ..desQt import App

from icecream import ic

ic.configureOutput(includeContext=True)

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, TypeAlias, Union
  from ..menus import AbstractAction

  Action: TypeAlias = Union[AbstractAction, QAction]
  Actions: TypeAlias = Union[Action, tuple[Action, ...]]

  from . import ActionBox as Box

  Boxes: TypeAlias = Union[Box, tuple[Box, ...]]


class AbstractMenu(QMenu):
  """
  AbstractMenu provides the base class for menus in the worQt framework.
  """
