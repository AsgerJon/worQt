"""
DrawApp is the concrete 'worQt' application for the drawing app. A context
manager whose '__exit__' runs the Qt event loop on a clean exit. Its
'window' is a 'DrawWindow' and its 'settings' a 'DrawSettings'; the shared
app machinery lives on 'AbstractApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractApplication
from ..draw import DrawSettings
from ..window import DrawWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class DrawApp(AbstractApplication):
  """
  Concrete drawing application. Supports use as a context manager:

      with DrawApp(*sys.argv) as app:
        app.window.show()

  '__exit__' runs the Qt event loop and blocks until the application
  quits. If the with-body raises, the event loop is not started and the
  exception propagates.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = DrawWindow  # 'window' builds a DrawWindow
  __settings_class__ = DrawSettings  # 'settings' builds a DrawSettings

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args: str) -> None:
    """
    Construct the application. Positional arguments are forwarded to
    'QApplication' as the argv list. Typical usage is 'DrawApp(*sys.argv)'.
    """
    super().__init__([*args, ])

  def __enter__(self) -> DrawApp:
    return self

  def __exit__(self, _, exception: Optional[BaseException], __) -> None:
    """
    Run the Qt event loop on normal exit. If the with-body raised,
    skip the event loop and let the exception propagate.
    """
    if exception is None:
      self.__return_code__ = self.exec()
