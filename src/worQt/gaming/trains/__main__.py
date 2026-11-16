"""
Running 'python -m worQt.gaming.trains' opens the sandbox on the loop's
world; 'python -m worQt.gaming.trains steam' on the steam train's oval.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from ._steamapp import SteamApp
from ._trainsapp import TrainsApp

#  The window's size, pixels.
WIDE, HIGH = 1920, 1080


def main() -> int:
  """The 'main' function opens the trains (the steam train's oval when
  the first argument is 'steam') and returns the window's exit code."""
  kind = SteamApp if sys.argv[1:2] == ['steam'] else TrainsApp
  with kind(*sys.argv) as app:
    app.window.resize(WIDE, HIGH)
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
