"""
Running 'python -m worQt.gaming.billiards' opens the billiard room,
walked first person to either table (the user), speaking the language
last chosen.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import BilliardsApp, savedLanguage


def main() -> int:
  """The 'main' function opens the billiard room, walking, and returns
  its exit code."""
  with BilliardsApp(*sys.argv) as app:
    app.window.show()
    app.window.setLanguage(savedLanguage())
    app.window.enterRoom()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
