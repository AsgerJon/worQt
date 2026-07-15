"""
ConditionWaiter blocks the running event loop until a predicate holds or a
timeout elapses. It suits state that settles asynchronously - a hover flag,
a dirty marker - where no single signal marks the change.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QEventLoop, QTimer
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable, Optional, TypeAlias

  Predicate: TypeAlias = Callable[[], bool]
  MaybeLoop: TypeAlias = Optional[QEventLoop]


class ConditionWaiter(BaseObject):
  """
  ConditionWaiter blocks the running event loop until 'predicate' returns
  True or 'timeout' milliseconds elapse, then reports whether the predicate
  held. It polls the predicate on a short interval while the loop spins, so
  reactions delivered by other events or timers are observed. 'wait'
  returns immediately when the predicate already holds.

      waiter = ConditionWaiter(lambda: button.hovered, 500)
      self.move(button)
      self.assertTrue(waiter.wait())
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __poll_interval__: int = 10  # milliseconds between predicate checks

  #  Private Variables
  __the_predicate__ = None
  __timeout_ms__ = None
  __wait_loop__: MaybeLoop = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _check(self, ) -> None:
    """The '_check' slot quits the nested loop once the predicate holds."""
    if self.__the_predicate__():
      loop = self.__wait_loop__
      if loop is not None:
        if loop.isRunning():
          loop.quit()

  def wait(self, ) -> bool:
    """The 'wait' method blocks until the predicate holds or the timeout
    elapses, returning whether the predicate held on exit."""
    if self.__the_predicate__():
      return True
    loop = QEventLoop()
    self.__wait_loop__ = loop
    poll = QTimer()
    poll.setInterval(self.__poll_interval__)
    poll.timeout.connect(self._check)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poll.start()
    deadline.start(self.__timeout_ms__)
    loop.exec()
    poll.stop()
    deadline.stop()
    self.__wait_loop__ = None
    return True if self.__the_predicate__() else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, predicate: Predicate, timeout: int = 1000) -> None:
    self.__the_predicate__ = predicate
    self.__timeout_ms__ = timeout
