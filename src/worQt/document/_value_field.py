"""
ValueField is a scalar, change-aware, serializable slot. It is the single
mechanism for plain data, used both as a 'field' on a 'Document' (a bool, a
title) and as an 'attribute' on a 'Member' (a node's x/y/z). Declared as
'x = ValueField[float](0.0)': the subscript fixes the value type, the call
captures the default.

It subclasses 'BaseObject', so it inherits worktoy's descriptor machinery -
'__set_name__'/'hookSetName', the 'getFieldName'/'getPrivateName' helpers and
the '__instance_get__'/'__instance_set__' routing - rather than reinventing
it. A non-JSON value type supplies a codec via the 'setEncoder'/'setDecoder'
decorators (positional only; worQt takes no kwargs).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException

from ._change import Change

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable, Self


class ValueField(BaseObject):
  """A typed scalar slot that notifies its host on change and round-trips
  through an optional codec."""

  #  Per-descriptor configuration (instance attributes; class defaults here).
  __value_type__ = None
  __value_default__ = None
  __value_encoder__ = None
  __value_decoder__ = None

  @classmethod
  def __class_getitem__(cls, valueType: type) -> Self:
    self = cls()
    self.__value_type__ = valueType
    return self

  def __call__(self, default: Any) -> Self:
    self.__value_default__ = default
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CODEC DECORATORS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setEncoder(self, func: Callable) -> Callable:
    """Register the value -> JSON-native function. Returns it unchanged so
    it stacks as a plain decorator in the class body."""
    self.__value_encoder__ = func
    return func

  def setDecoder(self, func: Callable) -> Callable:
    """Register the JSON-native -> value function."""
    self.__value_decoder__ = func
    return func

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DESCRIPTOR HOOKS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def hookSetName(self, owner: type, name: str, **kwargs) -> None:
    owner._registerValueField(name, self)

  def __instance_get__(self, instance: Any, owner: type, **kwargs) -> Any:
    #  'self.instance' is the context instance worktoy pushed in '__get__'.
    return getattr(self.instance, self.getPrivateName(), self.__value_default__)

  def __instance_set__(self, instance: Any, value: Any, **kwargs) -> None:
    if not isinstance(value, self.__value_type__):
      raise TypeException(self.getFieldName(), value, self.__value_type__)
    host = self.instance
    pvtName = self.getPrivateName()
    old = getattr(host, pvtName, self.__value_default__)
    setattr(host, pvtName, value)
    if value != old:
      host.notifyChange(Change(host, self.getFieldName(), 'set', old, value))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SERIALIZATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, instance: Any) -> Any:
    value = self.__get__(instance, type(instance))  # through the context
    return self.__value_encoder__(value) if self.__value_encoder__ else value

  def decode(self, instance: Any, raw: Any) -> None:
    value = self.__value_decoder__(raw) if self.__value_decoder__ else raw
    self.__set__(instance, value)  # through the context
