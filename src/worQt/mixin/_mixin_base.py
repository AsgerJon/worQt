"""
MixinBase provides a baseclass intended as a second baseclass when
subclassing PySide6 classes.
"""
#  Apache-2.0 license
#  Copyright (c) 2025-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication as QCoreApp
from PySide6.QtWidgets import QApplication as QApp
from PySide6.QtCore import QObject
from worktoy.desc import Field, AttriBox
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt

from . import MixinMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Never


class MixinBase(BaseObject, metaclass=MixinMeta):
  """
  MixinBase provides a baseclass intended as a second baseclass when
  subclassing PySide6 classes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __field_box__ = None  # set by 'AttriBox' when this object is a boxed value

  #  Public Variables
  app: Field[QCoreApp] = Field()
  src: Field[str] = Field()
  root: Field[str] = Field()
  etc: Field[str] = Field()
  eps: Field[float] = Field()  # Smallest value distinguishable from zero
  fieldOwner: Field[type] = Field()  # The class owning the AttriBox
  fieldName: Field[str] = Field()  # The name of the AttriBox on the owner
  fieldBox: Field[AttriBox] = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @app.GET
  def _getApp(self, **kwargs) -> QCoreApp:
    runningApp = QApp.instance()
    if runningApp is None:
      infoSpec = """No running 'QApplication' document was found while
      accessing 'app' on a live '%s' object. This should be unreachable:
      constructing a 'QObject' before a 'QApplication' exists hard-crashes
      the interpreter, so a live document implies a running application."""
      clsName = type(self).__name__
      info = textFmt(infoSpec % clsName)
      raise RuntimeError(info)
    return runningApp

  @src.GET
  def _getSrc(self, **kwargs) -> str:
    here: str = os.path.abspath(__file__)
    appDir = os.path.join(here, '..')
    worQtDir = os.path.join(appDir, '..')
    srcDir = os.path.join(worQtDir, '..')
    srcDir = os.path.abspath(srcDir)
    return srcDir

  @root.GET
  def _getRoot(self, **kwargs) -> str:
    return os.path.abspath(os.path.join(self.src, '..'))

  @etc.GET
  def _getEtc(self, **kwargs) -> str:
    return os.path.join(self.src, 'etc')

  def _validateDescriptor(self, ) -> None:
    """
    This method checks that this document is owned by an AttriBox.
    """
    boxObjects = [
      self.__field_owner__,
      self.__field_name__,
      self.__field_box__,
    ]
    for obj in boxObjects:
      if obj is None:
        infoSpec = """This '%s' object is not owned by another class or 
        AttriBox!"""
        clsName = type(self).__name__
        info = textFmt(infoSpec % clsName)
        raise TypeError(info)

  @eps.GET
  def _getEps(self, ) -> float:
    return sys.float_info.epsilon

  @fieldOwner.GET
  def _getFieldOwner(self, **kwargs) -> type:
    self._validateDescriptor()
    return self.__field_owner__

  @fieldName.GET
  def _getFieldName(self, **kwargs) -> str:
    self._validateDescriptor()
    return self.__field_name__

  @fieldBox.GET
  def _getFieldBox(self, **kwargs) -> AttriBox:
    self._validateDescriptor()
    return self.__field_box__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, *_) -> Never:
    """
    'QObject' objects must not be instantiated in class bodies. This
    causes leakage between instances of the same class. By overriding
    '__set_name__' to immediately raise 'RuntimeError', we stop this
    immediately at class creation time.
    """
    infoSpec = """The '%s' class cannot be used as a class variable 
    because it inherits from 'QObject'!"""
    clsName = type(self).__name__
    info = textFmt(infoSpec % clsName)
    raise RuntimeError(info)

  def __len__(self, ) -> Never:
    """
    Subclasses should implement '__len__' as appropriate. Implementation
    is a prerequisite for certain support methods such as '_rollIndex'.
    """
    infoSpec = """The '%s' class does not implement '__len__'!"""
    info = textFmt(infoSpec % type(self).__name__)
    raise TypeError(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _resolveParent(*args) -> Optional[QObject]:
    """
    This method returns the first 'QObject' found in the positional
    arguments or 'None' if no such object is found.
    """
    for arg in args:
      if isinstance(arg, QObject):
        return arg
    else:
      return None

  def _rollIndex(self, index: int) -> int:
    """
    Rolls the index to be non-negative while smaller than the length of
    the document.
    """
    try:
      n = len(self)
    except TypeError as typeError:
      infoSpec = """Cannot roll index on document of type '%s' since it 
      does not implement '__len__'!"""
      clsName = type(self).__name__
      info = textFmt(infoSpec % clsName)
      raise TypeError(info) from typeError
    if index < 0:
      return self._rollIndex(index + n)
    if index < n:
      return index
    raise IndexError(index)
