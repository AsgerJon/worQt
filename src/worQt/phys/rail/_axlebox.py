"""
Axlebox holds a wheelset's journal in a vehicle's frame (user,
2026-11-16: "let's get a 'minecart' but fr on that track"; the spec
"Trains: the math first": "Next comes a two-axle cart with axleboxes,
whose bearing drag shows up as height lost"). At wheelset scale the
spec makes an axlebox a rigid hinge plus Palmgren's friction torque
(ISO 15312, after NSK): here the hinge is stiff springs and dampers
holding the journal in its box each way of the frame's own axes (the
primary suspension: rubber, a few MN/m), the axle free to turn in its
bearing but for the torque
  M = M0 + M1, M0 = 1e-7 f0 (nu n)^(2/3) dm^3 (nu n >= 2000; else
  160e-7 f0 dm^3), M1 = f1 P1 dm  (N mm; nu mm²/s, n rpm, dm mm, P1 N),
against the axle's turning in its box, eased through standstill over
'BEARING_EASE' rad/s.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._wheelset import AXLE_END, JOURNAL_FROM

#  Where a journal sits along the axle from the wheelset's middle, m:
#  halfway along it.
JOURNAL_AT = 0.5 * (JOURNAL_FROM + AXLE_END)
#  Palmgren's tapered roller bearing (the spec's example, assumed):
#  f0 (grease or oil bath, 3 to 4), f1 (0.0004 to 0.0005), the oil's
#  viscosity, mm²/s, the bearing's mean diameter, mm.
PALMGREN = (4.0, 0.0004, 20.0, 180.0)
#  How the bearing's torque eases in through standstill, rad/s (its
#  sign is the turning's: smoothed so the explicit steps hold still).
BEARING_EASE = 0.01
#  How a brake's torque eases in through standstill, rad/s (as the
#  bearing's: below this the shoes hold less than they would; user,
#  2026-11-16: the FourthPeep's first lever is the cart's brake).
BRAKE_EASE = 0.02
#  The least spin a motor's power is shared over, rad/s (standing, its
#  torque is its most: power over spin would be endless).
MOTOR_LEAST = 1e-3


def brakeOf(spin: float, most: float) -> float:
  """Returns the torque, N m, of brake shoes on a wheel's tread holding
  'most' N m against its turning at 'spin' rad/s (of 'spin''s sign),
  eased through standstill over 'BRAKE_EASE'."""
  return most * math.tanh(spin / BRAKE_EASE)


def motorOf(spin: float, drive: float, power: float) -> float:
  """Returns the torque, N m, of a traction motor in an axlebox driving
  its axle at 'spin' rad/s (rolling the frame ahead: above nought): its
  'drive' (N m, its most now, of the way it drives: above nought ahead)
  while that is within its 'power' (W, its most now), else that power
  shared over the spin ('MOTOR_LEAST' at least); nought driving nought."""
  if drive == 0.0:
    return 0.0
  turning = max(abs(spin), MOTOR_LEAST)
  if power > 0.0 and abs(drive) * turning > power:
    return power / turning if drive > 0.0 else -power / turning
  return drive


def palmgrenOf(spin: float, load: float, bearing: tuple) -> float:
  """Returns the friction torque, N m, of a bearing ('bearing': f0, f1,
  viscosity mm²/s, mean diameter mm) turning at 'spin' rad/s under
  'load' N; against the turning, so of 'spin''s sign."""
  f0, f1, viscosity, middle = bearing
  rpm = abs(spin) * 60.0 / (2.0 * math.pi)
  if viscosity * rpm >= 2000.0:
    m0 = 1e-7 * f0 * (viscosity * rpm) ** (2.0 / 3.0) * middle ** 3
  else:
    m0 = 160e-7 * f0 * middle ** 3
  m1 = f1 * abs(load) * middle
  return 1e-3 * (m0 + m1) * math.tanh(spin / BEARING_EASE)


class Axlebox:
  """
  Axlebox holds the journal of wheelset 'wheelset' (its index; 'side'
  +1: the end along its own +z, -1: along -z, 'JOURNAL_AT' m out) in a
  box on body 'frame' (its index) at 'box' (a point in the frame's own
  frame, where the journal sits unloaded): pushed back each way of the
  frame's own axes by 'stiffness' (N/m: along x, across y, up z) and
  'damping' (N s/m, likewise) on how far and how fast the journal has
  left the box; the axle turning in it against 'bearing''s torque
  ('palmgrenOf', the box's load its push) and against its 'brake' (N m:
  how hard the shoes there hold now, nought released; 'brakeOf'; set as
  the vehicle goes), driven by its traction motor's 'drive' (N m, its
  most now, above nought rolling the frame ahead along its own x) within
  its 'power' (W; 'motorOf'), the frame taking the motor's torque back
  (both nought: no motor). The rail world steps it, the wheelset in its
  own steps, the frame by what the box hands it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  wheelset: int
  side: float
  frame: int
  box: tuple
  stiffness: tuple
  damping: tuple
  bearing: tuple
  brake: float
  drive: float
  power: float

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, wheelset: int, side: float, frame: int, box: tuple,
               stiffness: tuple, damping: tuple,
               bearing: tuple = PALMGREN) -> None:
    if side not in (1.0, -1.0):
      raise ValueError('a journal is at side 1 or -1, not %r' % (side,))
    if wheelset == frame:
      raise ValueError('a wheelset cannot ride in its own box')
    self.wheelset, self.side, self.frame = wheelset, float(side), frame
    self.box = tuple(float(x) for x in box)
    self.stiffness = tuple(float(x) for x in stiffness)
    self.damping = tuple(float(x) for x in damping)
    self.bearing, self.brake = bearing, 0.0
    self.drive, self.power = 0.0, 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def renumbered(self, wheelset: int, frame: int) -> Axlebox:
    """The 'renumbered' method returns the axlebox with its bodies'
    indices 'wheelset' and 'frame' instead."""
    box = Axlebox(wheelset, self.side, frame, self.box, self.stiffness,
                  self.damping, self.bearing)
    box.brake, box.drive, box.power = self.brake, self.drive, self.power
    return box
