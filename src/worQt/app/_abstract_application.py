"""
AbstractApplication provides an abstract base for applications in the worQt
framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025-2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QApplication
from worktoy.desc import Field
from worktoy.waitaminute import TypeException

from ..mixin import MixinBase
from ..waitaminute.events import EventException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, TypeAlias, Optional

  EXIT: TypeAlias = Optional[bool]


class AbstractApplication(QApplication, MixinBase):
  """
  An abstract base class for worQt applications.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __fallback_result__ = True

  #  Fallback Variables
  __fallback_context__ = False

  #  Private Variables
  __context_flag__ = None
  __exit_code__ = None

  #  Public Variables
  context = Field()
  exitCode = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @context.GET
  def _getContext(self, **kwargs) -> bool:
    if self.__context_flag__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__context_flag__ = self.__fallback_context__
      return self._getContext(_recursion=True)
    return True if self.__context_flag__ else False

  @exitCode.GET
  def _getExitCode(self, ) -> int:
    if self.__exit_code__ is None:
      raise RuntimeError("The application has not exited yet!")
    return self.__exit_code__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __enter__(self, *args, **kwargs) -> Self:
    """
    Subclasses should implement the 'enterHook' method rather than this if
    possible. That method is called before the context flag is updated.
    """
    self.enterHook(*args, **kwargs)
    self.__context_flag__ = True
    return self

  def __exit__(self, _, exception: Exception, __) -> None:
    """
    Exiting the application context manager updates the context flag.
    Please note the unusual signature that ignores the type and traceback
    since these are available from the exception instance. This is more in
    line with modern Python practices.

    Please note the seemingly redundant inclusion of the 'except' block.
    While adding nothing, 'Python' requires the presence of an 'except'
    block before an 'else' block in a 'try' statement. The standard 'try'
    statement consists of the blocks shown in the example below:

    def evenTest(n: int) -> None:
      if n % 2:
        raise ValueError('n is not even!')

    def handler(exception: Exception) -> bool:
      if isinstance(exception, ValueError):
        if 'n is not even!' in str(exception):
          return True
      return False


    N = 69 if random() * 2 > 1 else 420  # odd or even chosen randomly

    try:
      evenTest(N)
    except Exception as exception:
      #  This block runs only when an exception is raised during the 'try'
      #  block.
      if not handler(exception):
        raise exception
    else:
      #  This block runs only when no exception is raised during the 'try'
      print('%d is even!' % N)
    finally:
      #  Come hell or high water, this block always runs. The interpreter
      #  always runs this block last, even in the presence of a 'return'
      #  statement in any of other blocks. Unless 'os._exit' is called,
      #  the interpreter will always run this block, even if new unhandled
      #  exceptions were raised in other blocks.
      #
      #  This block is used to run important cleanup code such as closing
      #  files, network connections, database transactions, etc.
      #
      #  While syntactically implemented, it is very poor practice to
      #  issue 'return', 'continue' or 'break' statements in this block as
      #  it overrides prior control flow in unpredictable and unexpected
      #  ways making debugging begin with removing such statements. As of
      #  Python 3.14 any such statement in a 'finally'
      #  block will cause a 'SyntaxWarning'.
      print('Example complete!')

    The above example shows the full structure, but not all blocks are
    strictly required and the allowable combinations not particularly
    intuitive. Please note that the 'cpython' implementation of 'Python'
    implements the 'else' block such that updates to the syntax here will
    require disproportionate changes to the implementation. Therefore,
    the implementation of more intuitive flexibility is left as an
    exercise to the try-hard readers.

    The most common combination is the 'try-except':
    try:
      evenTest(N)
    except Exception as exception:
      if not handler(exception):
        raise exception

    The full 'try-except-else-finally' combination will not be repeated
    here. It is an underestimated feature of the language that deserves
    more use in the wild.

    The final combination is the cheeky 'try-finally':

    try:
      #  This simple two block structure provides for the case where
      #  cleanup code must run, but no exception handling is required.
      evenTest(N)
    finally:
      #  Any exception raised in the 'try' block will wait patiently
      #  until the finally block has completed before being propagated
      print('Example complete!')

    Now for the structure one would think is implemented, but which will
    raise 'SyntaxError':

    try:  # Bad, will raise SyntaxError!
      evenTest(N)
    else:
      #  Code here will not run if the code in the 'try' block raises any
      #  exception. But requires an 'except' block be present, even if it
      #  just re-raises.
    finally:
      #  The 'else' requirement applied both with and without the
      #  'finally' block
      print('Example complete!')
    """
    try:
      if exception is None:
        self.exitHook(None)
      elif isinstance(exception, Exception):
        if not self.exitHook(exception):
          raise exception
      elif isinstance(exception, BaseException):
        raise exception
      else:
        raise TypeException('exception', exception, BaseException)
    except Exception as exception:  # Redundant, but required syntactically
      raise exception
    else:
      self.__exit_code__ = QApplication.exec_(self, )
    finally:
      self.__context_flag__ = False

  def __int__(self, ) -> int:
    """
    Get the exit code of the application as an integer.
    """
    return self.exitCode

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def enterHook(self, *args, **kwargs) -> None:
    """
    Subclasses may implement this method to perform actions when entering
    the context manager. By default, it does nothing. It runs *before* the
    context flag is updated. It should return 'None'. This method *can*
    raise exceptions, in which case the context manager will not be
    entered. Such exceptions will *not* be passed to the 'exitHook' method.
    """
    pass

  def exitHook(self, exception: Exception = None) -> EXIT:
    """
    This method decides how to handle exceptions raised during the
    application. Subclasses may implement it to provide custom handling of
    exceptions or to perform cleanup actions.

    'exception: Optional[BaseException]'
    - None: No exception occurred during the application.
    - Exception: An exception instance that was raised during the
      application. Subclasses can return True in this case to indicate
      having handled the exception, preventing it from being propagated.

    Please note that if the context manager exits with a BaseException
    that is not also an Exception (e.g., KeyboardInterrupt, SystemExit),
    this method does not run. Such exceptions should generally be allowed
    to propagate.
    """
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def panic(self, exception: Exception) -> None:
    """
    Subclasses may implement this method to provide custom exception. By
    default, all exceptions propagate.
    """
    try:
      raise exception
    finally:
      self.exit(1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def notify(self, receiver: QObject, event: QEvent) -> bool:
    """
    notify is overridden to catch unhandled exceptions during event
    processing. Such exceptions are emitted via the 'handleException'
    method.

    :param receiver: The QObject receiving the event.
    :param event: The QEvent being processed.
    :return: True if the event was processed successfully, False otherwise.
    """

    res = self.__fallback_result__
    try:
      res = QApplication.notify(self, receiver, event)
    except EventException as eventException:
      self.panic(eventException)
    return True if res else False
