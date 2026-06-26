"""
Document is the root of a relational document: a set of value fields and
array fields, a global member index keyed by stable id, a dirty/revision
change channel with subscribers, and atomic JSON persistence. Loading is two
pass - every member of every array field is materialised first, then the
references are resolved against the completed index.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException

from ._member import Member
from ._schema import Schema

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Callable, Optional, Self

  from ._change import Change


class Document(Schema):
  """The file-backed root that owns fields, members and the change channel."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    super().__init__()
    self.__document_members__ = {}
    self.__document_next_id__ = 1
    self.__document_listeners__ = []
    self.__document_dirty__ = False
    self.__document_revision__ = 0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CHANGE CHANNEL   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def notifyChange(self, change: Change) -> None:
    self.markDirty(change)

  def markDirty(self, change: Change) -> None:
    self.__document_dirty__ = True
    self.__document_revision__ += 1
    for callback in [*self.__document_listeners__]:
      callback(change)

  def clean(self, ) -> None:
    """Mark the document saved: clear unsaved changes but keep 'revision',
    so undo history survives a save."""
    self.__document_dirty__ = False

  def markPristine(self, ) -> None:
    """Establish the current state as the clean baseline - no unsaved
    changes and no undo history. A freshly loaded or freshly created
    document reads identically to a brand-new 'Document'."""
    self.__document_dirty__ = False
    self.__document_revision__ = 0

  def isDirty(self, ) -> bool:
    return self.__document_dirty__

  def revision(self, ) -> int:
    return self.__document_revision__

  def subscribe(self, callback: Callable) -> Callable:
    """Register a listener called with each 'Change'. Returns it so it can
    be kept for 'unsubscribe'."""
    self.__document_listeners__.append(callback)
    return callback

  def unsubscribe(self, callback: Callable) -> None:
    if callback in self.__document_listeners__:
      self.__document_listeners__.remove(callback)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MEMBER REGISTRY  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _adoptMember(self, member: Member) -> None:
    """Take ownership of a member: assign it an id if it has none, index it,
    and point it back at this document. A member keeps an id it already
    carries (the load path), advancing the counter past it."""
    if not isinstance(member, Member):
      raise TypeException('member', member, Member)
    owner = member.__owning_document__
    if owner is not None and owner is not self:
      raise ValueError('member already belongs to another document')
    if member.__member_id__ is None:
      member.__member_id__ = self.__document_next_id__
      self.__document_next_id__ += 1
    elif member.__member_id__ >= self.__document_next_id__:
      self.__document_next_id__ = member.__member_id__ + 1
    self.__document_members__[member.__member_id__] = member
    member.__owning_document__ = self

  def _releaseMember(self, member: Member) -> None:
    """Drop a member from the index. References still pointing at it are not
    auto-cleared; they become dangling and resolve to None on next load."""
    self.__document_members__.pop(member.__member_id__, None)
    member.__owning_document__ = None

  def member(self, memberId: int) -> Optional[Member]:
    return self.__document_members__.get(memberId)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SERIALIZATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, ) -> dict:
    cls = type(self)
    data = {}
    for name, field in cls._valueFields().items():
      data[name] = field.encode(self)
    for name, field in cls._arrayFields().items():
      data[name] = field.encode(self)
    return data

  @classmethod
  def decode(cls, data: dict) -> Self:
    document = cls()
    for name, field in cls._valueFields().items():
      if name in data:
        field.decode(document, data[name])
    #  Pass 1: materialise every member, keeping its stored id.
    pending = []
    for name, field in cls._arrayFields().items():
      observable = field.__get__(document, cls)
      for raw in data.get(name, []):
        member = field.buildMember(raw)
        observable.append(member)
        pending.append((member, raw))
    #  Pass 2: resolve references against the completed index.
    index = document.__document_members__
    for member, raw in pending:
      memberCls = type(member)
      for name, field in memberCls._references().items():
        if name in raw:
          field.resolve(member, raw[name], index)
      for name, field in memberCls._referenceLists().items():
        if name in raw:
          field.resolve(member, raw[name], index)
    #  A freshly loaded document is a clean slate: zero the revision the
    #  load's own sets/appends accumulated, unlike 'save' which only clears
    #  'dirty' (you can still undo after saving).
    document.markPristine()
    return document

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PERSISTENCE (ATOMIC)   # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def save(self, path: str) -> None:
    data = self.encode()
    fullPath = os.path.abspath(path)
    os.makedirs(os.path.dirname(fullPath), exist_ok=True)
    tmpPath = '%s.tmp' % fullPath  # same dir = same fs = atomic replace
    try:
      with open(tmpPath, 'w') as handle:
        json.dump(data, handle, indent=2)
      os.replace(tmpPath, fullPath)
    except BaseException:
      if os.path.exists(tmpPath):
        os.remove(tmpPath)
      raise
    self.clean()

  @classmethod
  def load(cls, path: str) -> Self:
    with open(os.path.abspath(path), 'r') as handle:
      data = json.load(handle)
    return cls.decode(data)
