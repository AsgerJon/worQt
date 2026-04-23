"""
WBase provides a baseclass intended as a second baseclass when subclassing
PySide6 classes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication as QCoreApp
from PySide6.QtWidgets import QApplication as QApp
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field, AttriBox
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt

from . import MixinMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Optional, Never, Union

  Parent: TypeAlias = Union[Optional[QObject], QWidget]
  AppField: TypeAlias = Union[QCoreApp, Field]
  StrField: TypeAlias = Union[str, Field]
  FloatField: TypeAlias = Union[float, Field]
  TypeField: TypeAlias = Union[type, Field]
  BoxField: TypeAlias = Union[AttriBox, Field]


class MixinBase(BaseObject, metaclass=MixinMeta):
  """
  WBase provides a baseclass intended as a second baseclass when subclassing
  PySide6 classes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  app: AppField = Field()
  src: StrField = Field()
  root: StrField = Field()
  etc: StrField = Field()
  eps: FloatField = Field()  # Smallest value distinguishable from zero
  fieldOwner: TypeField = Field()  # The class owning the AttriBox
  fieldName: StrField = Field()  # The name of the AttriBox on the owner
  fieldBox: BoxField = Field()  # The AttriBox containing the descriptor

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @app.GET
  def _getApp(self, **kwargs) -> QCoreApp:
    return QApp.instance()

  @src.GET
  def _getSrc(self, **kwargs) -> str:
    here = os.path.abspath(__file__)
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
    This method checks that this instance is owned by an AttriBox.
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
  def _resolveParent(*args) -> Parent:
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
    the instance.
    """
    try:
      n = len(self)
    except TypeError as typeError:
      infoSpec = """Cannot roll index on instance of type '%s' since it 
      does not implement '__len__'!"""
      clsName = type(self).__name__
      info = textFmt(infoSpec % clsName)
      raise TypeError(info) from typeError
    if index < 0:
      return self._rollIndex(index + n)
    if index < n:
      return index
    raise IndexError(index)
