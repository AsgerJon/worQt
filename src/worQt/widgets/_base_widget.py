"""
BaseWidget provides a base for the widgets in the worQt framework. It
derives from both 'ObjectType' which is the custom metaclass provided by
'PySide6' but also from 'BaseMeta' (through some finagling) which is the
custom metaclass provided by 'worktoy.mcls'. This combination is the main
benefit provided by this base. Additionally,
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.mcls import BaseSpace
from worktoy.utilities import maybe

from ..core import WBaseObject
from ..nums import Alignum, SizePolicy, SizeNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Any, Optional

  Bases: TypeAlias = tuple[type, ...]
  Space: TypeAlias = Union[dict[str, Any], BaseSpace]

  Parsed: TypeAlias = tuple[Optional[Any], list[Any],]


class BaseWidget(QWidget, WBaseObject):
  """
  BaseWidget provides a base for the widgets in the worQt framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __min_width__ = 32
  __min_height__ = 32

  #  Fallback Variables
  __fallback_align__ = Alignum.CENTER
  __fallback_policy__ = SizePolicy(SizeNum.PREF, )

  #  Private Variables
  __align_value__ = None
  __size_policy__ = None

  #  Public Variables
  align = Field()
  sizePolicy = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @align.GET
  def _getAlign(self, **kwargs) -> Alignum:
    return maybe(self.__align_value__, self.__fallback_align__)

  @sizePolicy.GET
  def _getSizePolicy(self, **kwargs) -> SizePolicy:
    return maybe(self.__size_policy__, self.__fallback_policy__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    parent, args = self._parseParent(*args)
    if parent is not None:
      QWidget.__init__(self, parent)
    else:
      QWidget.__init__(self, )
    if args:
      sizePolicy, args = self._parseSizePolicy(*args)
      if sizePolicy is not None:
        self.__size_policy__ = sizePolicy
        self.setSizePolicy(sizePolicy.Q)
    if args:
      alignum, args = self._parseAlign(*args)
      if alignum is not None:
        self.__align_value__ = alignum
    self.setMinimumHeight(self.__min_height__)
    self.setMinimumWidth(self.__min_width__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _parseParent(*args) -> Parsed:
    posArgs = [*args, ]
    out = []
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, QWidget):
        return arg, [*out, *posArgs, ]
      out.append(arg)
    return None, out

  @staticmethod
  def _parseSizePolicy(*args) -> Parsed:
    posArgs = [*reversed([*args, ]), ]
    out = []
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, SizePolicy):
        return arg, [*out, *posArgs, ]
      out.append(arg)
    return None, out

  @staticmethod
  def _parseAlignum(*args) -> Parsed:
    posArgs = [*args, ]
    out = []
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, Alignum):
        return arg, [*out, *posArgs, ]
      out.append(arg)
    return None, out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    This hook runs before the widget is shown for the first time. It is
    intended to be overridden by subclasses to set up the widget and any
    child widgets it may have. Setting up signals and slots should be
    organized by 'initLogic' instead as it runs immediately after the
    widget is first shown.
    """
    pass

  def initLogic(self, ) -> None:
    """
    This hook runs immediately after the super call to
    'QWidget.showEvent'. Subclasses should connect signals and slots by
    reimplementing this method.

    IMPORTANT:
    Avoid duplicate connections by *always* preceding every 'connect' call
    with a corresponding 'disconnect' call. For example:

    def initLogic(self, ) -> None:
      # Connect self.foo to self.bar
      self.foo.disconnect(self.bar)
      self.foo.connect(self.bar)

    Please note that disconnecting where no connection exists is safe and
    will not raise an exception. As such, multiple calls to 'initLogic'
    will not result in duplicate connections. The signal-slot architecture
    designed in the 1990's does not expose the existing connections,
    not even on the C++ side. This makes it impossible to prevent
    duplicate connections by inspecting existing connections. In this
    context, 'impossible' actually means 'impossible', not 'requires
    metaclass customization'. In conclusion: setup all internal signal
    slot connections in this method and disconnect before every connect.
    """
    pass

  def showEvent(self, event: QShowEvent) -> None:
    self.initUI()
    super().showEvent(event)
    self.initLogic()
