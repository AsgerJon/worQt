"""
AbstractException provides an abstract baseclass for custom exceptions in
the 'worQt.waitaminute'. This class provides the communication to the
running application which must be a subclass of
'worQt.app.AbstractApplication'. These custom apps are required to
implement the 'panic' method, which subclasses of 'AbstractException'
alerts when raised.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from abc import abstractmethod, ABCMeta


class AbstractException(Exception, metaclass=ABCMeta):
  """
  AbstractException provides an abstract baseclass for custom exceptions in
  the 'worQt.waitaminute'. This class provides the communication to the
  running application which must be a subclass of
  'worQt.app.AbstractApplication'. These custom apps are required to
  implement the 'panic' method, which subclasses of 'AbstractException'
  alerts when raised.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @abstractmethod
  def getExitCode(self, ) -> int:
    """
    Subclasses must implement this method to specify what 'int' in range 0
    to 255 should be passed to the 'sys.exit' function when exiting
    because of this exception. This method is called by the '__int__'
    method on the abstract base class.
    """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __int__(self, ) -> int:
    """
    Defers to the 'getExitCode' implementation. Please note that
    subclasses should not override this method.
    """
    return self.getExitCode()
