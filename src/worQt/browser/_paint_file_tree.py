"""
PaintFileTree subclasses 'AbstractPaintOp' and paints the tree of a
'FileBrowser'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QPainterPath

from ..paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtGui import QPaintEvent

  from ..utils import WPainter
  from ..utils.geom import Rect
  from . import FileBrowser, FileNode as Node

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_ELIDE = Qt.TextElideMode.ElideRight


class PaintFileTree(AbstractPaintOp):
  """
  PaintFileTree subclasses 'AbstractPaintOp' and paints the tree of a
  'FileBrowser' in the area it is given: the root folder's name as a
  header, then a row per file or folder in view, indented by its depth,
  a folder with an arrow telling whether it is open, the selected row
  highlighted and the open file marked.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: FileBrowser

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """
    The 'paint' method paints the header and the rows in view, scrolled
    so the selected row shows.
    """
    browser = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, browser.paddingsColor.fillBrush)
    painter.setClipRect(rect.Q)
    rowHeight = browser.rowHeight
    header = QRectF(rect.left, rect.top, rect.width, rowHeight)
    self._paintHeader(painter, header)
    rows = browser.rows
    browser.followSelection(rect.height)
    for number in range(browser.scrollTop, len(rows)):
      top = rect.top + rowHeight * (number - browser.scrollTop + 1)
      if top > rect.bottom:
        break
      box = QRectF(rect.left, top, rect.width, rowHeight)
      self._paintRow(painter, box, rows[number])
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _paintHeader(self, painter: WPainter, box: QRectF) -> None:
    """The root folder's name, in bold, over a line."""
    browser = self.widget
    painter.fillRect(box, browser.headerColor.fillBrush)
    font = QFont(browser.font)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(browser.headerTextColor.Q)
    textBox = box.adjusted(browser.indent / 2, 0, 0, 0)
    painter.drawText(textBox, _LEFT, browser.rootName)

  def _paintRow(self, painter: WPainter, box: QRectF, node: Node) -> None:
    """One file or folder: its highlight, its arrow and its name."""
    browser = self.widget
    if node.path == browser.selectedPath:
      color = browser.selectionColor if browser.hasFocus() else None
      color = browser.dimSelectionColor if color is None else color
      painter.fillRect(box, color.fillBrush)
    left = box.left() + browser.indent * node.depth
    if node.isDir:
      self._paintArrow(painter, left, box, node.expanded)
    left += browser.indent
    textColor = browser.folderColor if node.isDir else browser.fileColor
    if node.path == browser.markedPath:
      textColor = browser.markedColor
    painter.setFont(browser.font)
    painter.setPen(textColor.Q)
    width = max(box.right() - left, 0)
    metrics = browser.font.metrics
    name = metrics.elidedText(node.name, _ELIDE, int(width))
    textBox = QRectF(left, box.top(), width, box.height())
    painter.drawText(textBox, _LEFT, name)

  def _paintArrow(
      self,
      painter: WPainter,
      left: float,
      box: QRectF,
      isOpen: bool,
  ) -> None:
    """A small triangle: pointing down for an open folder, right for a
    closed one."""
    size = self.widget.indent * 0.6
    x = left + self.widget.indent * 0.5
    y = box.center().y()
    path = QPainterPath()
    if isOpen:
      path.moveTo(x - size / 2, y - size / 4)
      path.lineTo(x + size / 2, y - size / 4)
      path.lineTo(x, y + size / 3)
    else:
      path.moveTo(x - size / 4, y - size / 2)
      path.lineTo(x + size / 3, y)
      path.lineTo(x - size / 4, y + size / 2)
    path.closeSubpath()
    painter.fillPath(path, self.widget.arrowColor.fillBrush)
