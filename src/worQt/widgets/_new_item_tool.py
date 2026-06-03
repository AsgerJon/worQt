"""
NewItemToolPanel is the left-panel editor for the drawing app. Its contents
are bespoke per kind rather than a generic vertex grid: an anchor edits its
coordinates and its applied load by component (and, when it carries a
support, its prescribed displacement), and lists the members attached to it;
a member (an element) just shows the two anchors it connects; dimensions and
angles still use the '(x, y)' vertex fields. The window owns the wiring and
supplies the per-item data; this panel only lays out its sections and shows
or hides them, and reads the edited values back.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
  QVBoxLayout,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QPushButton,
  QListWidget,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ._base_widget import BaseWidget
from ._container import Container
from ._vertex_editor import VertexEditor
from ..cad.draw import KINDS

if TYPE_CHECKING:  # pragma: no cover
  pass

#  The starting per-kind default vertices for the coordinate fields, before
#  any item has been added. Members are not listed: they are drawn between
#  existing anchors, not typed in.
_INITIAL_DEFAULTS = {
  'Anchor': [(0.0, 0.0)],
  'Module': [(0.0, 0.0), (1.0, 0.0)],
  'Dimension': [(0.0, 0.0), (10.0, 0.0)],
  'Angle': [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)],
}


def _number(edit: QLineEdit) -> float:
  """The value typed in 'edit' as a float; empty reads as zero. Raises
  'ValueError' on non-numeric input."""
  text = edit.text().strip()
  return float(text) if text else 0.0


class NewItemToolPanel(BaseWidget):
  """Bespoke per-kind editor for composing, editing and removing an item."""

  #  Private Variables
  __defaults_store__ = None  # per-kind defaults: the most recently used

  #  Public Variables
  built = AttriBox[bool](False)
  vbox = AttriBox[QVBoxLayout]()
  kindLabel = AttriBox[QLabel]('New item', THIS)
  vertexEditor = AttriBox[VertexEditor](THIS)
  supportLabel = AttriBox[QLabel]('', THIS)  # read-only support kind
  loadHost = AttriBox[Container](THIS)  # the Fx / Fy load fields
  loadRow = AttriBox[QHBoxLayout]()
  loadXEdit = AttriBox[QLineEdit]('0', THIS)
  loadYEdit = AttriBox[QLineEdit]('0', THIS)
  dispHost = AttriBox[Container](THIS)  # the dx / dy settlement fields
  dispRow = AttriBox[QHBoxLayout]()
  dispXEdit = AttriBox[QLineEdit]('0', THIS)
  dispYEdit = AttriBox[QLineEdit]('0', THIS)
  infoLabel = AttriBox[QLabel]('', THIS)  # member node summary / hints
  membersList = AttriBox[QListWidget](THIS)  # an anchor's attached members
  addButton = AttriBox[QPushButton]('Add item', THIS)
  deleteButton = AttriBox[QPushButton]('Delete item', THIS)

  def build(self, ) -> None:
    """Assemble the coordinate/load/settlement fields and the buttons."""
    if self.built:
      return
    self.__defaults_store__ = {k: list(v) for k, v in
                               _INITIAL_DEFAULTS.items()}
    self._buildPairRow(self.loadHost, self.loadRow, 'Fx', self.loadXEdit,
                       'Fy', self.loadYEdit)
    self._buildPairRow(self.dispHost, self.dispRow, 'dx', self.dispXEdit,
                       'dy', self.dispYEdit)
    self.infoLabel.setWordWrap(True)
    self.membersList.setMaximumHeight(110)
    self.vbox.addWidget(self.kindLabel)
    self.vbox.addWidget(self.vertexEditor)
    self.vbox.addWidget(self.supportLabel)
    self.vbox.addWidget(self.loadHost)
    self.vbox.addWidget(self.dispHost)
    self.vbox.addWidget(self.infoLabel)
    self.vbox.addWidget(self.membersList)
    self.vbox.addWidget(self.addButton)
    self.deleteButton.setVisible(False)  # only shown while editing an item
    self.vbox.addWidget(self.deleteButton)
    self.vbox.addStretch(1)  # keep the fields top-aligned in the tool window
    self.setLayout(self.vbox)
    self.configureFor(KINDS[0])
    self.built = True

  def _buildPairRow(self, host: Container, row: QHBoxLayout, labelX: str,
                    editX: QLineEdit, labelY: str, editY: QLineEdit) -> None:
    """Lay 'host' out as 'labelX [editX]  labelY [editY]' on one line."""
    row.setContentsMargins(0, 0, 0, 0)
    editX.setMaximumWidth(64)
    editY.setMaximumWidth(64)
    row.addWidget(QLabel(labelX, host))
    row.addWidget(editX)
    row.addWidget(QLabel(labelY, host))
    row.addWidget(editY)
    host.setLayout(row)

  def _show(self, *sections: str) -> None:
    """Show only the named content sections; hide every other one."""
    visible = set(sections)
    self.vertexEditor.setVisible('vertex' in visible)
    self.supportLabel.setVisible('support' in visible)
    self.loadHost.setVisible('load' in visible)
    self.dispHost.setVisible('disp' in visible)
    self.infoLabel.setVisible('info' in visible)
    self.membersList.setVisible('members' in visible)
    self.addButton.setVisible('add' in visible)

  def configureFor(self, kind: str) -> None:
    """
    Set the panel up for creating a new item of 'kind'. Coordinate kinds show
    their vertex fields; a member shows only a hint, since members are drawn
    between two anchors rather than typed in.
    """
    self.kindLabel.setText(kind)
    if kind == 'Member':
      self.infoLabel.setText('Drag between two anchors to add a member.')
      self._show('info')
      return
    vertices = self.__defaults_store__.get(kind, [(0.0, 0.0)])
    self.vertexEditor.configure(len(vertices), False, vertices)
    self._show('vertex', 'add')

  def rememberLast(self, kind: str, vertices: list) -> None:
    """Adopt 'vertices' as the running default for 'kind', after an add."""
    self.__defaults_store__[kind] = [tuple(v) for v in vertices]
    self.vertexEditor.configure(len(vertices), False, vertices)

  def loadItem(self, kind: str, vertices: list) -> None:
    """Fill the coordinate fields with a vertex item's coordinates (edit)."""
    self.kindLabel.setText(kind)
    self.vertexEditor.configure(len(vertices), False, vertices)
    self._show('vertex', 'add')

  def editAnchor(self, anchor: object, members: list) -> None:
    """
    Edit 'anchor': its '(x, y)' coordinates, its read-only support kind, its
    load by component, the settlement components (only when it has a support)
    and the list of members attached to it.
    """
    self.kindLabel.setText('Anchor')
    self.vertexEditor.configure(1, False, [(anchor.x, anchor.y)])
    kind = anchor.supportKind()
    if kind == 'free':
      self.supportLabel.setText('support: none')
    else:
      self.supportLabel.setText('support: %s' % (kind,))
    self.loadXEdit.setText('%g' % anchor.loadX)
    self.loadYEdit.setText('%g' % anchor.loadY)
    self.dispXEdit.setText('%g' % anchor.dispX)
    self.dispYEdit.setText('%g' % anchor.dispY)
    self.membersList.clear()
    for text in members:
      self.membersList.addItem(text)
    sections = ['vertex', 'support', 'load', 'members', 'add']
    if kind != 'free':  # settlement only applies at a supported node
      sections.append('disp')
    self._show(*sections)

  def anchorValues(self, ) -> tuple:
    """
    The edited anchor values '(x, y, loadX, loadY, dispX, dispY)'. Raises
    'ValueError' if any field is not a number.
    """
    (x, y) = self.vertexEditor.vertices()[0]
    return (x, y, _number(self.loadXEdit), _number(self.loadYEdit),
            _number(self.dispXEdit), _number(self.dispYEdit))

  def editMember(self, info: str) -> None:
    """Edit a member (an element): show the two anchors it connects. There
    are no coordinates to edit, so only the delete action applies."""
    self.kindLabel.setText('Member')
    self.infoLabel.setText(info)
    self._show('info')
