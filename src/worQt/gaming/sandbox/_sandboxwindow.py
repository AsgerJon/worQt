"""
SandboxWindow shows a world through its avatar's eyes and hands the
avatar the player's keys and mouse; E opens the GUI. It knows nothing of
what is in the world.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QMainWindow

from worQt.phys._poke import hitOf
from worQt.phys._vectors import matrixOf

from ._avatar import TILT, TURN
from ._gui import GUI
from ._pointer import Pointer
from ._speaker import Speaker
from ._viewport import Viewport

#  The keys the avatar takes, by the names it knows them by; how often
#  the window draws, ms.
KEYS = {Qt.Key.Key_W: 'w', Qt.Key.Key_A: 'a', Qt.Key.Key_S: 's',
        Qt.Key.Key_D: 'd', Qt.Key.Key_Space: 'space',
        Qt.Key.Key_Shift: 'shift', Qt.Key.Key_Control: 'ctrl'}
TICK = 16
#  The keys that take a hotbar slot into the hands, by slot; a wheel's
#  notch, in the wheel's own units.
SLOT_KEYS = {getattr(Qt.Key, 'Key_%d' % (k + 1)): k for k in range(9)}
NOTCH = 120
#  How loud the sound is (nought to one), the ambience's pad; how far
#  off a vehicle sounds a quarter as loud as riding it, m (half at half
#  that).
LOUDNESS, PAD = 0.8, 1.0
HEARD_AT = 8.0
#  The mouse's buttons, by the names a tool knows them by.
BUTTONS = {Qt.MouseButton.LeftButton: 'left',
           Qt.MouseButton.RightButton: 'right'}
#  The views Tab goes through (user, 2026-11-16: "have the TAB button
#  changes view between first person and chase-third person", then "we
#  also need second person like in minecraft"): through the avatar's
#  eyes, from behind it, from before it looking back at it. Seen from
#  outside: how far from the avatar's eyes and how far over them the
#  view is, m; how far short of what stands between it stops, and how
#  near the eyes at most, m.
VIEWS = ('eyes', 'behind', 'before')
CHASE, CHASE_OVER = 4.0, 0.8
CHASE_GAP, CHASE_LEAST = 0.25, 0.4
#  Seen from outside, the avatar not moving itself ('Avatar.propelled';
#  user, 2026-11-16: "whilst not moving in third person moving the mouse
#  should not turn the player to pan around", "if the player is not
#  moving under his owner propulsion, the mouse should orbit. So orbit
#  should happen in the train"), the mouse swings the view round it
#  ('orbit'); moving itself, the mouse turns it and the view swings back
#  to its place this fast, a second.
RETURN = 5.0
#  How far over the seat of a vehicle near enough to board its prompt
#  floats, m (user, 2026-11-16: "a floating key_E button should appear
#  with a prompt like 'board'").
PROMPT_OVER = 1.2
#  A lever ('FourthPeep') is used from no further than this from the
#  avatar's eyes, m; the one looked at is the nearest whose knob lies no
#  further than this from the line through the view's middle, m; its
#  prompt floats this far over its knob, m.
PEEP_REACH, PEEP_AIM, PEEP_OVER = 2.5, 0.2, 0.15


class SandboxWindow(QMainWindow):
  """
  SandboxWindow shows a world through the eyes of an avatar in it (both
  from 'made', a call returning a world made anew and an avatar
  entered: 'world', 'avatar'; again on 'Reset world'), through its
  'viewport', the world's status along the bottom. A click into the
  view takes the mouse ('pointer') to look round with, Esc lets it go;
  the keys in 'KEYS' held go to the avatar, and every key and the mouse
  are let go when the window loses the focus. Looking round, the mouse's
  buttons go to the tool in the avatar's hands, the wheel too (else it
  scrolls the hotbar), keys 1 to 9 take a hotbar slot. Tab goes through
  the 'VIEWS' ('seen'): the avatar's eyes, from behind it, from before
  it (its figure drawn, wearing its skin; no cross: the middle is not
  where it aims); seen from outside while the avatar does not move
  itself (standing, or riding: 'propelled'), the mouse swings the view
  round it ('orbit', yaw and pitch from the view's place) and does not
  turn it; moving itself, the mouse turns it and the view swings
  back.
  E uses the lever ('FourthPeep') the view's middle is on within reach
  ('looked': a prompt floats over its knob, 'E Pull brake'); else E
  opens the
  'gui' over the view (the mouse let go), its items ('items') spawned
  before the avatar's eyes, or in a vehicle the vehicle's page; near a
  vehicle on foot E boards it instead (a prompt floats over it, 'E
  Board' and its name), Shift riding leaves it; E closes
  the gui back to looking round. The sound ('speaker', a process of its
  own) hears the wind, the vehicles, the gun. Shown,
  it starts the world; closed, it stops it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, made: object, items: tuple) -> None:
    QMainWindow.__init__(self)
    self.made, self.held = made, set()
    self.seen, self.orbit = 0, (0.0, 0.0)
    self.looked, self._knob = None, None
    self.world, self.avatar = made()
    self._wheel, self._ticked = 0, time.perf_counter()
    self.setWindowTitle('Sandbox')
    self.viewport = Viewport()
    self.setCentralWidget(self.viewport)
    self.viewport.quick.installEventFilter(self)
    self.pointer = Pointer(self.viewport.quick)
    self.gui = GUI(items, self.viewport)
    self.gui.picked.connect(self._spawned)
    self.gui.closed.connect(self._guiClosed)
    self.gui.respawnAsked.connect(self._respawned)
    self.gui.resetAsked.connect(self._reset)
    self.gui.leaveAsked.connect(self._left)
    self.speaker, self._counted, self._shots = Speaker(), {}, [0, 0]
    self.status = QLabel()
    self.statusBar().addWidget(self.status, 1)
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.tick)
    application = QGuiApplication.instance()
    application.focusWindowChanged.connect(self._focusMoved)
    application.applicationStateChanged.connect(self._stateMoved)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: object) -> None:
    """Shown the first time, the world starts and the window draws it."""
    if not self.timer.isActive():
      self.world.start()
      self.speaker.start()
      self.timer.start(TICK)
    QMainWindow.showEvent(self, event)

  def closeEvent(self, event: object) -> None:
    """Closed, the window stops drawing and the world stops."""
    self.timer.stop()
    self.world.stop()
    self.speaker.close()
    QMainWindow.closeEvent(self, event)

  def eventFilter(self, watched: object, event: object) -> bool:
    """Takes the keys and the mouse from the viewport's scene window."""
    if watched is not self.viewport.quick:
      return False
    kind = event.type()
    if kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease) and (
        not self._focused()):
      self._letGo()
      return False
    if self.gui.open:
      return self._menuEvent(kind, event)
    if kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
      self.pointer.letGo()
      return True
    if kind == QEvent.Type.KeyPress and not event.isAutoRepeat():
      if event.key() == Qt.Key.Key_E:
        if self.looked is not None:
          self.looked.used()
          return True
        avatar = self.avatar
        if avatar.riding is None and avatar.nearby() is not None:
          avatar.pressed('e')
          return True
        self._letGo()
        self.gui.opened(avatar.riding, self.world.snapshot()[1])
        return True
      if event.key() in SLOT_KEYS:
        self.avatar.hotbar.select(SLOT_KEYS[event.key()])
        return True
      if event.key() == Qt.Key.Key_Tab:
        self.seen, self.orbit = (self.seen + 1) % len(VIEWS), (0.0, 0.0)
        return True
    if kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
      name = KEYS.get(event.key())
      if name is None or event.isAutoRepeat():
        return False
      if kind == QEvent.Type.KeyPress:
        self.held.add(name)
        self.avatar.pressed(name)
      else:
        self.held.discard(name)
      self.avatar.held = frozenset(self.held)
      return True
    if kind == QEvent.Type.MouseButtonPress and not self.pointer.taken:
      if event.button() == Qt.MouseButton.LeftButton:
        self.pointer.take()
        return True
    elif kind in (QEvent.Type.MouseButtonPress,
                  QEvent.Type.MouseButtonRelease):
      return self._clicked(event)
    elif kind == QEvent.Type.Wheel and self.pointer.taken:
      self._wheeled(event.angleDelta().y())
      return True
    elif kind == QEvent.Type.MouseMove:
      self.pointer.movedTo(event.globalPosition(), event.position())
    elif kind == QEvent.Type.FocusOut:
      self._letGo()
    elif kind == QEvent.Type.Leave:
      self.pointer.forget()
    return False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def tick(self, ) -> None:
    """The 'tick' method turns the avatar's head as the mouse moved and
    draws the world as its last step left it, seen through the avatar's
    eyes."""
    right, down = self.pointer.moved()
    still = self.seen > 0 and not self.avatar.propelled()
    if right or down:
      if still:
        yaw, pitch = self.orbit
        self.orbit = (yaw - TURN * right, pitch - TURN * down)
      else:
        self.avatar.turned(right, down)
    assembly, states, _ = self.world.snapshot()
    problems = '    '.join(self.viewport.problems)
    self.status.setText('  %s%s' % (self.world.statusText(), (
      '    the view: %s' % problems) if problems else ''))
    if self.avatar.index is None or self.avatar.index >= len(states):
      return
    now = time.perf_counter()
    seconds, self._ticked = min(0.1, now - self._ticked), now
    self.viewport.debugShown(
      '%.0f fps\nphysics: %.1f ms a step, %.1f s in%s' % (
        self.viewport.fps, 1000.0 * self.world.took, self.world.time,
        '' if self.speaker.trouble is None else '\nno sound: %s' % (
          self.speaker.trouble)),
      self.world.warningText())
    me = states[self.avatar.index]
    eye, forward, up = self.avatar.viewed(me, seconds)
    hotbar = self.avatar.hotbar
    if self.seen > 0:
      if not still:
        share = max(0.0, 1.0 - RETURN * seconds)
        self.orbit = (share * self.orbit[0], share * self.orbit[1])
      forward = self._orbited()
      camera = self._chasedFrom(eye, forward, up)
      soles, turn, angles = self.avatar.posed(me)
      self.viewport.figureShown(self.avatar.skin, self.avatar.scale(),
                                soles, turn, angles,
                                hotbar.tool() is not None)
    else:
      camera = eye
      self.viewport.figureHidden()
    self.viewport.shown(self.world, camera, forward, self.pointer.taken,
                        up, self.seen == 0)
    self._peeped(assembly, states, eye, camera, forward)
    self._prompted(states)
    self.viewport.hotbarShown(hotbar.names(), hotbar.icons(),
                              hotbar.selected)
    tool = hotbar.tool()
    self.viewport.inHand(tool)
    self.viewport.glowShown(tool is not None and tool.held is not None)
    self._heard(states, tool)
    right, up = self.avatar.gait.carried()
    self.viewport.handsMoved((right, up, self.avatar.thrust(tool, now)))
    self.viewport.marked(None if tool is None else tool.pointed,
                         None if tool is None else tool.held)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _peeped(self, assembly: object, states: tuple, eye: tuple,
              camera: tuple, forward: tuple) -> None:
    """Draws the world's levers ('FourthPeep') and notes the one the
    view's middle is on ('looked', its knob kept): within 'PEEP_REACH' of
    the avatar's 'eye', its knob within 'PEEP_AIM' of the line from
    'camera' along 'forward', the nearest along it (none while the menu
    is open)."""
    handles, self.looked, best = [], None, math.inf
    for peep in self.world.peeps:
      base, turn, knob = peep.handleOf(assembly, states)
      handles.append((base, turn, peep.length))
      if self.gui.open or math.dist(knob, eye) > PEEP_REACH:
        continue
      gap = [k - c for k, c in zip(knob, camera)]
      along = sum(g * f for g, f in zip(gap, forward))
      off = math.sqrt(max(0.0, sum(g * g for g in gap) - along * along))
      if 0.0 < along < best and off <= PEEP_AIM:
        best, self.looked, self._knob = along, peep, knob
    self.viewport.peepsShown(handles)

  def _prompted(self, states: tuple) -> None:
    """Floats a prompt: over the lever looked at ('PEEP_OVER' m over its
    knob: what E does with it), else over the vehicle E would board now
    ('PROMPT_OVER' m over its seat, along its up; on foot, the menu
    shut); else takes it away."""
    if self.looked is not None:
      knob = self._knob
      self.viewport.promptShown((knob[0], knob[1], knob[2] + PEEP_OVER),
                                'E', self.looked.prompt())
      return
    vehicle = None
    if self.avatar.riding is None and not self.gui.open:
      vehicle = self.avatar.nearby()
    if vehicle is None:
      self.viewport.promptHidden()
      return
    seat = vehicle.seatOf(states).place
    m = matrixOf(states[vehicle.frame].turn)
    place = tuple(seat[i] + PROMPT_OVER * m[i][2] for i in range(3))
    self.viewport.promptShown(place, 'E', 'Board %s' % vehicle.name)

  def _orbited(self, ) -> tuple:
    """Returns the way the view looks seen from outside: along a look
    swung from the avatar's by 'orbit' as the mouse would turn its head
    (yaw and pitch added, the pitch kept within 'TILT', the orbit held
    there; user, 2026-11-16: in the view from before, mouse up first
    swung it down, under the avatar's eyes), from behind along it, from
    before back against it."""
    avatar = self.avatar
    swung = min(TILT, max(-TILT, avatar.pitch + self.orbit[1]))
    self.orbit = (self.orbit[0], swung - avatar.pitch)
    yaw = avatar.yaw + self.orbit[0]
    if VIEWS[self.seen] == 'before':
      return avatar.looking(yaw + math.pi, -swung)
    return avatar.looking(yaw, swung)

  def _chasedFrom(self, eye: tuple, forward: tuple, up: tuple) -> tuple:
    """Returns where the avatar is seen from outside, its eyes at 'eye',
    the view looking along 'forward', 'up' its way up: 'CHASE' m back
    from the eyes along it and 'CHASE_OVER' over them, or, should a body
    of the world stand between (but the avatar and the vehicle it
    rides), 'CHASE_GAP' m short of it (no nearer than
    'CHASE_LEAST')."""
    back = tuple(CHASE_OVER * u - CHASE * f for f, u in zip(forward, up))
    far = math.sqrt(sum(b * b for b in back))
    assembly, states, _ = self.world.snapshot()
    riding = self.avatar.riding
    passed = (self.avatar.index,) + (() if riding is None
                                     else tuple(riding.bodies))
    hit = hitOf(assembly, states, eye, back, passed)
    reach = far
    if hit is not None:
      reach = max(CHASE_LEAST, min(far, math.dist(hit[1], eye)
                                   - CHASE_GAP))
    return tuple(e + b * reach / far for e, b in zip(eye, back))

  def _clicked(self, event: object) -> bool:
    """Hands a mouse button pressed or let go, looking round, to the tool
    in the avatar's hands; tells whether it was taken."""
    name, tool = BUTTONS.get(event.button()), self.avatar.hotbar.tool()
    if name is None or not self.pointer.taken:
      return False
    if tool is not None:
      if event.type() == QEvent.Type.MouseButtonPress:
        tool.pressed(name)
      else:
        tool.released(name)
    return True

  def _wheeled(self, turned: int) -> None:
    """Hands the wheel's whole notches to the tool in hand, or, should it
    not take them, scrolls the hotbar (a notch toward the player, the
    next slot)."""
    self._wheel += turned
    notches = int(self._wheel / NOTCH)
    if notches == 0:
      return
    self._wheel -= notches * NOTCH
    tool = self.avatar.hotbar.tool()
    if tool is None or not tool.wheeled(float(notches)):
      self.avatar.hotbar.scrolled(-notches)

  def _heard(self, states: tuple, tool: object) -> None:
    """Tells the sound what is going on: the wind (more the faster the
    avatar goes), the loudest vehicle as heard here (riding it: all of
    it; else less with the distance), the gun's hum, its yeets and
    punts."""
    avatar = self.avatar
    me = states[avatar.index]
    wind = min(1.0, 0.3 + math.sqrt(sum(v * v for v in me.velocity))
               / 40.0)
    gain, rail = 0.0, (0.0, 1.0, 0.0)
    for vehicle in self.world.vehicles:
      sound = vehicle.rumble(states)
      if sound is None:
        continue
      gap = math.dist(me.place, states[vehicle.frame].place)
      heard = 1.0 if vehicle is avatar.riding else 1.0 / (
        1.0 + (gap / HEARD_AT) ** 2)
      if heard > gain:
        gain, rail = heard, sound
    hum = 0
    if tool is not None:
      hum = tool.humming
      last = self._counted.get(id(tool), (tool.yeets, tool.punts))
      self._shots[0] += max(0, tool.yeets - last[0])
      self._shots[1] += max(0, tool.punts - last[1])
      self._counted[id(tool)] = (tool.yeets, tool.punts)
    speed, load, flange = rail
    self.speaker.heard((LOUDNESS, wind, speed, gain, load, flange, hum,
                        self._shots[0], self._shots[1], PAD))

  def _left(self, ) -> None:
    """Has the avatar leave its vehicle."""
    self.avatar.leave()

  def _respawned(self, ) -> None:
    """Sets the avatar back where it entered."""
    self.avatar.respawned()

  def _reset(self, ) -> None:
    """Makes the world anew ('made': the old one stopped, the new one
    started, a new avatar entered in it)."""
    self._letGo()
    self.world.stop()
    self.world, self.avatar = self.made()
    self.world.start()

  def _spawned(self, item: object) -> None:
    """Spawns 'item' before the avatar's eyes."""
    item.spawned(self.world, self.avatar.front())

  def _menuEvent(self, kind: object, event: object) -> bool:
    """Takes a key or the mouse while the GUI is open: E shuts it back
    to looking round, Esc shuts it leaving the mouse free, other keys
    are nobody's; the mouse is the menu's (drawn in the scene)."""
    if kind == QEvent.Type.KeyPress and not event.isAutoRepeat():
      if event.key() in (Qt.Key.Key_E, Qt.Key.Key_Escape):
        self.gui.shut(event.key() == Qt.Key.Key_E)
    return kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease)

  def _guiClosed(self, byE: bool) -> None:
    """The GUI shut by E or a button: back to looking round (the window
    has the focus: the key or the click came to it; nothing asks for
    it)."""
    if byE and self._focused():
      self.pointer.take()

  def _letGo(self, ) -> None:
    """Lets every key and the mouse go, and every grab of the scene's
    window."""
    self.held.clear()
    self.avatar.held = frozenset()
    self.pointer.letGo()
    self.viewport.quick.setKeyboardGrabEnabled(False)
    self.viewport.quick.setMouseGrabEnabled(False)

  def _focused(self, ) -> bool:
    """Tells whether the scene's window has the focus and the program
    is the one in front: only then are keys the avatar's."""
    application = QGuiApplication.instance()
    return (application.focusWindow() is self.viewport.quick
            and application.applicationState()
            == Qt.ApplicationState.ApplicationActive)

  def _focusMoved(self, window: object) -> None:
    """Lets every key and the mouse go when the focus goes to another
    window than the scene's (a key let go elsewhere never comes back up
    here)."""
    if window is not self.viewport.quick:
      self._letGo()

  def _stateMoved(self, state: object) -> None:
    """Lets every key and the mouse go when the program is no longer the
    one in front."""
    if state != Qt.ApplicationState.ApplicationActive:
      self._letGo()

