"""
ArrayField subclasses 'AbstractField' and provides a field holding any
number of objects of a given type [T] in the document.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic

from worktoy.waitaminute import TypeException, SubclassException

from . import AbstractField, ArrayLike, AbstractItem

T = TypeVar('T')

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Never, TypeAlias, Type, Iterable

  from . import AbstractDocument as Doc

  DocType: TypeAlias = Type[Doc]


class ArrayField(AbstractField, Generic[T]):
  """
  ArrayField subclasses 'AbstractField' and provides a field holding any
  number of objects of a given type [T] in the document.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DECORATORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __class_getitem__(cls, valueType: type) -> Self:
    if not isinstance(valueType, type):
      raise TypeException('valueType', valueType, type)
    if not issubclass(valueType, AbstractItem):
      raise SubclassException(valueType, AbstractItem)
    return super().__class_getitem__(valueType)

  def __call__(self, *values, **kwargs) -> Self:
    valueTypeCache = self.valueType
    for value in values:
      if not isinstance(value, valueTypeCache):
        raise TypeException('value', value, valueTypeCache)
    setattr(self, '__fallback_value__', ArrayLike(values))
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, instance: Any, array: ArrayLike, **kwargs) -> str:
    raise NotImplementedError

  def decode(self, instance: Any, value: str, **kwargs) -> ArrayLike:
    raise NotImplementedError

  def notifyChange(self, doc: Doc, ) -> None:
    pass

  def _itemTypeGuard(self, item: T) -> T:
    if isinstance(item, self.valueType):
      return item
    raise TypeException('item', item, self.valueType)

  def _arrayTypeGuard(self, arrayLike: ArrayLike) -> ArrayLike:
    if not isinstance(arrayLike, ArrayLike):
      raise TypeException('arrayLike', arrayLike, ArrayLike)
    typeCache = self.valueType
    for item in arrayLike:
      if isinstance(item, typeCache):
        continue
      break
    else:
      return arrayLike
    raise TypeException('arrayLike', item, typeCache)

  def append(self, doc: Doc, item: T) -> None:
    self.extend(doc, (item,))

  def extend(self, doc: Doc, items: Iterable[T]) -> None:
    arrayLike = self.__instance_get__(doc, type(doc))
    items = self._arrayTypeGuard(ArrayLike(items))
    newArray = ArrayLike((*arrayLike, *items))
    setattr(newArray, '__owning_field__', self)
    setattr(newArray, '__owning_document__', doc)
    pvtName = self.getPrivateName()
    setattr(doc, pvtName, newArray)
    self.notifyChange(doc)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __instance_get__(self, doc: Doc, docType: DocType, **kw) -> ArrayLike:
    pvtName = self.getPrivateName()
    try:
      arrayLike = getattr(doc, pvtName)
    except AttributeError as attributeError:
      if kw.get('_recursion', False):
        raise RecursionError from attributeError
      newArray = ArrayLike(self, )
      setattr(newArray, '__owning_document__', doc)
      setattr(doc, pvtName, newArray)
      return self.__instance_get__(doc, docType, _recursion=True)
    else:
      return self._arrayTypeGuard(arrayLike)

  def __instance_set__(self, instance: Any, value: Any, **kwargs) -> Never:
    raise TypeError("""Do not override!""")
