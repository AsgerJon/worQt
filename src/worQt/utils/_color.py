"""
WColor provides a color class for the 'worQt' framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QPen
from worktoy.core.sentinels import THIS
from worktoy.desc import Field, FixBox
from worktoy.dispatch import overload
from worktoy.keenum import KeeNum
from worktoy.mcls import BaseObject
from worktoy.utilities import stringList
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Iterator, Self, Union

  ColorField: TypeAlias = Union[QColor, Field]
  PenField: TypeAlias = Union[QPen, Field]
  BrushField: TypeAlias = Union[QBrush, Field]
  IntBox: TypeAlias = Union[FixBox, int]
  TupleField: TypeAlias = Union[tuple[str, ...], Field]


class Color(BaseObject):
  """
  WColor provides a color class for the 'worQt' framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __red_keys__: TupleField = (*stringList("""red, rouge, r"""),)
  __green_keys__: TupleField = (*stringList("""green, vert, g"""),)
  __blue_keys__: TupleField = (*stringList("""blue, bleu, b"""),)
  __alpha_keys__: TupleField = (*stringList("""alpha, a"""),)

  #  Public Variables
  red: IntBox = FixBox[int](255)
  green: IntBox = FixBox[int](255)
  blue: IntBox = FixBox[int](255)
  alpha: IntBox = FixBox[int](255)

  #  Virtual Variables
  Q: ColorField = Field()
  fillBrush: BrushField = Field()
  solidPen: PenField = Field()
  dashedPen: PenField = Field()
  dottedPen: PenField = Field()
  dashDotPen: PenField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQ(self, ) -> QColor:
    color = QColor()
    color.setRed(self.red)
    color.setGreen(self.green)
    color.setBlue(self.blue)
    color.setAlpha(self.alpha)
    return color

  @fillBrush.GET
  def _getFillBrush(self, ) -> QBrush:
    brush = QBrush()
    brush.setColor(self.Q)
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    return brush

  @solidPen.GET
  def _getSolidPen(self, ) -> QPen:
    pen = QPen()
    pen.setColor(self.Q)
    pen.setStyle(Qt.PenStyle.SolidLine)
    return pen

  @dashedPen.GET
  def _getDashedPen(self, ) -> QPen:
    pen = QPen()
    pen.setColor(self.Q)
    pen.setStyle(Qt.PenStyle.DashLine)
    return pen

  @dottedPen.GET
  def _getDottedPen(self, ) -> QPen:
    pen = QPen()
    pen.setColor(self.Q)
    pen.setStyle(Qt.PenStyle.DotLine)
    return pen

  @dashDotPen.GET
  def _getDashDotPen(self, ) -> QPen:
    pen = QPen()
    pen.setColor(self.Q)
    pen.setStyle(Qt.PenStyle.DashDotLine)
    return pen

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    """
    Returns a string with the hex code of the color, for example:
    #RRGGBBAA or #RRGGBB if alpha is 255.
    """
    r = self.red
    g = self.green
    b = self.blue
    a = self.alpha
    if a == 255:
      return f'#{r:02X}{g:02X}{b:02X}'
    return f'#{r:02X}{g:02X}{b:02X}{a:02X}'

  def __repr__(self, ) -> str:
    """
    Returns a code representation of the WColor instance.
    """
    infoSpec = """%s(%s, %s, %s, %s)"""
    red = '%d' % self.red
    green = '%d' % self.green
    blue = '%d' % self.blue
    alpha = '%d' % self.alpha
    clsName = type(self).__name__
    return infoSpec % (clsName, red, green, blue, alpha,)

  def __iter__(self, ) -> Iterator[int]:
    yield self.red
    yield self.green
    yield self.blue
    yield self.alpha

  def __hash__(self, ) -> int:
    return hash((*self,))

  def __len__(self, ) -> int:
    return 4

  def _resolveKey(self, key: str, ) -> int:
    KEYS = (
      (*self.__red_keys__,),
      (*self.__green_keys__,),
      (*self.__blue_keys__,),
      (*self.__alpha_keys__,),
      )
    VALUES = (
      self.red,
      self.green,
      self.blue,
      self.alpha,
      )
    for keys, value in zip(KEYS, VALUES):
      if key in keys:
        return value
    raise KeyError(key)

  def _resolveIndex(self, index: int) -> int:
    if index < 0:
      return self._resolveIndex(index + len(self))
    if index < len(self):
      return (*self,)[index]
    raise IndexError(index)

  def _resolveSlice(self, sliceObj: slice) -> tuple[int, ...]:
    return tuple.__getitem__((*self,), sliceObj)

  def __getitem__(self, identifier: Any) -> Any:
    """
    Resolves the identifier as key, index or slice and returns the
    corresponding value(s).
    """
    if isinstance(identifier, slice):
      return self._resolveSlice(identifier)
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    raise TypeException('identifier', identifier, str, int, slice)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int)
  def __init__(self, *args, **kwargs) -> None:
    r, g, b, a = args
    self.red = r
    self.green = g
    self.blue = b
    self.alpha = a
    if kwargs:
      self.__init__(**kwargs)

  @overload(int, int, int)
  def __init__(self, red: int, green: int, blue: int, **kwargs, ) -> None:
    self.red = red
    self.green = green
    self.blue = blue
    if kwargs:
      self.__init__(**kwargs)

  @overload(int)
  def __init__(self, gray: int, **kwargs, ) -> None:
    self.red = gray
    self.green = gray
    self.blue = gray
    if kwargs:
      self.__init__(**kwargs)

  @overload(QColor)
  def __init__(self, color: QColor, **kwargs) -> None:
    self.red = color.red()
    self.green = color.green()
    self.blue = color.blue()
    self.alpha = color.alpha()
    if kwargs:
      self.__init__(**kwargs)

  @overload(KeeNum)
  def __init__(self, color: KeeNum, **kwargs) -> None:
    self.__init__(color.value, **kwargs)

  @overload(THIS)
  def __init__(self, other: Self, **kwargs) -> None:
    self.red = other.red
    self.green = other.green
    self.blue = other.blue
    self.alpha = other.alpha
    if kwargs:
      self.__init__(**kwargs)

  @overload()
  def __init__(self, **kwargs, ) -> None:
    KEYS = [
      (*self.__red_keys__,),
      (*self.__green_keys__,),
      (*self.__blue_keys__,),
      (*self.__alpha_keys__,),
      ]
    VALS = dict()
    NAMES = ('red', 'green', 'blue', 'alpha',)
    for keys, name in zip(KEYS, NAMES):
      for key in keys:
        if key in kwargs:
          value = kwargs[key]
          if isinstance(value, int):  # bool is subclass of int
            VALS[name] = value
            break
          raise TypeException(key, value, int)
    if 'red' in VALS:
      self.red = VALS['red']
    if 'green' in VALS:
      self.green = VALS['green']
    if 'blue' in VALS:
      self.blue = VALS['blue']
    if 'alpha' in VALS:
      self.alpha = VALS['alpha']

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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
