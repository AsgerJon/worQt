"""
The real car's racing driver (user, 2026-11-15: "park the old car ...
inside the grass on the Dover track, put this car there instead, have
an AI driver take the wheel").

'RealCarRacer' races the real car round the oval as the racing robot
races the old one ('_robot.RacingRobot': its line low on the banking,
its speed plan, pure pursuit with the counter-steer, the damping and
the trim against drift), through the real car's own controls as a
driver works them ('_realcar.RealCarControls'): its hands turn the
steering wheel (at a hand's pace, 'HANDS'; the column's answer
measured on the car, 'ANSWER'), its right foot the throttle or the
brakes (the foot's pressure through the anti-lock system), its left
foot the clutch and its hand the gear stick: it pulls away in first
slipping the clutch by the engine's revolutions ('LAUNCH_HIGH',
'LAUNCH_LOW'), shifts up near the limiter ('UP') and down when the
engine labours ('DOWN'), each shift the throttle shut, the clutch down,
the stick through the gate (the synchro holding it till the gear is at
speed), the clutch let up as the throttle opens again; it starts a
stalled engine, and stuck it backs out in reverse. It moves nothing
else: the caller works the drivetrain and the brakes each call as the
controls say ('drivetrainWorked', 'Antilock.worked').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._assembly import Assembly
from ._drivetrain import FINAL, GEARS, NAMES, Reading, readingOf
from ._realcar import CHASSIS, CORNERS, FIRST_CORNER, FOOT, WHEELBASE
from ._realcar import RealCarControls
from ._robot import RacingRobot
from ._vectors import conjugate, rotated

#  How the real car answers its steering wheel, steady: the wheel's
#  angle a curve of 1/m asks is the wheelbase times this, at 'v' m/s,
#  first + second x v (at a crawl 15.3: its rack's 15.4 to 1, neutral;
#  the second a guess at its understeer, the trim takes the rest); the
#  most the hands turn the wheel either way, rad (its lock, as the
#  player's: 'STEER_MOST'), and how fast, rad/s (the player's
#  'STEER_RATE'); the old car's column gains in the real car's wheel
#  (its column turned 1.33 to its front wheels, the real car's wheel
#  15.4).
ANSWER = (15.3, 0.1)
LOCK, HANDS = 3.0 * math.pi + 0.3, 2.0 * math.pi
SCALE = 15.4 / 1.33
#  The engine's revolutions a minute it shifts up past and down under
#  (its limiter 7500; up at 6800 each next gear lands at 4500 to 5600,
#  down at 3500 each lower at 4300 to 5300: no hunting); while pulling
#  away in first, the clutch let up while the engine turns faster than
#  'LAUNCH_HIGH', pressed back while slower than 'LAUNCH_LOW', a second's
#  travel each way 'LAUNCH_UP', 'LAUNCH_DOWN'; the throttle held open
#  at least 'LAUNCH_OPEN' then; the clutch let up after a shift in
#  'RELEASE' s; pulling away below 'LAUNCH_SPEED' m/s; under 'STALL_GUARD'
#  rpm in gear the clutch goes down (not to stall braking).
UP, DOWN = 6800.0, 3500.0
LAUNCH_HIGH, LAUNCH_LOW, LAUNCH_UP, LAUNCH_DOWN = 3000.0, 1800.0, 1.0, 3.0
LAUNCH_OPEN, RELEASE, LAUNCH_SPEED, STALL_GUARD = 0.5, 0.25, 4.0, 1300.0
#  The throttle backing out in reverse (stuck).
BACKING_OPEN = 0.6
#  How the driver's foot feathers the throttle as the driven wheels spin
#  (found in the window, 2026-11-15: flat out pulling away on the
#  banking, the open differential spun the right rear's rim to 29 m/s
#  with the car at 4): a driven wheel's rim faster than the car by more
#  than 'SPIN_FREE' m/s and 'SPIN_SHARE' of its speed, the share of the
#  throttle it gives falls 'TRACTION_CUT' a second (to 'TRACTION_LEAST'),
#  else rises back 'TRACTION_BACK' a second.
SPIN_FREE, SPIN_SHARE = 1.5, 0.08
TRACTION_CUT, TRACTION_BACK, TRACTION_LEAST = 5.0, 1.5, 0.15
#  The gears forward in order, each one's ratio (input over output), the
#  final drive's; the brakes' share rolling back before first goes in.
FORWARD = NAMES[:5]
RATIOS = tuple(driven / driving for driving, driven in GEARS)
FINAL_RATIO = FINAL[1] / FINAL[0]
ROLLING_BACK = 0.5


class RealCarRacer(RacingRobot):
  """
  RealCarRacer races the real car ('assembly', worked by 'controls')
  round the oval ('RacingRobot'), working its steering wheel, pedals
  and gear stick ('act'); 'shifting' says what its left foot and hand
  are doing: 'driving' (the clutch up), 'clutching' (down, the stick on
  its way to 'gear'), 'releasing' (letting the clutch up after a
  shift), 'launching' (pulling away in first), 'starting' (the starter
  turning a stalled engine).
  """

  def __init__(self, assembly: Assembly,
               controls: RealCarControls) -> None:
    RacingRobot.__init__(self, None)
    self.assembly, self.controls = assembly, controls
    self.chassis = CHASSIS
    self.wheels = tuple(FIRST_CORNER + 6 * corner + 3
                        for corner in range(len(CORNERS)))
    self.wheelbase, self.answer, self.lock = WHEELBASE, ANSWER, LOCK
    self.hands, self.scale = HANDS, SCALE
    self.shifting, self.gear, self.traction = 'driving', 'N', 1.0

  def speedOf(self, states: tuple) -> float:
    """The 'speedOf' method returns how fast the real car goes along its
    chassis' own forward, m/s."""
    chassis = states[self.chassis]
    return rotated(conjugate(chassis.turn), chassis.velocity)[0]

  def wantedGear(self, reading: Reading, speed: float) -> str:
    """The 'wantedGear' method returns the gear the driver wants, the
    stick as 'reading' says, the car going 'speed' m/s forward (below
    nought back): reverse backing out; first pulling away (or rolling
    back); then by the revolutions the car's speed makes in each gear
    ('rpmIn': a driven wheel spinning, or the clutch slipping as it pulls
    away, the engine's own are far higher): out of gear the highest
    that turns the engine no slower than 'DOWN'; the next up past 'UP'
    (if it turns it no slower than 'DOWN'), the next down under 'DOWN'
    (if it turns it no faster than 'UP'); else as it is."""
    if self.backing > 0.0:
      return 'R'
    if speed < LAUNCH_SPEED:
      return '1'
    gear = reading.gear
    if gear not in FORWARD:
      for name in reversed(FORWARD):
        if self.rpmIn(speed, name) >= DOWN:
          return name
      return '1'
    at = FORWARD.index(gear)
    now = self.rpmIn(speed, gear)
    if now > UP and at + 1 < len(FORWARD) and (
        self.rpmIn(speed, FORWARD[at + 1]) >= DOWN):
      return FORWARD[at + 1]
    if now < DOWN and at > 0 and self.rpmIn(speed, FORWARD[at - 1]) < UP:
      return FORWARD[at - 1]
    return gear

  @staticmethod
  def rpmIn(speed: float, gear: str) -> float:
    """The 'rpmIn' method returns the revolutions a minute the engine
    would turn in forward gear 'gear' rolling at 'speed' m/s."""
    from ._tyred import tyreOf
    turning = speed / tyreOf(1, 2.3e5).radius
    return turning * RATIOS[FORWARD.index(gear)] * FINAL_RATIO * (
      30.0 / math.pi)

  def feathered(self, reading: Reading, speed: float,
                seconds: float) -> float:
    """The 'feathered' method returns the share of the throttle the foot
    gives now: less while a driven wheel spins past the car ('SPIN_FREE',
    'SPIN_SHARE'), more again once none does."""
    spin = max(reading.left, reading.right) - max(speed, 0.0)
    if spin > SPIN_FREE + SPIN_SHARE * abs(speed):
      self.traction = max(TRACTION_LEAST,
                          self.traction - TRACTION_CUT * seconds)
    else:
      self.traction = min(1.0, self.traction + TRACTION_BACK * seconds)
    return self.traction

  def act(self, states: tuple, seconds: float) -> None:
    """The 'act' method turns the steering wheel to 'column', and works
    the throttle or the brakes as 'throttle' asks (the brakes below
    nought, the foot's 'FOOT' at -1), the clutch and the stick for the
    gear it wants ('wantedGear'), the starter if the engine stalled."""
    controls = self.controls
    drive = controls.drive
    controls.steer.value = self.column
    reading = readingOf(drive, states)
    speed = self.speedOf(states)
    feather = self.feathered(reading, speed, seconds)
    open_ = max(0.0, self.throttle) * feather
    if self.backing > 0.0:
      open_ = BACKING_OPEN
    controls.line.pressure = FOOT * min(1.0, max(0.0, -self.throttle))
    controls.brakes.pulled = False
    drive.starting = False
    if not drive.running:
      self.shifting = 'starting'
      drive.pedal, drive.asked, drive.throttle = 1.0, 'N', 0.0
      drive.starting = True
      return
    if self.shifting == 'starting':
      self.shifting = 'driving'
    engaged = drive.shifter.engaged
    if self.shifting == 'driving':
      wanted = self.wantedGear(reading, speed)
      if wanted != engaged:
        self.shifting, self.gear = 'clutching', wanted
    if self.shifting == 'clutching':
      if self.backing > 0.0 or self.gear == 'R':
        self.gear = 'R' if self.backing > 0.0 else '1'
      elif speed < LAUNCH_SPEED:
        self.gear = '1'
      wanted = self.gear
      drive.pedal, drive.asked, drive.throttle = 1.0, wanted, 0.0
      if (wanted == 'R') != (speed < -0.5) and abs(speed) > 0.5 and (
          wanted in ('1', 'R')):
        controls.line.pressure = max(controls.line.pressure,
                                     FOOT * ROLLING_BACK)
      if engaged == wanted and drive.pressed > 0.9:
        self.shifting = ('launching' if wanted in ('1', 'R')
                         and abs(speed) < LAUNCH_SPEED else 'releasing')
      return
    if self.shifting == 'launching':
      drive.throttle = max(open_, LAUNCH_OPEN * feather)
      if reading.rpm > LAUNCH_HIGH:
        drive.pedal = max(0.0, drive.pedal - LAUNCH_UP * seconds)
      elif reading.rpm < LAUNCH_LOW:
        drive.pedal = min(1.0, drive.pedal + LAUNCH_DOWN * seconds)
      if drive.pedal <= 0.0 or abs(speed) > LAUNCH_SPEED:
        self.shifting = 'releasing'
      return
    if self.shifting == 'releasing':
      drive.pedal = max(0.0, drive.pedal - seconds / RELEASE)
      drive.throttle = open_ * (1.0 - drive.pedal)
      if drive.pedal <= 0.0:
        self.shifting = 'driving'
      return
    drive.pedal, drive.throttle = 0.0, open_
    if engaged is not None and reading.rpm < STALL_GUARD:
      self.shifting, self.gear = 'clutching', '1'

  def _unstuck(self, speed: float, seconds: float) -> None:
    """Counts the robot stuck ('RobotDriver._unstuck') only while it
    drives with the clutch up (pulling away is slow at first)."""
    if self.shifting != 'driving' and self.backing <= 0.0:
      self._stuck = 0.0
    RacingRobot._unstuck(self, speed, seconds)
