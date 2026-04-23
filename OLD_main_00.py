"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import Iterator

from PySide6.QtCore import QRect
from PySide6.QtGui import QKeySequence, QIcon
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow
from worktoy.utilities import textFmt, wordWrap

from main_cls import Number
from main_cls_02 import LOL
from main_cls_03 import SliceTest
from worQt.app import App
from worQt.windows import MainWindow
from yolo import yolo, runTests


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
  Testing QKeySequences from strings
  """

  upperGood = """CTRL+X"""
  lowerGood = """ctrl+x"""
  capGood = """Ctrl+X"""
  caseBad = """cTrL+x"""
  trollBad = """never ever gonna give you up"""
  blankGood = str()  # blank sequence
  withComma = """Ctrl+X, Ctrl+C, Ctrl+V"""
  sequences = [
    upperGood,
    lowerGood,
    capGood,
    blankGood,
    caseBad,
    trollBad,
    withComma,
  ]
  for seq in sequences:
    keySeq = QKeySequence.fromString(seq)
    info = """Testing: '%s' -> '%s'""" % (textFmt(seq), keySeq.toString())
    print(info, keySeq.isEmpty())
  else:
    return 0


def tester03(*args, ) -> int:
  """Testing looping empty iterator followed by else"""

  for _ in ():
    print('FAIL')
    return 1
  else:
    print('SUCCESS')
    return 0
  return -1


def tester04(*args, ) -> int:
  """Testing sum and __add__"""

  base = [69, 420, 1337, 80085, 8008135]
  numbers = [Number(i) for i in base]
  print(sum(base), sum(numbers))
  return 0


def tester05(*args, ) -> int:
  """Testing EZData class with mixed defaults"""
  ARGS = [(), (69, 420), (1337, 80085, 6, 7)]
  lols = []

  for args_ in ARGS:
    try:
      lol = LOL(*args_)
    except Exception as exception:
      infoSpec = """Caught '%s': %s"""
      excType = type(exception).__name__
      excMsg = str(exception)
      info = infoSpec % (excType, excMsg,)
      print(info)
    else:
      infoSpec = """Successfully created LOL: %s"""
      info = infoSpec % str(lol)
      print(info)
      lols.append(lol)
  for lol in lols:
    print("""Testing attributes of LOL object: '%s'""" % str(lol))
    for slot in LOL.__slots__:
      try:
        value = getattr(lol, slot)
      except Exception as exception:
        infoSpec = """Caught '%s' when accessing attribute '%s': %s"""
        excType = type(exception).__name__
        excMsg = str(exception)
        info = infoSpec % (excType, slot, excMsg,)
        print(info)
      else:
        infoSpec = """  Attribute '%s' has value: %s"""
        info = infoSpec % (slot, str(value),)
        print(info)
  lol = lols[0]
  print('Modifying attributes of first LOL object...')
  try:
    lol.row = 69
  except Exception as exception:
    infoSpec = """Caught '%s' when modifying attribute 'row': %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    info = infoSpec % (excType, excMsg,)
    print(info)
  else:
    infoSpec = """  Successfully modified attribute 'row' to: %d"""
    info = infoSpec % lol.row
    print(info)
  try:
    lol.col = 420
  except Exception as exception:
    infoSpec = """Caught '%s' when modifying attribute 'col': %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    info = infoSpec % (excType, excMsg,)
    print(info)
  else:
    infoSpec = """  Successfully modified attribute 'col' to: %d"""
    info = infoSpec % lol.col
    print(info)
  print(lols[0].asDict())
  lol = lols[1]
  try:
    value = (*lol.cells,)
  except Exception as exception:
    infoSpec = """Caught '%s' when accessing 'cells' attribute: %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    info = infoSpec % (excType, excMsg,)
    print(info)
  else:
    infoSpec = """  Successfully accessed 'cells' attribute: %s"""
    info = infoSpec % str(value)
    print(info)
  return 0


def tester06(*args, ) -> int:
  """Testing hashing of LOL"""
  lol1 = LOL()
  lol2 = LOL(69, 420)
  lol3 = LOL(69, 420, 1337, 80085)
  try:
    lolSet = {lol1, lol2, lol3}
  except Exception as exception:
    infoSpec = """Caught '%s' when creating set of LOL: %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    info = wordWrap(77, infoSpec % (excType, excMsg,))
    print(info)
    return 1
  else:
    infoSpec = """Successfully created set of LOL: %s"""
    info = wordWrap(77, infoSpec % str(lolSet))
    print(info)
    return 0


def tester07(*args, ) -> int:
  """
  Testing the SliceTest
  """

  test = SliceTest()
  try:
    value = test[69:420:2]
  except Exception as exception:
    infoSpec = """Caught '%s' when slicing SliceTest: %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    info = wordWrap(77, infoSpec % (excType, excMsg,))
    print(info)
    return 1
  else:
    infoSpec = """Successfully sliced SliceTest: %s"""
    info = wordWrap(77, infoSpec % str(value))
    print(info)
    return 0


def tester08(*args, ) -> int:
  """
  Testing dict types
  """

  data = {
    'one': 1,
    'two': 2,
    'three': 3,
  }

  dataItems = dict.items(data, )
  dataKeys = dict.keys(data, )
  dataValues = dict.values(data, )

  dataObjects = dataKeys, dataValues, dataItems
  titles = 'Keys', 'Values', 'Items'

  for title, obj in zip(titles, dataObjects):
    clsName = type(obj).__name__
    headerSpec = """%s object of type '%s'"""
    header = headerSpec % (title, clsName,)
    subHeader = """<tab>Having MRO:"""
    bodyLines = []
    for cls in type(obj).mro():
      line = """<tab><tab>%s""" % cls.__name__
      bodyLines.append(line)
    body = '<br>'.join(bodyLines)
    footer = '¨' * 48
    contents = [header, subHeader, body, footer]
    info = '<br>'.join(contents)
    print(textFmt(info))

  return 0


if __name__ == '__main__':
  yolo(runTests, tester01)
