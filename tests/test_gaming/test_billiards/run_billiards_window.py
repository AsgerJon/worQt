"""
RunBilliardsWindow covers 'BilliardsApp', its 'BilliardsWindow' and the
'TableView' in it: the window opens titled; the scene loads without
errors and is given the table's sizes and pieces, the balls where the
game opens them and turned as they lie, and the twenty diamonds; places
and turns on the table turn into the scene's, the cloth's middle at the
origin and the head end away; resting, the camera turns round the cue
ball and the aim shows; a game lags, breaks and calls the user's first
break a point, the call shown as the point is made, before all rest;
the last shot replays, the balls then as they lay; the sandbox calls
shots, takes them back (a mulligan) with their mark, even under way,
moves balls and respots them; the keys A, D, W and S turn the aim and
tilt the camera by the aim step; looking from the ghost carries it round
its ball as the view turns, and leaves it there; the
camera looks from any ball, chosen or tapped, and on another than the
cue ball 'Shoot' marks a ghost ball two radii behind it, kept until the
shot; 'Top view' swaps the camera's view and the view from above, the
table's length across it; 'Field of view' sets how much the camera
takes in; the aim line follows the shot's speed; the point struck is
chosen on the ball's face; new balls move in the scene. Seen from above,
a shot is drawn as it goes, the cue ball's way bold with the hand behind
it, until the balls are laid anew; 'Hand' shows the hand or not. While
the balls lie as a game opens, 'Left spot' and 'Right spot' lay the cue
ball either side of the head spot, the side kept by 'Reset'. With the
frames running, 'New game' and 'Reset' lay the balls anew mid-shot.
'Unfolded' shows the map of the table unfolded beside it, lit, the arc
from the cue ball along the camera's heading, bending the way of the
English; again, it hides. 'Full map' shows 7 by 7 tables instead of the
table, every ball in every copy; again, the table is back. The next shot
takes the last one's trails away as it is struck, and draws only the
ways of the balls moving in it. A press on the full map leaves the aim
as it is; a drag turns it about the cue ball as the pointer turns
about it. A shot struck is watched from above, the
table shown in the full map's place, the cushions the cue ball meets
counted over the view; at rest the view is as it was, the map back.
'Shoot' looks from above at once and strikes a second later, the shot
as set up when pressed. The arrow keys move the point struck, End takes
the middle again. 'Sound' turns the sounds
off and on. Beside 'Shoot', '▸▸ Fast' held down plays the shot under
way five times as fast, as long as it is held; greyed out between
shots. The full map draws the cue ball's way as the engine plays the
shot aimed, once it comes. 'Skip lag' lets a coin decide who breaks.
The score shows as a scoreboard, a row each player with the ball he
plays and his run so far.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import time

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QVector3D
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from worQt.gaming.billiards import Ball, CaromTable, KegleTable, turnOf
from worQt.gaming.billiards.gui import BilliardsApp, BilliardsWindow, Prism
from worQt.gaming.billiards.gui import STROKE_MOST

from . import BilliardsWidgetTest, breakAim


def upOf(row: tuple) -> float:
  """How far up a pin's axis points as a sample holds it, a share: one
  upright, nought lying."""
  return 1.0 - 2.0 * (row[5] * row[5] + row[6] * row[6])


class RunBilliardsWindow(BilliardsWidgetTest):
  """Tests for 'BilliardsWindow' and its 'TableView'."""

  #  Some twenty-seven windows, each loading its scene and spawning its shot
  #  worker and its sounds, some playing shots out: some four seconds
  #  apiece on the real display.
  __time_out__ = 270.0

  def openWindow(self) -> BilliardsWindow:
    """The window, shown live, its scene loaded."""
    window = BilliardsWindow()
    self.showLive(window)
    view = window.view
    self.assertTrue(self.waitUntil(lambda: view.loaded, 10000))
    return window

  def run_opens(self) -> None:
    """It opens titled, its scene loaded without errors."""
    window = self.openWindow()
    self.assertEqual(window.windowTitle(), 'Three-cushion')
    self.assertEqual(window.view.problems, ())
    self.assertIsNotNone(window.view.rootObject())
    self.assertIs(BilliardsApp.__window_class__, BilliardsWindow)
    window.close()

  def run_scene_values(self) -> None:
    """The scene has the table's sizes, the balls where they lie, at
    the lag as a game opens, and the twenty diamonds."""
    window = self.openWindow()
    view = window.view
    table = view.table
    self.assertEqual(table, CaromTable())
    self.assertAlmostEqual(view.sceneValue('tableLength'), 2840.0, 9)
    self.assertAlmostEqual(view.sceneValue('tableWidth'), 1420.0, 9)
    self.assertAlmostEqual(view.sceneValue('ballRadius'), 30.75, 9)
    self.assertEqual(view.balls, table.lagPosition())
    for ball in view.balls:
      place = view.sceneValue('%sPlace' % ball.name)
      wanted = view.scenePlace(ball.x, ball.y, table.radius)
      self.assertAlmostEqual(place.x(), wanted.x(), 3)
      self.assertAlmostEqual(place.y(), wanted.y(), 3)
      self.assertAlmostEqual(place.z(), wanted.z(), 3)
    self.assertEqual(len(view.sceneValue('diamondPlaces')), 20)
    self.assertAlmostEqual(view.sceneValue('cushionTop'), table.top, 9)
    shapes = view.sceneValue('shapes')
    self.assertEqual(sorted(shapes), [
      'apron', 'corner', 'cueButt', 'cueFerrule', 'cueShaft', 'cueTip',
      'cushionLong', 'cushionLongNotched', 'cushionShort',
      'cushionShortNotched', 'diamond', 'pedestal', 'pin',
      'pocketLeather', 'railLong', 'railShort'])
    for shape in shapes.values():
      self.assertIsInstance(shape, Prism)
    window.close()

  def run_scene_turns(self) -> None:
    """Each ball's turn reaches the scene, the table's 'y' the scene's
    negative 'z', its up the scene's 'y'."""
    window = self.openWindow()
    view = window.view
    for ball in view.balls:
      turn = view.sceneValue('%sTurn' % ball.name)
      w, x, y, z = ball.turn
      self.assertAlmostEqual(turn.scalar(), w, 5)
      self.assertAlmostEqual(turn.x(), x, 5)
      self.assertAlmostEqual(turn.y(), z, 5)
      self.assertAlmostEqual(turn.z(), -y, 5)
    up = view.sceneTurn(turnOf(90.0, 0.0, 0.0, 1.0))
    turned = up.rotatedVector(QVector3D(1.0, 0.0, 0.0))
    self.assertAlmostEqual(turned.x(), 0.0, 5)
    self.assertAlmostEqual(turned.z(), -1.0, 5)
    window.close()

  def run_scene_place(self) -> None:
    """The cloth's middle is the origin, x across, the head end away,
    height up."""
    window = self.openWindow()
    view = window.view
    middle = view.scenePlace(710.0, 1420.0, 0.0)
    self.assertEqual((middle.x(), middle.y(), middle.z()), (0.0, 0.0, 0.0))
    head = view.scenePlace(0.0, 2840.0, 30.0)
    self.assertEqual((head.x(), head.y(), head.z()), (-710.0, 30.0, -1420.0))
    window.close()

  def settle(self, window: BilliardsWindow) -> None:
    """Shows the shot under way played out, all at rest."""
    window.finish()
    self.assertTrue(window.resting())

  def run_aiming(self) -> None:
    """Resting, the camera turns round the cue ball and the aim shows,
    the trenches with it, ball 1's at least (the user); aimed at red,
    red's too, each in its ball's tint, and a clear copy of the cue ball
    where it meets red (the user); in the sandbox,
    choosing yellow moves both to it; the camera faces down the table at
    first."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel = window.view, window.panel
    self.assertTrue(panel.ready)
    self.assertTrue(view.sceneValue('aiming'))
    window.tick()
    self.assertTrue(view.sceneValue('trenchesShown'))
    self.assertGreaterEqual(len(view.sceneValue('trenchNames')), 1)
    red = {ball.name: ball for ball in view.balls}['red']
    radius = view.table.radius
    view.faceCamera(red.x - window.cueBall().x, red.y - window.cueBall().y)
    self.wait(50)
    window.tick()
    self.assertTrue(view.sceneValue('impactShown'))
    self.assertEqual(list(view.sceneValue('trenchNames'))[:2],
                     ['white', 'red'])
    impact = view.sceneValue('impactPlace')
    self.assertAlmostEqual(
      (impact - view.scenePlace(red.x, red.y, radius)).length(),
      2.0 * radius, 2)
    white = window.cueBall()
    focus = view.sceneValue('cameraFocus')
    self.assertAlmostEqual(focus.x(), white.x - 0.5 * view.table.width, 3)
    heading = view.cameraHeading()
    self.assertAlmostEqual(math.hypot(*heading), 1.0, 9)
    self.assertLess(heading[1], -0.9)
    self.click(window.toolBar.sandboxButton)
    self.click(panel.yellowButton)
    self.assertEqual(panel.cueName, 'yellow')
    self.assertTrue(panel.yellowButton.checked)
    self.assertFalse(panel.whiteButton.checked)
    yellow = window.cueBall()
    focus = view.sceneValue('cameraFocus')
    self.assertAlmostEqual(focus.x(), yellow.x - 0.5 * view.table.width,
                           3)
    window.close()

  def run_game(self) -> None:
    """A game opens on the lag, the cue ball fixed; white's lag shot is
    set, then yellow's strikes both; the winner chooses to break and plays
    white from spot 4 or 5; the user's first break is called a point and
    he plays on, the score shown."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel = window.view, window.panel
    self.assertEqual(window.mode(), 'game')
    self.assertEqual(window.match().phase, 'lag')
    self.assertFalse(panel.cueFree)
    self.assertEqual(view.balls, view.table.lagPosition())
    panel.picker.setHit(0.4, 0.0)
    panel.powerSlider.quantity = 1.6
    window.shoot(0.0, -1.0)
    self.assertEqual(panel.cueName, 'yellow')
    self.assertTrue(window.resting())
    panel.powerSlider.quantity = 1.5
    window.shoot(0.0, -1.0)
    self.assertFalse(window.resting())
    self.settle(window)
    match = window.match()
    self.assertIn(match.phase, ('choose', 'lag'))
    if match.phase == 'lag':
      window.close()
      return
    self.assertIn('wins the lag', panel.callWords)
    self.assertTrue(panel.breakButton.isVisibleTo(panel))
    self.click(panel.breakButton)
    match = window.match()
    self.assertEqual(match.phase, 'break')
    self.assertEqual(match.cueBall(), 'white')
    self.assertEqual(view.balls, view.table.openingFor('white', 4))
    self.click(panel.spotFiveButton)
    self.assertEqual(view.balls, view.table.openingFor('white', 5))
    self.click(panel.spotFourButton)
    white, yellow, red = view.balls
    panel.picker.setHit(0.38, -0.26)
    panel.powerSlider.quantity = 4.0
    window.shoot(*breakAim(white, red, view.table.radius))
    self.assertFalse(window.toolBar.replayButton.isEnabled())
    self.assertTrue(self.waitUntil(lambda: window.recording().over, 10000))
    called = 0.0
    while window.playing and not window.callShown and called < 30.0:
      window.advance(0.01)
      called += 0.01
    self.assertTrue(window.playing)
    self.assertIn('Point', panel.callWords)
    self.assertEqual(window.match().run, 0)
    self.settle(window)
    self.assertIn('Point', panel.callWords)
    match = window.match()
    self.assertEqual((match.phase, match.run), ('play', 1))
    self.assertEqual(panel.scoreRows[match.current][2], '1')
    window.close()

  def run_replay(self) -> None:
    """The last shot replays from the moment it was struck, the call
    cleared until it is made again; then the balls lie as they did; 'Replay'
    is greyed out while a shot is shown."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel, bar = window.view, window.panel, window.toolBar
    self.click(bar.sandboxButton)
    self.assertFalse(bar.replayButton.isEnabled())
    panel.powerSlider.quantity = 2.0
    window.shoot(0.0, -1.0)
    self.settle(window)
    words, lying = panel.callWords, view.balls
    self.assertTrue(bar.replayButton.isEnabled())
    self.click(bar.replayButton)
    self.assertTrue(window.playing)
    self.assertFalse(bar.replayButton.isEnabled())
    self.assertEqual(panel.callWords, '')
    self.assertEqual(view.balls, window.recording().ballsAt(0.0))
    window.advance(0.5)
    self.assertNotEqual(view.balls, lying)
    window.finish()
    self.assertFalse(window.playing)
    self.assertEqual(view.balls, lying)
    self.assertEqual(panel.callWords, words)
    self.assertTrue(bar.replayButton.isEnabled())
    window.close()

  def run_sandbox(self) -> None:
    """In the sandbox any ball is struck, the shot still called;
    'Mulligan' lays the balls as they were; 'Move balls' drags one frozen to
    another, and 'Respot' puts them on their spots, white on yellow's,
    spot 2, yellow lying on white's, spot 3."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel, bar = window.view, window.panel, window.toolBar
    self.click(bar.sandboxButton)
    self.assertEqual(window.mode(), 'sandbox')
    self.assertTrue(panel.cueFree)
    self.assertTrue(bar.mulliganButton.isEnabled())
    self.click(bar.resetButton)
    before = view.balls
    self.assertEqual(before, view.table.opening())
    panel.powerSlider.quantity = 2.0
    window.shoot(0.0, -1.0)
    self.settle(window)
    self.assertIn('missed', panel.callWords)
    self.click(bar.mulliganButton)
    self.assertEqual(view.balls, before)
    window.shoot(0.0, -1.0)
    window.advance(0.2)
    self.click(bar.mulliganButton)
    self.assertFalse(window.playing)
    self.assertEqual(view.balls, before)
    self.assertTrue(window.resting())
    self.click(bar.moveButton)
    self.assertTrue(window.moving)
    self.assertTrue(view.sceneValue('moving'))
    named = {ball.name: ball for ball in view.balls}
    white, red = named['white'], named['red']
    radius = view.table.radius
    window.grab(white.x + 5.0, white.y)
    window.drag(red.x + 2.0 * radius + 0.05, red.y)
    window.letGo()
    self.assertTrue(panel.respotButton.isVisibleTo(panel))
    self.click(panel.respotButton)
    named = {ball.name: ball for ball in view.balls}
    self.assertEqual((named['white'].x, named['white'].y),
                     view.table.spot(2))
    self.assertEqual((named['red'].x, named['red'].y), view.table.spot(1))
    self.click(bar.gameButton)
    self.assertFalse(window.moving)
    self.assertEqual(window.match().phase, 'lag')
    window.close()

  def run_look_and_mark(self) -> None:
    """Looking from the red, the camera turns round it and 'Mark' shows;
    marking leaves a ghost of the cue ball two radii behind the red,
    against the aim, in the cue ball's colour; looking from the cue ball
    again keeps it, 'Mark' hidden again; a tap near a ball
    looks from it, one far from all does nothing; the shot takes the
    mark away."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel = window.view, window.panel
    self.click(window.toolBar.sandboxButton)
    self.assertTrue(panel.markButton.isHidden())
    self.click(panel.lookRedButton)
    self.assertEqual(panel.lookName, 'red')
    self.assertEqual(panel.cueName, 'white')
    self.assertTrue(panel.marking())
    self.assertFalse(panel.markButton.isHidden())
    red = window.lookBall()
    focus = view.sceneValue('cameraFocus')
    wanted = view.scenePlace(red.x, red.y, view.table.radius)
    self.assertAlmostEqual(focus.x(), wanted.x(), 3)
    self.assertAlmostEqual(focus.z(), wanted.z(), 3)
    self.assertIsNone(window.markPlace())
    window.mark(0.6, 0.8)
    x, y = window.markPlace()
    apart = 2.0 * view.table.radius
    self.assertAlmostEqual(x, red.x - 0.6 * apart, 9)
    self.assertAlmostEqual(y, red.y - 0.8 * apart, 9)
    self.assertTrue(view.sceneValue('markShown'))
    self.assertEqual(view.sceneValue('markColor').name(), '#f2ecd9')
    self.assertFalse(window.playing)
    white = window.cueBall()
    window.tapTable(white.x + 10.0, white.y - 5.0)
    self.assertEqual(panel.lookName, 'white')
    self.assertTrue(panel.markButton.isHidden())
    self.assertEqual(window.markPlace(), (x, y))
    window.tapTable(white.x + 300.0, white.y)
    self.assertEqual(panel.lookName, 'white')
    window.mark(0.0, 1.0)
    self.assertEqual(window.markPlace(), (x, y))
    window.shoot(0.0, -1.0)
    self.assertIsNone(window.markPlace())
    self.assertFalse(view.sceneValue('markShown'))
    self.settle(window)
    window.close()

  def run_overhead(self) -> None:
    """'Top view' shows the table from straight above, lit, the corner
    hidden; again, back, the view from above in the corner; the view
    from above has the table's length across it and takes in all the
    table."""
    window = self.openWindow()
    view, bar = window.view, window.toolBar
    self.assertFalse(view.sceneValue('overhead'))
    forward = view.sceneValue('overheadForward')
    self.assertAlmostEqual(forward.y(), -1.0, 6)
    right = view.sceneValue('overheadRight')
    self.assertAlmostEqual(abs(right.z()), 1.0, 6)
    corner = view.sceneValue('overheadView')
    self.assertTrue(view.sceneValue('cornerShown'))
    self.click(bar.topButton)
    self.assertTrue(window.overhead)
    self.assertTrue(bar.topButton.checked)
    self.assertTrue(view.sceneValue('overhead'))
    self.assertFalse(view.sceneValue('cornerShown'))
    self.assertNotAlmostEqual(view.sceneValue('overheadView'), corner, 3)
    self.click(bar.topButton)
    self.assertFalse(window.overhead)
    self.assertFalse(bar.topButton.checked)
    self.assertFalse(view.sceneValue('overhead'))
    self.assertTrue(view.sceneValue('cornerShown'))
    window.close()

  def run_mulligan(self) -> None:
    """A mulligan lays the balls as they were before the shot and puts
    its mark back where it was, looking from the ghost possible again."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel, bar = window.view, window.panel, window.toolBar
    self.click(bar.sandboxButton)
    before = view.balls
    self.click(panel.lookRedButton)
    window.mark(0.0, 1.0)
    mark = window.markPlace()
    self.click(panel.lookWhiteButton)
    window.shoot(0.0, -1.0)
    self.assertIsNone(window.markPlace())
    self.assertFalse(panel.lookGhostButton.isEnabled())
    self.settle(window)
    self.click(bar.mulliganButton)
    self.assertEqual(view.balls, before)
    self.assertEqual(window.markPlace(), mark)
    self.assertEqual(window.markBall(), 'red')
    self.assertTrue(view.sceneValue('markShown'))
    self.assertTrue(panel.lookGhostButton.isEnabled())
    window.close()

  def press(self, window: BilliardsWindow, key: Qt.Key) -> None:
    """Presses 'key' on 'window' as the keyboard would, so its shortcuts
    hear it, the window made active first, as shortcuts want."""
    window.activateWindow()
    QTest.qWaitForWindowActive(window, 1000)
    QTest.keyClick(window, key)
    self.wait(10)

  def run_aim_keys(self) -> None:
    """A and D turn the aim left and right, W and S tilt the camera up
    over the ball and down, by the aim step a press, never lower than 10
    degrees over the cloth, where the cue would hide the ball (the
    user); the step runs from 0.01 to 1 degree on a log scale, 0.1 at
    first."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, bar = window.view, window.toolBar
    step = bar.stepSlider
    self.assertTrue(step.logScale)
    self.assertAlmostEqual(step.quantity, 0.1, 9)
    self.assertEqual((step.low, step.high), (0.01, 1.0))
    start = view.sceneValue('cameraTurnNow')
    self.press(window, Qt.Key.Key_A)
    turned = view.sceneValue('cameraTurnNow')
    self.assertAlmostEqual(turned.y() - start.y(), 0.1, 4)
    step.quantity = 5.0
    self.assertAlmostEqual(step.quantity, 1.0, 9)
    step.quantity = 0.5
    self.press(window, Qt.Key.Key_D)
    self.press(window, Qt.Key.Key_W)
    later = view.sceneValue('cameraTurnNow')
    self.assertAlmostEqual(later.y() - turned.y(), -0.5, 4)
    self.assertAlmostEqual(later.x() - turned.x(), -0.5, 4)
    self.press(window, Qt.Key.Key_S)
    self.assertAlmostEqual(view.sceneValue('cameraTurnNow').x(),
                           turned.x(), 4)
    step.quantity = 1.0
    for _ in range(30):
      self.press(window, Qt.Key.Key_S)
    self.assertAlmostEqual(view.sceneValue('cameraTurnNow').x(), -10.0, 4)
    window.close()

  def run_ghost_look(self) -> None:
    """Looking from the ghost is offered only once a mark is there; the
    camera then stands at the ghost, facing the way the cue ball leaves
    the marked ball after the hit, square to the line of their middles;
    turning the view chooses that way, and the ghost moves round the ball
    to the hit that gives it, two radii off, the cue ball coming at it;
    looking from a ball again leaves the ghost where it was."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel = window.view, window.panel
    self.click(window.toolBar.sandboxButton)
    self.assertFalse(panel.lookGhostButton.isEnabled())
    self.click(panel.lookRedButton)
    window.mark(0.6, -0.8)
    mark = window.markPlace()
    self.assertTrue(panel.lookGhostButton.isEnabled())
    self.click(panel.lookGhostButton)
    self.assertTrue(window.ghosting)
    self.assertFalse(panel.markButton.isHidden())
    named = {ball.name: ball for ball in view.balls}
    red, cue = named['red'], named['white']
    apart = 2.0 * view.table.radius
    for turn in (0.0, 15.0, -40.0):
      window.turnAim(turn / window.toolBar.stepSlider.quantity, 0.0)
      x, y = window.markPlace()
      if not turn:
        self.assertAlmostEqual(x, mark[0], 3)
        self.assertAlmostEqual(y, mark[1], 3)
      hx, hy = view.cameraHeading()
      nx, ny = (red.x - x) / apart, (red.y - y) / apart
      self.assertAlmostEqual(math.hypot(nx, ny), 1.0, 4)
      self.assertAlmostEqual(nx * hx + ny * hy, 0.0, 4)
      dx, dy = x - cue.x, y - cue.y
      along = dx * nx + dy * ny
      self.assertGreater(along, 0.0)
      self.assertGreater((dx - along * nx) * hx + (dy - along * ny) * hy,
                         0.0)
    self.click(panel.lookWhiteButton)
    self.assertFalse(window.ghosting)
    self.assertFalse(view.sceneValue('ghostLook'))
    left = window.markPlace()
    self.assertAlmostEqual(left[0], x, 3)
    self.assertAlmostEqual(left[1], y, 3)
    window.turnAim(20.0, 0.0)
    self.assertEqual(window.markPlace(), left)
    window.close()

  def run_unfolded(self) -> None:
    """'Unfolded' shows the map beside the table, lit; resting, aimed
    from the cue ball, its arc leaves the cue ball along the camera's
    heading, straight without side, bending right with right English;
    again, it hides."""
    window = self.openWindow()
    bar, unfolded, panel = window.toolBar, window.unfoldedMap, window.panel
    self.assertFalse(unfolded.isVisible())
    self.click(bar.mapButton)
    self.assertTrue(window.unfolded)
    self.assertTrue(bar.mapButton.checked)
    self.assertTrue(unfolded.isVisible())
    self.assertTrue(self.waitUntil(lambda: unfolded.aim is not None, 3000))
    heading = window.view.cameraHeading()
    self.assertAlmostEqual(unfolded.aim[0], heading[0], 6)
    self.assertAlmostEqual(unfolded.aim[1], heading[1], 6)
    self.assertEqual(unfolded.cueName, panel.cueName)
    cue = unfolded.cueBall()
    arc = unfolded.arc()
    self.assertGreater(len(arc), 2)
    self.assertEqual(arc[0], (cue.x, cue.y))
    panel.picker.setHit(0.0, 0.4)
    self.assertTrue(self.waitUntil(lambda: unfolded.side > 0.0, 1000))
    arc = unfolded.arc()
    ax, ay = unfolded.aim
    end = arc[-1]
    left = ax * (end[1] - cue.y) - ay * (end[0] - cue.x)
    self.assertLess(left, 0.0)
    self.assertIn('right English', unfolded.caption())
    self.click(bar.mapButton)
    self.assertFalse(window.unfolded)
    self.assertFalse(unfolded.isVisible())
    window.close()

  def run_full_map(self) -> None:
    """'Full map' shows 7 by 7 tables instead of the table, lit, every
    ball in every copy; resting, the arc leaves the cue ball; again, the
    table is back."""
    window = self.openWindow()
    bar, full, view = window.toolBar, window.fullMap, window.view
    self.assertFalse(full.isVisible())
    self.assertEqual((full.unfolded.across, full.unfolded.along), (3, 3))
    self.assertEqual(len(full.unfolded.copies()), 49)
    self.assertTrue(full.fanned)
    self.assertFalse(window.unfoldedMap.fanned)
    self.click(bar.fullButton)
    self.assertTrue(window.fullShown)
    self.assertTrue(bar.fullButton.checked)
    self.assertTrue(full.isVisible())
    self.assertFalse(view.isVisible())
    self.assertTrue(self.waitUntil(lambda: full.aim is not None, 3000))
    self.assertEqual(full.balls, view.balls)
    self.assertGreater(len(full.arc()), 2)
    self.click(bar.fullButton)
    self.assertFalse(window.fullShown)
    self.assertFalse(full.isVisible())
    self.assertTrue(view.isVisible())
    window.close()

  def run_map_drag(self) -> None:
    """A press on the full map leaves the aim as it is; a drag turns it
    about the cue ball by as much as the pointer turns about it from
    where it was pressed, the camera turning with it."""
    window = self.openWindow()
    bar, full, view = window.toolBar, window.fullMap, window.view
    self.click(bar.fullButton)
    self.assertTrue(self.waitUntil(lambda: full.aim is not None, 3000))
    cue = full.cueBall()

    def way() -> tuple[float, float]:
      aim = full.aim
      size = math.hypot(*aim)
      return aim[0] / size, aim[1] / size

    def angleAt(point) -> float:
      x, y = full.placeAt(QPointF(point))
      return math.atan2(y - cue.y, x - cue.x)

    before = way()
    press = full.pointOf(cue.x + 2000.0, cue.y).toPoint()
    drag = full.pointOf(cue.x + 2000.0, cue.y + 1200.0).toPoint()
    left, plain = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    QTest.mousePress(full, left, plain, press)
    self.wait(300)
    after = way()
    self.assertLess(math.hypot(after[0] - before[0], after[1] - before[1]),
                    0.01)
    QTest.mouseMove(full, drag)
    QTest.mouseRelease(full, left, plain, drag)
    want = math.atan2(before[1], before[0]) + angleAt(drag) - angleAt(press)

    def aimed() -> bool:
      heading = view.cameraHeading()
      return heading is not None and math.hypot(
        heading[0] - math.cos(want), heading[1] - math.sin(want)) < 0.02

    self.assertTrue(self.waitUntil(aimed, 2000))
    window.close()

  def run_engine_way(self) -> None:
    """Aimed, the full map has the engine play the shot at once, saying
    so, and draws it as the engine plays it, the cue ball's way from the
    cue ball on, then the aim off to either side played too; turned, the
    old shot no longer shows, and the new one is played at once."""
    window = self.openWindow()
    full = window.fullMap
    self.click(window.toolBar.fullButton)
    self.assertTrue(self.waitUntil(lambda: full.aim is not None, 3000))
    self.assertTrue(self.waitUntil(
      lambda: full.engineWay() is not None or full.working(), 1000))
    self.assertTrue(self.waitUntil(lambda: full.engineWay() is not None,
                                   8000))
    cue = full.cueBall()
    self.assertEqual(full.arc()[0], (cue.x, cue.y))
    self.assertNotIn('Working', full.caption())
    self.assertTrue(self.waitUntil(lambda: len(full.runs()) == 3, 8000))
    self.assertEqual(full.runs()[0].cue, cue.name)
    window.turnAim(1.0, 0.0)
    self.assertTrue(self.waitUntil(lambda: full.engineWay() is None, 2000))
    self.assertIn('Working', full.caption())
    self.assertTrue(self.waitUntil(lambda: full.engineWay() is not None,
                                   8000))
    window.close()

  def run_overhead_and_count(self) -> None:
    """Struck, the shot is watched from above, the table shown in the
    full map's place; the cushions the cue ball meets counted over the
    view; once all rest, the view is as it was and the map is back; Top
    view chosen meanwhile stays. 'Sound' turns the sounds off and
    on."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel, bar = window.view, window.panel, window.toolBar
    self.click(bar.sandboxButton)
    self.click(bar.resetButton)
    self.click(bar.fullButton)
    self.assertFalse(view.isVisible())
    self.assertFalse(window.overhead)
    panel.powerSlider.quantity = 3.0
    window.shoot(0.0, -1.0)
    self.assertTrue(window.overhead)
    self.assertTrue(view.sceneValue('overhead'))
    self.assertFalse(view.sceneValue('cornerShown'))
    self.assertTrue(bar.topButton.checked)
    self.assertTrue(view.isVisible())
    self.assertFalse(window.fullMap.isVisible())
    self.assertTrue(self.waitUntil(
      lambda: window.recording().count() > 300, 10000))
    window.advance(0.3)
    self.assertTrue(view.sceneValue('counterShown'))
    self.assertIn('cushions', view.sceneValue('counterText'))
    self.settle(window)
    self.assertFalse(window.overhead)
    self.assertFalse(view.sceneValue('overhead'))
    self.assertTrue(view.sceneValue('cornerShown'))
    self.assertFalse(bar.topButton.checked)
    self.assertTrue(window.fullMap.isVisible())
    self.assertFalse(view.isVisible())
    self.click(bar.fullButton)
    window.shoot(0.0, 1.0)
    self.assertTrue(window.overhead)
    window.toggleOverhead()
    window.toggleOverhead()
    self.settle(window)
    self.assertTrue(window.overhead)
    self.assertTrue(window.sounds.enabled)
    self.click(bar.soundBox)
    self.assertFalse(window.sounds.enabled)
    self.click(bar.soundBox)
    self.assertTrue(window.sounds.enabled)
    window.close()

  def run_shot_from_above(self) -> None:
    """A shot struck otherwise than by the stroke ('shoot', tests) is
    watched from above, the table shown in the full map's place, the
    hand behind the cue ball, its cue following through as it meets the
    ball, drawn back the further the harder, never into the bridge; once
    all rest the view is as it was, the map back. 'Shoot' is gone: the
    stroke is the only way a shot is made (the user); the point struck
    and the power show in the panel, to be set, only while the full map
    shows; else they are gone from it (the user)."""
    window = self.openWindow()
    view, panel, bar = window.view, window.panel, window.toolBar
    self.click(bar.sandboxButton)
    self.click(bar.resetButton)
    self.assertFalse(panel.controlsLive())
    for part in (panel.picker, panel.centreButton, panel.powerSlider):
      self.assertTrue(part.isHidden())
    self.click(bar.fullButton)
    self.assertTrue(panel.controlsLive())
    for part in (panel.picker, panel.centreButton, panel.powerSlider):
      self.assertFalse(part.isHidden())
    heading = view.cameraHeading()
    self.assertIsNotNone(heading)
    panel.powerSlider.quantity = 2.0
    window.shoot(*heading)
    self.assertTrue(window.playing)
    self.assertTrue(window.overhead)
    self.assertTrue(view.isVisible())
    self.assertFalse(window.fullMap.isVisible())
    self.assertFalse(panel.controlsLive())
    self.assertFalse(panel.ready)
    self.assertFalse(view.sceneValue('aiming'))
    self.assertTrue(self.waitUntil(
      lambda: view.sceneValue('cueBack') < -20.0, 1000))
    self.assertEqual(window.backswingOf(1e6), STROKE_MOST)
    self.assertLess(window.backswingOf(1000.0), window.backswingOf(3000.0))
    self.assertTrue(self.waitUntil(
      lambda: window.recording().count() > 0, 5000))
    named = {ball.name: ball for ball in window.recording().ballsAt(0.0)}
    struck = named[panel.cueName]
    speed = math.hypot(struck.vx, struck.vy)
    self.assertAlmostEqual(speed, 2000.0, 3)
    self.assertAlmostEqual(struck.vx / speed, heading[0], 3)
    self.assertAlmostEqual(struck.vy / speed, heading[1], 3)
    self.settle(window)
    self.assertFalse(window.overhead)
    self.assertTrue(window.fullMap.isVisible())
    self.assertTrue(panel.controlsLive())
    self.assertTrue(list(view.sceneValue('trailNames')))
    self.assertFalse(hasattr(panel, 'shootButton'))
    window.close()

  def run_kegler_look(self) -> None:
    """Laid out for keglebillard, the second game: the cloth more cyan,
    the six holes and the five pins on their spots, three grooves round
    each, the whites on the layout spots, red the cue ball in hand at
    the head end. Red struck at the right pin knocks it over, the pins
    shown as the shot goes, keglebillard's referee calling it a foul,
    red's pin (5.8); once all rest the pins stand on their spots again
    (the user: they respawn before each shot); Reset lays it out so
    again."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, bar, panel = window.view, window.toolBar, window.panel
    self.assertFalse(view.sceneValue('kegler'))
    window.showKegler()
    kegle = KegleTable(view.table)
    self.assertTrue(view.sceneValue('kegler'))
    self.assertEqual(len(view.sceneValue('pinPlaces')), 5)
    self.assertEqual(len(view.sceneValue('pinTurns')), 5)
    self.assertEqual(list(view.sceneValue('pinShown')), [True] * 5)
    self.assertEqual(len(view.sceneValue('holePlaces')), 6)
    self.assertEqual(len(view.sceneValue('pinGrooves')), 3)
    self.assertEqual(view.balls, kegle.opening())
    self.assertEqual(panel.cueName, 'red')
    self.assertEqual([upOf(row) for row in view.__pin_rows__], [1.0] * 5)
    red = view.balls[2]
    x, y = kegle.pinSpots()[2]
    panel.picker.setHit(0.2, 0.0)
    panel.powerSlider.quantity = 3.0
    window.shoot(x - red.x + 4.0, y - red.y)
    window.finish()
    recording = window.recording()
    self.assertTrue(recording.over)
    self.assertEqual(len(recording.pinParts), len(recording.parts))
    fallen = window.recorderFor(recording.ballsAt(0.0)).fallenOf(recording)
    self.assertIn(2, [number for number, _ in fallen])
    self.assertIn(('pin', 'red', '2'), recording.touchesOf())
    self.assertLess(upOf(recording.lastPins()[2]), 0.5)
    self.assertIn('(5.8)', panel.callWords)
    self.assertEqual([upOf(row) for row in view.__pin_rows__], [1.0] * 5)
    self.click(bar.resetButton)
    self.assertEqual(view.balls, kegle.opening())
    self.assertEqual([upOf(row) for row in view.__pin_rows__], [1.0] * 5)
    window.close()

  def run_kegler_game(self) -> None:
    """A keglebillard game is a game loop of its own: 'Kegler' lays the
    table out for it at its lag, the distance stepped before it ('To
    400'); the lag skipped, the winner lays out, red in hand; 'Place red'
    lets a drag put red down only within a quarter of either short
    cushion; red struck at yellow scores nothing, the turn passes, the
    pins stand again; both object balls white, one marked (the user);
    'Three-cushion' plays three-cushion again."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, bar, panel = window.view, window.toolBar, window.panel
    window.setMode('game')
    self.click(bar.kegleButton)
    self.assertTrue(window.isKegler())
    self.assertTrue(view.sceneValue('kegler'))
    self.assertEqual(view.bodyOf('yellow'), view.bodyOf('white'))
    self.assertEqual(panel.yellowButton.text, 'Marked')
    self.assertEqual(panel.heading, 'Kegler to 400')
    self.assertEqual(window.match().phase, 'lag')
    self.assertEqual(view.balls, view.table.lagPosition())
    self.assertTrue(panel.distanceButton.isVisibleTo(panel))
    self.click(panel.distanceButton)
    self.assertEqual(window.match().distance, 500)
    self.assertEqual(panel.distanceButton.text, 'To 500')
    window.skipLag('white')
    match = window.match()
    self.assertEqual((match.phase, match.current), ('play', 0))
    self.assertTrue(match.inHand)
    self.assertEqual(panel.cueName, 'red')
    self.assertTrue(panel.redButton.isVisibleTo(panel))
    self.click(panel.redButton)
    red = {ball.name: ball for ball in view.balls}['red']
    window.grab(red.x, red.y)
    window.drag(300.0, 2600.0)
    window.drag(300.0, 1500.0)
    window.letGo()
    red = {ball.name: ball for ball in view.balls}['red']
    self.assertEqual((red.x, red.y), (300.0, 2600.0))
    yellow = {ball.name: ball for ball in view.balls}['yellow']
    panel.picker.setHit(0.0, 0.0)
    panel.powerSlider.quantity = 3.0
    window.shoot(yellow.x - red.x, yellow.y - red.y)
    window.finish()
    match = window.match()
    self.assertEqual((match.current, match.series[0]), (1, 1))
    self.assertIn('No score', panel.callWords)
    self.assertEqual([upOf(row) for row in view.__pin_rows__], [1.0] * 5)
    self.click(bar.caromButton)
    self.assertFalse(window.isKegler())
    self.assertEqual(panel.yellowButton.text, 'Yellow')
    self.assertEqual(panel.heading[:7], 'Game to')
    window.close()

  def run_stroke(self) -> None:
    """The stroke is a spring (the user): the right button pressed and
    the mouse pulled back draws the cue back, the speedometer over the
    ball showing how hard, the harder the further, the panel's least
    just past the least pull and its most at the reach; let go, the cue
    ball is struck that hard, W A S D moving the point struck meanwhile,
    not the aim (the user), the cue drawn in the scene while it is pulled
    back, gone as it strikes, the shot watched from where the player
    stands, not from above, the view widened to take in the whole table,
    back as it was once all rest (the user), the point struck the
    middle again; pulled back too little, or pushed back to where it was
    pressed, nothing is struck; a left click or Escape while pulling
    back calls it off, nothing struck as the right button is let go
    (the user)."""
    window = self.openWindow()
    window.frameTimer.stop()
    panel = window.panel
    slider = panel.powerSlider
    window.setMode('sandbox')
    least, reach = window.__pull_least__, window.__pull_reach__
    self.assertAlmostEqual(window.springSpeed(least), slider.low, 9)
    self.assertAlmostEqual(window.springSpeed(reach), slider.high, 9)
    self.assertAlmostEqual(window.springSpeed(2.0 * reach), slider.high, 9)
    middle = window.springSpeed(0.5 * (least + reach))
    self.assertAlmostEqual(
      middle, slider.low + 0.25 * (slider.high - slider.low), 9)
    window.pullPressed(400.0, 300.0)
    window.pullMoved(400.0, 300.0 + 0.5 * least)
    window.pullReleased()
    self.assertFalse(window.playing)
    self.assertFalse(window.view.sceneValue('stickShown'))
    window.pullPressed(400.0, 300.0)
    window.pullMoved(400.0, 380.0)
    self.assertTrue(window.view.sceneValue('stickShown'))
    window.pullMoved(400.0, 290.0)
    window.pullReleased()
    self.assertFalse(window.playing)
    self.assertFalse(window.view.sceneValue('stickShown'))
    self.assertFalse(window.view.sceneValue('gaugeShown'))
    window.pullPressed(400.0, 300.0)
    window.pullMoved(400.0, 500.0)
    self.press(window, Qt.Key.Key_Escape)
    self.assertFalse(window.view.sceneValue('stickShown'))
    self.assertFalse(window.view.sceneValue('gaugeShown'))
    window.pullReleased()
    self.assertFalse(window.playing)
    window.pullPressed(400.0, 300.0)
    window.pullMoved(400.0, 500.0)
    self.leftClickHolding(window)
    self.assertFalse(window.view.sceneValue('stickShown'))
    window.pullMoved(400.0, 520.0)
    self.assertFalse(window.view.sceneValue('stickShown'))
    window.pullReleased()
    self.assertFalse(window.playing)
    view = window.view.sceneValue('cameraView')
    window.pullPressed(400.0, 300.0)
    window.pullMoved(400.0, 380.0)
    self.assertTrue(window.view.sceneValue('stickShown'))
    turn = window.view.sceneValue('cameraTurnNow')
    step = window.__spin_step__
    self.press(window, Qt.Key.Key_W)
    self.press(window, Qt.Key.Key_D)
    self.assertAlmostEqual(panel.top, step, 9)
    self.assertAlmostEqual(panel.side, step, 9)
    self.assertEqual(window.view.sceneValue('cameraTurnNow'), turn)
    window.pullMoved(400.0, 500.0)
    self.assertTrue(window.view.sceneValue('gaugeShown'))
    speed = window.springSpeed(200.0)
    self.assertAlmostEqual(window.view.sceneValue('gaugeSpeed'), speed, 6)
    self.assertFalse(window.playing)
    window.pullReleased()
    self.assertFalse(window.view.sceneValue('stickShown'))
    self.assertFalse(window.view.sceneValue('gaugeShown'))
    self.assertTrue(window.playing)
    self.assertFalse(window.overhead)
    self.assertAlmostEqual(window.view.sceneValue('cameraView'), 60.0, 6)
    self.assertAlmostEqual(slider.quantity, speed, 1)
    window.finish()
    self.settle(window)
    self.assertAlmostEqual(window.view.sceneValue('cameraView'), view, 6)
    self.assertEqual((panel.top, panel.side), (0.0, 0.0))
    window.close()

  def run_early_setup(self) -> None:
    """The next shot may be set up as soon as the ball it is played with
    lies still, the others still rolling (the user): the view back from
    above, the aim round that ball; a stroke begun then is refused, a
    barrier flashed over the ball, nothing pulled back or struck; once
    all rest, the stroke strikes."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel = window.view, window.panel
    window.setMode('sandbox')
    view.balls = (Ball('white', 700.0, 1200.0),
                  Ball('yellow', 1200.0, 2500.0),
                  Ball('red', 680.0, 1100.0))
    panel.powerSlider.quantity = 1.0
    window.refresh()
    window.shoot(0.0, -1.0)
    self.assertTrue(window.overhead)
    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
      window.advance(0.02)
      if window.playing and window.settingUp():
        break
      self.wait(5)
    self.assertTrue(window.playing and window.settingUp())
    self.assertFalse(window.resting())
    self.assertFalse(window.overhead)
    self.assertTrue(view.sceneValue('aiming'))
    count = view.sceneValue('barrierCount')
    recording = window.__shot_recording__
    window.pullPressed(400.0, 300.0)
    self.assertEqual(view.sceneValue('barrierCount'), count + 1)
    window.pullMoved(400.0, 500.0)
    self.assertFalse(view.sceneValue('stickShown'))
    window.pullReleased()
    self.assertIs(window.__shot_recording__, recording)
    self.settle(window)
    window.pullPressed(400.0, 300.0)
    window.pullMoved(400.0, 500.0)
    self.assertTrue(view.sceneValue('stickShown'))
    window.pullReleased()
    self.assertIsNot(window.__shot_recording__, recording)
    self.assertTrue(window.playing)
    self.assertEqual(view.sceneValue('barrierCount'), count + 1)
    window.close()

  def run_minimap_menu(self) -> None:
    """The last shot's ways stay on the corner till the next shot begins
    to be aimed (the user): the aim turned, the view pressed; the
    corner's menu (a right click on it) has 'Previous', bringing them
    back, 'Clear', 'Options', none yet, and 'History', each shot of this
    game, newest first, its ways shown when chosen; a new game begins
    a new history; the corner has no view cone."""
    window = self.openWindow()
    window.frameTimer.stop()
    view = window.view
    window.setMode('sandbox')
    menu = self.menuTexts(window.minimapMenu())
    self.assertEqual(list(menu), ['Previous', 'Clear', 'Options',
                                  'History'])
    self.assertFalse(menu['Previous'].isEnabled())
    self.assertEqual(self.menuTexts(menu['History'].menu()),
                     {'No shots yet': menu['History'].menu().actions()[0]})
    window.shoot(0.0, -1.0)
    self.settle(window)
    self.assertTrue(view.sceneValue('trailsShown'))
    window.turnAim(1.0, 0.0)
    self.assertFalse(view.sceneValue('trailsShown'))
    menu = self.menuTexts(window.minimapMenu())
    menu['Previous'].trigger()
    self.assertTrue(view.sceneValue('trailsShown'))
    self.assertIn('white', list(view.sceneValue('trailNames')))
    menu['Clear'].trigger()
    self.assertFalse(view.sceneValue('trailsShown'))
    options = menu['Options'].menu().actions()
    self.assertEqual([option.text() for option in options], ['None yet'])
    self.assertFalse(options[0].isEnabled())
    window.shoot(1.0, 0.0)
    self.settle(window)
    view.aimTouched.emit()
    self.assertFalse(view.sceneValue('trailsShown'))
    shots = window.minimapMenu().actions()[3].menu().actions()
    self.assertEqual(len(shots), 2)
    self.assertTrue(shots[0].text().startswith('2. '))
    self.assertTrue(shots[1].text().startswith('1. '))
    shots[1].trigger()
    self.assertTrue(view.sceneValue('trailsShown'))
    view.minimapMenuAsked.emit(20.0, 20.0)
    self.assertTrue(self.waitUntil(
      lambda: window.__minimap_menu__.isVisible(), 1000))
    window.__minimap_menu__.hide()
    self.click(window.toolBar.resetButton)
    shots = window.minimapMenu().actions()[3].menu().actions()
    self.assertEqual([shot.text() for shot in shots], ['No shots yet'])
    window.close()

  def menuTexts(self, menu: object) -> dict:
    """The actions of 'menu' by their words, in order."""
    return {action.text(): action for action in menu.actions()}

  def run_walking(self) -> None:
    """The game opens walking the billiard room (the user): the bar and
    the panel gone, the aiming keys the walker's, the mouse looking
    round, its pointer hidden; at the door near no table, both club
    boards free, E opens the inventory, the cue in it and in hand, a
    click putting it away and taking it again, E closing it; Esc lets
    the mouse go; beside the kegler table E's menu has
    its name, 'Play a game', 'Sandbox' and 'Walk on'; playing a game
    sits down to kegler at its lag, the bar, the panel and the keys
    back, the room set round that table, its board live; at the table
    E's menu leaves it, the player standing at its foot, walking."""
    window = self.openWindow()
    window.frameTimer.stop()
    view = window.view
    window.enterRoom()
    self.assertTrue(window.walking)
    self.assertTrue(view.sceneValue('walking'))
    self.assertTrue(window.panel.isHidden())
    self.assertTrue(window.toolBar.isHidden())
    self.assertFalse(window.turnLeftKey.isEnabled())
    self.assertTrue(view.isLooking())
    self.assertEqual(view.cursor().shape(), Qt.CursorShape.BlankCursor)
    view.walkTo(*window.room.door, 0.0, -8.0)
    self.assertEqual(view.nearTable(), '')
    self.assertEqual(view.sceneValue('idleBoard')['title'], 'FREE TABLE')
    window.useAsked()
    self.assertTrue(view.sceneValue('inventoryOpen'))
    self.assertFalse(view.isLooking())
    self.assertEqual([item['name'] for item in view.sceneValue('inventory')],
                     ['cue'])
    self.assertEqual(view.sceneValue('held'), 'cue')
    view.itemChosen.emit('cue')
    self.assertEqual(view.sceneValue('held'), '')
    view.itemChosen.emit('cue')
    self.assertEqual(view.sceneValue('held'), 'cue')
    window.useAsked()
    self.assertFalse(view.sceneValue('inventoryOpen'))
    self.assertTrue(view.isLooking())
    view.escapeAsked.emit()
    self.assertFalse(view.isLooking())
    view.setLooking(True)
    view.walkTo(*window.room.beside('kegler'))
    self.assertEqual(view.nearTable(), 'kegler')
    menu = window.startMenu('kegler')
    self.assertEqual([action.text() for action in menu.actions()
                      if action.text()],
                     ['Kegler table', 'Play a game', 'Sandbox', 'Walk on'])
    self.actionOf(menu, 'Play a game').trigger()
    self.assertFalse(window.walking)
    self.assertTrue(window.isKegler())
    self.assertEqual(window.mode(), 'game')
    self.assertFalse(window.panel.isHidden())
    self.assertTrue(window.turnLeftKey.isEnabled())
    self.assertEqual(view.sceneValue('activeX'),
                     window.room.tableAt('kegler')[0])
    self.assertEqual(view.sceneValue('liveBoard')['title'], 'TO 400')
    self.actionOf(window.tableMenu(), 'Leave the table').trigger()
    self.assertTrue(window.walking)
    self.assertEqual(view.nearTable(), 'kegler')
    window.close()

  def actionOf(self, menu: object, text: str) -> object:
    """The action of 'menu' saying 'text'."""
    return next(action for action in menu.actions()
                if action.text() == text)

  def leftClickHolding(self, window: BilliardsWindow) -> None:
    """Clicks the left button on the view while the right is held, as
    a player calling a stroke off does."""
    at = QPointF(400.0, 500.0)
    held = Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
    for kind, buttons in ((QEvent.Type.MouseButtonPress, held),
                          (QEvent.Type.MouseButtonRelease,
                           Qt.MouseButton.RightButton)):
      event = QMouseEvent(kind, at, window.view.mapToGlobal(at),
                          Qt.MouseButton.LeftButton, buttons,
                          Qt.KeyboardModifier.NoModifier)
      QApplication.sendEvent(window.view, event)

  def run_spin_keys(self) -> None:
    """The arrow keys move the point struck, up and down for follow and
    draw, left and right for English, a step a press, never past where
    the cue would miscue; End takes the middle again."""
    window = self.openWindow()
    window.frameTimer.stop()
    panel = window.panel
    step = window.__spin_step__
    self.assertEqual((panel.top, panel.side), (0.0, 0.0))
    self.press(window, Qt.Key.Key_Up)
    self.assertAlmostEqual(panel.top, step, 9)
    self.press(window, Qt.Key.Key_Up)
    self.press(window, Qt.Key.Key_Right)
    self.assertAlmostEqual(panel.top, 2.0 * step, 9)
    self.assertAlmostEqual(panel.side, step, 9)
    self.press(window, Qt.Key.Key_Left)
    self.press(window, Qt.Key.Key_Left)
    self.press(window, Qt.Key.Key_Down)
    self.assertAlmostEqual(panel.top, step, 9)
    self.assertAlmostEqual(panel.side, -step, 9)
    self.press(window, Qt.Key.Key_End)
    self.assertEqual((panel.top, panel.side), (0.0, 0.0))
    for _ in range(round(1.0 / step)):
      self.press(window, Qt.Key.Key_Down)
    self.assertAlmostEqual(panel.top, -window.cue.limit, 9)
    self.assertAlmostEqual(panel.side, 0.0, 9)
    window.close()

  def run_fast_and_board(self) -> None:
    """'▸▸ Fast', after 'Mark' when it shows, is greyed out until a shot
    is under way; held down then, it plays the shot five times as fast,
    as long as it is held; let go, as it happened; once the balls rest
    it is greyed out again, let go. In a game the club board over the
    table shows both players, their points and the distance, the panel
    no longer (the user)."""
    window = self.openWindow()
    window.frameTimer.stop()
    panel, bar = window.panel, window.toolBar
    self.click(panel.lookRedButton)
    mark, fast = panel.markButton.geometry(), panel.fastButton.geometry()
    self.assertEqual(mark.top(), fast.top())
    self.assertGreater(fast.left(), mark.right())
    self.click(panel.lookWhiteButton)
    rows = panel.scoreRows
    self.assertEqual(len(rows), 2)
    self.assertEqual([row[6] for row in rows], ['white', 'yellow'])
    self.assertEqual([row[7] for row in rows], ['0', '0'])
    board = window.view.sceneValue('liveBoard')
    self.assertEqual(board['title'], 'TO %d' % window.match().rules.distance)
    self.assertEqual(list(board['points']), [0, 0])
    self.assertEqual(len(board['names']), 2)
    self.assertFalse(panel.fastButton.isEnabled())
    self.click(bar.sandboxButton)
    self.click(bar.resetButton)
    panel.powerSlider.quantity = 3.0
    window.shoot(0.0, -1.0)
    self.assertTrue(panel.fastButton.isEnabled())
    self.assertEqual(window.playRate(), 1.0)
    middle = panel.fastButton.rect().center()
    QTest.mousePress(panel.fastButton, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, middle)
    self.assertTrue(panel.fast)
    self.assertEqual(window.playRate(), window.__fast_rate__)
    QTest.mouseRelease(panel.fastButton, Qt.MouseButton.LeftButton,
                       Qt.KeyboardModifier.NoModifier, middle)
    self.assertFalse(panel.fast)
    self.assertEqual(window.playRate(), 1.0)
    QTest.mousePress(panel.fastButton, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, middle)
    self.settle(window)
    self.assertFalse(panel.fastButton.isEnabled())
    self.assertFalse(panel.fast)
    self.assertFalse(panel.fastButton.pressed)
    window.close()

  def run_skip_lag(self) -> None:
    """'Skip lag', beside '▸▸ Fast', shows while a game is at its lag;
    clicked, a coin decides who breaks and the winner breaks at once,
    playing white from the spot chosen, the camera facing the foot; then
    it hides; in the sandbox it never shows."""
    window = self.openWindow()
    panel = window.panel
    self.assertEqual(window.match().phase, 'lag')
    self.assertFalse(panel.skipButton.isHidden())
    fast, skip = panel.fastButton.geometry(), panel.skipButton.geometry()
    self.assertEqual(fast.top(), skip.top())
    self.assertGreater(skip.left(), fast.right())
    self.assertLessEqual(skip.right(), panel.width())
    self.click(panel.skipButton)
    match = window.match()
    self.assertEqual(match.phase, 'break')
    self.assertEqual(match.cueBall(), 'white')
    self.assertEqual(window.view.balls,
                     window.view.table.openingFor('white', 4))
    self.assertIn('Lag skipped', panel.callWords)
    self.assertTrue(panel.skipButton.isHidden())
    window.newGame()
    window.skipLag('yellow')
    self.assertEqual(window.match().starter, 1)
    self.click(window.toolBar.sandboxButton)
    self.assertTrue(panel.skipButton.isHidden())
    window.close()

  def run_aim_speed(self) -> None:
    """The aim line shows the shot's speed: the panel's power reaches the
    scene in mm/s, at once and whenever it changes."""
    window = self.openWindow()
    view, panel = window.view, window.panel
    self.assertAlmostEqual(view.sceneValue('aimSpeed'), panel.speed, 6)
    panel.powerSlider.quantity = 6.5
    self.assertAlmostEqual(view.sceneValue('aimSpeed'), 6500.0, 6)
    panel.powerSlider.quantity = 0.5
    self.assertAlmostEqual(view.sceneValue('aimSpeed'), 500.0, 6)
    window.close()

  def run_field_of_view(self) -> None:
    """The camera takes in 36 degrees at first; 'Field of view' sets
    it, 20 to 90."""
    window = self.openWindow()
    view, slider = window.view, window.toolBar.viewSlider
    self.assertAlmostEqual(view.sceneValue('cameraView'), 36.0, 6)
    slider.quantity = 60.0
    self.assertAlmostEqual(view.sceneValue('cameraView'), 60.0, 6)
    slider.quantity = 200.0
    self.assertAlmostEqual(view.sceneValue('cameraView'), 90.0, 6)
    window.close()

  def run_hit_picker(self) -> None:
    """In the regular view the face is not in the panel (the user);
    while the full map shows, a click on it chooses the point struck,
    said in words; past the miscue limit it is drawn in; 'Centre' takes
    the middle again; the power sets the speed."""
    window = self.openWindow()
    panel = window.panel
    picker = panel.picker
    self.assertTrue(picker.isHidden())
    self.click(window.toolBar.fullButton)
    self.assertFalse(picker.isHidden())
    self.click(picker, picker.pointOf(0.3, -0.2))
    self.assertAlmostEqual(panel.top, 0.3, 1)
    self.assertAlmostEqual(panel.side, -0.2, 1)
    self.assertIn('up', panel.hitWords())
    self.assertIn('left', panel.hitWords())
    self.click(picker, picker.pointOf(0.9, 0.0))
    self.assertAlmostEqual(panel.top, 0.5, 2)
    self.click(panel.centreButton)
    self.assertEqual((panel.top, panel.side), (0.0, 0.0))
    self.assertIn('middle', panel.hitWords())
    panel.powerSlider.quantity = 4.5
    self.assertAlmostEqual(panel.speed, 4500.0, 6)
    window.close()

  def run_new_balls(self) -> None:
    """New balls move in the scene."""
    window = self.openWindow()
    view = window.view
    view.balls = (Ball('white', 100.0, 200.0),
                  Ball('yellow', 700.0, 1400.0),
                  Ball('red', 1300.0, 2600.0))
    place = view.sceneValue('redPlace')
    self.assertAlmostEqual(place.x(), 590.0, 3)
    self.assertAlmostEqual(place.z(), -1180.0, 3)
    self.assertEqual(view.balls[0].name, 'white')
    window.close()

  def assertLaid(self, window: BilliardsWindow, balls: tuple) -> None:
    """The balls lie as 'balls' say, in the scene too."""
    view = window.view
    self.assertEqual(view.balls, balls)
    for ball in balls:
      place = view.sceneValue('%sPlace' % ball.name)
      wanted = view.scenePlace(ball.x, ball.y, view.table.radius)
      self.assertAlmostEqual(place.x(), wanted.x(), 3)
      self.assertAlmostEqual(place.z(), wanted.z(), 3)

  def run_trails(self) -> None:
    """Seen from above, a shot is drawn as it goes: the cue ball's way
    bold, the hand behind where it set off, pointing the way it went,
    lying over the balls, the cushions and the rails,
    a faint ball where it set off; once all rest the trails stay; 'Hand'
    hides the hand and shows it again; 'Reset' takes the trails away."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel, bar = window.view, window.panel, window.toolBar
    self.click(bar.sandboxButton)
    self.click(bar.resetButton)
    self.assertFalse(view.sceneValue('trailsShown'))
    self.assertTrue(bar.handBox.checked)
    self.assertTrue(view.sceneValue('handShown'))
    lift = view.sceneValue('handLift')
    self.assertGreater(lift, view.sceneValue('cushionTop'))
    self.assertGreater(lift, 2.0 * view.table.radius)
    white = window.cueBall()
    start = view.scenePlace(white.x, white.y, 0.0)
    panel.powerSlider.quantity = 3.0
    window.shoot(0.0, -1.0)
    self.assertTrue(self.waitUntil(
      lambda: window.recording().count() > 300, 10000))
    window.advance(0.3)
    self.assertTrue(view.sceneValue('trailsShown'))
    self.assertEqual(list(view.sceneValue('boldTrails')), ['white'])
    hands = view.sceneValue('hands')
    self.assertEqual(len(hands), 1)
    self.assertAlmostEqual(hands[0]['x'], start.x(), 3)
    self.assertAlmostEqual(hands[0]['z'], start.z(), 3)
    self.assertAlmostEqual(hands[0]['angle'], -90.0, 6)
    starts = view.sceneValue('trailStarts')
    self.assertEqual([place['color'] for place in starts], ['#f2ecd9'])
    self.assertAlmostEqual(starts[0]['z'], start.z(), 3)
    self.assertIsInstance(view.sceneValue('trailShapes')['white'], Prism)
    self.settle(window)
    self.assertTrue(view.sceneValue('trailsShown'))
    self.click(bar.handBox)
    self.assertFalse(bar.handBox.checked)
    self.assertFalse(view.sceneValue('handShown'))
    self.click(bar.handBox)
    self.assertTrue(view.sceneValue('handShown'))
    self.click(bar.resetButton)
    self.assertFalse(view.sceneValue('trailsShown'))
    window.close()

  def run_trails_cleared(self) -> None:
    """The next shot takes the last one's trails away as it is struck:
    every ball's way, the faint balls and the hands, the hand then
    behind where the cue ball sets off, pointing the way it goes; then
    it draws only the ways of the balls moving in it."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel, bar = window.view, window.panel, window.toolBar
    self.click(bar.sandboxButton)
    self.click(bar.resetButton)
    panel.powerSlider.quantity = 3.0
    window.shoot(0.0, -1.0)
    self.assertTrue(self.waitUntil(
      lambda: window.recording().count() > 300, 10000))
    window.advance(0.3)
    self.assertEqual(list(view.sceneValue('trailNames')), ['white'])
    self.settle(window)
    self.assertTrue(view.sceneValue('trailsShown'))
    panel.chooseCue('yellow')
    yellow = window.cueBall()
    window.shoot(0.0, 1.0)
    for name in ('trailNames', 'trailStarts'):
      self.assertEqual(list(view.sceneValue(name)), [])
    self.assertTrue(view.sceneValue('trailsShown'))
    hands = view.sceneValue('hands')
    self.assertEqual(len(hands), 1)
    start = view.scenePlace(yellow.x, yellow.y, 0.0)
    self.assertAlmostEqual(hands[0]['x'], start.x(), 3)
    self.assertAlmostEqual(hands[0]['z'], start.z(), 3)
    self.assertAlmostEqual(hands[0]['angle'], 90.0, 6)
    self.assertTrue(self.waitUntil(
      lambda: window.recording().count() > 300, 10000))
    window.advance(0.1)
    self.assertTrue(view.sceneValue('trailsShown'))
    self.assertEqual(list(view.sceneValue('trailNames')), ['yellow'])
    window.close()

  def run_opening_side(self) -> None:
    """While the balls lie as a game opens, 'Left spot' and 'Right spot'
    lay the cue ball on spot 4 or 5, the one it lies on lit; spot 5 is
    on the right of the head spot as the player breaking sees it, from
    the head end; 'Reset' keeps the side, and lays the opening for the
    cue ball chosen; once a shot is played the choice is gone."""
    window = self.openWindow()
    window.frameTimer.stop()
    view, panel, bar = window.view, window.panel, window.toolBar
    table = view.table
    self.click(bar.sandboxButton)
    self.click(bar.resetButton)
    self.assertEqual(window.openingSpot(), 4)
    self.assertTrue(panel.spotFourButton.isVisibleTo(panel))
    self.assertEqual((panel.spotFourButton.text, panel.spotFiveButton.text),
                     ('Left spot', 'Right spot'))
    self.assertTrue(panel.spotFourButton.checked)
    self.click(panel.spotFiveButton)
    self.assertEqual(view.balls, table.openingFor('white', 5))
    self.assertTrue(panel.spotFiveButton.checked)
    self.assertFalse(panel.spotFourButton.checked)
    self.assertLess(window.cueBall().x, table.headSpot()[0])
    self.click(bar.resetButton)
    self.assertEqual(view.balls, table.openingFor('white', 5))
    self.click(panel.yellowButton)
    self.assertEqual(window.openingSpot(), 0)
    self.assertFalse(panel.spotFourButton.isVisibleTo(panel))
    self.click(bar.resetButton)
    self.assertEqual(view.balls, table.openingFor('yellow', 5))
    self.click(panel.spotFourButton)
    self.assertEqual(view.balls, table.openingFor('yellow', 4))
    panel.powerSlider.quantity = 1.0
    window.shoot(0.0, -1.0)
    self.assertFalse(panel.spotFourButton.isVisibleTo(panel))
    self.settle(window)
    self.assertEqual(window.openingSpot(), 0)
    self.assertFalse(panel.spotFourButton.isVisibleTo(panel))
    lying = view.balls
    window.chooseSpot(5)
    self.assertEqual(view.balls, lying)
    window.close()

  def run_new_game_running(self) -> None:
    """With the frames running, 'New game' in the middle of the lag lays
    the balls for the lag again, and in the sandbox 'Reset' in the middle
    of a shot lays them as a game opens, in the scene too; they stay so
    as the frames go on."""
    window = self.openWindow()
    view, panel, bar = window.view, window.panel, window.toolBar
    table = view.table
    window.shoot(0.0, -1.0)
    window.shoot(0.0, -1.0)
    self.assertTrue(window.playing)
    self.wait(300)
    self.click(bar.resetButton)
    self.assertFalse(window.playing)
    self.assertLaid(window, table.lagPosition())
    self.wait(600)
    self.assertLaid(window, table.lagPosition())
    self.click(bar.sandboxButton)
    self.click(bar.resetButton)
    panel.powerSlider.quantity = 3.0
    window.shoot(0.0, -1.0)
    self.wait(400)
    self.click(bar.resetButton)
    self.assertLaid(window, table.opening())
    self.wait(600)
    self.assertLaid(window, table.opening())
    window.close()
