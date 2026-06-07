"""
Section is the array element of a 'TextDocument': one block of body text. It
subclasses 'AbstractItem' so it can live in an 'ArrayField', and holds its
text in a 'NotifyBox' (required on items) so an in-place edit propagates
through the document's change chain. Named 'Section' to avoid colliding with
'worktoy.lorem_ipsum.Paragraph'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.dispatch import overload

from worQt.data import AbstractItem, NotifyBox

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class Section(AbstractItem):
  """One block of body text in a 'TextDocument'."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  text = NotifyBox[str]('')  # the section body; notifies on every write

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __init__(self, text: str) -> None:
    self.text = text

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    return self.text

  def __repr__(self, ) -> str:
    return 'Section(%r)' % (self.text,)
