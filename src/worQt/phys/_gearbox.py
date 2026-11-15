"""
The car's gearbox and the engine behind it (user, 2026-11-13: "sound.
engine. sound. and a gearbox with 4 or 5 speeds, for the sake of the
sound").

'Gearbox' is the engine's state as it drives: the gear it is in, its
revolutions, its load, a shift under way. 'driven' takes the driven
wheels' spin, the throttle and the time passed, shifts as an automatic
does (up at 'SHIFT_UP', down at 'SHIFT_DOWN', 'SHIFT_TIME' with the
clutch open between), and returns the torque the engine puts on the
driven wheels together: its full-load torque at its revolutions
('engineTorque', the curve 'TORQUE_CURVE') times the throttle, the gear
and the final drive, less the driveline's loss. Standing (or crawling
under 'LAUNCH'), the clutch slips: the engine runs at its launch
revolutions and passes its torque there. At 'REDLINE' the limiter cuts
it. The revolutions the sound hears are the ones the torque comes
from.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

#  The forward gears (the 2019+ roadster's six-speed's first five) and
#  the final drive; the gearbox and differential lose 'DRIVELINE' of
#  what goes through them.
GEARS = (5.087, 2.991, 2.035, 1.594, 1.286)
FINAL, DRIVELINE = 2.866, 0.9
#  The engine's full-load torque at the crank, N m, by revolutions a
#  minute (the 2.0 litre's spec sheet: 205 N m at 4000, 135 kW at 7000,
#  power held to the redline); between, drawn straight.
TORQUE_CURVE = ((800.0, 120.0), (1500.0, 160.0), (2500.0, 188.0),
                (3500.0, 202.0), (4000.0, 205.0), (5000.0, 203.0),
                (6000.0, 196.0), (7000.0, 184.2), (7500.0, 171.9))
#  Idling, launching (the clutch slipping, at full throttle), shifting
#  up, shifting down, and cutting out, revolutions a minute; how long a
#  shift takes, s (no drive meanwhile).
IDLE, LAUNCH, SHIFT_UP, SHIFT_DOWN, REDLINE = (850.0, 3500.0, 7200.0,
                                               3200.0, 7500.0)
SHIFT_TIME = 0.25
#  Backing: first gear's ratio, at this share of the engine's torque.
REVERSE = 0.35
#  Revolutions a minute in a radian a second.
RPM = 60.0 / (2.0 * math.pi)


def engineTorque(rpm: float) -> float:
  """The 'engineTorque' function returns the engine's full-load torque
  at the crank at 'rpm' revolutions a minute, N m ('TORQUE_CURVE'; at
  its ends, the end's)."""
  points = TORQUE_CURVE
  if rpm <= points[0][0]:
    return points[0][1]
  for (low, first), (high, second) in zip(points, points[1:]):
    if rpm <= high:
      return first + (second - first) * (rpm - low) / (high - low)
  return points[-1][1]


class Gearbox:
  """
  Gearbox is the car's engine and gearbox as they drive: 'gear' (1 to
  the number of 'GEARS'), 'rpm' (the engine's revolutions a minute),
  'load' (the share of its full torque it gives now, nought shifting
  or cut), 'shifting' (how long the shift under way still takes, s, and
  the gear it goes to); 'boost' times its torque (a stronger engine);
  'driven' drives it on, 'reset' puts it in first, idling.
  """

  def __init__(self, boost: float = 1.0) -> None:
    self.boost = boost
    self.gear, self.rpm, self.load = 1, IDLE, 0.0
    self.shifting, self._next = 0.0, 1

  def reset(self, ) -> None:
    """The 'reset' method puts it in first, idling, no shift under way."""
    self.gear, self.rpm, self.load = 1, IDLE, 0.0
    self.shifting, self._next = 0.0, 1

  def rpmAt(self, spin: float, gear: int) -> float:
    """The 'rpmAt' method returns the engine's revolutions a minute
    with the driven wheels turning 'spin' rad/s in 'gear', the clutch
    shut."""
    return abs(spin) * GEARS[gear - 1] * FINAL * RPM

  def driven(self, spin: float, speed: float, throttle: float,
             seconds: float) -> float:
    """The 'driven' method drives the engine on for 'seconds', the
    driven wheels turning 'spin' rad/s (their mean), the car going
    'speed' m/s, 'throttle' asked (-1 to 1; below nought backing,
    once all but stopped): shifts as an automatic does, and returns the
    torque on the driven wheels together, N m (forward counted up)."""
    if abs(speed) < 1.0 and not self.shifting:
      self.gear = 1
    if self.shifting:
      self.shifting = max(0.0, self.shifting - seconds)
      wheels = self.rpmAt(spin, self._next)
      share = 1.0 - self.shifting / SHIFT_TIME
      self.rpm += share * (max(wheels, IDLE) - self.rpm)
      self.load = 0.0
      if not self.shifting:
        self.gear = self._next
      return 0.0
    wheels = self.rpmAt(spin, self.gear)
    if wheels >= SHIFT_UP and self.gear < len(GEARS) and throttle > 0.0:
      self._shift(self.gear + 1)
    elif wheels < SHIFT_DOWN and self.gear > 1:
      self._shift(self.gear - 1)
    if self.shifting:
      self.rpm, self.load = max(wheels, IDLE), 0.0
      return 0.0
    asked = abs(throttle)
    slipping = IDLE + (LAUNCH - IDLE) * asked if self.gear == 1 else IDLE
    self.rpm = max(wheels, slipping)
    if self.rpm >= REDLINE:
      self.load = 0.0
      return 0.0
    self.load = asked * (REVERSE if throttle < 0.0 else 1.0)
    ratio = GEARS[self.gear - 1] * FINAL * DRIVELINE
    whole = self.boost * engineTorque(self.rpm) * ratio * self.load
    return -whole if throttle < 0.0 else whole

  def _shift(self, gear: int) -> None:
    """Begins a shift to 'gear': the clutch opens for 'SHIFT_TIME'."""
    self.shifting, self._next = SHIFT_TIME, gear
