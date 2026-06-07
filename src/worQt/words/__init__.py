"""
The 'worQt.words' subpackage is the next 'larp': a deliberately small text
editor whose job is to press on the core and surface reusable abstractions
(pluggable document serialization, a document-window controller, the
dirty/title chain, real 'MainFile' use, single-field/widget binding). The
example is the vehicle; the abstractions it forces out are the product.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._section import Section
from ._text_document import TextDocument
from ._text_window import TextWindow

__all__ = [
  'Section',
  'TextDocument',
  'TextWindow',
]
