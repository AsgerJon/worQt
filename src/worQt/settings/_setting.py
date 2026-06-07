"""
A single application setting: one named, typed value with a default, plus a
human label and optional help text for display.

'Setting' is a 'worktoy.desc.BaseDescriptor' subclass, generic in its value
type 'T'. It is declared in the 'AttriBox' mould - the subscript fixes the
type and the call fixes the default:

  volume = Setting[int](80)      # an int setting defaulting to 80
  muted = Setting[bool](False)   # a bool setting defaulting to False

so 'valueType', 'default' and 'value' are all typed by 'T'. Assigning the
value coerces it to 'T'. Because it is a descriptor, a 'Setting' placed in a
class body takes its 'name' from '__set_name__'; used standalone (the tab
builds them this way) the name is set explicitly.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from worktoy.core import Object
from worktoy.desc import Field, BaseDescriptor
from worktoy.utilities import maybe
from worktoy.waitaminute import MissingVariable, TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self

T = TypeVar('T')


def humanizeName(name: str) -> str:
  """A display label from a setting or tab name: underscores and hyphens
  become spaces and the first letter is capitalised."""
  spaced = (name or '').replace('_', ' ').replace('-', ' ').strip()
  return '%s%s' % (spaced[:1].upper(), spaced[1:]) if spaced else ''


class Setting(BaseDescriptor[T]):
  """
  One named, typed setting, declared as 'Setting[T](default)'. Carries its
  value type 'T', current value and default (all typed 'T'), plus a human
  'label' and optional 'description'. Assigning 'value' coerces to 'T'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __value_type__ = None  # 'T', captured from the 'Setting[T]' subscript
  __setting_name__ = None  # explicit name, else the descriptor field name
  __fallback_value__ = None  # the factory default
  __setting_value__ = None  # the current value
  __setting_label__ = None  # an explicit label, else humanised from the name
  __setting_description__ = None  # the optional help text

  #  Public Variables
  valueType: Field[type[T]] = Field()  # the declared type (read-only)
  name: Field[str] = Field()  # the setting key
  default: Field[T] = Field()  # the factory default (read-only)
  value: Field[T] = Field()  # current value (assignment coerces to T)
  label: Field[str] = Field()  # the display label
  description: Field[str] = Field()  # the optional help text

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @valueType.GET
  def _getValueType(self, ) -> type:
    if self.__value_type__ is None:
      raise MissingVariable(self, '__value_type__', type)
    return self.__value_type__

  def _createName(self, ) -> None:
    """
    This method sets the '__setting_name__' through the fallback path.
    """
    fieldName = self.getFieldName()
    if fieldName is None:
      raise MissingVariable(self, '__field_name__', str)
    self.__setting_name__ = fieldName

  @name.GET
  def _getName(self, **kwargs) -> str:
    if self.__setting_name__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createName()
      return self._getName(_recursion=True)
    if isinstance(self.__setting_name__, str):
      return self.__setting_name__
    raise TypeException('__setting_name__', self.__setting_name__, str)

  @default.GET
  def _getDefault(self, ) -> Any:
    return self.__fallback_value__

  @value.GET
  def _getValue(self, ) -> Any:
    return self.__setting_value__

  @label.GET
  def _getLabel(self, ) -> str:
    if self.__setting_label__ is not None:
      return self.__setting_label__
    return humanizeName(self.name or '')

  @description.GET
  def _getDescription(self, ) -> str:
    return maybe(self.__setting_description__, '')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @name.SET
  def _setName(self, name: str) -> None:
    self.__setting_name__ = name

  @value.SET
  def _setValue(self, raw: Any) -> None:
    self.__setting_value__ = self.coerce(raw)

  @label.SET
  def _setLabel(self, text: Any) -> None:
    self.__setting_label__ = '' if text is None else str(text)

  @description.SET
  def _setDescription(self, text: Any) -> None:
    self.__setting_description__ = '' if text is None else str(text)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def coerce(self, raw: Any) -> Any:
    """
    Cast 'raw' to the declared type 'T', leniently. A 'bool' setting reads
    the usual truthy strings ('1', 'true', 'yes', 'on'); otherwise an
    already-correct value passes through and anything else is run through
    the type's constructor.
    """
    valueType = self.valueType
    if valueType is bool:
      if isinstance(raw, str):
        truthy = raw.strip().lower() in ('1', 'true', 'yes', 'on')
        return True if truthy else False
      return True if raw else False
    if isinstance(raw, valueType):
      return raw
    return valueType(raw)

  def set(self, raw: Any) -> None:
    """Set the value (coerced to the declared type)."""
    self.value = raw

  def reset(self, ) -> None:
    """Restore the value to the factory default."""
    self.__setting_value__ = self.__fallback_value__

  def withName(self, name: str) -> Self:
    """Set the key and return self, for fluent standalone definitions."""
    self.name = name
    return self

  def withLabel(self, label: str) -> Self:
    """Set the display label and return self, for fluent definitions."""
    self.label = label
    return self

  def withHelp(self, description: str) -> Self:
    """Set the help text and return self, for fluent definitions."""
    self.description = description
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_getitem__(cls, valueType: object) -> Self:
    """Capture the value type 'T' from the 'Setting[T]' subscript. A
    'TypeVar' is forwarded to the generic machinery; a concrete type
    produces a fresh, type-parametrised 'Setting' awaiting its default."""
    if isinstance(valueType, TypeVar):
      return super().__class_getitem__(valueType)  # noqa
    self = object.__new__(cls)
    self.__value_type__ = valueType
    return self  # noqa

  def __call__(self, default: T) -> Self:
    """Capture the default (coerced to 'T') for the type-parametrised
    'Setting' from the subscript, seeding the value to match."""
    Object.__init__(self)
    self.__fallback_value__ = self.coerce(default)
    self.__setting_value__ = self.__fallback_value__
    return self

  def __str__(self, ) -> str:
    return '%s = %r' % (self.name, self.__setting_value__)

  __repr__ = __str__
