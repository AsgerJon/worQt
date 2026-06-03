"""
Entry point for the worQt CAD tool: 'python -m worQt' opens the
structural-drawing / FEA-modeller window and keeps it open on the running
event loop until the window is closed. The saved settings (colours and view
defaults) are loaded on entry.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from worQt.cad import CADApp


def main(*args: str) -> int:
  """Open the CAD window and run the event loop until it closes."""
  with CADApp(*args) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main(*sys.argv))
