"""
Running 'python -m worQt.engineering' opens the disk app.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import DiskApp


def main() -> int:
  """The 'main' function runs the disk app and returns its exit code."""
  with DiskApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
