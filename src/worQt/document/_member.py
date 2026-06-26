"""
Member is an entry in an array field - a node, an element, a paragraph. It
carries a stable id (assigned by the document when adopted) so references
survive a save/load, and it forwards every change to its owning document.
Its state is declared with 'ValueField' (its own data) and 'Reference' /
'ReferenceList' (pointers to other members).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._schema import Schema

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional

  from ._change import Change
  from ._document import Document


class Member(Schema):
  """An identified, change-aware entry in an array field."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  __owning_document__ = None  # set when adopted by a document
  __member_id__ = None  # the document-scoped stable id

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def memberId(self) -> Optional[int]:
    return self.__member_id__

  @property
  def document(self) -> Optional[Document]:
    return self.__owning_document__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CHANGE CONTRACT  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def notifyChange(self, change: Change) -> None:
    """Forward to the owning document, if any. A member not yet added to a
    document has nowhere to forward to, so this is a no-op until then."""
    document = self.__owning_document__
    if document is not None:
      document.markDirty(change)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SERIALIZATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self) -> dict:
    cls = type(self)
    out = {'__type__': cls.__name__, '__id__': self.__member_id__}
    for name, field in cls._valueFields().items():
      out[name] = field.encode(self)
    for name, field in cls._references().items():
      out[name] = field.encode(self)
    for name, field in cls._referenceLists().items():
      out[name] = field.encode(self)
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self) -> str:
    return '%s(id=%r)' % (type(self).__name__, self.__member_id__)
