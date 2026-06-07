"""
BoxDims provides a simple data structure assigning a rectangle for each
layer in a 'BoxModel' instance.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, QRectF
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from . import Rect, Point2D, Size
from ..qee_num import BoxNum, SizePolicy

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Union, Self, Iterator
  from . import BoxModel

  RectLike: TypeAlias = Union[Rect, QRect, QRectF, Size]


class BoxDims(BaseObject):
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __margined_rect__ = None
  __bordered_rect__ = None
  __padded_rect__ = None
  __content_rect__ = None

  #  Public Variables
  margined = Field()
  bordered = Field()
  padded = Field()
  content = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __getitem__(self, key: str) -> Any:
    if key == 'margined':
      return self.__margined_rect__
    elif key == 'bordered':
      return self.__bordered_rect__
    elif key == 'padded':
      return self.__padded_rect__
    elif key == 'content':
      return self.__content_rect__
    else:
      raise KeyError(key)

  @overload(BoxNum)
  def __getitem__(self, key: BoxNum) -> Any:
    if key == BoxNum.MARGIN:
      return self.__margined_rect__
    elif key == BoxNum.BORDER:
      return self.__bordered_rect__
    elif key == BoxNum.PADDING:
      return self.__padded_rect__
    elif key == BoxNum.CONTENT:
      return self.__content_rect__
    else:
      raise KeyError(key)

  @overload(slice)
  def __getitem__(self, key: slice) -> RectLike:
    num, type_ = key.start, key.step
    if not isinstance(num, BoxNum):
      raise KeyError(num)
    out = self.__getitem__(num)
    if type_ is Rect:
      return out
    elif type_ is QRect:
      return out.Q
    elif type_ is QRectF:
      return out.QF
    elif type_ is Size:
      return out.size
    raise KeyError(type_)

  def __iter__(self, ) -> Iterator[tuple[BoxNum, Rect]]:
    yield BoxNum.Margined, self.__margined_rect__
    yield BoxNum.Bordered, self.__bordered_rect__
    yield BoxNum.Padded, self.__padded_rect__
    yield BoxNum.Content, self.__content_rect__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def extrinsic(cls, outer: Rect, box: BoxModel) -> Self:
    self = cls()
    self.__margined_rect__ = outer
    self.__bordered_rect__ = self.__margined_rect__ - box.marginDims
    self.__padded_rect__ = self.__bordered_rect__ - box.borderDims
    self.__content_rect__ = self.__padded_rect__ - box.paddingDims
    return self

  @classmethod
  def intrinsic(cls, content: Rect, box: BoxModel) -> Self:
    self = cls()
    self.__content_rect__ = content
    self.__padded_rect__ = self.__content_rect__ + box.paddingDims
    self.__bordered_rect__ = self.__padded_rect__ + box.borderDims
    self.__margined_rect__ = self.__bordered_rect__ + box.marginDims
    return self

  @classmethod
  def fromRect(cls, box: BoxModel, *args) -> Self:
    rects, pols = [], []
    for arg in args:
      if isinstance(arg, (Rect, QRect, QRectF)):
        rects.append(Rect(arg))
      if isinstance(arg, SizePolicy):
        pols.append(arg)
    if not rects:
      infoSpec = """Received no Rect-like arguments: %s"""
      info = infoSpec % (args,)
      raise ValueError(info)
    if len(rects) == 1:
      inner, outer = rects[0], rects[0]
    elif len(rects) == 2:
      inner, outer = rects
    else:
      infoSpec = """Received too many Rect-like arguments: %s"""
      info = infoSpec % (rects,)
      raise ValueError(info)
    if not pols:
      return cls.intrinsic(inner, box)
    if len(pols) > 2:
      infoSpec = """Received too many size policies: %s"""
      info = infoSpec % (pols,)
      raise ValueError(info)
    if len(pols) == 1:
      h, v = pols[0], pols[0]
    else:
      h, v = pols
    if h is SizePolicy.EXTRINSIC:  # Content shrinks to fit
      marginedLeft = outer.left()
      borderedLeft = marginedLeft + box.marginDims.left
      paddedLeft = borderedLeft + box.borderDims.left
      contentLeft = paddedLeft + box.paddingDims.left
      marginedRight = outer.right()
      borderedRight = marginedRight - box.marginDims.right
      paddedRight = borderedRight - box.borderDims.right
      contentRight = paddedRight - box.paddingDims.right
    elif h is SizePolicy.INTRINSIC:  # Content grows to fit
      contentLeft = inner.left()
      paddedLeft = contentLeft - box.paddingDims.left
      borderedLeft = paddedLeft - box.borderDims.left
      marginedLeft = borderedLeft - box.marginDims.left
      contentRight = inner.right()
      paddedRight = contentRight + box.paddingDims.right
      borderedRight = paddedRight + box.borderDims.right
      marginedRight = borderedRight + box.marginDims.right
    else:
      infoSpec = """Received invalid horizontal size policy: %s"""
      info = infoSpec % (h,)
      raise ValueError(info)
    if v is SizePolicy.EXTRINSIC:  # Content shrinks to fit
      marginedTop = outer.top()
      borderedTop = marginedTop + box.marginDims.top
      paddedTop = borderedTop + box.borderDims.top
      contentTop = paddedTop + box.paddingDims.top
      marginedBottom = outer.bottom()
      borderedBottom = marginedBottom - box.marginDims.bottom
      paddedBottom = borderedBottom - box.borderDims.bottom
      contentBottom = paddedBottom - box.paddingDims.bottom
    elif v is SizePolicy.INTRINSIC:  # Content grows to fit
      contentTop = inner.top()
      paddedTop = contentTop - box.paddingDims.top
      borderedTop = paddedTop - box.borderDims.top
      marginedTop = borderedTop - box.marginDims.top
      contentBottom = inner.bottom()
      paddedBottom = contentBottom + box.paddingDims.bottom
      borderedBottom = paddedBottom + box.borderDims.bottom
      marginedBottom = borderedBottom + box.marginDims.bottom
    else:
      infoSpec = """Received invalid vertical size policy: %s"""
      info = infoSpec % (v,)
      raise ValueError(info)
    marginedTopLeft = Point2D(marginedLeft, marginedTop)
    marginedBottomRight = Point2D(marginedRight, marginedBottom)
    marginedRect = Rect(marginedTopLeft, marginedBottomRight)
    contentTopLeft = Point2D(contentLeft, contentTop)
    contentBottomRight = Point2D(contentRight, contentBottom)
    contentRect = Rect(contentTopLeft, contentBottomRight)
    borderedRect = marginedRect - box.marginDims
    paddedRect = contentRect + box.paddingDims
    #  Sanity Check
    if borderedRect != paddedRect + box.borderDims:
      infoSpec = """Inconsistent BoxDims construction: borderedRect=%s, 
      paddedRect=%s, borderDims=%s"""
      info = infoSpec % (borderedRect, paddedRect, box.borderDims)
      raise ValueError(info)
    self = cls()
    self.__margined_rect__ = marginedRect
    self.__bordered_rect__ = borderedRect
    self.__padded_rect__ = paddedRect
    self.__content_rect__ = contentRect
    return self
