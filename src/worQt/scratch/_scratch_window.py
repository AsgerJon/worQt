"""
ScratchWindow provides the sample window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QGridLayout
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..widgets import BaseWidget
from ..windows import MainWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Type

MinExpPol: QSizePolicy.Policy = QSizePolicy.Policy.MinimumExpanding
MaxPol: QSizePolicy.Policy = QSizePolicy.Policy.Maximum


class ScratchWindow(MainWindow):
  """
  ScratchWindow provides the sample window.
  """

  baseWidget = AttriBox[BaseWidget](THIS, )
  baseLayout = AttriBox[QGridLayout]()
