"""
TextDocument is the persisted model for 'new_words': a
'worQt.document.Document' with four scalar attributes. Persistence (atomic
JSON save/load, the dirty flag, the revision/undo baseline) all come from
'worQt.document' for free; this class only declares the fields.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.document import Document, ValueField

if TYPE_CHECKING:  # pragma: no cover
  pass


class TextDocument(Document):
  """A single authored text: creation/modified stamps, an author and the
  body content."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  creationDate = ValueField[str]('')  # ISO stamp, set when the doc is new
  modifiedDate = ValueField[str]('')  # ISO stamp, refreshed on every save
  author = ValueField[str]('unknown')  # falls back to 'unknown'
  content = ValueField[str]('')  # the body text from the editor
