"""
Running 'python -m worQt.engineering.springs' opens the springs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import SpringsApp


def main() -> int:
  """The 'main' function runs the springs and returns its exit code."""
  with SpringsApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
