"""
Running 'python -m worQt.ezword' starts EZWord.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import EZWordApp


def main() -> int:
  """The 'main' function runs EZWord and returns its exit code."""
  with EZWordApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
