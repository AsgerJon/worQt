"""
SignalWaiter blocks the running event loop until a Qt signal fires or a
timeout elapses. It is used as a context manager wrapping the acting code,
so a test can act and then block until the reaction lands or the deadline
trips, at which point 'timedOut' reports the miss.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEventLoop, QTimer
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Self, TypeAlias, Union

  from PySide6.QtCore import SignalInstance

  Args: TypeAlias = tuple[Any, ...]
  MaybeArgs: TypeAlias = Optional[Args]
  MaybeBool: TypeAlias = Optional[bool]
  MaybeLoop: TypeAlias = Optional[QEventLoop]
  BoolField: TypeAlias = Union[bool, Field]
  ArgsField: TypeAlias = Union[Args, Field]


class SignalWaiter(BaseObject):
  """
  SignalWaiter blocks the running event loop until a Qt signal fires or a
  timeout elapses. Use it as a context manager around the acting code:

      with SignalWaiter(button.leftClick, 500) as waiter:
        self.click(button)
      self.assertTrue(waiter.caught)

  On '__enter__' it connects to the signal; the emission may arrive while
  the body runs (a synchronous reaction) or later (a timer-driven one). On
  '__exit__' it returns at once when the signal has already fired,
  otherwise it spins a nested 'QEventLoop' until the signal fires or the
  timeout 'QTimer' quits the loop. 'caught' and 'timedOut' report the
  outcome and 'args' carries the emitted arguments. A raising body skips
  the wait and propagates.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __the_signal__ = None
  __timeout_ms__ = None
  __caught_flag__: MaybeBool = None
  __caught_args__: MaybeArgs = None
  __wait_loop__: MaybeLoop = None

  #  Public Variables
  caught: BoolField = Field()
  timedOut: BoolField = Field()
  args: ArgsField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @caught.GET
  def _getCaught(self, ) -> bool:
    """The 'caught' getter reports whether the signal has fired."""
    return True if self.__caught_flag__ else False

  @timedOut.GET
  def _getTimedOut(self, ) -> bool:
    """The 'timedOut' getter reports whether the wait ended on the
    deadline rather than on the signal."""
    return False if self.__caught_flag__ else True

  @args.GET
  def _getArgs(self, ) -> Args:
    """The 'args' getter returns the arguments the signal carried, an
    empty tuple when it has not fired."""
    return maybe(self.__caught_args__, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _onSignal(self, *args) -> None:
    """The '_onSignal' slot records the emission and, when a nested loop
    is spinning, quits it so '__exit__' returns."""
    if self.__caught_flag__:
      return
    self.__caught_flag__ = True
    self.__caught_args__ = (*args,)
    loop = self.__wait_loop__
    if loop is not None:
      if loop.isRunning():
        loop.quit()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, signal: SignalInstance, timeout: int = 1000) -> None:
    self.__the_signal__ = signal
    self.__timeout_ms__ = timeout

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __enter__(self, ) -> Self:
    self.__caught_flag__ = False
    self.__caught_args__ = None
    self.__the_signal__.connect(self._onSignal)
    return self

  def __exit__(self, _, exception: BaseException, __) -> bool:
    signal = self.__the_signal__
    if exception is not None:
      signal.disconnect(self._onSignal)
      return False
    if not self.__caught_flag__:
      loop = QEventLoop()
      self.__wait_loop__ = loop
      timer = QTimer()
      timer.setSingleShot(True)
      timer.timeout.connect(loop.quit)
      timer.start(self.__timeout_ms__)
      loop.exec()
      timer.stop()
      self.__wait_loop__ = None
    signal.disconnect(self._onSignal)
    return False
