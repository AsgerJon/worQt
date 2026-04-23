"""
DimHook subclasses 'worktoy.mcls.space_hooks.AbstractSpaceHook'
implementing awareness of 'Dimension' objects encountered during class
body execution.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic
from worktoy.core.sentinels import THIS
from worktoy.dispatch import overload
from worktoy.mcls.space_hooks import AbstractSpaceHook
from worktoy.utilities import typeCast, maybe, textFmt
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.dispatch import TypeCastException

from . import Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable, TypeAlias, Iterator, Self

  from . import EuclidianSpace

  INIT: TypeAlias = Callable[[Any], None]
  Overloads: TypeAlias = Iterator[tuple[str, tuple[overload, ...]]]

ic.configureOutput(includeContext=True)


class DimHook(AbstractSpaceHook):
  """
  DimHook subclasses 'worktoy.mcls.space_hooks.AbstractSpaceHook'
  implementing awareness of 'Dimension' objects encountered during class
  body execution.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public variables
  space: EuclidianSpace

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setItemPhase(self, key: str, val: Any, old: Any = None, ) -> bool:
    """
    Registers 'Dimension' objects and registers them in the namespace.
    """
    if isinstance(val, Dimension):
      self.space.registerDimensionObject(key, val)
      return True
    return False

  def preCompilePhase(self, compiledSpace: dict) -> dict:
    """
    When subclassing classes in the 'worQt.utils.geom.euclid' package,
    the 'Dimension' objects registered on base classes are registered on
    the subclass directly. This emulates the expected behaviour,
    but retrieves the 'Dimension' objects from the subclass directly,
    rather than resolving through the MRO. This flattening greatly
    simplifies implementing functionality emerging from modularly defined
    parts.
    """
    #  Setting up dimensions
    compiledSpace['getDimensions'] = self._getDimsFactory()
    dimObjects = self.space.getDimensionObjects()
    dimRegistry = dict()
    for dim in dimObjects:
      compiledSpace[dim.__field_name__] = dim
      dimRegistry[dim.__field_name__] = dim
    else:
      compiledSpace['__dim_registry__'] = dimRegistry

    #  Container methods
    compiledSpace['__iter__'] = self._iterFactory()
    compiledSpace['__len__'] = self._lenFactory()
    compiledSpace['__bool__'] = self._boolFactory()
    compiledSpace['__getattr__'] = self._getAttrFactory()

    #  Implementing '__str__', '__repr__', and '__dim_helper__'
    compiledSpace['__dim_helper__'] = self._dimFactory(self.space)
    compiledSpace['__str__'] = self._strFactory()
    compiledSpace['__repr__'] = self._reprFactory()

    #  Implementing arithmetic operations
    compiledSpace['__neg__'] = self._negFactory()

    #  Implementing overloads ('__init__' and '__getitem__')
    names = '__init__', '__getitem__'
    loadedFuncs = self._initLoads(), self._getItemLoads()
    for name, loads in zip(names, loadedFuncs):
      for load in loads:
        for sig, func in load:
          self.space.addOverload(name, sig, func)
    #  Adding overloads
    for name, loads in self._overloads():
      for load in loads:
        for sig, func in load:
          self.space.addOverload(name, sig, func)
    return AbstractSpaceHook.preCompilePhase(self, compiledSpace)

  def _overloads(self, ) -> Overloads:
    yield '__init__', (*self._initLoads(),)
    yield '__getitem__', (*self._getItemLoads(),)
    yield '__mul__', (self._mulScalarLoad(),)
    yield '__imul__', (self._imulScalarLoad(),)
    yield '__rmul__', (self._rmulScalarLoad(),)
    yield '__matmul__', (self._matmulScalarLoad(),)
    yield '__imatmul__', (self._imatmulScalarLoad(),)
    yield '__rmatmul__', (self._rmatmulScalarLoad(),)
    yield '__add__', (self._addTHISLoad(), self._addScalarLoad(),)
    yield '__iadd__', (self._iaddTHISLoad(), self._iaddScalarLoad(),)
    yield '__radd__', (self._raddTHISLoad(), self._raddScalarLoad(),)
    yield '__sub__', (self._subTHISLoad(), self._subScalarLoad(),)
    yield '__isub__', (self._isubTHISLoad(), self._isubScalarLoad(),)
    yield '__rsub__', (self._rsubTHISLoad(), self._rsubScalarLoad(),)
    yield '__truediv__', (self._truedivScalarLoad(),)
    yield '__itruediv__', (self._itruedivScalarLoad(),)
    yield '__mod__', (self._modScalarLoad(),)
    yield '__imod__', (self._imodScalarLoad(),)

  @classmethod
  def _modScalarLoad(cls, ) -> overload:
    """
    This method generates the overload for modulo with scalar values.
    Scalars are applied to each component.
    """

    @overload(float)
    @overload(int)
    def __mod__(self, other: Any) -> Self:
      if isinstance(other, (int, float)):
        if abs(other) < self.eps:
          raise ZeroDivisionError
        cls_ = type(self)
        dimObjects = cls_.getDimensions()
        args = (dim.__get__(self, cls_) % other for dim in dimObjects)
        return cls_(*args)
      return NotImplemented

    return __mod__

  _imodScalarLoad = _modScalarLoad

  @classmethod
  def _truedivScalarLoad(cls, ) -> overload:
    """
    This method generates the overload for true division with scalar values.
    Scalars are divided into each component.
    """

    @overload(float)
    @overload(int)
    def __truediv__(self, other: Any) -> Self:
      if isinstance(other, (int, float)):
        if abs(other) < self.eps:
          raise ZeroDivisionError
        return self * (1 / other)
      return NotImplemented

    return __truediv__

  _itruedivScalarLoad = _truedivScalarLoad

  @classmethod
  def _rsubTHISLoad(cls, ) -> overload:
    """
    This method generates the overload for right-side subtraction with
    'THIS',
    allowing for the subtraction of two objects of the same class.
    """

    @overload(THIS)
    def __rsub__(self, other: Self) -> Self:
      if isinstance(other, type(self)):
        return (-self) + other
      return NotImplemented

    return __rsub__

  @classmethod
  def _subTHISLoad(cls, ) -> overload:
    """
    This method generates the overload for subtraction with 'THIS', allowing
    for the subtraction of two objects of the same class.
    """

    @overload(THIS)
    def __sub__(self, other: Self) -> Self:
      if isinstance(other, type(self)):
        return self + (-other)
      return NotImplemented

    return __sub__

  _isubTHISLoad = _subTHISLoad

  @classmethod
  def _addTHISLoad(cls, ) -> overload:
    """
    This method generates the overload for addition with 'THIS', allowing
    for the addition of two objects of the same class.
    """

    @overload(THIS)
    def __add__(self, other: Self) -> Self:
      if isinstance(other, type(self)):
        cls_ = type(self)
        return cls_(*(i + j for i, j in zip(self, other)), )
      return NotImplemented

    return __add__

  _iaddTHISLoad = _addTHISLoad
  _raddTHISLoad = _addTHISLoad

  @classmethod
  def _rsubScalarLoad(cls, ) -> overload:
    """
    This method generates the overload for right-side subtraction with scalar
    values. Scalars are subtracted from each component.
    """

    @overload(float)
    @overload(int)
    def __rsub__(self, other: Any) -> Self:
      if isinstance(other, (int, float)):
        cls_ = type(self)
        dims = cls_.getDimensions()
        return cls_(*(other for _ in dims), ) - self
      return NotImplemented

    return __rsub__

  @classmethod
  def _subScalarLoad(cls, ) -> overload:
    """
    This method generates the overload for subtraction with scalar values.
    Scalars are subtracted from each component.
    """

    @overload(float)
    @overload(int)
    def __sub__(self, other: Any) -> Self:
      if isinstance(other, (int, float)):
        cls_ = type(self)
        dims = cls_.getDimensions()
        return self - cls_(*(other for _ in dims), )
      return NotImplemented

    return __sub__

  _isubScalarLoad = _subScalarLoad

  @classmethod
  def _addScalarLoad(cls, ) -> overload:
    """
    This method generates the overload for addition with scalar values.
    Scalars are added to each component.
    """

    @overload(float)
    @overload(int)
    def __add__(self, other: Any) -> Self:
      if isinstance(other, (int, float)):
        cls_ = type(self)
        dims = cls_.getDimensions()
        return self + cls_(*(other for _ in dims), )
      return NotImplemented

    return __add__

  _iaddScalarLoad = _addScalarLoad
  _raddScalarLoad = _addScalarLoad

  @classmethod
  def _mulScalarLoad(cls, ) -> overload:
    """
    This method generates scaling multiplication overload. Other
    implementations of multiplication is left to the subclass.
    """

    @overload(float)
    @overload(int)
    def __mul__(self, other: Any) -> Self:
      if isinstance(other, (int, float)):
        cls_ = type(self)
        dimObjects = self.getDimensions()
        args = (dim.__get__(self, cls_) * other for dim in dimObjects)
        return cls_(*args)
      return NotImplemented

    return __mul__

  _imulScalarLoad = _mulScalarLoad
  _rmulScalarLoad = _mulScalarLoad
  _matmulScalarLoad = _mulScalarLoad
  _imatmulScalarLoad = _matmulScalarLoad
  _rmatmulScalarLoad = _matmulScalarLoad

  @classmethod
  def _negFactory(cls, ) -> Callable[[Self], Self]:
    """
    This method generates the '__neg__' method for the class, providing a
    mechanism to negate the object by negating each of its 'Dimension'
    values.
    """

    def __neg__(self, ) -> Self:
      cls_ = type(self)
      dimObjects = self.getDimensions()
      negatedValues = (-(dim.__get__(self, cls_)) for dim in dimObjects)
      return cls_(*negatedValues)

    return __neg__

  @classmethod
  def _resolveOtherFactory(cls, ) -> Callable[[Self, Any], Self]:
    """
    This method generates the '_resolveOther' method for the class, providing
    a mechanism to resolve another object to an instance of the class.
    """

    def _resolveOther(self, other: Any) -> Self:
      cls_ = type(self)
      if isinstance(other, cls_):
        return other
      try:
        casted = typeCast(cls_, other)
      except TypeCastException as typeCastException:
        if typeCastException.type_ is cls_:
          if typeCastException.arg is other:
            return NotImplemented
        raise TypeException('other', other, cls_) from typeCastException
      else:
        return casted

    return _resolveOther

  @classmethod
  def _getAttrFactory(cls, ) -> Callable[[Any, str], Any]:
    """
    This factory creates the '__getattr__' method such that it tries
    '__getitem__' before falling back to raising an 'AttributeError' with
    the original key. """

    def __getattr__(self, key: str) -> Any:
      try:
        value = self[key]
      except (KeyError, IndexError, TypeError) as exception:
        raise AttributeError(key) from exception
      else:
        return value

    return __getattr__

  @classmethod
  def _getItemLoads(cls, ) -> Iterator[overload]:
    """
    This method generates the overloads of the '__getitem__' method for
    the class, providing support for integer, string, and slice based
    indexing.
    """
    yield cls._getItemIndexLoad()
    yield cls._getItemKeyLoad()
    yield cls._getItemSliceLoad()

  @classmethod
  def _getItemSliceLoad(cls) -> overload:
    """
    This factory creates the '__getitem__' overload for slice based
    indexing.
    """

    @overload(slice)
    def __getitem__(self, s: slice) -> tuple[int, ...]:
      return tuple((*self,)[s])

    return __getitem__

  @classmethod
  def _getItemKeyLoad(cls) -> overload:
    """
    This factory creates the '__getitem__' overload for string based
    indexing.
    """

    @overload(str)
    def __getitem__(self, key: str) -> int:
      for dim in self.getDimensions():
        if key in dim.keyGroup:
          return dim.__get__(self, cls)
      raise KeyError(key)

    return __getitem__

  @classmethod
  def _getItemIndexLoad(cls) -> overload:
    """
    This factory creates the '__getitem__' overload for integer based
    indexing.
    """

    @overload(int)
    def __getitem__(self, index: int) -> int:
      if index < 0:
        return self.__getitem__(len(self) + index)
      if index < len(self):
        return (*self,)[index]
      infoSpec = """%s index out of range. Received index %d, expected 
      less than %d (exclusive)."""
      clsName = type(self).__name__
      info = infoSpec % (clsName, index, len(self))
      raise IndexError(textFmt(info))

    return __getitem__

  @classmethod
  def _boolFactory(cls, ) -> Callable[[Any], bool]:
    """
    This method generates the '__bool__' method for the class, providing a
    boolean representation of the object based on the presence of 'Dimension'
    objects registered in the namespace.
    """

    def __bool__(self, ) -> bool:
      return True if any((*self,)) else False

    return __bool__

  @classmethod
  def _iterFactory(cls) -> Callable[[Any], Iterator[Dimension]]:
    """
    This method generates the '__iter__' method for the class, providing an
    iterator over the 'Dimension' objects registered in the namespace.
    """

    def __iter__(self, ) -> Iterator[Dimension]:
      dimObjects = self.getDimensions()
      for dim in dimObjects:
        yield dim.__get__(self, cls)

    return __iter__

  @classmethod
  def _lenFactory(cls, ) -> Callable[[Any], int]:
    """
    This method generates the '__len__' method for the class, providing a
    length representation of the object based on the number of 'Dimension'
    objects registered in the namespace.
    """

    def __len__(self, ) -> int:
      i = -1
      for i, _ in enumerate(maybe(self.__dim_registry__, ())):
        pass
      else:
        return i + 1

    return __len__

  @classmethod
  def _dimFactory(cls, space: EuclidianSpace) -> Callable:
    dimObjects = space.getDimensionObjects()

    def __dim_helper__(self) -> dict[str, Dimension]:
      dimNames = (*(dim.fieldName for dim in dimObjects),)
      dimValues = (*(dim.__get__(self, cls, ) for dim in dimObjects),)
      return {n: v for n, v in zip(dimNames, dimValues)}

    return __dim_helper__

  @classmethod
  def _strFactory(cls, ) -> Callable:
    """
    This method generates the '__str__' method for the class, providing a
    string representation of the object based on its 'Dimension' objects.
    """

    def __str__(self, ) -> str:
      dimDict = self.__dim_helper__()
      dimSpec = """%s=%s"""  # name=value
      dimStrs = (dimSpec % (name, val) for name, val in dimDict.items())
      dimStr = ', '.join(dimStrs)
      clsName = type(self).__name__
      return """<%s: %s>""" % (clsName, dimStr)

    return __str__

  @classmethod
  def _reprFactory(cls, ) -> Callable:
    """
    This method generates the '__repr__' method for the class, providing a
    string representation of the object based on its 'Dimension' objects.
    """

    def __repr__(self, ) -> str:
      dimDict = self.__dim_helper__()
      dimSpec = """%s=%s"""  # name=value
      dimStrs = (dimSpec % (name, val) for name, val in dimDict.items())
      dimStr = ', '.join(dimStrs)
      clsName = type(self).__name__
      infoSpec = """%s(%s)"""  # ClassName(name=value, ...)
      return infoSpec % (clsName, dimStr)

    return __repr__

  @classmethod
  def _initKwargs(cls, ) -> overload:
    """
    This method generates the overload of the '__init__' method for
    keyword arguments.

    Please note, that this factory requires the 'Dimension' objects to
    already be registered on the namespace, ensuring that they have
    awareness of their '__field_name__' that is normally first available
    at the moment of class creation. This note applies to '_initArgs' as
    well.
    """

    @overload()
    def __init__(self, **kwargs) -> None:
      for dim in self.getDimensions():
        for key in dim.keyGroup:
          if key in kwargs:
            value = typeCast(dim.valueType, kwargs[key])
            setattr(self, dim.pvtName, value)
            break

    return __init__

  def _initArgs(self, ) -> overload:
    """
    This method generates the overload of the '__init__' method for
    positional arguments. This method requires awareness of the number of
    dimensions registered on the namespace. Thus, this factory cannot be a
    'classmethod' like other factories.
    """
    dimObjects = self.space.getDimensionObjects()

    @overload(*(dim.valueType for dim in dimObjects))
    def __init__(this, *args, **kwargs) -> None:  # 'this' -> 'self'
      for dim, arg in zip(dimObjects, args):
        value = typeCast(dim.valueType, arg)
        setattr(this, dim.pvtName, value)
      if kwargs:
        this.__init__(**kwargs)

    return __init__

  @classmethod
  def _initTHIS(cls, ) -> overload:
    """
    This method generates the overload of the '__init__' method for
    no arguments, initializing all 'Dimension' objects to their default
    values.
    """

    @overload(THIS)
    def __init__(self, other: Self, ) -> None:
      for dim in self.getDimensions():
        value = dim.__get__(other, cls)
        setattr(self, dim.pvtName, value)

    return __init__

  def _initLoads(self, ) -> Iterator[overload]:
    """
    Iterates through the overloads of the '__init__'.
    """
    yield self._initKwargs()
    yield self._initArgs()
    yield self._initTHIS()

  @staticmethod
  def _getDimsFactory() -> Callable[[Any], Iterator[Dimension]]:
    """
    This method generates the '__getDims__' method for the class, providing
    an iterator over the 'Dimension' objects registered in the namespace.
    """

    @classmethod  # noqa, trust me bro
    def getDimensions(cls) -> Iterator[Dimension]:
      dimDict = maybe(cls.__dim_registry__, dict())
      for key, val in dimDict.items():
        yield val

    return getDimensions
