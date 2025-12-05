"""
RougeVertBleu provides the base class for color classes in the 'worQt'
library. The base may be used directly or may be subclassed to provide
operations. The base does not provide any operations.

The base defines the following defining attributes:
- red: The red component of the color (0-255).
- green: The green component of the color (0-255).
- blue: The blue component of the color (0-255).
- alpha: The alpha (opacity) component of the color (0-255).

Additionally, the base defines the following virtual attributes:

- hex: The hexadecimal representation of the color.
- Q: The QColor representation of the color.
- pen: A QPen object initialized with the color, width 1 and solid line
style.
- brush: A QBrush object initialized with the color and solid pattern.
- hue: The hue component of the color in HSV color space.
- saturation: The saturation component of the color in HSV color space.
- value: The value component of the color in HSV color space.

Subclasses should preserve the overloaded constructors.


"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import torch
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen, QBrush
from torch import Tensor
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt, maybe
from worktoy.waitaminute import TypeException, WriteOnceError


class RougeVertBleu(BaseObject):
  """
  RougeVertBleu provides the base class for color classes in the 'worQt'
  library. The base may be used directly or may be subclassed to provide
  operations. The base does not provide any operations.

  The base defines the following defining attributes:
  - red: The red component of the color (0-255).
  - green: The green component of the color (0-255).
  - blue: The blue component of the color (0-255).
  - alpha: The alpha (opacity) component of the color (0-255).

  Additionally, the base defines the following virtual attributes:

  - hex: The hexadecimal representation of the color.
  - Q: The QColor representation of the color.
  - pen: A QPen object initialized with the color, width 1 and solid line
  style.
  - brush: A QBrush object initialized with the color and solid pattern.
  - hue: The hue component of the color in HSV color space.
  - saturation: The saturation component of the color in HSV color space.
  - value: The value component of the color in HSV color space.

  Subclasses should preserve the overloaded constructors.


  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_red__ = 255
  __fallback_green__ = 255
  __fallback_blue__ = 255
  __fallback_alpha__ = 255

  #  Private Variables
  __red_channel__ = None
  __green_channel__ = None
  __blue_channel__ = None
  __alpha_channel__ = None

  #  Public Variables
  red = Field()
  green = Field()
  blue = Field()
  alpha = Field()

  #  Virtual Variables
  hex = Field()
  Q = Field()
  pen = Field()
  brush = Field()
  hue = Field()
  saturation = Field()
  luminance = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @red.GET
  def _getRed(self, **kwargs) -> int:
    if self.__red_channel__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__red_channel__ = self.__fallback_red__
      return self._getRed(_recursion=True)
    if isinstance(self.__red_channel__, int):
      if kwargs.get('_recursion', False):
        raise RecursionError
      if 0 <= self.__red_channel__ <= 255:
        return self.__red_channel__
      infoSpec = """Red channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % self.__red_channel__)
    try:
      value = int(self.__red_channel__)
    except Exception as exception:
      name, val = '__red_channel__', self.__red_channel__
      raise TypeException(name, val, int) from exception
    else:
      self.__red_channel__ = value
      return self._getRed(_recursion=True)

  @green.GET
  def _getGreen(self, **kwargs) -> int:
    if self.__green_channel__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__green_channel__ = self.__fallback_green__
      return self._getGreen(_recursion=True)
    if isinstance(self.__green_channel__, int):
      if kwargs.get('_recursion', False):
        raise RecursionError
      if 0 <= self.__green_channel__ <= 255:
        return self.__green_channel__
      infoSpec = """Green channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % self.__green_channel__)
    try:
      value = int(self.__green_channel__)
    except Exception as exception:
      name, val = '__green_channel__', self.__green_channel__
      raise TypeException(name, val, int) from exception
    else:
      self.__green_channel__ = value
      return self._getGreen(_recursion=True)

  @blue.GET
  def _getBlue(self, **kwargs) -> int:
    if self.__blue_channel__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__blue_channel__ = self.__fallback_blue__
      return self._getBlue(_recursion=True)
    if isinstance(self.__blue_channel__, int):
      if kwargs.get('_recursion', False):
        raise RecursionError
      if 0 <= self.__blue_channel__ <= 255:
        return self.__blue_channel__
      infoSpec = """Blue channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % self.__blue_channel__)
    try:
      value = int(self.__blue_channel__)
    except Exception as exception:
      name, val = '__blue_channel__', self.__blue_channel__
      raise TypeException(name, val, int) from exception
    else:
      self.__blue_channel__ = value
      return self._getBlue(_recursion=True)

  @alpha.GET
  def _getAlpha(self, **kwargs) -> int:
    if self.__alpha_channel__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__alpha_channel__ = self.__fallback_alpha__
      return self._getAlpha(_recursion=True)
    if isinstance(self.__alpha_channel__, int):
      if kwargs.get('_recursion', False):
        raise RecursionError
      if 0 <= self.__alpha_channel__ <= 255:
        return self.__alpha_channel__
      infoSpec = """Alpha channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % self.__alpha_channel__)
    try:
      value = int(self.__alpha_channel__)
    except Exception as exception:
      name, val = '__alpha_channel__', self.__alpha_channel__
      raise TypeException(name, val, int) from exception
    else:
      self.__alpha_channel__ = value
      return self._getAlpha(_recursion=True)

  #  Virtual Getters

  @hex.GET
  def _getHex(self, **kwargs) -> str:
    r = self.red
    g = self.green
    b = self.blue
    a = self.alpha
    return f'#{r:02X}{g:02X}{b:02X}'

  @Q.GET
  def _getQ(self, **kwargs) -> QColor:
    return QColor(self.red, self.green, self.blue, self.alpha)

  @pen.GET
  def _getPen(self, **kwargs) -> QPen:
    pen = QPen()
    pen.setColor(self.Q)
    pen.setWidth(1)
    pen.setStyle(Qt.PenStyle.SolidLine)
    return pen

  @brush.GET
  def _getBrush(self, **kwargs) -> QBrush:
    brush = QBrush()
    brush.setColor(self.Q)
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    return brush

  @hue.GET
  def _getHue(self, **kwargs) -> int:
    return QColor.hslHue(self.Q, )

  @saturation.GET
  def _getSaturation(self, **kwargs) -> int:
    return QColor.hslSaturation(self.Q, )

  @luminance.GET
  def _getLuminance(self, **kwargs) -> int:
    return QColor.lightness(self.Q, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @red.SET
  def _setRed(self, redChannel: int) -> None:
    if self.__red_channel__ is not None:
      cls = type(self)
      raise WriteOnceError(cls.red, self.__red_channel__, redChannel)
    if isinstance(redChannel, complex):
      if redChannel.imag ** 2 > 1e-06:
        raise TypeException('redChannel', redChannel, int)
      self._setRed(redChannel.real)
    if isinstance(redChannel, float):
      if abs(redChannel - round(redChannel)) > 1e-06:
        raise TypeException('redChannel', redChannel, int)
      self._setRed(int(round(redChannel)))
    if isinstance(redChannel, str):
      try:
        value = int(redChannel)
      except Exception as exception:
        raise TypeException('redChannel', redChannel, int) from exception
      else:
        self._setRed(value)
    if not isinstance(redChannel, int):
      raise TypeException('redChannel', redChannel, int)
    if redChannel * (255 - redChannel) < 0:
      infoSpec = """Red channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % redChannel)
    self.__red_channel__ = redChannel

  @green.SET
  def _setGreen(self, greenChannel: int) -> None:
    if self.__green_channel__ is not None:
      cls = type(self)
      raise WriteOnceError(cls.green, self.__green_channel__, greenChannel)
    if isinstance(greenChannel, complex):
      if greenChannel.imag ** 2 > 1e-06:
        raise TypeException('greenChannel', greenChannel, int)
      self._setGreen(greenChannel.real)
    if isinstance(greenChannel, float):
      if abs(greenChannel - round(greenChannel)) > 1e-06:
        raise TypeException('greenChannel', greenChannel, int)
      self._setGreen(int(round(greenChannel)))
    if isinstance(greenChannel, str):
      try:
        value = int(greenChannel)
      except Exception as exception:
        raise TypeException('greenChannel', greenChannel, int) from exception
      else:
        self._setGreen(value)
    if not isinstance(greenChannel, int):
      raise TypeException('greenChannel', greenChannel, int)
    if greenChannel * (255 - greenChannel) < 0:
      infoSpec = """Green channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % greenChannel)
    self.__green_channel__ = greenChannel

  @blue.SET
  def _setBlue(self, blueChannel: int) -> None:
    if self.__blue_channel__ is not None:
      cls = type(self)
      raise WriteOnceError(cls.blue, self.__blue_channel__, blueChannel)
    if isinstance(blueChannel, complex):
      if blueChannel.imag ** 2 > 1e-06:
        raise TypeException('blueChannel', blueChannel, int)
      self._setBlue(blueChannel.real)
    if isinstance(blueChannel, float):
      if abs(blueChannel - round(blueChannel)) > 1e-06:
        raise TypeException('blueChannel', blueChannel, int)
      self._setBlue(int(round(blueChannel)))
    if isinstance(blueChannel, str):
      try:
        value = int(blueChannel)
      except Exception as exception:
        raise TypeException('blueChannel', blueChannel, int) from exception
      else:
        self._setBlue(value)
    if not isinstance(blueChannel, int):
      raise TypeException('blueChannel', blueChannel, int)
    if blueChannel * (255 - blueChannel) < 0:
      infoSpec = """Blue channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % blueChannel)
    self.__blue_channel__ = blueChannel

  @alpha.SET
  def _setAlpha(self, alphaChannel: int) -> None:
    if self.__alpha_channel__ is not None:
      cls = type(self)
      raise WriteOnceError(cls.alpha, self.__alpha_channel__, alphaChannel)
    if isinstance(alphaChannel, complex):
      if alphaChannel.imag ** 2 > 1e-06:
        raise TypeException('alphaChannel', alphaChannel, int)
      self._setAlpha(alphaChannel.real)
    if isinstance(alphaChannel, float):
      if abs(alphaChannel - round(alphaChannel)) > 1e-06:
        raise TypeException('alphaChannel', alphaChannel, int)
      self._setAlpha(int(round(alphaChannel)))
    if isinstance(alphaChannel, str):
      try:
        value = int(alphaChannel)
      except Exception as exception:
        raise TypeException('alphaChannel', alphaChannel, int) from exception
      else:
        self._setAlpha(value)
    if not isinstance(alphaChannel, int):
      raise TypeException('alphaChannel', alphaChannel, int)
    if alphaChannel * (255 - alphaChannel) < 0:
      infoSpec = """Alpha channel value %d is out of range [0, 255]."""
      raise ValueError(infoSpec % alphaChannel)
    self.__alpha_channel__ = alphaChannel

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    return self.hex

  def __repr__(self, ) -> str:
    if self.alpha == 255:
      argSpec = """(%d, %d, %d)"""
      args = argSpec % (self.red, self.green, self.blue)
    else:
      argSpec = """(%d, %d, %d, %d)"""
      args = argSpec % (self.red, self.green, self.blue, self.alpha)
    infoSpec = """%s%s"""
    clsName = type(self).__name__
    info = infoSpec % (clsName, args)
    return textFmt(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    someArgs = [arg for arg in args if arg is not None]
    base = QColor(*someArgs, )  # noqa
    self.__red_channel__ = base.red()
    self.__green_channel__ = base.green()
    self.__blue_channel__ = base.blue()
    self.__alpha_channel__ = base.alpha()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintTensor(self, *args) -> Tensor:
    """
    Paints a target tensor with this color as defined by the 'mask'
    object, which is expected to be a tensor of the same shape as the target
    tensor. The base implementation supports only boolean masks and will
    cast to boolean if necessary. The mask is optional and defaults to
    painting the entire target tensor.

    This method 'paintTensor' applies the color in-place. Alternatively,
    the method 'paintedTensor' may be used to return a painted copy of the
    target tensor.

    Subclasses may override this method to provide more advanced painting
    operations.

    """
    target, mask, *_ = [*args, None, None]
    if target is None:
      infoSpec = """No target tensor provided to paintTensor method!"""
      info = textFmt(infoSpec)
      raise ValueError(info)
    mask = maybe(mask, torch.ones_like(target))
    if not isinstance(mask, Tensor):
      raise TypeException('mask', mask, Tensor)
    targetW, targetH = target.shape[-2], target.shape[-1]
    maskW, maskH = mask.shape[-2], mask.shape[-1]
    if targetW != maskW or targetH != maskH:
      infoSpec = """Target tensor has shape (%d, %d) but mask has shape 
      (%d, %d)! Shapes must match in the last two dimensions."""
      info = infoSpec % (targetW, targetH, maskW, maskH)
      raise ValueError(textFmt(info))
    if mask.dtype != torch.bool:
      mask = mask.bool()
    if len(mask.shape) == 2:
      mask = mask.unsqueeze(0)
    if len(target.shape) < 3:
      infoSpec = """Target tensor must have at least 3 dimensions, got %d."""
      info = infoSpec % len(target.shape)
      raise ValueError(textFmt(info))
    if target.shape[-3] not in (3, 4):
      infoSpec = """Target tensor must have 3 or 4 channels in dimension 
      -3, got %d."""
      info = infoSpec % target.shape[-3]
      raise ValueError(textFmt(info))
    squeezed = False
    if len(target.shape) == 3:
      squeezed = True
      target.unsqueeze_(0)
    mask = mask.to(torch.bool).to(torch.float32)
    invMask = (torch.ones_like(mask) - mask)
    r, g, b = self.red, self.green, self.blue
    target[:, 0, :, :] = r * mask + target[:, 0, :, :] * invMask
    target[:, 1, :, :] = g * mask + target[:, 1, :, :] * invMask
    target[:, 2, :, :] = b * mask + target[:, 2, :, :] * invMask
    if target.shape[-3] == 4:
      a = self.alpha
      target[:, 3, :, :][mask[0, :, :]] = a
    if squeezed:
      target.squeeze_(0)
    return target

  def paintedTensor(self, *args, ) -> Tensor:
    """
    Same as 'paintTensor' but returns a painted copy of the target tensor
    instead of painting in-place.
    """
    target, mask, *_ = [*args, None, None]
    newTarget = torch.ones_like(target) * target
    return self.paintTensor(newTarget, mask)

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
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
