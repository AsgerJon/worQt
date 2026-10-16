"""
AbstractApplication subclasses 'QApplication' and provides the entry of
the application of the worQt framework.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QEvent
from worktoy.utilities import maybe

from . import ApplicationMixin

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Type

  MaybeBool: TypeAlias = Optional[bool]
  MaybeObject: TypeAlias = Optional[QObject]
  MaybeEvent: TypeAlias = Optional[QEvent]


class AbstractApplication(ApplicationMixin):
  """
  AbstractApplication subclasses 'QApplication' and provides the entry of
  the application of the worQt framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
