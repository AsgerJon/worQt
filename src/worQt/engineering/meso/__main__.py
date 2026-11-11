"""
Running 'python -m worQt.engineering.meso' opens the concrete testing
app.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import MesoApp


def main() -> int:
  """The 'main' function runs the concrete testing app and returns its
  exit code."""
  with MesoApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
