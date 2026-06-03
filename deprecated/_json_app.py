"""
JsonApp is the concrete 'worQt' application for editing JSON documents. A
context manager whose '__exit__' runs the Qt event loop on a clean exit.
Its 'window' is a 'JsonWindow'; the shared app machinery lives on
'AbstractApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractApplication
from ..window import JsonWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class JsonApp(AbstractApplication):
  """
  Concrete JSON document application. Supports use as a context manager:

      with JsonApp(*sys.argv) as app:
        app.window.show()

  '__exit__' runs the Qt event loop and blocks until the application
  quits. If the with-body raises, the event loop is not started and the
  exception propagates.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = JsonWindow  # 'window' builds a JsonWindow

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args: str) -> None:
    """
    Construct the application. Positional arguments are forwarded to
    'QApplication' as the argv list. Typical usage is 'JsonApp(*sys.argv)'.
    """
    super().__init__([*args, ])

  def __enter__(self) -> JsonApp:
    return self

  def __exit__(self, _, exception: Optional[BaseException], __) -> None:
    """
    Run the Qt event loop on normal exit. If the with-body raised,
    skip the event loop and let the exception propagate.
    """
    if exception is None:
      self.__return_code__ = self.exec()
