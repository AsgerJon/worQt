"""
The robot driver (user, 2026-11-12: "something is seriously wrong with
this car. We should be able to navigate the oval easily. we can't.
Let's do what Musk never did: Actual self driving. Make a robot that
can navigate the oval, record the vibrations of the vehicle during
driving and then saving them to a file so we can analyze").

'RobotDriver' drives the car round the oval through the controls a
person has: it turns the column as the hands do ('steer', any angle,
no faster than 'HANDS_RATE'), and works the pedals ('drive', any share
of the throttle or the brakes); it moves nothing else. It senses what
a robot with satellite navigation and a gyro would: where the car is,
which way it faces, how fast it goes. Steering: pure pursuit of a point
on its line ('out' m from the oval's middle line) 'LOOK_TIME' s ahead
(no nearer than 'LOOK_LEAST'), the curve to it asked of the column as
the car answers its column on the flat (column = curve x wheelbase x
(1.45 + 0.014 v), measured on the car); speed: the throttle by how far
under its 'speed' the car is, the brakes (gently) by how far over.
Stuck on the throttle (nose in the wall) it backs out on the opposite
lock; making no way for long it is 'stranded' (whoever runs it sets it
on the start line again).

'VibrationRecorder' samples the car as it goes ('CHANNELS'): where it
is on the oval, its speed and slip, the column asked and had, the
throttle; an accelerometer and a gyro at the chassis' centre of mass
(specific force, as a real one reads: gravity in it, m/s², in the
chassis' frame; turning rates, rad/s, likewise); and each corner's
knuckle: its rise over its ride height on the chassis, its upward
acceleration in the chassis' frame, its wheel's toe, camber and spin.
Accelerations are the change in velocity over a sample (what an
accelerometer averaging over that time reads). 'saved' writes a CSV
(a header row of the channels' names, a row a sample) and a JSON beside
it (the channels' units and meanings, the rate, the run).

'robotLaps' builds the car on the oval, lets the robot drive it from
the start line for so many laps, recording as it goes, and reports its
progress.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import math
import random
import time

import numpy

from ._car import CORNERS, STEER_LOCK, WHEELBASE, CarBuild, camberOf
from ._car import carBuilt, carPlaced, drive, ovalWorld, speedOf, steer
from ._car import steeringOf, toeOf, wheelSpinOf
from ._course import OVAL
from ._terrain import OVAL_LENGTH
from ._vectors import conjugate, dot, minus, rotated
from ._world import FULL, LIVE, Fidelity

#  How far ahead the robot looks, s at its speed, and at least, m.
LOOK_TIME, LOOK_LEAST = 0.6, 8.0
#  How fast its hands turn the column, rad/s.
HANDS_RATE = 1.5
#  The throttle a m/s under its speed, and the brakes a m/s over.
SPEED_GAIN, BRAKE_GAIN = 0.5, 0.1
#  How the car answers its column on the flat, steady (measured on it,
#  5 to 30 m/s): the column a curve of 1/m asks is the wheelbase times
#  this, at 'v' m/s: first + second x v.
_ANSWER = (1.45, 0.014)
#  How often the robot decides, s.
DECIDES = 0.01
#  The most a robot's hands trim the column against a lasting error off
#  its line, rad (see 'RACE_TRIM'); only ever outward, up the banking.
TRIM_MOST = 0.05
#  The most a PID steering robot's integral holds, m s ('_pidWanted').
PID_I_MOST = 3.0
#  Stuck (on the throttle but under 'STUCK_SPEED' m/s for 'STUCK' s:
#  nose in the wall), the robot backs out for 'BACKING' s on the
#  opposite lock, swinging its nose toward its line; making no
#  'RESCUE_GAIN' m of way in 'RESCUE' s (rolled over, or stuck all the
#  same) it is 'stranded' (the window, or the trainer, sets it on the
#  start line again). Found 2026-11-13: paced 1.3 all round, the racer
#  hit the wall at 32 m/s in turn three, rolled over and back onto its
#  wheels, drove through the infield and back, and stopped nose in the
#  wall for good, flat on the throttle.
STUCK, STUCK_SPEED, BACKING = 1.5, 1.0, 2.5
RESCUE, RESCUE_GAIN = 20.0, 10.0


class RobotDriver:
  """
  RobotDriver drives 'car' round the oval at 'speed' m/s, 'out' m out
  from its middle line ('take'); 'column' and 'throttle' are what it
  last asked; 'along' how far round the oval the car has gone since it
  started (laps counted), 'off' how far it is from its line now, m;
  'backing' how long it still backs out of where it got stuck, s;
  'stranded' whether it has made no way for 'RESCUE' s. What it drives
  ('car': None for another car, which a subclass drives, 'act'): the
  chassis' body ('chassis') and the wheels' ('wheels'), the wheelbase,
  m, how the car answers its column ('answer': the column a curve asks,
  over the curve times the wheelbase, first + second x speed), the most
  the column turns either way ('lock', rad) and how fast the hands turn
  it ('hands', rad/s; 'handsAccel', rad/s², how fast its hands speed up
  and slow down: None, at once), how it steers ('steering': 'pursuit',
  pure pursuit with its counter-steer, damping and trim; 'pid', a PID on
  the line ahead, 'kp', 'ki', 'kd': '_pidWanted'), and how much of the
  column a radian of its own
  gains ask for ('scale': the counter-steer, the damping and the trim
  were found on the old car's column, 1.33 to its wheels); and the
  'course' it drives round ('_course': the oval by default); how near
  it looks ahead at least ('least', m: 'LOOK_LEAST').
  """

  least, handsAccel = LOOK_LEAST, None
  steering, kp, ki, kd = 'pursuit', 1.0, 0.0, 0.0

  def __init__(self, car: CarBuild, speed: float, out: float,
               course: object = None) -> None:
    self.car, self.speed, self.out = car, speed, out
    self.course = OVAL if course is None else course
    if car is not None:
      self.chassis, self.wheels = car.chassis, car.wheels
    self.wheelbase, self.answer, self.lock = WHEELBASE, _ANSWER, STEER_LOCK
    self.hands, self.scale, self.turning = HANDS_RATE, 1.0, 0.0
    self.integral, self.lastError = 0.0, None
    self.look, self.braking, self.counter = LOOK_TIME, BRAKE_GAIN, 0.0
    self.trimming, self.trim, self.damping = 0.0, 0.0, 0.0
    self.column, self.throttle = 0.0, 0.0
    self.along, self.off, self._round = 0.0, 0.0, None
    self.backing, self._stuck, self._way = 0.0, 0.0, (0.0, 0.0)

  @property
  def stranded(self, ) -> bool:
    """Whether the robot has made no 'RESCUE_GAIN' m of way round for
    'RESCUE' s."""
    return self._way[1] > RESCUE

  def take(self, states: tuple, seconds: float) -> None:
    """The 'take' method works the column and the pedals for the next
    'seconds', the car being in 'states'."""
    chassis = states[self.chassis]
    x, y = chassis.place[0], chassis.place[1]
    course = self.course
    out, round_ = course.placeOf(x, y)
    if self._round is not None:
      moved = round_ - self._round
      moved -= course.length * round(moved / course.length)
      self.along += moved
    self._round, self.off = round_, out - self.lineAt(round_)
    speed = self.speedOf(states)
    ahead = rotated(chassis.turn, (1.0, 0.0, 0.0))
    heading = math.atan2(ahead[1], ahead[0])
    if self.steering == 'pid':
      wanted = self._pidWanted(chassis, round_, speed, heading, seconds)
    else:
      wanted = self._pursued(chassis, round_, speed, heading, seconds)
    wanted = max(-self.lock, min(self.lock, wanted))
    if self.backing > 0.0:
      wanted = -self.lock if wanted > 0.0 else self.lock
    self.column += self._turned(wanted, seconds)
    under = self.wantedAt(round_, speed) - speed
    gain = SPEED_GAIN if under > 0.0 else self.braking
    self.throttle = max(-1.0, min(1.0, gain * under))
    self.throttle = min(self.throttle, self.liftFor(states))
    self._unstuck(speed, seconds)
    self.act(states, seconds)

  def _pursued(self, chassis: object, round_: float, speed: float,
               heading: float, seconds: float) -> float:
    """Returns the column pure pursuit asks for: the curve to the line's
    point 'look' s ahead (no nearer than 'least') as the car answers it,
    and its counter-steer, damping and trim ('counter', 'damping',
    'trimming')."""
    course = self.course
    x, y = chassis.place[0], chassis.place[1]
    reach = max(self.least, self.look * abs(speed))
    aimX, aimY, _ = course.at(round_ + reach, self.lineAt(round_ + reach))
    angle = math.atan2(aimY - y, aimX - x) - heading
    angle = (angle + math.pi) % (2.0 * math.pi) - math.pi
    curve = 2.0 * math.sin(angle) / max(math.hypot(aimX - x, aimY - y),
                                        1e-6)
    answer, scale = self.answer, self.scale
    wanted = curve * self.wheelbase * (answer[0] + answer[1] * abs(speed))
    if self.counter and abs(speed) > 5.0:
      local = rotated(conjugate(chassis.turn), chassis.velocity)
      wanted += scale * self.counter * math.atan2(local[1], abs(local[0]))
    if self.damping and abs(speed) > 5.0:
      line = course.at(round_, self.lineAt(round_))[2]
      wanted += scale * self.damping * (
        chassis.velocity[0] * math.sin(line)
        - chassis.velocity[1] * math.cos(line))
    if self.trimming and abs(speed) > 5.0:
      self.trim = max(-TRIM_MOST, min(0.0, self.trim + self.trimming
                                      * self.off * seconds))
      wanted += scale * self.trim
    return wanted

  def _pidWanted(self, chassis: object, round_: float, speed: float,
                 heading: float, seconds: float) -> float:
    """Returns the column a PID asks for (user, 2026-11-15: "Implement
    PID. Start D at 0 and only let it rise if abs necessary and only by a
    small bit"): the error how far right of its line the car would be
    'look' s ahead (no nearer than 'least') going on as it points, in
    the line's own frame here: its offset ('off') less the reach times
    its heading's angle to the line (ahead, so that a P alone holds: the
    offset alone answers the column twice over, an undamped swing; the
    chassis' heading, so a slide counter-steers itself); fed forward the
    line's own bend over that reach as the car answers it ('answer');
    then 'kp' times the error, 'ki' its integral ('integral', m s,
    within 'PID_I_MOST'), 'kd' its rate, each in the column pure pursuit
    would give a m of it at that reach (P one: pursuit's own). (First
    the error was where the point straight ahead lies from the line's
    point at that reach: on a curve that holds the line's own bend, so
    the bend was asked twice, the car cut in metres at each corner and
    swung out after: 1.1 m off on the mean, pursuit 0.64; now 0.68.
    The bend over the whole reach turns in early, cutting a corner by
    1.3 to 2.3 m; fed at a point 0, 0.15 or 0.3 s ahead, the street
    corners' sharp bends came in whole and late: slides of 34 to 67
    degrees, 5 to 7 m off.)"""
    course = self.course
    reach = max(self.least, self.look * abs(speed))
    lineWay = course.at(round_ + reach, self.lineAt(round_ + reach))[2]
    hereWay = course.at(round_, self.lineAt(round_))[2]
    turned = (heading - hereWay + math.pi) % (2.0 * math.pi) - math.pi
    error = self.off - reach * math.sin(turned)
    bend = ((lineWay - hereWay + math.pi) % (2.0 * math.pi) - math.pi) / (
      reach)
    answer = self.answer
    feed = bend * self.wheelbase * (answer[0] + answer[1] * abs(speed))
    gain = 2.0 * self.wheelbase * answer[0] / (reach * reach)
    self.integral = max(-PID_I_MOST, min(PID_I_MOST, self.integral
                                         + error * seconds))
    rate = 0.0 if self.lastError is None else (
      error - self.lastError) / max(seconds, 1e-9)
    self.lastError = error
    return feed + gain * (self.kp * error + self.ki * self.integral
                          + self.kd * rate)

  def _turned(self, wanted: float, seconds: float) -> float:
    """Returns how far the hands turn the column toward 'wanted' in
    'seconds': as far as 'hands' lets; with 'handsAccel' (smooth hands:
    user, 2026-11-15, "put a limit on how hard the ai changes inputs.
    Like put a penalty on jerky driving") their speed ('turning', rad/s)
    changing no faster than it, and no faster than lets them stop at
    'wanted' (the quickest smooth turn: no overshoot)."""
    left = wanted - self.column
    if self.handsAccel is None:
      step = self.hands * seconds
      return max(-step, min(step, left))
    accel = self.handsAccel
    aim = math.copysign(min(self.hands, math.sqrt(2.0 * accel * abs(left)),
                            abs(left) / max(seconds, 1e-9)), left)
    change = accel * seconds
    self.turning += max(-change, min(change, aim - self.turning))
    return self.turning * seconds

  def speedOf(self, states: tuple) -> float:
    """The 'speedOf' method returns how fast the car goes forward, m/s
    (backward below nought), 'states' having it."""
    return speedOf(self.car, states)

  def act(self, states: tuple, seconds: float) -> None:
    """The 'act' method works the car's controls as the robot last
    asked ('column', 'throttle': the brakes below nought) for the next
    'seconds', the car in 'states'."""
    steer(self.car, self.column)
    drive(self.car, states, self.throttle, seconds)

  def _unstuck(self, speed: float, seconds: float) -> None:
    """Backs out once stuck ('STUCK'), and counts how long the robot has
    made no way ('stranded')."""
    if self.backing > 0.0:
      self.backing = max(0.0, self.backing - seconds)
      self.throttle = -1.0
    elif self.throttle > 0.5 and speed < STUCK_SPEED:
      self._stuck += seconds
      if self._stuck > STUCK:
        self.backing, self._stuck = BACKING, 0.0
    else:
      self._stuck = 0.0
    best, since = self._way
    if self.along > best + RESCUE_GAIN:
      self._way = (self.along, 0.0)
    else:
      self._way = (best, since + seconds)

  def lineAt(self, along: float) -> float:
    """The 'lineAt' method returns how far out from the oval's middle
    line the robot's line runs 'along' m round it: 'out'."""
    return self.out

  def wantedAt(self, along: float, speed: float) -> float:
    """The 'wantedAt' method returns the speed the robot wants 'along'
    m round, going 'speed' m/s: its 'speed'."""
    return self.speed

  def liftFor(self, states: tuple) -> float:
    """The 'liftFor' method returns the most throttle the robot dares,
    the car being in 'states': all of it."""
    return 1.0


#  The racing robot (user, 2026-11-12: "Can you do something to the
#  robot to make it actually race? Like trying to go as fast as
#  possible?"): how much sideways grip it plans on, of the car's weight
#  pressing it into the banking (the road grips 1.0, but flat out the
#  car made 0.60 through turns one and two at 46 m/s and ran up the
#  bank at 0.71 into turn three at 50: its springs on their stops); how
#  far above the racing surface's inside edge its line runs, m (the
#  shortest way round; the car is 1.76 m across its tyres); how hard it
#  plans to brake, m/s², and brakes a m/s over (gently, mostly lifting:
#  at 5 m/s² and 0.3 its anti-lock worked at the turns' entries and the
#  fronts' flutter slid it 5.5 degrees; now 3.8, laps 0.1 s quicker);
#  how far ahead it plans, m, and steers, s (0.6 s weaved +-4 m at 50
#  m/s; 0.8 with 'RACE_DAMPING' holds the line closest); the slip of
#  the car past which it lifts (all of it at twice that), rad; how much
#  column it gives a radian of the car's slip, steering into a slide as
#  a driver does (its front wheels kept along the way it goes: at 0.6 of
#  grip, 3 degrees of slip and no countersteer, on the throttle at 42
#  m/s in turn three the tail stepped out to 20 degrees and it spun).
RACE_GRIP, RACE_MARGIN, RACE_BRAKING, RACE_BRAKE = 0.5, 2.0, 2.5, 0.05
RACE_PLAN, RACE_LOOK, RACE_SLIP = 200.0, 0.8, math.radians(2.0)
RACE_COUNTER = 1.33
#  How fast the racing robot's hands trim the column outward against a
#  lasting error below its line, rad a metre a second, and let the trim
#  go again above it (the integral of a PI, one-sided: on the back
#  straight's 9 degree banking pure pursuit settled 1.7 to 2.8 m below
#  its line, the more the faster it went, its inside wheels on the apron
#  10 s a lap; trimming both ways it also steered in harder against the
#  turns' understeer and slid 45 degrees).
RACE_TRIM = 0.01
#  How much column the racing robot gives a m/s of the car's drift across
#  its line, rad (steering against the drift, not only against where it
#  is: the user, 2026-11-13: "the robot keeps driving down on [the
#  apron]"; pure pursuit alone, at double power, came out of each turn 3
#  m over its line, rose to 5.8 and swung down through it to 2.5 m
#  under, mid straight, the inside wheels 1.5 m onto the apron, and
#  over its edge, 9 degrees on the straights, the car wobbled in yaw).
#  Flying laps at double power, damping / look-ahead: 0 / 1.0 s: 37.14
#  s, 3.13 s on the apron, -2.63..+5.83 m off; 0.003 / 1.0: 1.97 s;
#  0.006 / 1.0: none, -0.73..+4.40; 0.012 / 1.0: none, 36.95; 0.006 /
#  0.8: none, 36.88; 0.012 / 0.8 (these, 'RACE_LOOK'): none, 36.87,
#  -0.67..+2.36 m, the lowest wheel 0.51 m over the edge, slip <= 1.9.
RACE_DAMPING = 0.012
#  The racing robot's speed plan's parts, about this long, m, each its
#  own pace (a share of what the plan's grip allows; one, unless
#  learnt: 'LearningRacer'); the slip it counts as clean, rad.
RACE_PART, RACE_CLEAN = 50.0, math.radians(2.5)
#  How finely the racing robot's speed plan is laid round the oval, m.
_PLANNED = 2.0


class RacingRobot(RobotDriver):
  """
  RacingRobot races the oval: flat out but where its plan says
  ('wantedAt': the fastest each point of its line allows, 'capAt', the
  turns' curve and banking taken with the grip it dares there, and the
  slowest it must get down to ahead within 'RACE_PLAN' m, braking
  'RACE_BRAKING'); its line low on the banking ('lineAt'); lifting as
  the car slips ('liftFor'); a pace for each part of the oval ('paces',
  'partOf': all one; 'LearningRacer' learns them), 'partDone' told as
  it leaves each (its number, how long it took, s, the slip and the
  time on the apron met there, the speed it came in at); its line's
  curve measured through its points 'span' m either side ('shapeAt');
  how hard its plan brakes, m/s² ('decel': 'RACE_BRAKING').
  """

  span, decel = 6.0, RACE_BRAKING

  def __init__(self, car: CarBuild, course: object = None) -> None:
    RobotDriver.__init__(self, car, math.inf, 0.0, course)
    self.look, self.braking, self.counter = (RACE_LOOK, RACE_BRAKE,
                                             RACE_COUNTER)
    self.trimming, self.damping = RACE_TRIM, RACE_DAMPING
    length = self.course.length
    self.paces = [1.0] * max(1, int(round(length / RACE_PART)))
    self.slip, self.apron, self._part, self._entered = 0.0, 0.0, None, 0.0
    self._clock, self._worst, self._speed = 0.0, 0.0, 0.0
    count = int(round(length / _PLANNED))
    self._shapes = [self.shapeAt(k * length / count)
                    for k in range(count)]
    self._caps = [self.capAt(k * length / count)
                  for k in range(count)]

  def partOf(self, along: float) -> int:
    """The 'partOf' method returns which part of the oval 'along' m
    round lies in, counted from the start line."""
    count = len(self.paces)
    course = self.course
    return min(count - 1, int(((along - course.start) % course.length)
                              * count / course.length))

  def take(self, states: tuple, seconds: float) -> None:
    """The 'take' method races on for the next 'seconds' ('RobotDriver.
    take'), noting how the car goes in the part it is in (its slip, and
    how long a wheel of it is on the apron: 'onApron'), telling
    'partDone' of the part it has left."""
    RobotDriver.take(self, states, seconds)
    chassis = states[self.chassis]
    local = rotated(conjugate(chassis.turn), chassis.velocity)
    self.slip = math.atan2(local[1], max(abs(local[0]), 1e-6))
    part = self.partOf(self._round)
    if part != self._part:
      if self._part is not None:
        self.partDone(self._part, self._clock - self._entered,
                      self._worst, self.apron, self._speed)
      self._part, self._entered = part, self._clock
      self._worst, self.apron, self._speed = 0.0, 0.0, local[0]
    self._clock += seconds
    if abs(local[0]) > 5.0:
      self._worst = max(self._worst, abs(self.slip))
    if self.onApron(states):
      self.apron += seconds

  def onApron(self, states: tuple) -> bool:
    """The 'onApron' method tells whether a wheel of the car is on the
    apron (or below it), its middle inside the racing surface's edge."""
    for wheel in self.wheels:
      place = states[wheel].place
      if self.course.inside(place[0], place[1]) < 0.0:
        return True
    return False

  def gaveUp(self, ) -> None:
    """The 'gaveUp' method tells 'partDone' of the part the robot is in
    as though it left it now (stranded there: its time so far, the
    slip met), so what got it stranded is learnt from."""
    if self._part is not None:
      self.partDone(self._part, self._clock - self._entered, self._worst,
                    self.apron, self._speed)
      self._part = None

  def partDone(self, part: int, took: float, slip: float,
               apron: float, speed: float) -> None:
    """The 'partDone' method is told of each part as the robot leaves
    it: its number, how long it took, s, its worst slip, rad, how long a
    wheel was on the apron there, s, and how fast the car came into it,
    m/s. The plain racer learns nothing from it."""

  def paced(self, part: int) -> None:
    """The 'paced' method lays the plan anew over 'part' at its pace."""
    count = len(self._caps)
    for k in range(count):
      if self.partOf(k * self.course.length / count) == part:
        self._caps[k] = self.paces[part] * _capOf(*self._shapes[k],
                                                  RACE_GRIP)

  def lineAt(self, along: float) -> float:
    """The 'lineAt' method returns how far out from the middle line the
    racing line runs 'along' m round: 'RACE_MARGIN' over the inside
    edge."""
    return RACE_MARGIN - 0.5 * self.course.shapeAt(along)[0]

  def shapeAt(self, along: float) -> tuple:
    """The 'shapeAt' method returns the racing line's curve 'along' m
    round (through its points 6 m either side), 1/m, and the banking
    there, rad."""
    span = self.span
    points = [self.course.at(along + way, self.lineAt(along + way))[:2]
              for way in (-span, 0.0, span)]
    (ax, ay), (bx, by), (cx, cy) = points
    twice = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
    sides = (math.hypot(bx - ax, by - ay) * math.hypot(cx - bx, cy - by)
             * math.hypot(cx - ax, cy - ay))
    return 2.0 * twice / sides, self.course.shapeAt(along)[1]

  def capAt(self, along: float) -> float:
    """The 'capAt' method returns the fastest the racing line can be
    taken 'along' m round, m/s: its curve on its banking ('shapeAt')
    with 'RACE_GRIP', at the pace learnt there; without end on a
    straight."""
    return self.paces[self.partOf(along)] * _capOf(*self.shapeAt(along),
                                                   RACE_GRIP)

  def wantedAt(self, along: float, speed: float) -> float:
    """The 'wantedAt' method returns the speed the robot wants 'along' m
    round: the least of what each point of its plan ahead allows, braked
    down to from here."""
    count, best = len(self._caps), math.inf
    first = int(along / _PLANNED)
    for step in range(int(RACE_PLAN / _PLANNED) + 1):
      cap = self._caps[(first + step) % count]
      if cap < math.inf:
        best = min(best, math.sqrt(cap ** 2 + 2.0 * self.decel
                                   * step * _PLANNED))
    return best

  def liftFor(self, states: tuple) -> float:
    """The 'liftFor' method returns the most throttle the robot dares as
    the car slips: all of it under 'RACE_SLIP', none at twice that; all
    of it under 5 m/s (a slip at a walk means nothing: spun round and
    stopped, it must drive off again)."""
    chassis = states[self.chassis]
    local = rotated(conjugate(chassis.turn), chassis.velocity)
    if abs(local[0]) < 5.0:
      return 1.0
    slip = abs(math.atan2(local[1], abs(local[0])))
    return max(0.0, min(1.0, 2.0 - slip / RACE_SLIP))


#  The learning racer (user, 2026-11-12: "can't we do something fun?
#  Like a robot that reinforcement learns itself to go ever faster? He
#  would need a punishment if touching the apron though"). Each part of
#  the oval its pace and its lane (how far over the inside edge its line
#  runs there, m; the line drawn straight between the parts' middles);
#  each lap it tries each part a little otherwise ('LEARN_PACE',
#  'LEARN_LANE': the spread of its trials, a Gaussian policy) and is
#  scored there: the seconds it took, and punished 'APRON_COST' s for
#  every second a wheel was on the apron, 'SLIDE_COST' s for every
#  degree its worst slip there went past 'RACE_CLEAN', 'SPIN_COST' s for
#  a slip past 'SPIN'; scored better than it usually is there (its
#  baseline, followed at 'LEARN_MEMORY', as is the scores' spread), it
#  moves its pace and lane toward what it tried, worse, away
#  ('LEARN_RATE' of the trial a spread of score: REINFORCE with a
#  baseline, each part its own); within 'PACES' and 'LANES' (no lane
#  under 1 m: under 0.88, half the track, the inside wheels run on the
#  apron by design). A part is
#  scored with the 'LEARN_REACH' parts either side of it (its pace sets
#  the speed carried out of it, and the braking before it), and only
#  from a run come into at 'LEARN_FROM' m/s or more (not the crawl back
#  after a spin), and not in its first lap (a standing start: baselines
#  laid then made every flying pass after look far better, and the
#  first learning threw paces to their ends, 0.8 and 1.4, in a lap); a
#  pass counts at most 'LEARN_MOST' spreads, the spread first
#  'LEARN_SPREAD' s. Trained from scratch (LIVE):
#  trials 0.02 and 0.4 m at a rate 0.3 took 20 laps to 36.78 s (pace
#  +3.5 %); the rate 1.0 alone wandered, 37.95 to 38.97; trials 0.03
#  and 0.6 m at 1.0 made 36.70 by lap 8 (pace +5.2 %), its lanes rising
#  off the apron (2.3 m). The user, 2026-11-13: "it just repeats the
#  same lap over and over again": paced alike all round (LIVE, flying
#  laps), 1.0 laps 38.03 s again and again, 1.1 35.77 and 35.71, 1.2
#  37.23 then slid (47.97): two seconds to find, but each part scored
#  alone, by its own time, the trials hardly moved it. Scored with its
#  neighbours, each part learning alone (trials 0.06, rates 0.5-1.0),
#  laps stayed 38.0-38.8 for five laps of learning, the mean pace up to
#  +8.8 %: the plan brakes for the least cap ahead, so the parts learnt
#  slow held the lap ('LEARN_SHARED' below). From scratch (LIVE), 10
#  laps (the first standing, the second laying the baselines): trials
#  0.04, own 0.5, shared 2.0: 37.96 .. 36.74 35.70 35.64 35.73 35.50,
#  pace +12 %; these (0.03, 0.2, 4.0): 38.39 38.50 37.49 36.95 37.08
#  36.19 35.04 34.88, then over the edge at +22 % (36.96, 6.1 s on the
#  apron) and back to +17 %: pushing, overstepping, backing off.
LEARN_PACE, LEARN_LANE, LEARN_RATE, LEARN_MEMORY = 0.03, 0.6, 0.2, 0.2
LEARN_REACH, LEARN_FROM, LEARN_MOST, LEARN_SPREAD = 1, 20.0, 2.0, 0.1
#  The racer's pace shared by every part, learnt from every part's
#  trials at once ('LEARN_SHARED' of the trial a spread of score, over
#  the number of parts: one pass a lap gave each part too little to go
#  on, laps hardly quicker after two laps of learning), each part's own
#  pace on it ('LEARN_RATE': where it must back off, or may push on).
LEARN_SHARED = 4.0
APRON_COST, SLIDE_COST, SPIN_COST = 2.0, 0.05, 5.0
SPIN = math.radians(30.0)
PACES, LANES = (0.8, 1.4), (1.0, 8.0)


class LearningRacer(RacingRobot):
  """
  LearningRacer is a racing robot that learns by trial ('partDone',
  'learned'): the pace all parts share ('shared'), each part's own on
  it and its lane as learnt ('pace', 'lane'; 'paceLearnt' their mean)
  and as tried this lap ('paces', 'lanes'), its scores'
  baselines ('means', 'spreads'), how many passes it has 'learnt' from,
  its last pass' own 'score' and the parts it last passed ('passes':
  part, score, speed in); its 'brain' (what it has learnt) given to a
  new one carries on (its baselines only if scored over as many
  parts; one of another 'form' is not taken); 'seed' its trials' (None:
  as chance has it).
  """

  def __init__(self, car: CarBuild, brain: dict = None,
               seed: int = None) -> None:
    RacingRobot.__init__(self, car)
    count = len(self.paces)
    self.pace, self.lane = [1.0] * count, [RACE_MARGIN] * count
    self.lanes, self.shared = list(self.lane), 0.0
    self.means, self.spreads = [None] * count, [LEARN_SPREAD] * count
    self.learnt, self.score, self.passes = 0, 0.0, []
    self.trials = [(0.0, 0.0)] * count
    self.random = random.Random(seed)
    if brain is not None and brain.get('form') == BRAIN_FORM:
      self.pace, self.lane = list(brain['pace']), list(brain['lane'])
      self.learnt, self.shared = brain['learnt'], brain['shared']
      if brain.get('reach') == LEARN_REACH:
        self.means = list(brain['means'])
        self.spreads = list(brain['spreads'])
    for part in range(count):
      self.tried(part)

  @property
  def brain(self, ) -> dict:
    """What it has learnt, to be kept (JSON as it is)."""
    return {'pace': self.pace, 'lane': self.lane, 'means': self.means,
            'spreads': self.spreads, 'learnt': self.learnt,
            'reach': LEARN_REACH, 'shared': self.shared,
            'form': BRAIN_FORM}

  @property
  def paceLearnt(self, ) -> float:
    """The pace learnt, the parts' mean (the shared pace and each part's
    own on it)."""
    return self.shared + sum(self.pace) / len(self.pace)

  def tried(self, part: int) -> None:
    """The 'tried' method draws the trial 'part' is driven with next: its
    pace (the shared and its own) and lane as learnt, each spread a
    little at random."""
    pace = self.random.gauss(0.0, LEARN_PACE)
    lane = self.random.gauss(0.0, LEARN_LANE)
    self.trials[part] = (pace, lane)
    self.paces[part] = max(PACES[0], min(PACES[1], self.shared
                                         + self.pace[part] + pace))
    self.lanes[part] = max(LANES[0], min(LANES[1], self.lane[part] + lane))
    self.paced(part)

  def partDone(self, part: int, took: float, slip: float,
               apron: float, speed: float) -> None:
    """The 'partDone' method scores the pass through 'part' (its time,
    the apron's, the slide's and a spin's punishment); once the parts
    'LEARN_REACH' either side of one are passed, one after the other,
    the first come into fast enough ('LEARN_FROM'), a lap on from where
    it started, it learns from their scores together for the middle one
    and draws its next trial."""
    score = -took - APRON_COST * apron - SLIDE_COST * max(
      0.0, math.degrees(slip - RACE_CLEAN)) - (SPIN_COST if slip > SPIN
                                               else 0.0)
    self.score = score
    count, window = len(self.paces), 2 * LEARN_REACH + 1
    self.passes = (self.passes + [(part, score, speed)])[-window:]
    if (len(self.passes) < window or self.passes[0][2] < LEARN_FROM
            or self.along < self.course.length):
      return
    for (first, _, _), (then, _, _) in zip(self.passes, self.passes[1:]):
      if then != (first + 1) % count:
        return
    middle = self.passes[LEARN_REACH][0]
    self.learned(middle, sum(passed[1] for passed in self.passes))
    self.tried(middle)

  def learned(self, part: int, score: float) -> None:
    """The 'learned' method learns from 'score' for 'part' driven with
    its trial: toward the trial if it beat the part's baseline, away if
    not, its own pace 'LEARN_RATE' of it a spread of score, the shared
    'LEARN_SHARED' over the number of parts; the baseline and the
    spread follow."""
    mean = self.means[part]
    if mean is None:
      self.means[part] = score
      return
    spread = max(self.spreads[part], 1e-3)
    advantage = max(-LEARN_MOST, min(LEARN_MOST,
                                     (score - mean) / spread))
    pace, lane = self.trials[part]
    self.shared = max(PACES[0] - 1.0, min(PACES[1] - 1.0, self.shared
                      + LEARN_SHARED * advantage * pace / len(self.pace)))
    self.pace[part] = max(PACES[0] - self.shared, min(
      PACES[1] - self.shared, self.pace[part]
      + LEARN_RATE * advantage * pace))
    self.lane[part] = max(LANES[0], min(LANES[1], self.lane[part]
                                        + LEARN_RATE * advantage * lane))
    self.means[part] = mean + LEARN_MEMORY * (score - mean)
    self.spreads[part] = math.sqrt((1.0 - LEARN_MEMORY) * spread ** 2
                                   + LEARN_MEMORY * (score - mean) ** 2)
    self.learnt += 1

  def lineAt(self, along: float) -> float:
    """The 'lineAt' method returns how far out from the middle line the
    line runs 'along' m round: the lanes tried, drawn straight between
    the parts' middles, over the inside edge (the plain racer's line
    while they are not yet laid)."""
    lanes = getattr(self, 'lanes', None)
    if lanes is None:
      return RacingRobot.lineAt(self, along)
    count = len(lanes)
    course = self.course
    where = ((along - course.start) % course.length) * count / (
      course.length) - 0.5
    first = math.floor(where)
    share = where - first
    lane = ((1.0 - share) * lanes[first % count]
            + share * lanes[(first + 1) % count])
    return lane - 0.5 * self.course.shapeAt(along)[0]


#  Where a learning racer's brain is kept between runs (gitignored).
BRAIN = 'previews/racer-brain.json'
#  The form of brain the learning racer takes ('LearningRacer.brain'):
#  2, with its shared pace (2026-11-13). The first learner's (no form)
#  is not taken: in 81 laps in the window its parts' paces ran to their
#  ends (0.80 .. 1.40 side by side) and its lanes 0 to 8 m part to part.
BRAIN_FORM = 2


def brainOf(path: str) -> dict | None:
  """The 'brainOf' function returns the brain kept at 'path' ('Learning
  Racer.brain'), or None if none is (or it cannot be read)."""
  try:
    with open(path) as file:
      return json.load(file)
  except (OSError, ValueError):
    return None


def keptBrain(racer: 'LearningRacer', path: str) -> None:
  """The 'keptBrain' function writes 'racer''s brain to 'path'."""
  with open(path, 'w') as file:
    json.dump(racer.brain, file)


def trainRacer(laps: int, path: str, fidelity: Fidelity = LIVE,
               report: object = None) -> tuple:
  """The 'trainRacer' function has a learning racer (its brain from
  'path', if kept there) race 'laps' laps of the oval from the start
  line in a world as faithful as 'fidelity' says, keeping its brain at
  'path' after each lap; 'report' (if given) is called after each lap
  with (lap, its time, s, seconds on the apron in it, the racer), and
  with the time None when the racer was 'stranded' (set on the start
  line again, standing, its brain kept, the lap not counted). Returns
  the laps' times, s."""
  from ._laps import LapTimer
  car, world = carBuilt(0.5, fidelity), ovalWorld(fidelity)
  terrain = world.ground.terrain
  start = carPlaced(car.states, (0.0, 0.0, terrain.heightAt(0.0, 0.0)),
                    terrain.normalAt(0.0, 0.0))
  states, racer = start, LearningRacer(car, brainOf(path))
  timer, times, counted = LapTimer(0.0), [], 0
  clock, frame, apron = 0.0, 1.0 / 60.0, 0.0
  try:
    while len(times) < laps and clock < 120.0 * laps:
      racer.take(states, frame)
      states = world.advancedAll(car.assembly, states, frame, clock)
      clock += frame
      chassis = states[car.chassis]
      timer.seen(chassis.place[0], chassis.place[1], clock)
      if racer.onApron(states):
        apron += frame
      done = len(timer.laps) > counted
      if racer.stranded:
        racer.gaveUp()
      if done or racer.stranded:
        keptBrain(racer, path)
        if done:
          counted = len(timer.laps)
          times.append(timer.laps[-1])
        if report is not None:
          report(len(times), timer.laps[-1] if done else None, apron,
                 racer)
        apron = 0.0
      if racer.stranded:
        states, racer = start, LearningRacer(car, brainOf(path))
        timer, counted = LapTimer(clock), 0
  finally:
    steer(car, 0.0)
    drive(car, car.states, 0.0, DECIDES)
  return tuple(times)


def _capOf(curve: float, bank: float, grip: float) -> float:
  """Returns the fastest a curve of 'curve' 1/m banked 'bank' rad can be
  taken with 'grip' of the weight pressing the car in to steer by, m/s
  (without end for no curve, or too steep a banking to need any)."""
  if curve < 1e-5:
    return math.inf
  across = math.cos(bank) - grip * math.sin(bank)
  if across <= 0.0:
    return math.inf
  return math.sqrt(9.81 / curve * (math.sin(bank) + grip
                                   * math.cos(bank)) / across)


#  The channels a sample holds: name, unit, meaning. The corners' four
#  ('fl', 'fr', 'rl', 'rr') follow these, each corner's five channels.
CHANNELS = (
  ('time', 's', 'since the robot started'),
  ('along', 'm', 'round the oval since the start, laps counted'),
  ('off', 'm', "off the robot's line, out of the oval counted up"),
  ('speed', 'm/s', 'forward'),
  ('slip', 'deg', "the car's slip angle: its way off its heading, left "
                  "up"),
  ('asked', 'deg', 'the column the robot asked, left up'),
  ('column', 'deg', 'the column as it is, left up'),
  ('throttle', '1', 'the pedals: 1 full throttle, -1 full brakes'),
  ('ax', 'm/s²', "accelerometer at the chassis' centre of mass, "
                 "forward (specific force: gravity in it)"),
  ('ay', 'm/s²', 'accelerometer, left'),
  ('az', 'm/s²', 'accelerometer, up (9.81 standing level)'),
  ('wx', 'rad/s', 'gyro, roll rate (right side down counted up)'),
  ('wy', 'rad/s', 'gyro, pitch rate (nose down counted up)'),
  ('wz', 'rad/s', 'gyro, yaw rate (left counted up)'),
)
CORNER_CHANNELS = (
  ('rise', 'mm', "the knuckle over its ride height on the chassis "
                 "(bump up)"),
  ('kz', 'm/s²', "the knuckle's acceleration along the chassis' up "
                 "(its motion's own: no gravity in it)"),
  ('toe', 'deg', 'toe in counted up (a left wheel turned right, a right '
                 'one left; the steering in it)'),
  ('camber', 'deg', 'top leaning out counted up'),
  ('spin', 'rad/s', 'the wheel on the chassis, rolling forward up'),
)
CORNER_NAMES = ('fl', 'fr', 'rl', 'rr')


def channelsOf() -> tuple:
  """The 'channelsOf' function returns every channel of a sample, the
  corners' named by their corner: (name, unit, meaning)."""
  out = list(CHANNELS)
  for name in CORNER_NAMES:
    for channel, unit, meaning in CORNER_CHANNELS:
      out.append(('%s_%s' % (name, channel), unit, meaning))
  return tuple(out)


class VibrationRecorder:
  """
  VibrationRecorder samples 'car' driven by 'robot' ('sample', at each
  time a sample is due): 'rows', one a sample, in the order of
  'channelsOf'. The first call only notes the car (an acceleration needs
  two).
  """

  def __init__(self, car: CarBuild, robot: RobotDriver) -> None:
    self.car, self.robot, self.rows = car, robot, []
    self._before = None
    self._ride = [self._riseOf(car.states, knuckle)
                  for knuckle in car.knuckles]

  def _riseOf(self, states: tuple, knuckle: int) -> float:
    """Returns how high 'knuckle' is over the chassis in its frame."""
    chassis = states[self.car.chassis]
    return rotated(conjugate(chassis.turn),
                   minus(states[knuckle].place, chassis.place))[2]

  def sample(self, states: tuple, time_: float) -> None:
    """The 'sample' method notes the car in 'states' at 'time_' s."""
    car = self.car
    chassis = states[car.chassis]
    back = conjugate(chassis.turn)
    velocities = [chassis.velocity] + [states[knuckle].velocity
                                       for knuckle in car.knuckles]
    before, self._before = self._before, (time_, velocities)
    if before is None:
      return
    passed = time_ - before[0]
    changes = [tuple((now[i] - then[i]) / passed for i in range(3))
               for now, then in zip(velocities, before[1])]
    force = rotated(back, (changes[0][0], changes[0][1],
                           changes[0][2] + 9.81))
    spin = rotated(back, chassis.spin)
    local = rotated(back, chassis.velocity)
    robot = self.robot
    row = [time_, robot.along, robot.off, speedOf(car, states),
           math.degrees(math.atan2(local[1], max(abs(local[0]), 1e-6))),
           math.degrees(robot.column),
           math.degrees(steeringOf(car, states)), robot.throttle,
           force[0], force[1], force[2], spin[0], spin[1], spin[2]]
    up = rotated(chassis.turn, (0.0, 0.0, 1.0))
    for corner, knuckle in enumerate(car.knuckles):
      row.extend((
        1000.0 * (self._riseOf(states, knuckle) - self._ride[corner]),
        dot(changes[1 + corner], up),
        -CORNERS[corner][1] * math.degrees(toeOf(car, states, corner)),
        math.degrees(camberOf(car, states, corner)),
        wheelSpinOf(car, states, corner)))
    self.rows.append(row)

  def saved(self, path: str, meta: dict) -> tuple:
    """The 'saved' method writes the rows to 'path' (CSV) and, beside
    it, the channels, the rate and 'meta' (JSON). Returns both paths."""
    names = [name for name, _, _ in channelsOf()]
    numpy.savetxt(path, numpy.array(self.rows), '%.7g', ',', '\n',
                  ','.join(names), '', '')
    about = dict(meta)
    about['channels'] = [{'name': name, 'unit': unit, 'meaning': meaning}
                         for name, unit, meaning in channelsOf()]
    about['samples'] = len(self.rows)
    side = path.rsplit('.', 1)[0] + '.json'
    with open(side, 'w') as file:
      json.dump(about, file, indent=2, ensure_ascii=False)
    return path, side


def robotLaps(laps: float, speed: float, out: float, rate: float,
              fidelity: Fidelity = FULL, report: object = None) -> tuple:
  """The 'robotLaps' function builds the car on the oval's start line,
  has the robot drive it 'laps' laps at 'speed' m/s, 'out' m from the
  middle line, recording it 'rate' times a second, in a world as
  faithful as 'fidelity' says; 'report' (if given) is called each
  simulated second with (time, robot, compute seconds). Returns (the
  recorder, the lap times, s, the car's states at the end)."""
  car, world = carBuilt(0.5, fidelity), ovalWorld(fidelity)
  terrain = world.ground.terrain
  states = carPlaced(car.states, (0.0, 0.0, terrain.heightAt(0.0, 0.0)),
                     terrain.normalAt(0.0, 0.0))
  robot = RobotDriver(car, speed, out)
  recorder = VibrationRecorder(car, robot)
  sample, every = 1.0 / rate, max(1, int(round(DECIDES * rate)))
  began, clock, count, laps_ = time.perf_counter(), 0.0, 0, []
  recorder.sample(states, clock)
  try:
    while robot.along < laps * OVAL_LENGTH:
      if count % every == 0:
        robot.take(states, every * sample)
      states = world.advancedAll(car.assembly, states, sample, clock)
      count += 1
      clock = count * sample
      recorder.sample(states, clock)
      if robot.along >= (len(laps_) + 1) * OVAL_LENGTH:
        laps_.append(clock - sum(laps_))
      if report is not None and count % int(round(rate)) == 0:
        report(clock, robot, time.perf_counter() - began)
      if clock > 120.0 * max(laps, 1.0) + 60.0:
        break
  finally:
    steer(car, 0.0)
    drive(car, car.states, 0.0, DECIDES)
  return recorder, tuple(laps_), states
