"""
TestRougeVertBleu module tests the functionality of the RougeVertBleu
color class.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING
from random import randint

import torch
from PySide6.QtGui import QColor

from worQt.core import RougeVertBleu

from . import ColorTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type, Callable, Self, Union, Optional

  RandColor: TypeAlias = tuple[RougeVertBleu, tuple[int, int, int, int]]


class TestRougeVertBleu(ColorTest):
  """
  The TestRougeVertBleu module tests the functionality of the
  RougeVertBleu color class.
  """

  def setUp(self, ) -> None:
    """
    Sets up the test case by initializing a RougeVertBleu instance.
    """
    self.sampleColors = [
        RougeVertBleu(255, 0, 0),  # Red
        RougeVertBleu(0, 255, 0),  # Green
        RougeVertBleu(0, 0, 255),  # Blue
        RougeVertBleu(255, 255, 0),  # Yellow
        RougeVertBleu(0, 255, 255),  # Cyan
        RougeVertBleu(255, 0, 255),  # Magenta
    ]
    self.alphaColors = [
        RougeVertBleu(255, 0, 0, 128),  # Semi-transparent Red
        RougeVertBleu(0, 255, 0, 128),  # Semi-transparent Green
        RougeVertBleu(0, 0, 255, 128),  # Semi-transparent Blue
    ]

  @staticmethod
  def _randomColor(**kwargs) -> RandColor:
    r = randint(0, 255)
    g = randint(0, 255)
    b = randint(0, 255)
    a = kwargs.get('alpha', )
    if isinstance(a, bool) and a:
      a = randint(0, 255)
    return RougeVertBleu(r, g, b, a), (r, g, b, a)

  def test_initialization(self, ) -> None:
    """
    Tests the initialization of the RougeVertBleu class.
    """
    for color in [*self.sampleColors, *self.alphaColors]:
      self.assertIsInstance(color, RougeVertBleu)

  def test_components(self) -> None:
    """
    Tests the individual color components of the RougeVertBleu class.
    """
    for _ in range(69):
      rougeVertBleu, rgba = self._randomColor()
      r, g, b, a = rgba
      self.assertEqual(rougeVertBleu.red, r)
      self.assertEqual(rougeVertBleu.green, g)
      self.assertEqual(rougeVertBleu.blue, b)
      self.assertEqual(rougeVertBleu.alpha, 255)
    for _ in range(420):
      rougeVertBleu, rgba = self._randomColor(alpha=True)
      r, g, b, a = rgba
      self.assertEqual(rougeVertBleu.red, r)
      self.assertEqual(rougeVertBleu.green, g)
      self.assertEqual(rougeVertBleu.blue, b)
      self.assertEqual(rougeVertBleu.alpha, a)

  def test_q(self, ) -> None:
    """
    Tests the QColor conversion of the RougeVertBleu class.
    """
    for _ in range(7):
      rvb, rgba = self._randomColor()
      self.assertIsInstance(rvb.Q, QColor)
    for _ in range(69):
      rvb, rgba = self._randomColor(alpha=True)
      self.assertIsInstance(rvb.Q, QColor)
      self.assertEqual(QColor.red(rvb.Q), rvb.red)
      self.assertEqual(QColor.green(rvb.Q), rvb.green)
      self.assertEqual(QColor.blue(rvb.Q), rvb.blue)
      self.assertEqual(QColor.alpha(rvb.Q), rvb.alpha)

  def test_hex(self, ) -> None:
    """
    Tests the hexadecimal representation of the RougeVertBleu class.
    """
    for _ in range(69):
      rvb, rgba = self._randomColor()
      r, g, b, a = rgba
      expectedHex = f'#{r:02X}{g:02X}{b:02X}'
      self.assertEqual(rvb.hex, expectedHex)
    for _ in range(420):
      rvb, rgba = self._randomColor(alpha=True)
      r, g, b, a = rgba
      expectedHex = f'#{r:02X}{g:02X}{b:02X}'
      self.assertEqual(rvb.hex, expectedHex)

  def test_hue(self, ) -> None:
    """
    Tests the hue calculation of the RougeVertBleu class.
    """

    for _ in range(69):
      rvb, rgba = self._randomColor()
      expectedHue = QColor.hslHue(rvb.Q)
      actualHue = rvb.hue
      self.assertEqual(actualHue, expectedHue)

  def test_saturation(self, ) -> None:
    """
    Tests the saturation calculation of the RougeVertBleu class.
    """

    for _ in range(69):
      rvb, rgba = self._randomColor()
      expectedSaturation = QColor.hslSaturation(rvb.Q)
      actualSaturation = rvb.saturation
      self.assertEqual(actualSaturation, expectedSaturation)

  def test_luminance(self, ) -> None:
    """
    Tests the luminance calculation of the RougeVertBleu class.
    """

    for _ in range(69):
      rvb, rgba = self._randomColor()
      expectedLuminance = QColor.lightness(rvb.Q)
      actualLuminance = rvb.luminance
      self.assertEqual(actualLuminance, expectedLuminance)

  def test_paint_tensor(self, ) -> None:
    """
    Tests the paint_tensor method of the RougeVertBleu class.
    """
    for _ in range(69):
      rvb, rgba = self._randomColor()
      mask = torch.zeros((64, 64), dtype=torch.float32)
      for i in range(64):
        for j in range(64):
          if (i - 32) ** 2 + (j - 32) ** 2 < 16 ** 2:
            mask[i, j] = 1.0
      mask = mask.to(torch.bool)
      mask.unsqueeze_(0)
      target = torch.randn((3, 64, 64), dtype=torch.float32)
      rvb.paintTensor(target, mask)
      for _ in range(420):
        ii = randint(0, 63)
        jj = randint(0, 63)
        if mask[0, ii, jj].item():
          self.assertEqual(target[0, ii, jj].item(), rvb.red)
          self.assertEqual(target[1, ii, jj].item(), rvb.green)
          self.assertEqual(target[2, ii, jj].item(), rvb.blue)
