"""
ArrayField subclasses 'AbstractField' and provides a field holding any
number of objects of a given type [T] in the document.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic

from worktoy.utilities import textFmt
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
    """An array field starts empty on every document and takes no default
    contents - default items would be shared mutable state across documents.
    'ArrayField[T]' or 'ArrayField[T]()' declare the field; passing items
    raises. Items are added later with 'append' / 'extend'."""
    if values:
      infoSpec = """'ArrayField' takes no default items; it starts empty and
      is filled with 'append' or 'extend'. Received %d value(s)."""
      raise TypeError(textFmt(infoSpec % (len(values),)))
    return self

  def __set_name__(self, docType: DocType, name: str, **kwargs) -> None:
    super().__set_name__(docType, name)
    docType.registerArrayField(name, self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, instance: Any, array: ArrayLike, **kwargs) -> list:
    """Encode each item with the document's per-item encoder, returning a
    JSON-native list. The encoder is the same one a document declares with
    '@field.setEncoder'; here it is applied once per item."""
    encoder = self._getEncoderFunction()
    return [encoder(instance, item) for item in array]

  def decode(self, instance: Any, value: list, **kwargs) -> ArrayLike:
    """Rebuild the array from a list of encoded entries, decoding each with
    the document's per-item decoder, and tag the result with its owning
    field and document so 'append'/'extend' keep working after a load."""
    decoder = self._getDecoderFunction()
    items = ArrayLike([decoder(instance, raw) for raw in value])
    self._arrayTypeGuard(items)
    setattr(items, '__owning_field__', self)
    setattr(items, '__owning_document__', instance)
    self._adopt(items, instance)
    return items

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

  def _adopt(self, items: Iterable[T], doc: Doc) -> None:
    """Point each item at this field and document, so an in-place edit on an
    item (e.g. 'item.x = 5' through a 'NotifyBox') reaches 'notifyChange'."""
    for item in items:
      setattr(item, '__owning_field__', self)
      setattr(item, '__owning_document__', doc)

  def append(self, doc: Doc, item: T) -> None:
    self.extend(doc, (item,))

  def extend(self, doc: Doc, items: Iterable[T]) -> None:
    arrayLike = self.__instance_get__(doc, type(doc))
    items = self._arrayTypeGuard(ArrayLike(items))
    newArray = ArrayLike((*arrayLike, *items))
    setattr(newArray, '__owning_field__', self)
    setattr(newArray, '__owning_document__', doc)
    self._adopt(newArray, doc)
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
      newArray = ArrayLike(())  # an array field always starts empty
      setattr(newArray, '__owning_field__', self)
      setattr(newArray, '__owning_document__', doc)
      setattr(doc, pvtName, newArray)
      return self.__instance_get__(doc, docType, _recursion=True)
    else:
      return self._arrayTypeGuard(arrayLike)

  def __instance_set__(self, instance: Any, value: Any, **kwargs) -> Never:
    raise TypeError("""Do not override!""")
