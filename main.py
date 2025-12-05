"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2025 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

import inspect
import torch
from PySide6.QtCore import SignalInstance
from worktoy.utilities import textFmt
from worktoy.utilities.mathematics import pi

from worQt.core.images.functional import planeConv
from yolo import yolo, runTests
from worQt.app import Main
from worQt.windows import MainWindow


def tester00() -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset]
  for item in stuff:
    print(item)
  return 0


def tester01() -> int:
  """App test"""
  with Main[MainWindow, 'worQt'](*sys.argv) as main:
    print('_' * 77)
    print("""Entered main context. """)
    main.windowInstance.show()
    print("""Opened main window.""")
    print('¨' * 77)
  return 0


def tester02() -> int:
  """
  For some reason the torch documentation does not specify the range of
  angles returned by torch.atan2.
  """

  x = torch.randn(69420, dtype=torch.float32)
  y = torch.randn(69420, dtype=torch.float32)
  t = torch.atan2(y, x)
  minVal, maxVal = torch.min(t).item(), torch.max(t).item()
  minPiFactor = int(minVal / pi * 1000)
  maxPiFactor = int(maxVal / pi * 1000)
  infoSpec = """The torch.atan2 returns angles in range: %d pi/1000 to %d 
  pi/1000"""
  info = infoSpec % (minPiFactor, maxPiFactor)
  print(textFmt(info))
  return 0


def tester03() -> int:
  """Testing tensor slicing shapes"""
  data = torch.randn(1, 3, 256, 256, dtype=torch.float32)
  print("""data shape: %s""" % (str(data.shape),))
  print("""data[0] shape: %s""" % (str(data[0].shape),))
  print("""data[0, :, :, :] shape: %s""" % (str(data[0, :, :, :].shape),))
  infoSpec = """data[0].shape == data[0, :, :, :].shape: %s"""
  test = True if data[0].shape == data[0, :, :, :].shape else False
  info = infoSpec % (str(test),)
  print(textFmt(info))
  infoSpec = """data[0] == data[0, :, :, :]: %s"""
  test = (data[0] == data[0, :, :, :]).view(-1)
  testSpec = """%d == %s"""
  left = test.sum().item()
  right = test.shape
  testStr = testSpec % (int(left), str(right),)
  info = infoSpec % (testStr,)
  print(textFmt(info))

  return 0


def tester04() -> int:
  """Testing arange"""
  print("""torch.arange(0, 10, )""", torch.arange(0, 10, ))
  return 0


def tester05() -> int:
  """
  Testing the _kernelPixel method from OperatorProcedure
  """
  from worQt.core.images._operator_procedure import OperatorProcedure

  data = torch.randn(3, 64, 64, dtype=torch.float32)
  kernel = OperatorProcedure._gaussKernel(5, 1.0)
  print("""Data shape: %s""" % (str(data.shape),))
  print("""Kernel shape: %s""" % (str(kernel.shape),))
  output = OperatorProcedure._kernelPixel(data, kernel)
  print("""Output shape: %s""" % (str(output.shape),))
  return 0


def tester06() -> int:
  """
  Testing the SignalInstance
  """
  for (key, val) in SignalInstance.__dict__.items():
    infoSpec = """%s: %s"""
    typeName = type(val).__name__
    info = infoSpec % (key, typeName)
    print(textFmt(info))

  print(SignalInstance.connect)
  try:
    func = SignalInstance.connect.__func__
  except Exception as exception:
    infoSpec = """When trying to access the __func__ attribute of
    'SignalInstance.connect' caught %s: %s"""
    excType = type(exception).__name__
    excMsg = str(exception)
    info = infoSpec % (excType, excMsg)
    print(textFmt(info))
  else:
    infoSpec = """The 'SignalInstance.connect' function is a 
    %s object."""
    funcType = type(func).__name__
    info = infoSpec % (funcType,)
    print(textFmt(info))
  return 0


def tester07() -> int:
  """Placeholder tester07"""
  func = SignalInstance.connect

  return 0


def tester08() -> int:
  """Testing convolution function 'planeConv'"""

  image = torch.randn(3, 256, 256, dtype=torch.float32)
  kernel = torch.randn(3, 3, 3, dtype=torch.float32)
  convolved = planeConv(image, kernel, )
  print("""Convolved shape: %s""" % (str(convolved.shape),))

  return 0


def tester09() -> int:
  """Placeholder tester09"""

  from main_tester_class04 import Sus

  return 0


if __name__ == '__main__':
  yolo(runTests, tester01)
