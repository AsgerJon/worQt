"""
EuclideanObject provides the base class for math objects representing points,
rectangles, vectors, and similar geometric entities.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core import Object
from worktoy.desc import Field
from worktoy.mcls import BaseMeta, BaseSpace
from worktoy.mcls import BaseSpace as Space
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import TypeException

from worQt.utils import Eps
from worQt.utils.geom import Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, TypeVar, Iterator, TypeAlias, Type, Union, Any
  from typing import Callable

  from worQt.utils.geom.dunders import INIT

  DimDict: TypeAlias = dict[str, Dimension]
  DimTuple: TypeAlias = tuple[Dimension, ...]
  Dims: TypeAlias = Iterator[Dimension]
  Bases: TypeAlias = tuple[Type, ...]
  Scalar: TypeAlias = Union[int, float]
  Scalars: TypeAlias = Iterator[Scalar]
  Cls = TypeVar("Cls")
  CLS: TypeAlias = Type[Cls]

  ITER: TypeAlias = Callable[[Cls], Iterator[int]]
  Identifier: TypeAlias = Union[int, str, slice]
  Int = Union[int, tuple[int, ...]]


class _EuclidianSpace(BaseSpace):
  """
  Implements the 'keyGroups' descriptor on the space level for all
  EuclideanObject subclasses.
  """

  def __setitem__(self, key: str, val: Any, **kwargs) -> None:
    if isinstance(val, Dimension):
      setattr(val, '__field_name__', key)
    return BaseSpace.__setitem__(self, key, val, **kwargs)

  def __init_kwargs__(cls, ) -> INIT:
    dims = (*cls,)

    def __init__(self: Cls, *args: Scalar, **kwargs: Scalar) -> None:
      for dim in dims:
        for key in dim.keyGroup:
          if key in kwargs:
            value = kwargs[key]
            setattr(self, dim.pvtName, value)
            break

    return __init__


class _EuclidianMeta(BaseMeta):
  """
  Implements the 'keyGroups' descriptor on the metaclass level for all
  EuclideanObject subclasses.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  eps = Eps()
  __dimension_dict__ = None
  __dimension_tuple__ = None

  #  Public Variables
  keyGroups = Field()
  dimensionDict = Field()
  dimensionTuple = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @dimensionDict.GET
  def _getRegisteredDimensions(cls) -> DimDict:
    return maybe(cls.__dimension_dict__, dict())

  @dimensionTuple.GET
  def _getDimensionTuple(cls) -> DimTuple:
    return maybe(cls.__dimension_tuple__, ())

  def registerDimension(cls, key: str, dim: Dimension) -> None:
    existing = cls.dimensionDict
    if key in existing:
      infoSpec = """Received duplicate dimension registration for key: 
      '%s'. Existing dimension: %s. New dimension: %s."""
      info = textFmt(infoSpec % (key, existing[key], dim))
      raise KeyError(info)
    existing[key] = dim
    cls.__dimension_dict__ = existing
    existing = cls.dimensionTuple
    cls.__dimension_tuple__ = (*existing, dim)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(cls, ) -> Dims:
    for dim in cls.dimensionTuple:
      yield dim

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __new__(mcls, name: str, bases: Bases, space: Space, **kw) -> Self:
    cls = BaseMeta.__new__(mcls, name, bases, space, **kw)
    for base in bases:
      if isinstance(base, mcls):
        for key, dim in base.dimensionDict.items():
          cls.registerDimension(key, dim)
    iterFunc = cls.__iter_factory__()
    cls.__iter__ = iterFunc
    return cls

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DUNDER FACTORIES   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter_factory__(cls: CLS) -> ITER:
    """
    Factory function creating the '__iter__' method after '__new__' has
    created the new class, but before returning it.
    """
    dims = (*cls,)

    def __iter__(self: Cls) -> Iterator[int]:
      for dim in dims:
        yield Dimension.__get__(dim, self, cls)

    return __iter__


class EuclideanObject(Object, metaclass=_EuclidianMeta):
  """
  EuclideanObject provides the base class for math objects representing
  points, rectangles, vectors, and similar geometric entities.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  eps = Eps()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    cls = type(self)
    dimSpec = """%s=%d"""
    dimTuple = cls.dimensionTuple
    dimVals = [dim.__get__(self, cls) for dim in dimTuple]
    dimNames = [dim.fieldName for dim in dimTuple]
    dims = [dimSpec % (name, val) for name, val in zip(dimNames, dimVals)]
    dimStr = ', '.join(dims)
    clsName = type(self).__name__
    return """<%s: %s>""" % (clsName, dimStr)

  def __repr__(self, ) -> str:
    cls = type(self)
    dimSpec = """%s=%d"""
    dimTuple = cls.dimensionTuple
    dimVals = [dim.__get__(self, cls) for dim in dimTuple]
    dimNames = [dim.fieldName for dim in dimTuple]
    dims = [dimSpec % (name, val) for name, val in zip(dimNames, dimVals)]
    kwargStr = ', '.join(dims)
    clsName = type(self).__name__
    infoSpec = """%s(%s)"""
    return infoSpec % (clsName, kwargStr)

  def __len__(self, ) -> int:
    cls = type(self)
    return len(cls.dimensionTuple)

  def _resolveIndex(self, index: int) -> int:
    if index < 0:
      return self.resolveIndex(index + len(self))
    if index < len(self):
      cls = type(self)
      return cls.dimensionTuple[index]
    infoSpec = """Index %d is out of bounds for %s with %d dimensions!"""
    clsName = type(self).__name__
    info = infoSpec % (index, clsName, len(self))
    raise IndexError(textFmt(info))

  def _resolveKey(self, key: str) -> int:
    cls = type(self)
    for dim in cls.dimensionTuple:
      if key in dim.keyGroup:
        return dim.__get__(self, cls)
    raise KeyError(key)

  def _resolveSlice(self, sliceObj: slice) -> tuple[int, ...]:
    cls = type(self)
    dimTuple = cls.dimensionTuple
    return tuple(dim.__get__(self, cls) for dim in dimTuple[sliceObj])

  def __getitem__(self, identifier: Identifier) -> Int:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    if isinstance(identifier, slice):
      return self._resolveSlice(identifier)
    raise TypeException('identifier', identifier, int, str, slice)

  def __getattr__(self, identifier: Any) -> Any:
    try:
      value = self.__getitem__(identifier)
    except (TypeException, KeyError, IndexError) as exception:
      infoSpec = """'%s' object has no attribute '%s'!"""
      clsName = type(self).__name__
      info = infoSpec % (clsName, identifier)
      raise AttributeError(textFmt(info)) from exception
    else:
      return value
