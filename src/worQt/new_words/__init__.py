"""
The 'worQt.new_words' package is a minimal text editor whose persistence
rides entirely on 'worQt.document'. A 'TextDocument' holds four scalar
fields - 'creationDate', 'modifiedDate', 'author' (default 'unknown') and
'content' - and 'TextWindow' edits them with a 'QTextEdit' plus a few
'QLineEdit's, saving and loading through the document's atomic JSON I/O.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._text_document import TextDocument
from ._text_window import TextWindow
from ._app import NewWordsApp, main

__all__ = [
  'TextDocument',
  'TextWindow',
  'NewWordsApp',
  'main',
]
