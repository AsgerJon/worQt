"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMainWindow, QApplication
from worktoy.desc import Field
from worktoy.utilities import textFmt, stringList, ExceptionInfo

from worQt.app import App
from worQt.utils.geom import Point2D
from worQt.utils.geom.euclid import Dimension, EuclideanObject
from worQt.utils.font_nums import FontFamilyNum, FontWeightNum
from worQt.utils.font_nums import FontStyleNum, FontLineFlags
from worQt.windows import MainWindow
from yolo import yolo


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """
  Testing traditional QApplication entry points using a simple QMainWindow
  instance as the main application window.
  """
  with App(MainWindow, 'worQt') as app:
    QMainWindow.setWindowIcon(app.window, app.appIcon)
    app.window.update()
    app.window.show()
    app.window.setMinimumSize(400, 300)
  return int(app)


def tester02(*args, ) -> int:
  """
  Testing reversed list
  """

  def foo(*args2, ) -> None:
    posArgs = [*reversed(args2), ]
    while posArgs:
      arg = posArgs.pop()
      print(arg)

  roll = stringList(
    """never, gonna, give, you, up, never, gonna, let, you, down""")

  try:
    foo(*roll)
  except Exception as exception:
    infoSpec = """Caught '%s' during 'foo': %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    print(textFmt(infoSpec, excType, excMsg))
    return -1
  else:
    infoSpec = """Successfully called 'foo' with %d args."""
    info = infoSpec % len(roll)
    print(textFmt(info))
    return 0


def tester03(*args, ) -> int:
  """
  Testing the 'Dimension' class """
  dim = Dimension(100, 'w')

  class Size(EuclideanObject):
    width = Dimension(64, 'w')
    height = Dimension(48, 'h')
    area = Field()

  size = Size(width=69, height=420)

  print("""size: %s""" % str(size))
  print("""size: repr: %s""" % repr(size))

  return 0


def tester04(*args, ) -> int:
  """Testing EuclideanObject with a more complex example."""

  class Size(EuclideanObject):
    width = Dimension(64, 'w')
    height = Dimension(48, 'h')
    area = Field()

  size = Size(width=69, height=420)
  print("""Size(width=69, height=420): %s""" % size)

  size = Size(1337, 80085)
  print("""Size(1337, 80085): %s""" % size)

  return 0


def tester05(*args, ) -> int:
  """Testing the 'Number' class."""
  p = Point2D(69, 420)
  with ExceptionInfo() as info:
    _ = (p[(0, 1)])
  print(info.report)
  return 0


def tester06(*args, ) -> int:
  """
  Testing enumerations
  """

  QTop = Qt.AlignmentFlag.AlignTop
  QVCenter = Qt.AlignmentFlag.AlignVCenter
  QBottom = Qt.AlignmentFlag.AlignBottom

  QLeft = Qt.AlignmentFlag.AlignLeft
  QHCenter = Qt.AlignmentFlag.AlignHCenter
  QRight = Qt.AlignmentFlag.AlignRight

  QCenter = Qt.AlignmentFlag.AlignCenter

  flag = QTop | QLeft
  print(flag)
  print(QTop & flag)

  return 0


def tester07(*args) -> int:
  """
  testing string replacements
  """

  test = """all ur base r belong to us"""
  test2 = str.replace(test, 'urmom', 'fat')
  print(test)
  print(test2)
  return 0


def tester08(*args) -> int:
  """
  testing qfont database
  """

  print(FontFamilyNum.defaultSans)
  print(FontFamilyNum.defaultSerif)
  print(FontFamilyNum.defaultMono)

  return 0


def tester09(*args) -> int:
  """
  testing qfont database
  """

  app = QApplication.instance()
  if app is None:
    app = QApplication([])
  try:
    font = QFont()
    print(font.weight())
    font.setFamily(FontFamilyNum.MONTSERRAT.value)
    print(font.family())
    print(font.weight())
    for item in QFont.Weight:
      print(repr(item))

  finally:
    try:
      app.quit()
    except AttributeError:
      pass
    try:
      del app
    except NameError:
      pass
  return 0


def tester10(*args) -> int:
  """
  Testing QFont.Weight
  """
  app = QApplication.instance()
  if app is not None:
    print("""app is not None""")
    app.quit()
  del app

  print("""QApplication.instance()""", QApplication.instance())
  for item in QFont.Weight:
    print(repr(item))
  return 0


def tester11(*args) -> int:
  """
  Testing QFont.Weight
  """

  try:
    weight = FontWeightNum[QFont.Weight.Bold]
  except Exception as exception:
    infoSpec = """Caught '%s' during FontWeightNum[QFont.Weight.Bold]: %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    print(textFmt(infoSpec % (excType, excMsg)))
    return -1
  else:
    print("""FontFamilyNum[QFont.Weight.Bold]: %s""" % weight)
    return 0


def tester12(*args) -> int:
  """
  Testing QFont.Style
  """

  for item in FontStyleNum:
    print(repr(item), item.value)

  return 0


def tester13() -> int:
  """Testing num type recognition"""

  items = [69, '420', FontWeightNum.LIGHT, QFont.Weight.DemiBold]
  infoSpec = """isinstance(%s, %s): %s"""
  for item in items:
    print("""Testing item: %s""" % repr(item))
    for type_ in (FontWeightNum, QFont.Weight, int):
      res = 'True' if isinstance(item, type_) else 'False'
      info = infoSpec % (repr(item), type_.__name__, res)
      print(info)
    print('-' * 48)

  return 0


def tester14(*args) -> int:
  """
  Testing FontLineFlags
  """

  for item in FontLineFlags:
    print(item, len((*item.highs,)), len((*item.lows,)))

  print(FontLineFlags.NULL)

  return 0


if __name__ == '__main__':
  yolo(tester14)
  # yolo(runTests, tester08)
