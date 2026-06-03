"""
JsonHighlighter is a 'QSyntaxHighlighter' that colours JSON tokens in a
text document: keys, string values, numbers, the 'true'/'false'/'null'
keywords and structural punctuation. It needs no worktoy machinery, so it
is a plain 'QSyntaxHighlighter' subclass rather than a 'MixinBase' fusion.
Construct it against a live document, e.g.
'JsonHighlighter(editor.document())'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
  QSyntaxHighlighter,
  QTextCharFormat,
  QColor,
  QFont,
)

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtGui import QTextDocument


class JsonHighlighter(QSyntaxHighlighter):
  """
  Colours JSON tokens in a text document using a One Dark inspired
  palette. Rules are applied in order, so later rules override earlier
  ones on overlap: this lets the 'key' rule reclaim the strings that the
  generic 'string' rule already coloured.
  """

  @staticmethod
  def _format(color: str, bold: bool = False) -> QTextCharFormat:
    """Build a character format with the given foreground colour."""
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
      fmt.setFontWeight(QFont.Weight.Bold)
    return fmt

  def _buildRules(self, ) -> list:
    """The ordered '(pattern, format)' rules; later wins on overlap."""
    string = r'"(?:[^"\\]|\\.)*"'
    return [
      (QRegularExpression(r'[{}\[\],:]'), self._format('#5c6370')),
      (QRegularExpression(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'),
       self._format('#d19a66')),
      (QRegularExpression(r'\b(?:true|false|null)\b'),
       self._format('#c678dd', True)),
      (QRegularExpression(string), self._format('#98c379')),
      (QRegularExpression(string + r'(?=\s*:)'), self._format('#61afef')),
    ]

  def __init__(self, document: QTextDocument = None) -> None:
    """Attach the highlighter to 'document' and compile its rules."""
    super().__init__(document)
    self.__rules__ = self._buildRules()

  def highlightBlock(self, text: str) -> None:
    """Colour one text block by applying every rule across it."""
    for pattern, fmt in self.__rules__:
      matches = pattern.globalMatch(text)
      while matches.hasNext():
        match = matches.next()
        self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
