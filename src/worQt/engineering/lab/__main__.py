"""
Running 'python -m worQt.engineering.lab' opens the beam lab.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import LabApp


def main() -> int:
  """The 'main' function runs the beam lab and returns its exit code."""
  with LabApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
