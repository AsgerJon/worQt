"""
Entry point for the worQt demo: 'python -m worQt' opens the generic main
window on a running event loop until the window is closed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from worQt.app import App


def main(*args: str) -> int:
  """Open the demo window and run the event loop until it closes."""
  with App(*args) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main(*sys.argv))
