"""
Running 'python -m worQt.engineering.diagrams' opens the section force
diagrams.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import DiagramsApp


def main() -> int:
  """The 'main' function runs the diagrams and returns its exit code."""
  with DiagramsApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
