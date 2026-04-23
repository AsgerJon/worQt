"""
MainWindow subclasses LayoutWindow and is responsible for connecting
signals and slots and business logic generally.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize
from PySide6.QtGui import QFont, QFontDatabase
from icecream import ic
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from . import LayoutWindow, BaseWindow
from ..utils.font_nums import FontFamilyNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MainWindow(LayoutWindow):
  """
  MainWindow subclasses LayoutWindow and is responsible for connecting
  signals and slots and business logic generally.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initLogic(self) -> None:
    """
    initLogic connects signals and slots and provides business logic.
    """
    super().initLogic()
    self.testButton.leftClick.connect(self.leftClickFunc)
    self.testButton.rightClick.connect(self.rightClickFunc)
    self.testButton.leftHold.connect(self.leftHoldFunc)
    self.testButton.rightHold.connect(self.rightHoldFunc)
    self.testButton.leftDoubleClick.connect(self.leftDoubleClickFunc)
    self.testButton.rightDoubleClick.connect(self.rightDoubleClickFunc)
    self.testButton.leftDoubleHold.connect(self.leftDoubleHoldFunc)
    self.testButton.rightDoubleHold.connect(self.rightDoubleHoldFunc)
    self.resetButton.leftClick.connect(self.resetFunc)
    self.mainMenuBar.debug.debug01.triggered.connect(self.debug01Func)
    self.mainMenuBar.debug.debug02.triggered.connect(self.debug02Func)
    self.mainMenuBar.debug.debug03.triggered.connect(self.debug03Func)

  def debug01Func(self, ) -> None:
    """
    debug01Func is a function for testing purposes.
    """

  def leftClickFunc(self, ) -> None:
    """
    leftClickFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Left Clicked!""")

  def rightClickFunc(self, ) -> None:
    """
    rightClickFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Right Clicked!""")

  def leftHoldFunc(self, ) -> None:
    """
    leftHoldFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Left Held!""")

  def rightHoldFunc(self, ) -> None:
    """
    rightHoldFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Right Held!""")

  def leftDoubleClickFunc(self, ) -> None:
    """
    leftDoubleClickFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Left Double Clicked!""")

  def rightDoubleClickFunc(self, ) -> None:
    """
    rightDoubleClickFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Right Double Clicked!""")

  def leftDoubleHoldFunc(self, ) -> None:
    """
    leftDoubleHoldFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Left Double Held!""")

  def rightDoubleHoldFunc(self, ) -> None:
    """
    rightDoubleHoldFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Right Double Held!""")

  def resetFunc(self, ) -> None:
    """
    resetFunc is a function for testing purposes.
    """
    self.statusBar().showMessage("""Ready!""")

  def debug01Func(self, *args) -> None:
    big = QSize(5760, 1200)
    sourceText = """Never gonna give you up, never gonna let you down, 
    never gonna run around and desert you!"""
    _c = 1
    samples = dict()
    metrics = self.textWidget.font.metricsF
    while _c < len(sourceText):
      key = sourceText[:_c]
      value = metrics.horizontalAdvance(key)
      samples[key] = value
      _c *= 2
    header = """| Chars | Text Width | Width/Chars |"""
    charsWidth = len('Chars')
    widthWidth = len('Text Width')
    widthPerCharWidth = len('Width/Chars')
    charsSpec = """%%%dd""" % charsWidth
    widthSpec = """%%%df""" % widthWidth
    widthPerCharSpec = """%%%df""" % widthPerCharWidth
    widths = charsWidth, widthWidth, widthPerCharWidth
    border = """|=%s=|""" % '=|='.join(['=' * w for w in widths])
    seperator = """|-%s-|""" % '-|-'.join(['-' * w for w in widths])
    print(border)
    print(header)
    print(seperator)
    for key, value in samples.items():
      charsStr = charsSpec % len(key)
      widthStr = widthSpec % value
      if len(widthStr) > widthWidth:
        widthStr = widthStr[:widthWidth - 3] + '...'
      widthPerCharStr = widthPerCharSpec % (value / len(key))
      infoSpec = """| %s | %s | %s |"""
      info = infoSpec % (charsStr, widthStr, widthPerCharStr)
      print(info)
    print(border)
    print(self.textWidget.font)

  def debug02Func(self, *args) -> None:
    ic()
    self.textWidget.font.familyNum = FontFamilyNum.defaultMono

  def debug03Func(self, *args) -> None:
    for num in FontFamilyNum:
      print(num.name)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
