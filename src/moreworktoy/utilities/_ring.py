"""
Ring provides a performant and thread-safe ring buffer. The buffering is
implemented by using a `collections.deque` object, which is much faster
than appending to a list. The buffer is made thread-safe by using
'threading.Lock'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from collections import deque
from threading import Lock

from worktoy.desc import Field
from worktoy.utilities import maybe

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator


class Ring:
  """
  Ring provides a performant and thread-safe ring buffer. The buffering is
  implemented by using a `collections.deque` object, which is much faster
  than appending to a list. The buffer is made thread-safe by using
  'threading.Lock'.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __snap_limit__: int = 255

  #  Fallback Variables
  __fallback_size__: int = 64

  #  Private Variables
  __inner_buffer__: deque = None
  __thread_lock__: Lock = None
  __max_size__: int = None

  _threadLock = Field()
  _buffer = Field()
  _maxSize = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @_buffer.GET
  def _getInnerBuffer(self, **kwargs) -> deque:
    if self.__inner_buffer__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__inner_buffer__ = deque(maxlen=abs(self))
      return self._getInnerBuffer(_recursion=True)
    return self.__inner_buffer__

  @_threadLock.GET
  def _getLock(self, **kwargs) -> Lock:
    if self.__thread_lock__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__thread_lock__ = Lock()
      return self._getLock(_recursion=True)
    return self.__thread_lock__

  @_maxSize.GET
  def _getMaxSize(self, ) -> int:
    return maybe(self.__max_size__, self.__fallback_size__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __len__(self, ) -> int:
    buf = self._getInnerBuffer()
    return len(buf)

  def __abs__(self, ) -> int:
    return self._maxSize

  def __iter__(self, ) -> Iterator[Any]:
    snap = None
    with self._threadLock:
      if len(self) > self.__snap_limit__:
        snap = self.snapShot()
    if snap is None:
      yield from self._buffer
    else:
      yield from snap

  def __contains__(self, item: Any) -> bool:
    with self._threadLock:
      for element in self._buffer:
        if element == item:
          return True
    return False

  def __bool__(self, ) -> bool:
    with self._threadLock:
      return True if self.__inner_buffer__ else False

  def __getitem__(self, index: int) -> Any:
    with self._threadLock:
      while index < 0:
        index += len(self)
      if index > len(self) - 1:
        raise IndexError
      return self.__inner_buffer__[index]

  def snapShot(self, ) -> list[Any]:
    with self._threadLock:
      return [*self._buffer, ]

  def append(self, element: Any) -> None:
    with self._threadLock:
      self._buffer.append(element)

  def clear(self, ) -> None:
    with self._threadLock:
      self._buffer.clear()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args) -> None:
    if len(args) == 1:
      arg = args[0]
      if isinstance(arg, int):
        self.__max_size__ = abs(arg)
      else:
        elements = [*arg, ]
        self.__max_size__ = len(elements)
        for element in elements:
          self.append(element)
    elif args:
      self.__init__((*args,))
