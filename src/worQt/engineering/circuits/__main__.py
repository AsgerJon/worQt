"""
Running 'python -m worQt.engineering.circuits' opens the circuits.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import CircuitsApp


def main() -> int:
  """The 'main' function runs the circuits and returns its exit code."""
  with CircuitsApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
