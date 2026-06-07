"""
AbstractDocument subclasses 'BaseObject' from the 'worktoy.mcls' module
and provides a base for documents and projects.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from worktoy.dispatch import overload
from worktoy.utilities import maybe
from worktoy.desc import AttriBox, Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException

from . import MainFile

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias, IO

  from . import SingleField, ArrayField

  Bases: TypeAlias = tuple[type, ...]


class AbstractDocument(BaseObject):
  """
  AbstractDocument subclasses 'BaseObject' from the 'worktoy.mcls' module
  and provides a base for documents and projects.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  STATIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __single_fields__: Optional[dict[str, SingleField]] = None
  __array_fields__: Optional[dict[str, ArrayField]] = None

  #  Fallback Variables

  #  Public Variables
  mainFile = AttriBox[MainFile]()

  #  Virtual Variables
  mainDir: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _createSingleFields(cls, ) -> None:
    cls.__single_fields__ = {**maybe(cls.__single_fields__, dict()), }

  @classmethod
  def _getSingleFields(cls, **kwargs) -> dict[str, SingleField]:
    if cls.__dict__.get('__single_fields__') is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      cls._createSingleFields()
      return cls._getSingleFields(_recursion=True)
    if isinstance(cls.__single_fields__, dict):
      return cls.__single_fields__
    raise TypeException('__single_fields__', cls.__single_fields__, dict)

  @classmethod
  def registerSingleField(cls, name: str, field: SingleField) -> None:
    existing = cls._getSingleFields()
    existing[name] = field
    cls.__single_fields__ = existing

  @classmethod
  def _createArrayFields(cls, ) -> None:
    cls.__array_fields__ = {**maybe(cls.__array_fields__, dict()), }

  @classmethod
  def _getArrayFields(cls, **kwargs) -> dict[str, ArrayField]:
    if cls.__dict__.get('__array_fields__') is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      cls._createArrayFields()
      return cls._getArrayFields(_recursion=True)
    if isinstance(cls.__array_fields__, dict):
      return cls.__array_fields__
    raise TypeException('__array_fields__', cls.__array_fields__, dict)

  @classmethod
  def registerArrayField(cls, name: str, field: ArrayField) -> None:
    existing = cls._getArrayFields()
    existing[name] = field
    cls.__array_fields__ = existing

  @mainDir.GET
  def _getMainDir(self, ) -> str:
    return self.mainFile.dirPath

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mainDir.SET
  def _setMainDir(self, mainDir: str) -> None:
    self.mainFile.dirPath = mainDir

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __init__(self, directory: str) -> None:
    self.mainFile.dirPath = directory

  @overload()
  def __init__(self, **kwargs) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _encodeData(self, io: IO) -> None:
    data = dict()
    cls = type(self)
    for key, field in self._getSingleFields().items():
      value = type(field).__get__(field, self, cls)
      encoded = type(field).encode(field, self, value)
      data[key] = encoded
    for key, field in self._getArrayFields().items():
      array = type(field).__get__(field, self, cls)
      data[key] = type(field).encode(field, self, array)
    json.dump(data, io)

  def _decodeData(self, io: IO) -> None:
    encodedData = json.load(io)
    for key, field in self._getSingleFields().items():
      encoded = encodedData.get(key, '')
      decoded = type(field).decode(field, self, encoded)
      type(field).__set__(field, self, decoded, )
    for key, field in self._getArrayFields().items():
      raw = encodedData.get(key, [])
      decoded = type(field).decode(field, self, raw)
      #  ArrayField blocks '__set__' ("Do not override!"), so write the
      #  rebuilt 'ArrayLike' straight onto the field's private slot.
      setattr(self, field.getPrivateName(), decoded)

  def save(self, ) -> None:
    self.mainFile.save(self._encodeData)

  def load(self, ) -> None:
    self.mainFile.load(self._decodeData)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  REQUIRED METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
