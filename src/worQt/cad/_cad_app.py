"""
CADApp is the concrete 'worQt' application for the structural-drawing / FEA
modeller (the CAD tool). It builds a 'CADWindow' and carries 'CADSettings'
(the colour palette and view defaults), loaded from disk on entry. A context
manager whose '__exit__' runs the Qt event loop on a clean exit; the shared
app machinery lives on 'AbstractApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ..app import AbstractApplication
from ._cad_settings import CADSettings
from ._cad_window import CADWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class CADApp(AbstractApplication):
  """
  The structural-drawing / FEA-modeller application. Use as a context
  manager:

      with CADApp(*sys.argv) as app:
        app.window.show()

  On entry the saved settings are loaded over the defaults. '__exit__' runs
  the Qt event loop and blocks until the application quits; if the with-body
  raised, the event loop is not started and the exception propagates.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = CADWindow  # 'window' builds a CADWindow
  __settings_class__ = CADSettings  # 'settings' builds a CADSettings

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args: str) -> None:
    """
    Construct the application. Positional arguments are forwarded to
    'QApplication' as the argv list. Typical usage is 'CADApp(*sys.argv)'.
    """
    super().__init__([*args, ])

  def __enter__(self) -> CADApp:
    """Load the saved settings over the defaults, then enter."""
    self.settings.load()
    return self

  def __exit__(self, _, exception: Optional[BaseException], __) -> None:
    """
    Run the Qt event loop on normal exit. If the with-body raised,
    skip the event loop and let the exception propagate.
    """
    if exception is None:
      self.__return_code__ = self.exec()
