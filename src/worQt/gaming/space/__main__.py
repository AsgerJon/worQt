"""
Running 'python -m worQt.gaming.space' opens the space window: the
creative rocket on Terra's pad.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from ._spaceapp import SpaceApp

#  The window's size, pixels.
WIDE, HIGH = 1920, 1080


def main() -> int:
  """The 'main' function opens the space window and returns its exit
  code once it closes."""
  with SpaceApp(*sys.argv) as app:
    app.window.resize(WIDE, HIGH)
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
