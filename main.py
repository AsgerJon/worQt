"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from PySide6.QtCore import QTimer
from worktoy.core.sentinels import THIS

from worQt.app import App
from worQt.widgets import LabelWidget, TextWidget, PaintedWidget
from worQt.windows import MainWindow
from worQt.paint_ops import PaintBoxModel
from worQt.utils.geom import InSets, Size
from worQt.utils.qee_num import ColorNum
from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover
  pass


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, App]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """Run the 'new_words' editor: a 'QTextEdit' plus author/date fields,
  persisted through the 'worQt.document' model. Seeds the file dialogs
  with 'defaultDir' below - change it to point them wherever you like."""
  from worQt.new_words import NewWordsApp
  defaultDir = os.path.expanduser('~')  # <-- set your default dir here
  with NewWordsApp(*sys.argv) as app:
    window = app.window
    window.defaultDir = defaultDir
    window.show()
  return app.returnCode


if __name__ == '__main__':
  yolo(tester01)
  # yolo(tester00)
  # yolo(testMeBro, )
