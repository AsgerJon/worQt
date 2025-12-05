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

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Signal, QMetaObject
from PySide6.QtCore import SignalInstance as Sig
from PySide6.QtWidgets import QApplication, QMainWindow
from worktoy.desc import Field
from worktoy.utilities import maybe

from ..desQt import Etc

if TYPE_CHECKING:
  from typing import Self, Any, Type, TypeAlias, Union
  from PySide6.QtCore import Slot

  Window = Type[QMainWindow]  # type: TypeAlias
  Connection: TypeAlias = QMetaObject.Connection
  RegCon: TypeAlias = tuple[Connection, object, object]
  SigSlot: TypeAlias = frozenset[Union[Sig, Slot]]
  ConKey: TypeAlias = frozenset[int]
  Register: TypeAlias = dict[ConKey, Connection]


class AbstractApplication(QApplication):
  """AbstractApplication provides an abstract baseclass for subclasses of
  QApplication used across the worQt library. """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __startup_keys__ = ['_replaceConnect', '_replaceDisconnect', ]
  __shutdown_keys__ = ['_restoreConnect', '_restoreDisconnect', ]
  __startup_hooks__ = None
  __shutdown_hooks__ = None

  #  Fallback Variables
  __fallback_window__ = QMainWindow
  __fallback_return_code__ = 1

  #  Private Variables
  __window_class__ = None
  __window_instance__ = None
  __return_code__ = None
  __original_connect__ = None
  __original_disconnect__ = None
  __connection_register__ = None

  #  Public Variables
  etc = Etc()
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

  def _getRegister(self, ) -> Register:
    """
    Returns the register of connections established in the application.
    The keys are 'frozenset' objects containing the signal and slot objects
    used to create the connection which is the value.
    """
    return maybe(self.__connection_register__, dict())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _isRegistered(self, sig: Sig, slt: Slot) -> bool:
    """
    Checks if a connection between the given signal and slot is already
    registered in the application.
    """
    return False if self._getCon(sig, slt) is None else True

  def _getCon(self, sig: Sig, slt: Slot) -> Union[Connection, None]:
    """
    Returns the connection object corresponding to the given signal and
    slot if it exists in the register. Otherwise, returns None.
    """
    sigStr, sltStr = hash(str(sig)), hash(str(slt))
    sigSlot = frozenset((sigStr, sltStr,))
    existing = self._getRegister()
    try:
      con = existing[sigSlot]
    except KeyError:
      return None
    else:
      return con

  def _register(self, sig: Sig, slt: Slot, con: Connection) -> bool:
    """
    Adds an entry to the connection register add the key formed by the
    frozenset of the signal and slot used to create the connection.
    """
    sigStr, sltStr = hash(str(sig)), hash(str(slt))
    sigSlot = frozenset((sigStr, sltStr,))
    existing = self._getRegister()
    if sigSlot not in existing:
      existing[sigSlot] = con
      self.__connection_register__ = existing
      return True
    return False

  def _unregister(self, sig: Sig, slt: Slot) -> bool:
    """
    Removes an entry from the connection register corresponding to the
    frozenset of the signal and slot used to create the connection.
    """
    sigStr, sltStr = hash(str(sig)), hash(str(slt))
    sigSlot = frozenset((sigStr, sltStr,))
    existing = self._getRegister()
    try:
      con = existing[sigSlot]
    except KeyError:
      return False
    else:
      newReg = dict()
      for key, val in existing.items():
        if key == sigSlot:
          continue
        newReg[key] = val
      self.__connection_register__ = newReg
      return True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def pleaseExit(self, ) -> None:
    """
    Subclasses may implement this method to implement how the application
    respond to an exit request. This method is permissive and the
    application is free to not exit.
    """
    self.quit()

  def exitNow(self, ) -> None:
    """
    Subclasses may implement this method to implement how the application
    respond to an exit order. This method requires the application to exit
    even if the application is not ready to exit. The application should
    exit even if it has unsaved data or other issues that would normally
    prevent the application from exiting.
    """
    self.quit()

  def onStartUp(self, ) -> None:
    """
    Runs immediately after the 'QCoreApplication' starts. Please note that
    subclasses must implement this method to specify the opening sequence.
    Traditionally, this method opens the main window, but subclasses can
    implement any sequence of operations, for example a splash screen that
    opens the main window when closed.
    """
    self._replaceConnect()
    self._replaceDisconnect()

  def onShutdown(self, ) -> None:
    """
    Runs immediately after the 'QCoreApplication' exits. Please note that
    this method runs with the QCoreApplication instance no longer running.
    Slots and signals cannot run at this point.

    This method is not generally required.
    """
    self._restoreConnect()
    self._restoreDisconnect()

  def _replaceConnect(self, ) -> None:
    """
    Patches the 'SignalInstance.connect' method to register connections in
    a variable on the application instance.
    """

    if self.__original_connect__ is not None:
      info = """SignalInstance.connect has already been patched!"""
      raise RuntimeError(info)

    __old_connect__ = getattr(Sig, 'connect')

    def newConnect(sig: Sig, slt: Slot, *args, **kwargs) -> Connection:
      if self._isRegistered(sig, slt):
        return self._getCon(sig, slt)
      con = __old_connect__(sig, slt, *args, **kwargs)
      self._register(sig, slt, con)
      return con

    setattr(Sig, 'connect', newConnect)
    self.__original_connect__ = __old_connect__

  def _replaceDisconnect(self, ) -> None:
    """
    Patches the 'SignalInstance.disconnect' method to unregister connections
    from the variable on the application instance.
    """
    if self.__original_disconnect__ is not None:
      info = """SignalInstance.disconnect has already been patched!"""
      raise RuntimeError(info)

    __old_disconnect__ = getattr(Sig, 'disconnect')

    def newDisconnect(sig: Sig, slt: Slot, *args, **kwargs) -> None:
      if self._isRegistered(sig, slt):
        self._unregister(sig, slt)

    setattr(Sig, 'disconnect', newDisconnect)
    self.__original_disconnect__ = __old_disconnect__

  def _restoreConnect(self, ) -> None:
    """
    Restores the original 'SignalInstance.connect' method.
    """
    if self.__original_connect__ is None:
      info = """SignalInstance.connect has not been patched!"""
      raise RuntimeError(info)

    setattr(Sig, 'connect', self.__original_connect__)
    self.__original_connect__ = None

  def _restoreDisconnect(self, ) -> None:
    """
    Restores the original 'SignalInstance.disconnect' method.
    """
    if self.__original_disconnect__ is None:
      info = """SignalInstance.disconnect has not been patched!"""
      raise RuntimeError(info)

    setattr(Sig, 'disconnect', self.__original_disconnect__)
    self.__original_disconnect__ = None

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def exec(self) -> Any:  # int, but 'finally' confuses pycharm lmao
    """Executes the application. """
    try:
      QTimer.singleShot(0, self.onStartUp, )
      return super().exec()
    finally:
      self.onShutdown()
