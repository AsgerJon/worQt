"""
NewItemToolPanel is the left-panel editor, bespoke per kind. A node edits
its '(x, y)' coordinates plus its boundary-condition state: a Translation
selector (Free / Roller / Pinned) and a 'Charniere' (rotation-release)
checkbox pick one of 6 states, and the fields below swap to that state's SET
quantities (in the locked-in notation):
  - Free   -> 'F' = (Fx, Fy), the applied force.
  - Roller -> 'theta' (locked direction), a SET displacement along theta and
    a SET force across it.
  - Pinned -> the SET displacement '(x, y)' (settlement).
  - rotation: released -> 'Mf' (applied moment); locked -> 'xy' (prescribed
    rotation).
A member just names its two nodes; dimensions and angles use the vertex
grid. The window owns the wiring; this panel lays out the sections, swaps
them by state, and reads the edited values back onto a node.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
  QVBoxLayout,
  QHBoxLayout,
  QGridLayout,
  QLabel,
  QLineEdit,
  QCheckBox,
  QComboBox,
  QPushButton,
  QListWidget,
  QStackedWidget,
  QSizePolicy,
)
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..widgets import BaseWidget
from ..widgets import Container
from ._vertex_editor import VertexEditor
from .draw import KINDS

if TYPE_CHECKING:  # pragma: no cover
  pass

_INITIAL_DEFAULTS = {
  'Node': [(0.0, 0.0)],
  'Module': [(0.0, 0.0), (1.0, 0.0)],
  'Dimension': [(0.0, 0.0), (10.0, 0.0)],
  'Angle': [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)],
}

_TRANS = ('free', 'roller', 'pinned')  # the Translation combo entries


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
  vertexEditor = AttriBox[VertexEditor](THIS)  # Module / Dimension / Angle
  #  node coordinate
  coordHost = AttriBox[Container](THIS)
  coordRow = AttriBox[QHBoxLayout]()
  xEdit = AttriBox[QLineEdit]('0', THIS)
  yEdit = AttriBox[QLineEdit]('0', THIS)
  #  node state selectors
  stateHost = AttriBox[Container](THIS)
  stateRow = AttriBox[QHBoxLayout]()
  transCombo = AttriBox[QComboBox](THIS)  # Free / Roller / Pinned
  charniereCheck = AttriBox[QCheckBox](THIS)  # rotation released?
  #  the per-state fields, stacked so the panel keeps the tallest height
  stateStack = AttriBox[QStackedWidget](THIS)
  #  free state: F = (Fx, Fy)
  freeHost = AttriBox[Container](THIS)
  freeRow = AttriBox[QHBoxLayout]()
  fxEdit = AttriBox[QLineEdit]('0', THIS)
  fyEdit = AttriBox[QLineEdit]('0', THIS)
  #  roller state: theta, set displacement, set force
  rollerHost = AttriBox[Container](THIS)
  rollerGrid = AttriBox[QGridLayout]()
  thetaEdit = AttriBox[QLineEdit]('0', THIS)
  rsetEdit = AttriBox[QLineEdit]('0', THIS)  # rollerSet (disp along theta)
  rloadEdit = AttriBox[QLineEdit]('0', THIS)  # rollerLoad (force across)
  #  pinned state: settlement (x, y)
  pinnedHost = AttriBox[Container](THIS)
  pinnedRow = AttriBox[QHBoxLayout]()
  dxEdit = AttriBox[QLineEdit]('0', THIS)
  dyEdit = AttriBox[QLineEdit]('0', THIS)
  #  rotation value: Mf (released) or xy (locked)
  rotHost = AttriBox[Container](THIS)
  rotRow = AttriBox[QHBoxLayout]()
  rotLabel = AttriBox[QLabel]('Mf', THIS)
  rotEdit = AttriBox[QLineEdit]('0', THIS)
  #  shared
  supportLabel = AttriBox[QLabel]('', THIS)
  infoLabel = AttriBox[QLabel]('', THIS)
  membersList = AttriBox[QListWidget](THIS)
  addButton = AttriBox[QPushButton]('Add item', THIS)
  deleteButton = AttriBox[QPushButton]('Delete item', THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  BUILD    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def build(self, ) -> None:
    """Assemble the coordinate, state-selector and per-state fields."""
    if self.built:
      return
    self.__defaults_store__ = {k: list(v) for k, v in
                               _INITIAL_DEFAULTS.items()}
    self._buildCoordRow()
    self._buildStateRow()
    self._buildFreeRow()
    self._buildRollerRows()
    self._buildPinnedRow()
    self._buildRotRow()
    #  the 3 per-state hosts share one stack -> it sizes to the tallest, so
    #  switching state never squishes the fields or resizes the panel
    for host in (self.freeHost, self.rollerHost, self.pinnedHost):
      self.stateStack.addWidget(host)
    fixedV = QSizePolicy.Policy.Fixed
    pref = QSizePolicy.Policy.Preferred
    for host in (self.coordHost, self.stateHost, self.stateStack,
                 self.rotHost):
      host.setSizePolicy(pref, fixedV)  # keep their natural height
    self.infoLabel.setWordWrap(True)
    self.membersList.setMaximumHeight(90)
    for widget in (self.kindLabel, self.vertexEditor, self.coordHost,
                   self.stateHost, self.stateStack, self.rotHost,
                   self.supportLabel, self.infoLabel, self.membersList,
                   self.addButton):
      self.vbox.addWidget(widget)
    self.deleteButton.setVisible(False)
    self.vbox.addWidget(self.deleteButton)
    self.vbox.addStretch(1)
    self.setLayout(self.vbox)
    self.configureFor(KINDS[0])
    self.built = True

  def _buildCoordRow(self, ) -> None:
    """The node coordinate host: 'x [..]  y [..]'."""
    self.coordRow.setContentsMargins(0, 0, 0, 0)
    self.xEdit.setMaximumWidth(70)
    self.yEdit.setMaximumWidth(70)
    self.coordRow.addWidget(QLabel('x', self.coordHost))
    self.coordRow.addWidget(self.xEdit)
    self.coordRow.addWidget(QLabel('y', self.coordHost))
    self.coordRow.addWidget(self.yEdit)
    self.coordRow.addStretch(1)
    self.coordHost.setLayout(self.coordRow)

  def _buildStateRow(self, ) -> None:
    """The Translation combo and the Charniere checkbox."""
    self.stateRow.setContentsMargins(0, 0, 0, 0)
    self.transCombo.addItems(['Free', 'Roller', 'Pinned'])
    self.transCombo.currentIndexChanged.connect(self._refreshState)
    self.charniereCheck.setText('Charniere')
    self.charniereCheck.setChecked(True)  # released by default
    self.charniereCheck.toggled.connect(self._refreshState)
    self.stateRow.addWidget(self.transCombo)
    self.stateRow.addWidget(self.charniereCheck)
    self.stateRow.addStretch(1)
    self.stateHost.setLayout(self.stateRow)

  def _buildFreeRow(self, ) -> None:
    """The free-state load fields: 'Fx [..]  Fy [..]'."""
    self.freeRow.setContentsMargins(0, 0, 0, 0)
    self.fxEdit.setMaximumWidth(70)
    self.fyEdit.setMaximumWidth(70)
    self.freeRow.addWidget(QLabel('Fx', self.freeHost))
    self.freeRow.addWidget(self.fxEdit)
    self.freeRow.addWidget(QLabel('Fy', self.freeHost))
    self.freeRow.addWidget(self.fyEdit)
    self.freeRow.addStretch(1)
    self.freeHost.setLayout(self.freeRow)

  def _buildRollerRows(self, ) -> None:
    """The roller-state grid: locked direction, settlement, across force."""
    self.rollerGrid.setContentsMargins(0, 0, 0, 0)
    self.rollerGrid.setColumnStretch(2, 1)
    specs = (('theta (deg)', self.thetaEdit), ('set disp', self.rsetEdit),
             ('across F', self.rloadEdit))
    for index, (label, edit) in enumerate(specs):
      edit.setMaximumWidth(70)
      self.rollerGrid.addWidget(QLabel(label, self.rollerHost), index, 0)
      self.rollerGrid.addWidget(edit, index, 1)
    self.rollerHost.setLayout(self.rollerGrid)

  def _buildPinnedRow(self, ) -> None:
    """The pinned-state settlement fields: 'x [..]  y [..]'."""
    self.pinnedRow.setContentsMargins(0, 0, 0, 0)
    self.dxEdit.setMaximumWidth(70)
    self.dyEdit.setMaximumWidth(70)
    self.pinnedRow.addWidget(QLabel('set x', self.pinnedHost))
    self.pinnedRow.addWidget(self.dxEdit)
    self.pinnedRow.addWidget(QLabel('set y', self.pinnedHost))
    self.pinnedRow.addWidget(self.dyEdit)
    self.pinnedRow.addStretch(1)
    self.pinnedHost.setLayout(self.pinnedRow)

  def _buildRotRow(self, ) -> None:
    """The rotation value: 'Mf' when released, 'xy' when locked."""
    self.rotRow.setContentsMargins(0, 0, 0, 0)
    self.rotEdit.setMaximumWidth(70)
    self.rotRow.addWidget(self.rotLabel)
    self.rotRow.addWidget(self.rotEdit)
    self.rotRow.addStretch(1)
    self.rotHost.setLayout(self.rotRow)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  STATE    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _transType(self, ) -> str:
    """The selected translational type: 'free' / 'roller' / 'pinned'."""
    return _TRANS[self.transCombo.currentIndex()]

  def _refreshState(self, *_) -> None:
    """Swap the per-state stack page to match the Translation and Charniere
    selectors, shrink the stack to that page's height (so the shorter states
    leave no gap), and update the read-only support label."""
    trans = self._transType()
    self.stateStack.setCurrentIndex(_TRANS.index(trans))
    page = self.stateStack.currentWidget()
    if page is not None:  # size to the current page, not the tallest one
      self.stateStack.setFixedHeight(page.sizeHint().height())
    released = self.charniereCheck.isChecked()
    self.rotLabel.setText('Mf' if released else 'xy')
    kind = 'fixed' if (trans == 'pinned' and not released) else trans
    self.supportLabel.setText('support: %s' % (kind,))

  def _show(self, *sections: str) -> None:
    """Show only the named content sections; hide every other one."""
    v = set(sections)
    self.vertexEditor.setVisible('vertex' in v)
    self.coordHost.setVisible('coord' in v)
    self.stateHost.setVisible('state' in v)
    self.stateStack.setVisible('state' in v)
    self.supportLabel.setVisible('state' in v)
    self.rotHost.setVisible('state' in v)
    if 'state' in v:
      self._refreshState()
    self.infoLabel.setVisible('info' in v)
    self.membersList.setVisible('members' in v)
    self.addButton.setVisible('add' in v)

  def configureFor(self, kind: str) -> None:
    """Set the panel up for creating a new item of 'kind'."""
    self.kindLabel.setText(kind)
    if kind == 'Member':
      self.infoLabel.setText('Drag between two nodes to add a member.')
      self._show('info')
      return
    if kind == 'Node':
      (x, y) = self.__defaults_store__.get('Node', [(0.0, 0.0)])[0]
      self.xEdit.setText('%g' % x)
      self.yEdit.setText('%g' % y)
      self._resetState()
      self._show('coord', 'state', 'add')
      return
    vertices = self.__defaults_store__.get(kind, [(0.0, 0.0)])
    self.vertexEditor.configure(len(vertices), False, vertices)
    self._show('vertex', 'add')

  def _resetState(self, ) -> None:
    """Reset the BC selectors to a free, released node, values zeroed."""
    self.transCombo.setCurrentIndex(0)  # Free
    self.charniereCheck.setChecked(True)  # released
    for edit in (self.fxEdit, self.fyEdit, self.thetaEdit, self.rsetEdit,
                 self.rloadEdit, self.dxEdit, self.dyEdit, self.rotEdit):
      edit.setText('0')
    self._refreshState()

  def rememberLast(self, kind: str, vertices: list) -> None:
    """Adopt 'vertices' as the running default for 'kind', after an add."""
    self.__defaults_store__[kind] = [tuple(v) for v in vertices]
    if kind == 'Node':
      (x, y) = vertices[0]
      self.xEdit.setText('%g' % x)
      self.yEdit.setText('%g' % y)
    else:
      self.vertexEditor.configure(len(vertices), False, vertices)

  def loadItem(self, kind: str, vertices: list) -> None:
    """Fill the coordinate fields with a vertex item's coordinates (edit)."""
    self.kindLabel.setText(kind)
    self.vertexEditor.configure(len(vertices), False, vertices)
    self._show('vertex', 'add')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NODE <-> PANEL   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def editNode(self, node: object, members: list) -> None:
    """Fill the panel from 'node's coordinates and BC state."""
    self.kindLabel.setText('Node')
    self.xEdit.setText('%g' % node.x)
    self.yEdit.setText('%g' % node.y)
    self.transCombo.setCurrentIndex(_TRANS.index(node.supportType))
    self.charniereCheck.setChecked(True if node.released else False)
    self.fxEdit.setText('%g' % node.loadX)
    self.fyEdit.setText('%g' % node.loadY)
    self.thetaEdit.setText('%g' % node.theta)
    self.rsetEdit.setText('%g' % node.rollerSet)
    self.rloadEdit.setText('%g' % node.rollerLoad)
    self.dxEdit.setText('%g' % node.dispX)
    self.dyEdit.setText('%g' % node.dispY)
    self.rotEdit.setText('%g' % (node.loadMoment if node.released
                                 else node.setRot))
    self.membersList.clear()
    for text in members:
      self.membersList.addItem(text)
    sections = ['coord', 'state', 'add']
    if members:
      sections.append('members')
    self._show(*sections)

  def coords(self, ) -> tuple:
    """The edited '(x, y)' coordinate. Raises 'ValueError' if not numbers."""
    return (_number(self.xEdit), _number(self.yEdit))

  def applyTo(self, node: object) -> None:
    """
    Write the panel's BC state onto 'node', storing only the SET
    quantities the active state uses and zeroing the rest. Raises
    'ValueError' if a value field is not a number.
    """
    trans = self._transType()
    released = self.charniereCheck.isChecked()
    node.supportType = trans
    node.released = True if released else False
    for name in ('loadX', 'loadY', 'dispX', 'dispY', 'theta',
                 'rollerSet', 'rollerLoad', 'setRot', 'loadMoment'):
      setattr(node, name, 0.0)
    if trans == 'free':
      node.loadX = _number(self.fxEdit)
      node.loadY = _number(self.fyEdit)
    elif trans == 'roller':
      node.theta = _number(self.thetaEdit)
      node.rollerSet = _number(self.rsetEdit)
      node.rollerLoad = _number(self.rloadEdit)
    else:  # pinned
      node.dispX = _number(self.dxEdit)
      node.dispY = _number(self.dyEdit)
    if released:
      node.loadMoment = _number(self.rotEdit)
    else:
      node.setRot = _number(self.rotEdit)

  def editMember(self, info: str) -> None:
    """Edit a member (an element): show the two nodes it connects."""
    self.kindLabel.setText('Member')
    self.infoLabel.setText(info)
    self._show('info')
