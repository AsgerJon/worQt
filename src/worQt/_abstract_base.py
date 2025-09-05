"""
AbstractBase provides a general abstract base class for abstract classes
across the worQt framework. By subclassing QObject, it ensures metaclass
compatibility with other Qt classes. The intended use is for specific
abstract bases to inherit from both AbstractBase and the relevant QObject
subclass. Please note that AbstractBase must be first to ensure that all
'__init__' methods correctly runs.

class AbstractBase(QObject): pass

class AbstractWidget(AbstractBase, QWidget): pass

"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QObject
from worktoy.desc import Field
from worktoy.waitaminute import MissingVariable, TypeException

from .desQt import App

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


class AbstractBase(QObject):
  """
  The AbstractBase provides parsing of the 'parent' argument and
  implements the '__set_name__' method allowing compatibility with the
  'QtBox' class.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  app = App()

  #  Private Variables
  __field_name__ = None
  __field_owner__ = None

  #  Public Variables
  fieldName = Field()
  fieldOwner = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @fieldName.GET
  def _getFieldName(self) -> str:
    if self.__field_name__ is None:
      raise MissingVariable(self, '__field_name__', str)
    if isinstance(self.__field_name__, str):
      return self.__field_name__
    raise TypeException('__field_name__', self.__field_name__, str)

  @fieldOwner.GET
  def _getFieldOwner(self) -> type:
    if self.__field_owner__ is None:
      raise MissingVariable(self, '__field_owner__', type)
    if isinstance(self.__field_owner__, type):
      return self.__field_owner__
    raise TypeException('__field_owner__', self.__field_owner__, type)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    """
    AbstractBase treats as parent the first argument encountered that
    checks 'True' for the 'isinstance(arg, QObject)' test. Otherwise,
    it will not include a parent in the 'QObject' initializer.
    """

    for arg in args:
      if isinstance(arg, QObject):
        super().__init__(arg)
        break
    else:
      super().__init__()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: type, name: str) -> None:
    """
    The '__set_name__' method is implemented to allow compatibility with
    the 'QtBox' class.
    """
    self.__field_name__ = name
    self.__field_owner__ = owner
