"""
Trying to actually type hint makes the 'typing' module completely shit
itself.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Tuple, TypeAlias, Iterator, Self, Type, Union, Any
  from typing import Protocol, TypeVar
  from .. import Dimension

  Bases: TypeAlias = tuple[type, ...]
  DimDict: TypeAlias = dict[str, Dimension]
  DimTuple: TypeAlias = Tuple[Dimension, ...]
  Dims: TypeAlias = Iterator[Dimension]
  Scalar: TypeAlias = Union[int, float]
  Cls = TypeVar("Cls")
  CLS: TypeAlias = Type[Cls]


  class INIT(Protocol):
    def __call__(self: Any, *args: Scalar, **kwargs: Scalar) -> None: ...


  class ITER(Protocol):
    def __call__(self: Cls) -> Dims: ...


  class GETITEM(Protocol):
    def __call__(self: Cls, key: str) -> Scalar: ...

__all__ = [
  'Bases',
  'DimDict',
  'DimTuple',
  'Dims',
  'Scalar',
  'CLS',
  'INIT',
  'ITER',
]
