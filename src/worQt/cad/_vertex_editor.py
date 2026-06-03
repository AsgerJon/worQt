"""
VertexEditor presents a vertex as a labelled row, 'v1   x [..] y [..]', and
keeps a fixed baseline of rows on screen so the controls below it never
shift when the item kind changes. 'configure' sets how many leading rows are
*active* for the chosen kind: an 'Anchor' activates one, a 'Module' or
'Dimension' two, an 'Angle' three. Inactive rows stay visible but greyed out
(disabled) rather than removed, so the layout height is stable. 'vertices'
reads back only the active rows as '(x, y)' float pairs.

The fixed widgets are boxed in 'AttriBox'; the per-vertex rows are created
at run time (a 'QApplication' already exists by then) and held in a list so
they are not collected.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
  QWidget,
  QVBoxLayout,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QPushButton,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..widgets import BaseWidget
from ..widgets import Container

if TYPE_CHECKING:  # pragma: no cover
  pass


class VertexEditor(BaseWidget):
  """A stack of labelled '(x, y)' rows; inactive ones are greyed, not hidden."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __base_rows__ = 3  # rows always present, so the layout height is stable

  #  Private Variables
  __rows__ = None  # list of (host, indexLabel, xEdit, yEdit)
  __defaults__ = None  # list of (x, y) defaults, one per row
  __active__ = 0  # number of leading rows that are enabled / read back

  #  Public Variables
  built = AttriBox[bool](False)
  vbox = AttriBox[QVBoxLayout]()
  rowsHost = AttriBox[Container](THIS)
  rowsLayout = AttriBox[QVBoxLayout]()
  buttonHost = AttriBox[Container](THIS)
  buttonRow = AttriBox[QHBoxLayout]()
  addButton = AttriBox[QPushButton]('+ vertex', THIS)
  removeButton = AttriBox[QPushButton]('- vertex', THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def build(self, ) -> None:
    """Assemble the rows host and the add/remove buttons. Idempotent."""
    if self.built:
      return
    self.vbox.setContentsMargins(0, 0, 0, 0)
    self.rowsLayout.setContentsMargins(0, 0, 0, 0)
    self.rowsHost.setLayout(self.rowsLayout)
    self.vbox.addWidget(self.rowsHost)
    self.buttonRow.setContentsMargins(0, 0, 0, 0)
    self.buttonRow.addWidget(self.addButton)
    self.buttonRow.addWidget(self.removeButton)
    self.buttonHost.setLayout(self.buttonRow)
    self.vbox.addWidget(self.buttonHost)
    self.setLayout(self.vbox)
    self.addButton.clicked.connect(self._onAddVertex)
    self.removeButton.clicked.connect(self._onRemoveVertex)
    self.__rows__ = []
    self.__defaults__ = []
    self.__active__ = 0
    self.built = True

  def configure(self, active: int, variable: bool,
                defaults: list = None) -> None:
    """
    Activate 'active' leading rows, prefilled from 'defaults' (a list of
    '(x, y)' pairs). The total row count is held at 'max(baseline, active)'
    so fewer-input kinds grey out the surplus rather than removing it. When
    'variable', reveal the add and remove buttons.
    """
    self.build()
    self.__defaults__ = list(defaults) if defaults else []
    total = max(self.__base_rows__, active)
    while len(self.__rows__) > total:
      self._removeRow()
    while len(self.__rows__) < total:
      self._addRow(self._defaultAt(len(self.__rows__)))
    for index, (_, _, xEdit, yEdit) in enumerate(self.__rows__):
      defaultX, defaultY = self._defaultAt(index)
      xEdit.setText('%g' % defaultX)
      yEdit.setText('%g' % defaultY)
    self._setActive(active)
    self.addButton.setVisible(variable)
    self.removeButton.setVisible(variable)

  def vertices(self, ) -> list:
    """The '(x, y)' float pair from every active row; raises on bad input."""
    out = []
    for _, _, xEdit, yEdit in (self.__rows__ or [])[:self.__active__]:
      try:
        out.append((float(xEdit.text()), float(yEdit.text())))
      except ValueError as valueError:
        info = 'Each coordinate must be a number'
        raise ValueError(info) from valueError
    return out

  def clear(self, ) -> None:
    """Reset the active rows to their default coordinates."""
    for index in range(self.__active__):
      _, _, xEdit, yEdit = self.__rows__[index]
      defaultX, defaultY = self._defaultAt(index)
      xEdit.setText('%g' % defaultX)
      yEdit.setText('%g' % defaultY)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HELPERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _setActive(self, count: int) -> None:
    """Enable the first 'count' rows; grey out (disable) the rest."""
    self.__active__ = count
    for index, (host, _, _, _) in enumerate(self.__rows__):
      host.setEnabled(index < count)

  def _defaultAt(self, index: int) -> tuple:
    """The default '(x, y)' for row 'index', or the origin if unset."""
    if self.__defaults__ and index < len(self.__defaults__):
      return self.__defaults__[index]
    return (0.0, 0.0)

  def _addRow(self, default: tuple) -> None:
    """Append one labelled '(x, y)' line-edit row prefilled with 'default'."""
    host = QWidget(self.rowsHost)
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    indexLabel = QLabel('', host)
    xEdit = QLineEdit('%g' % default[0], host)
    yEdit = QLineEdit('%g' % default[1], host)
    row.addWidget(indexLabel)
    row.addWidget(QLabel('x', host))
    row.addWidget(xEdit)
    row.addWidget(QLabel('y', host))
    row.addWidget(yEdit)
    host.setLayout(row)
    self.rowsLayout.addWidget(host)
    self.__rows__.append((host, indexLabel, xEdit, yEdit))
    self._renumber()

  def _removeRow(self, ) -> None:
    """Drop the last vertex row."""
    if not self.__rows__:
      return
    host, _, _, _ = self.__rows__.pop()
    self.rowsLayout.removeWidget(host)
    host.setParent(None)
    host.deleteLater()
    self._renumber()

  def _renumber(self, ) -> None:
    """Relabel rows 'v1', 'v2', ... after any add or remove."""
    for index, (_, indexLabel, _, _) in enumerate(self.__rows__):
      indexLabel.setText('v%d' % (index + 1,))

  def _onAddVertex(self, *_) -> None:
    """Add an active vertex row at the origin (variable kinds only)."""
    self._addRow((0.0, 0.0))
    self._setActive(self.__active__ + 1)

  def _onRemoveVertex(self, *_) -> None:
    """Remove the last vertex row, never below the baseline."""
    if self.__active__ > self.__base_rows__:
      self._removeRow()
      self._setActive(self.__active__ - 1)
