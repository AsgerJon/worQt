"""
DiagramsWindow subclasses 'MainWindow' and draws the section force
diagrams of a plane frame, edited with the mouse and a panel.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field

from ....windows import MainWindow
from ...gui import TestStatus
from .. import Frame, LineLoad, Member, Node, PointLoad, PointMoment
from .. import Support
from . import DiagramsPanel, DiagramsToolBar, FrameView

#  The diagrams the toolbar's buttons choose, in their order
_KINDS = ('N', 'V', 'M', 'shape')


class DiagramsWindow(MainWindow):
  """
  DiagramsWindow subclasses 'MainWindow' and draws the section force
  diagrams, 'snitkraftkurver', of a plane frame: the 'toolBar' above,
  the 'panel' of the part selected, or of the frame and its reactions,
  on the left, the frame itself, 'frameView', and the 'status' along the
  bottom, saying how indeterminate the frame is and its greatest
  forces. It is reckoned anew at every change, at once.

  It opens on a portal, fixed at its left foot and pinned at its right,
  under a line load on its beam and wind at its top. 'Add member' runs a
  member 3 m from the node selected, to a new node, selected, to be
  dragged where it goes, or joins the two nodes selected, Ctrl and a
  click; 'Add support' pins the node selected; 'Add point load', 'Add
  line load' and 'Add moment' load the member selected; 'Remove' takes
  away what is selected. 'N', 'V', 'M' and 'Shape' choose the diagram
  shown.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __app_name__ = 'Section forces'
  __start_size__ = 1500, 900
  __new_reach__ = 3.0  # m: a new member's length
  __new_loads__ = (10.0, 5.0, 10.0)  # kN, kN/m and kNm

  #  Public Variables
  toolBar = AttriBox[DiagramsToolBar](THIS)
  panel = AttriBox[DiagramsPanel](THIS)
  frameView = AttriBox[FrameView](THIS)
  status = AttriBox[TestStatus](THIS)

  #  Virtual Variables
  frame: Field[Frame] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @frame.GET
  def _getFrame(self, ) -> Frame:
    """The 'frame' getter returns the frame shown."""
    return self.frameView.frame

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """The 'initUI' method lays the window out and sizes it."""
    layout = self.baseLayout
    layout.addWidget(self.toolBar, 0, 0, 1, 2)
    layout.addWidget(self.panel, 1, 0)
    layout.addWidget(self.frameView, 1, 1)
    layout.addWidget(self.status, 2, 0, 1, 2)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)
    layout.setRowStretch(1, 1)
    layout.setHorizontalSpacing(0)
    layout.setVerticalSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    MainWindow.initUI(self)
    self.setWindowTitle(self.__app_name__)
    self.resize(*self.__start_size__)
    self.frameView.setFocus()
    self.setKind('M')
    self.refresh()

  def initLogic(self, ) -> None:
    """The 'initLogic' method wires the buttons and the edits."""
    bar = self.toolBar
    bar.memberButton.clicked.connect(self.addMember)
    bar.supportButton.clicked.connect(self.addSupport)
    bar.pointButton.clicked.connect(self.addPointLoad)
    bar.lineButton.clicked.connect(self.addLineLoad)
    bar.momentButton.clicked.connect(self.addMoment)
    bar.removeButton.clicked.connect(self.frameView.removeSelected)
    for button, kind in zip(bar.diagramButtons(), _KINDS):
      button.clicked.connect(self._kindSetter(kind))
    self.frameView.frameEdited.connect(self.setFrame)
    self.frameView.selectionChanged.connect(self.selected)
    self.panel.frameEdited.connect(self.setFrame)
    self.mainMenuBar.fileMenu.exitAction.triggered.connect(self.close)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setFrame(self, frame: Frame) -> None:
    """The 'setFrame' method shows 'frame', reckoned."""
    if frame is not self.frameView.frame:
      self.frameView.frame = frame
    self.refresh()

  def setKind(self, kind: str) -> None:
    """The 'setKind' method shows the diagram 'kind', its button lit."""
    self.frameView.kind = kind
    for button, other in zip(self.toolBar.diagramButtons(), _KINDS):
      button.checked = other == kind
      button.update()

  def selected(self, part: tuple[str, int] | None) -> None:
    """The 'selected' method shows the part selected in the panel."""
    self.refresh()

  def addMember(self, ) -> None:
    """The 'addMember' method joins the two nodes selected by a member,
    or runs one 3 m from the node selected, or the last, to a new node,
    to the right, else up, left or down, where there is room;
    selected."""
    view, frame = self.frameView, self.frame
    nodes = view.selectedOf('node')
    if len(nodes) >= 2:
      member = Member(nodes[-2], nodes[-1], *self._stiffness(), False,
                      False)
      return self._edited(lambda: frame.withMembers(*frame.members,
                                                    member),
                          ('member', len(frame.members)))
    start = nodes[-1] if nodes else len(frame.nodes) - 1
    if start < 0:
      frame = frame.withNodes(Node(0.0, 0.0))
      start = 0
    x, y = frame.nodes[start]
    reach = self.__new_reach__
    for dx, dy in ((reach, 0.0), (0.0, reach), (-reach, 0.0),
                   (0.0, -reach)):
      spot = Node(x + dx, y + dy)
      if all(abs(n.x - spot.x) + abs(n.y - spot.y) > 1e-6
             for n in frame.nodes):
        break
    else:
      return
    grown = frame.withNodes(*frame.nodes, spot)
    member = Member(start, len(frame.nodes), *self._stiffness(), False,
                    False)
    self._edited(lambda: grown.withMembers(*grown.members, member),
                 ('node', len(frame.nodes)))

  def addSupport(self, ) -> None:
    """The 'addSupport' method pins the node selected, or the lowest
    node not held, selected."""
    frame = self.frame
    chosen = self.frameView.selectedOf('node')
    free = [i for i in range(len(frame.nodes))
            if frame.supportAt(i) is None]
    if chosen and chosen[-1] in free:
      node = chosen[-1]
    elif free:
      _, node = min((frame.nodes[i].y, i) for i in free)
    else:
      return
    self._edited(lambda: frame.withSupports(*frame.supports,
                                            Support(node, 'pin')),
                 ('support', len(frame.supports)))

  def addPointLoad(self, ) -> None:
    """The 'addPointLoad' method pushes down 10 kN at the middle of the
    member selected, or of the load selected, or the first, selected."""
    member = self._chosenMember()
    if member is None:
      return
    frame = self.frame
    load = PointLoad(member, frame.length(member) / 2,
                     self.__new_loads__[0], 0.0)
    self._added(load)

  def addLineLoad(self, ) -> None:
    """The 'addLineLoad' method lays 5 kN/m down along the whole member
    selected, or the first, selected."""
    member = self._chosenMember()
    if member is None:
      return
    q = self.__new_loads__[1]
    self._added(LineLoad(member, 0.0, self.frame.length(member), q, q,
                         'down'))

  def addMoment(self, ) -> None:
    """The 'addMoment' method turns the middle of the member selected,
    or the first, 10 kNm anticlockwise, selected."""
    member = self._chosenMember()
    if member is None:
      return
    self._added(PointMoment(member, self.frame.length(member) / 2,
                            self.__new_loads__[2]))

  def refresh(self, ) -> None:
    """The 'refresh' method greys out what cannot be done now, shows the
    panel, and says how indeterminate the frame is and its greatest
    forces."""
    bar, view = self.toolBar, self.frameView
    loadable = bool(self.frame.members)
    for button in (bar.pointButton, bar.lineButton, bar.momentButton):
      button.setEnabled(loadable)
      button.update()
    bar.removeButton.setEnabled(bool(view.selection))
    bar.removeButton.update()
    self.panel.showAnalysis(view.analysis, view.selected)
    self.status.showState(*self.statusOf())
    view.update()

  def statusOf(self, ) -> tuple[str, str, str]:
    """The 'statusOf' method says how indeterminate the frame is, and
    its greatest forces."""
    analysis, frame = self.frameView.analysis, self.frame
    if analysis.held:
      return 'paused', 'Not held', analysis.held
    count = frame.indeterminacy()
    text = 'Determinate' if count == 0 else 'Indeterminate %d×' % count
    parts = []
    for kind, unit in (('M', 'kNm'), ('V', 'kN'), ('N', 'kN')):
      value, member, s = analysis.most(kind)
      parts.append('max |%s| %.2f %s in M%d' % (kind, abs(value), unit,
                                                member + 1))
    return 'idle', text, ' · '.join(parts)

  def _kindSetter(self, kind: str) -> object:
    """What shows the diagram 'kind' when its button is clicked."""

    def setter(*_) -> None:
      self.setKind(kind)

    return setter

  def _stiffness(self, ) -> tuple[float, float]:
    """The stiffness of a new member: as the first member, or the
    frame's own."""
    members = self.frame.members
    if members:
      return members[0].EI, members[0].EA
    return 1e4, 1e6

  def _chosenMember(self, ) -> int | None:
    """The member selected last, or the member of the load selected
    last, or the first, or 'None' if there are none."""
    view = self.frameView
    for kind, index in view.selection[::-1]:
      if kind == 'member':
        return index
      if kind == 'load':
        return self.frame.loads[index].member
    return 0 if self.frame.members else None

  def _added(self, load: tuple) -> None:
    """Shows the frame with 'load' added, selected."""
    frame = self.frame
    self._edited(lambda: frame.withLoads(*frame.loads, load),
                 ('load', len(frame.loads)))

  def _edited(self, make: object, part: tuple[str, int]) -> None:
    """Shows the frame 'make' returns, with 'part' selected; or says why
    it cannot be."""
    try:
      frame = make()
    except ValueError as exception:
      words = str(exception)
      return self.panel.showNote('%s%s.' % (words[:1].upper(), words[1:]))
    self.frameView.frame = frame
    self.frameView.select(part)
    self.refresh()
