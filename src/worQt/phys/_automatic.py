"""
The stand-in car's drivetrain (user, 2026-11-15: "bro, automatic
transmission bro... fake in other words. audible only"): no flywheel,
shafts, gears or clutch among the bodies; the engine's torque, at the
revolutions the automatic's gear and the wheels give it, put on the
driven wheels (half each, an open differential's share: each wheel
twisted on its carrier by a 'Motor'), worked out in Python each frame.
Its gears and its revolutions are there to be heard ('_enginesim': the
sound, 'Reading.rpm'), shifted as an automatic shifts: up sooner at light
throttle, down as the revolutions fall; a slipping converter holds the
engine at a stall speed rising with the throttle while the wheels are
slower (pulling away); off the throttle a locked converter brakes with
the engine, never crawling or holding a car all but stopped; neutral, it
revs free on its flywheel (the tune-up's mass). The driver's controls
are the drivetrain of parts' ('DrivetrainControls'): the stick a
selector ('R' backing, 'N' neutral, any gear driving), the clutch pedal
felt by nothing; the engine never stalls. Each frame it works the
stand-in car's other Python too ('steering': its servos follow the
steering wheel).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._assembly import Drive
from ._drivetrain import DRAG, DRAG_RPM, FINAL, GEARS, IDLE, REDLINE
from ._drivetrain import REVERSE
from ._drivetrain import DrivetrainControls, Reading, engineTwist
from ._drivetrain import footWorked, spinAbout
from ._vectors import conjugate, product

#  Each forward gear's ratio (the gearbox of parts' teeth, out over in)
#  and reverse's (through its idler), times the final drive's.
FORWARD = tuple(teeth[1] / teeth[0] for teeth in GEARS)
BACKWARD = REVERSE[2] / REVERSE[0]
FINAL_RATIO = FINAL[1] / FINAL[0]
#  The automatic's shifts, revolutions a minute: up past 'UP_LEAST' at no
#  throttle to 'UP_MOST' at full, down under 'DOWN_LEAST' to
#  'DOWN_MOST' (the gap between keeps a shift from hunting: up from
#  first at full throttle lands at ~4500 in second, over 3500); how long
#  a shift takes, s (no drive meanwhile).
UP_LEAST, UP_MOST = 2500.0, 6800.0
DOWN_LEAST, DOWN_MOST = 1500.0, 3500.0
SHIFT_TIME = 0.15
#  How long it holds a gear before it shifts again, s (spinning its
#  wheels in first at full throttle, it shifted up on their revolutions,
#  down again as they slowed, and drove a third of the time).
SHIFT_HOLD = 1.0
#  The converter's stall speed at full throttle, revolutions a minute
#  (the engine held there pulling away); the throttle under which a car
#  all but stopped is neither driven nor held back ('CREEP_OPEN').
STALL_RPM, CREEP_OPEN = 3200.0, 0.02
#  How far the flywheel's stuff lies from its axle on average, m (its
#  moment over its mass, the root: the flywheel of parts' disc, 28 cm
#  across, with its snout): its moment is the tune-up's mass times its
#  square.
GYRATION = 0.0944
#  Its traction control: the driven wheels' rims may outrun the
#  undriven ones' by this share of their speed (of 'TRACTION_LEAST' m/s
#  at least) with the engine's drive in full, none by twice that (full
#  throttle in first spun the rear wheels to the limiter; let through to
#  a tenth, they ran at 14 % slip from 22 m/s on, their grip across
#  spent, and the car spun on the straight: the engine out-pulls the
#  rear tyres' grip into third).
TRACTION_SLIP, TRACTION_LEAST = 0.05, 3.0
#  How fast its share of the drive goes down and comes back, a second
#  (set at once each frame, it went all or nothing frame after frame:
#  each driven wheel rings on its tyre at ~27 Hz, a frame's snapshot of
#  its spin read it a fifth slow or fast; so the wheels are read by how
#  far they turned over the frame, and the share moves at these rates).
TRACTION_CUT, TRACTION_BACK = 8.0, 2.0
#  The most each driven wheel's motor twists, N m (a motor's twist is
#  held to its drive's 'most': none, it twists nothing; first gear's
#  full torque at the wheels, ~2600 N m, halved, with room).
SHAFT_MOST = 1e4
#  Revolutions a minute in a radian a second.
RPM = 60.0 / (2.0 * math.pi)


class AutomaticDrive(DrivetrainControls):
  """
  AutomaticDrive is the stand-in car's drivetrain (as
  'DrivetrainControls' is the car of parts', the same driver's
  controls): its driven wheels' motors' drives ('shafts', left and
  right rear), the gear it is in ('gear', 1 on), the engine's
  revolutions a minute ('rpm'), a shift under way ('shifting': how long
  it still takes, s; to 'nextGear'), how long it has kept its gear
  ('kept', s), the driven wheels' bodies and their axles in
  their own frames ('wheels', 'axles': out along the axle, the right's
  turning backwards as the car goes forward), the undriven wheels'
  bodies, left and right ('rolling': what the traction control reads
  the road's speed from; None, none), the share of the engine's drive
  its traction control lets through ('traction'), the wheels' turns as
  the last frame began and that frame's length ('turns', 'lastSeconds':
  how fast they turned over it, 'meanSpinOf'), the flywheel's mass
  ('flywheel', kg: how fast it revs free), and the car's other Python
  worked with it each frame ('steering': None, or what has a
  'worked(seconds)').
  """

  __slots__ = ('shafts', 'gear', 'rpm', 'shifting', 'nextGear', 'kept',
               'wheels', 'axles', 'rolling', 'traction', 'turns',
               'lastSeconds', 'flywheel', 'steering')

  def __init__(self, ) -> None:
    self.shafts = (Drive(), Drive())
    for shaft in self.shafts:
      shaft.most = SHAFT_MOST
    self.gear, self.rpm, self.shifting, self.nextGear = 1, IDLE, 0.0, 1
    self.kept = 0.0
    self.wheels, self.axles = None, ((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))
    self.rolling, self.traction = None, 1.0
    self.turns, self.lastSeconds = {}, 0.0
    self.flywheel, self.steering = 13.5, None
    DrivetrainControls.__init__(self)

  def reset(self, ) -> None:
    """The 'reset' method sets it back as at the start: in drive ('1',
    the selector), first gear, idling, the feet off, the brakes off, no
    shift under way, no drive on the wheels."""
    DrivetrainControls.reset(self)
    self.asked = '1'
    self.gear, self.rpm, self.shifting, self.nextGear = 1, IDLE, 0.0, 1
    self.kept, self.traction = 0.0, 1.0
    self.turns, self.lastSeconds = {}, 0.0
    for shaft in self.shafts:
      shaft.torque = shaft.damping = 0.0

  def spinOf(self, states: tuple) -> float:
    """The 'spinOf' method returns the driven wheels' mean spin, rad/s,
    forward counted up."""
    left, right = self.wheels
    return 0.5 * (spinAbout(states[left], self.axles[0])
                  - spinAbout(states[right], self.axles[1]))

  def meanSpinOf(self, states: tuple, pair: tuple) -> float:
    """The 'meanSpinOf' method returns the wheels 'pair''s (left, right)
    mean spin over the last frame, rad/s, forward counted up: how far
    each turned about its axle since that frame began, over its length
    (at the first frame, as they spin now)."""
    out = 0.0
    for k, (index, way) in enumerate(zip(pair, (1.0, -1.0))):
      axis, before = self.axles[k], self.turns.get(index)
      if before is None or self.lastSeconds <= 0.0:
        spin = spinAbout(states[index], axis)
      else:
        turned = product(conjugate(before), states[index].turn)
        if turned[0] < 0.0:
          turned = tuple(-part for part in turned)
        along = sum(a * b for a, b in zip(turned[1:], axis))
        spin = 2.0 * math.atan2(along, turned[0]) / self.lastSeconds
      out += 0.5 * way * spin
    return out

  def ratioOf(self, gear: int) -> float:
    """The 'ratioOf' method returns the engine's turns to the driven
    wheels' in 'gear' (0: reverse)."""
    return (BACKWARD if gear == 0 else FORWARD[gear - 1]) * FINAL_RATIO

  def worked(self, states: tuple, seconds: float) -> None:
    """The 'worked' method works the drivetrain for the next 'seconds',
    the bodies as 'states' have them: the feet ('footWorked'), the
    selector's place as the stick's ('shifter.engaged': at once), the
    driven wheels' spin over the last frame ('meanSpinOf') and the
    traction control's share (by their slip on the undriven ones', at
    'TRACTION_CUT' and 'TRACTION_BACK'), the automatic's gear and the
    engine's revolutions ('_geared'), half its
    drive's line on each driven wheel (its torque standing, less its
    damping times how fast the wheel turns on its carrier: worked in
    the small steps at every step, so a wheel spinning up loses its
    drive at once, as the engine's turning inertia had it); then the
    car's other Python ('steering')."""
    footWorked(self, seconds)
    self.running, self.starting = True, False
    asked = self.asked
    self.shifter.engaged = None if asked == 'N' else asked
    self.shifter.blocked = None
    spin = self.meanSpinOf(states, self.wheels)
    slip = 0.0
    if self.rolling is not None:
      road = self.meanSpinOf(states, self.rolling) * _radius()
      slip = (spin * _radius() - road) / max(abs(road), TRACTION_LEAST)
    for index in self.wheels + (self.rolling or ()):
      self.turns[index] = states[index].turn
    self.lastSeconds = seconds
    wanted = min(1.0, max(0.0, 2.0 - (-slip if asked == 'R' else slip)
                          / TRACTION_SLIP))
    rate = TRACTION_CUT if wanted < self.traction else TRACTION_BACK
    self.traction += max(-rate * seconds, min(rate * seconds,
                                              wanted - self.traction))
    if asked == 'N':
      torque, damping = self._revved(seconds), 0.0
    else:
      torque, damping = self._geared(spin, asked == 'R', seconds)
    governed = min(0.35, max(0.0, (IDLE - self.rpm) / 400.0))
    self.effective = 0.0 if self.rpm >= REDLINE else max(self.open,
                                                         governed)
    left, right = self.shafts
    left.torque, right.torque = 0.5 * torque, -0.5 * torque
    left.damping = right.damping = 0.5 * damping
    if self.steering is not None:
      self.steering.worked(seconds)

  def _revved(self, seconds: float) -> float:
    """Returns no drive on the wheels, the engine revving free in
    neutral on its flywheel for 'seconds' ('engineTwist' on its
    moment)."""
    moment = self.flywheel * GYRATION ** 2
    twist = engineTwist(self.rpm, self.open, True, False)
    self.engine.torque = twist
    self.rpm = max(IDLE * 0.9, self.rpm + twist / moment * seconds * RPM)
    self.shifting = 0.0
    return 0.0

  def _geared(self, spin: float, backing: bool,
              seconds: float) -> tuple[float, float]:
    """Returns the drive's line on the driven wheels together, the
    wheels turning 'spin' rad/s, for 'seconds': its torque standing, N m
    (forward counted up), and its damping, N m s: at the wheels' speed
    now the twist the engine gives at its throttle and revolutions,
    through the gear; a wheel spinning faster loses it as steeply as
    the whole drive fades from standing to the engine's drag at its
    limiter (the line's slope: a light damping, so the two wheels'
    own lines barely lock them together, no open differential's a
    spool; a wheel spun up frame after frame meets the limiter, and
    there the engine's drag). Backing in reverse;
    else the automatic's gear, shifted up and down by the revolutions
    and the throttle (a gear held 'SHIFT_HOLD' first), no drive while a
    shift takes 'SHIFT_TIME'; the engine at the wheels' revolutions, or
    the converter's stall speed pulling away; off the throttle all but
    stopped, nothing."""
    if backing:
      self.gear, self.shifting = 0, 0.0
    elif self.gear == 0:
      self.gear = 1
    if self.shifting > 0.0:
      self.shifting = max(0.0, self.shifting - seconds)
      wheels = abs(spin) * self.ratioOf(self.nextGear) * RPM
      self.rpm += (max(wheels, IDLE) - self.rpm) * min(
        1.0, seconds / max(self.shifting, seconds))
      if self.shifting <= 0.0:
        self.gear = self.nextGear
      self.engine.torque = 0.0
      return 0.0, 0.0
    self.kept += seconds
    wheels = abs(spin) * self.ratioOf(self.gear) * RPM
    if self.gear > 1 and wheels < IDLE:
      self.gear, self.kept = 1, 0.0
      wheels = abs(spin) * self.ratioOf(1) * RPM
    if self.gear > 0 and self.kept >= SHIFT_HOLD:
      up = UP_LEAST + (UP_MOST - UP_LEAST) * self.open
      down = DOWN_LEAST + (DOWN_MOST - DOWN_LEAST) * self.open
      if wheels > up and self.gear < len(FORWARD):
        self.shifting, self.nextGear = SHIFT_TIME, self.gear + 1
      elif wheels < down and self.gear > 1:
        self.shifting, self.nextGear = SHIFT_TIME, self.gear - 1
      if self.shifting > 0.0:
        self.kept = 0.0
        self.engine.torque = 0.0
        return 0.0, 0.0
    stall = IDLE + (STALL_RPM - IDLE) * self.open
    self.rpm = min(REDLINE, max(wheels, stall))
    if self.open < CREEP_OPEN and wheels < IDLE:
      self.engine.torque = 0.0
      return 0.0, 0.0
    twist = engineTwist(self.rpm, self.open, True, False)
    if wheels < stall:
      twist = max(0.0, twist)
    self.engine.torque = twist
    if twist > 0.0:
      twist *= self.traction
    ratio = self.ratioOf(self.gear)
    drive = max(0.0, twist + DRAG + DRAG_RPM * self.rpm) * ratio
    drag = (DRAG + DRAG_RPM * REDLINE) * ratio
    damping = (drive + drag) * ratio * RPM / REDLINE
    way = -1.0 if self.gear == 0 else 1.0
    return way * twist * ratio + damping * spin, damping

  def reading(self, states: tuple) -> Reading:
    """The 'reading' method returns what the drivetrain reads out: the
    engine's revolutions and twist, no clutch slip, the gear the
    automatic is in ('N' in neutral, 'R' backing), the stick nowhere,
    the driven wheels' speeds at the tyre's radius, m/s."""
    radius = _radius()
    left, right = self.wheels
    gear = 'N' if self.asked == 'N' else 'R' if self.gear == 0 else str(
      self.gear)
    return Reading(self.rpm, self.engine.torque, 0.0, gear, 0.0, 0.0,
                   spinAbout(states[left], self.axles[0]) * radius,
                   -spinAbout(states[right], self.axles[1]) * radius)


def _radius() -> float:
  """Returns the tyre's rolling radius, m (its pressure as built)."""
  from ._tyred import TYRE_PRESSURE, tyreOf
  return tyreOf(1, TYRE_PRESSURE).radius
