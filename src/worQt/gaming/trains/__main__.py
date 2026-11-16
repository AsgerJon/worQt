"""
Running 'python -m worQt.gaming.trains' opens the sandbox on the loop's
world.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from ._trainsapp import TrainsApp


def main() -> int:
  """The 'main' function opens the trains and returns its exit code."""
  with TrainsApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
