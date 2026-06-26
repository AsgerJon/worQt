"""
App is the concrete 'worQt' application class. It exposes a context
manager protocol: '__enter__' returns the application document and
'__exit__' runs the Qt event loop. The shared app handles ('returnCode',
'splash', 'window') live on 'AbstractApplication'; 'App' only fixes its
window type.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractApplication
from ..window import MainWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class App(AbstractApplication):
  """
  Concrete 'worQt' application. Supports use as a context manager:

      with App(*sys.argv) as app:
        app.splash.show()
        app.window.show()

  '__exit__' runs the Qt event loop and blocks until the application
  quits. If the with-body raises, the event loop is not started and
  the exception propagates.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = MainWindow  # 'window' builds a MainWindow

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args: str) -> None:
    """
    Construct the application. Positional arguments are forwarded to
    'QApplication' as the argv list. Typical usage is 'App(*sys.argv)'.
    """
    super().__init__([*args, ])

  def __enter__(self) -> App:
    return self

  def __exit__(self, _, exception: Optional[BaseException], __) -> None:
    """
    Run the Qt event loop on normal exit. If the with-body raised,
    skip the event loop and let the exception propagate.
    """
    if exception is None:
      self.__return_code__ = self.exec()
