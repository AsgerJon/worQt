"""
AbstractApplication provides an abstract baseclass for subclasses of
QApplication used across the worQt library. The baseclass provides the
following pattern:
1:  The class constructor receives a main window class as an argument.
2:  The .exec() method instantiates the main window class and shows it.
3:  When the application instance is first running, it emits the startUp
signal. This triggers the 'onStartUp' method which subclasses may
reimplement to perform tasks requiring the application to be running.
4:  When the QApplication instance is shutting down, the 'shuttingDown'
method runs. This method runs whilst the application is still running. It
is achieved by connecting the 'lastWindowClosed' to the 'shuttingDown'
method. As such, it is possible to ask for user input during this method
and even to cancel the shutdown.
5:  Immediately prior to the application instance shutting down,
the 'lastChance' method runs. It is not possible to ask for user input.
This method should be used to perform tasks that protect data integrity.
6:  When the application instance is closed, the 'closed' method runs.
Please note that this method runs after the QApplication instance has
been closed. Data required by this method should be saved by the prior
steps listed above.

"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QApplication, QMainWindow
from worktoy.desc import Field
from worktoy.utilities import maybe

from worQt.app.desQt import Etc, Resources, Sounds

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Self, Any, Type, TypeAlias

  Window = Type[QMainWindow]  # type: TypeAlias


class AbstractApplication(QApplication):
  """AbstractApplication provides an abstract baseclass for subclasses of
  QApplication used across the worQt library. """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_window__ = QMainWindow
  __fallback_return_code__ = 1

  #  Private Variables
  __window_class__ = None
  __window_instance__ = None
  __return_code__ = None

  #  Public Variables
  etc = Etc()
  resources = Resources()
  sounds = Sounds()
  returnCode = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Signals
  startUp = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @returnCode.GET
  def _getReturnCode(self) -> int:
    """Returns the return code of the application."""
    return maybe(self.__return_code__, self.__fallback_return_code__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def onStartUp(self, ) -> None:
    """
    Runs immediately after the 'QCoreApplication' starts. Please note that
    subclasses must implement this method to specify the opening sequence.
    Traditionally, this method opens the main window, but subclasses can
    implement any sequence of operations, for example a splash screen that
    opens the main window when closed.
    """

  def onExit(self, ) -> None:
    """
    Runs immediately after the 'QCoreApplication' exits. Please note that
    this method runs with the QCoreApplication instance no longer running.
    Slots and signals cannot run at this point.

    This method is not generally required.
    """

  def exec(self) -> Any:  # int, but 'finally' confuses pycharm lmao
    """Executes the application. """
    try:
      QTimer.singleShot(0, self.onStartUp, )
      return super().exec()
    finally:
      pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __enter__(self, ) -> Self:
    """Enter the application context. In the context manager, the main
    entry point can open relevant windows. For example a slash screen
    followed by the main window. """
    return self

  def __exit__(self, _, exception: BaseException, __) -> None:
    """Exit the application context. """
    try:
      if exception is not None:
        raise exception
    except Exception as exception:
      raise exception
    else:
      self.exec()
    finally:
      pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    super().__init__([*args, ])
