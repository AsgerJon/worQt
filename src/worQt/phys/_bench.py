"""
The suspension bench (user, 2026-11-12: "My suspicion is that
suspension is too soft generally. Let us see if we can make a very
simple test bench that shows us if the suspension respond correctly").
The car stands on a flat road ('carWorld') and is tested as a mechanic
and a kinematics-and-compliance rig would:

'weighed': four scales, the ground's push under each wheel at rest:
the corner loads and the front's share of the weight.

'bounced': the bounce test: a hammer taps the body ('tapped': at its
centre of mass straight down, heave; nose down and tail up at once,
pitch; left side down and right side up, roll) and the body rings; its
frequency and damping ratio are fitted ('ringOf', once the tyres' own
quick wobble, ~12 Hz, has died: 'SKIP'). 'designed' says what the
springs and dampers were made for, standing on the tyres (each spring
on its tyre, in series): heave as the four corners' rates and dampers
on the body's mass make it (the springs alone: 'RIDE' Hz damped
'RIDE_DAMPING' of critical); pitch likewise on the body's moment of
inertia; roll likewise but
about the ground under the body (the wishbones put the roll centre
there: pulled sideways, the load moved from side to side as the body's
weight at its full height asks), its weight leaning out with it, and
how far it then rolls a g.

'pulled': a cable pulls the body sideways at its centre of mass with a
share of the car's weight, as a steady turn's inertia does, the tyres
holding it: how far the body rolls a g (its roll gradient); each
corner's travel, the side force on its tyre, how far its rubber steers
it and leans it. Compliance steer is the steering per kN of side force
(left counted up both): above nought a wheel steers the way it is
pushed, which at the rear steers with the turn (stable) and at the
front into it (unstable).

'reportOf' runs them all and tells them, with what was designed beside.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
from scipy.optimize import curve_fit

from ._assembly import Assembly, Spring
from ._car import CAR_ROAD, CORNERS, RIDE, RIDE_DAMPING, TRACK, CarBuild
from ._car import camberOf, carWorld, drive, steer, toeOf
from ._poke import poked
from ._vectors import conjugate, dot, minus, product, rotated
from ._world import FULL, Fidelity, World

#  How hard the hammer taps: the speed it gives the body where it hits,
#  m/s; how far apart the two taps of a pitch or a roll are from the
#  centre of mass, m.
TAP, NOSE, SIDE = 0.1, 1.0, 0.5
#  How long the body is watched ringing, and how often, s; how long
#  after the tap the fit starts, s.
RING, EVERY, SKIP = 2.0, 0.002, 0.15
#  How long the cable pulls before the car is read, s, and with what
#  share of the car's weight; how far away it is anchored, m.
PULL, PULL_SHARE, CABLE = 2.0, 0.5, 50.0
#  The corners' names, in the corners' order.
NAMES = ('front left', 'front right', 'rear left', 'rear right')


def weighed(car: CarBuild, world: World, states: tuple) -> tuple:
  """The 'weighed' function returns what four scales under the wheels
  read, N, in the corners' order, and the front's share of it all."""
  bodies = car.assembly.bodies
  loads = tuple(world.groundPushOf(bodies[wheel], states[wheel])[2]
                for wheel in car.wheels)
  front = sum(load for load, (x, _) in zip(loads, CORNERS) if x > 0.0)
  return loads, front / sum(loads)


def _turnedBy(turn: tuple, rest: tuple) -> tuple:
  """Returns how far 'turn' is turned from 'rest', as a small turn's
  vector, rad, in the world's frame."""
  q = product(turn, conjugate(rest))
  sign = 1.0 if q[0] >= 0.0 else -1.0
  return tuple(2.0 * sign * q[i] for i in (1, 2, 3))


def tapped(car: CarBuild, states: tuple, mode: str) -> tuple:
  """The 'tapped' function returns the car's 'states' just after the
  hammer's tap for 'mode' ('heave', 'pitch' or 'roll'), the body
  moving 'TAP' m/s where it is hit."""
  body, state = car.assembly.bodies[car.chassis], states[car.chassis]
  middle = state.place
  inertia = body.inertiaIn(state)
  if mode == 'heave':
    taps = ((middle, (0.0, 0.0, -body.mass * TAP)),)
  elif mode == 'pitch':
    blow = inertia[1][1] * TAP / NOSE / (2.0 * NOSE)
    taps = (((middle[0] + NOSE, middle[1], middle[2]), (0.0, 0.0, -blow)),
            ((middle[0] - NOSE, middle[1], middle[2]), (0.0, 0.0, blow)))
  else:
    blow = inertia[0][0] * TAP / SIDE / (2.0 * SIDE)
    taps = (((middle[0], middle[1] + SIDE, middle[2]), (0.0, 0.0, -blow)),
            ((middle[0], middle[1] - SIDE, middle[2]), (0.0, 0.0, blow)))
  for point, impulse in taps:
    state = poked(body, state, point, impulse)
  out = list(states)
  out[car.chassis] = state
  return tuple(out)


def _ringing(t: numpy.ndarray, size: float, omega: float, damping: float,
             phase: float, rest: float) -> numpy.ndarray:
  """Returns a damped ring at times 't'."""
  damping = min(max(damping, 0.0), 0.99)
  return rest + size * numpy.exp(-damping * omega * t) * numpy.sin(
    omega * math.sqrt(1.0 - damping ** 2) * t + phase)


def ringOf(times: tuple, values: tuple, guess: float) -> tuple:
  """The 'ringOf' function returns the frequency (undamped, Hz) and the
  damping ratio of a damped ring through 'values' at 'times', fitted,
  starting from 'guess' Hz."""
  t, y = numpy.array(times), numpy.array(values)
  size = float(numpy.max(numpy.abs(y - y[-1])))
  found = curve_fit(_ringing, t, y, (size, 2.0 * math.pi * guess, 0.3,
                                     0.0, float(y[-1])), None, True,
                    False, (-numpy.inf, numpy.inf), 'trf')[0]
  return abs(found[1]) / (2.0 * math.pi), min(max(found[2], 0.0), 0.99)


def bounced(car: CarBuild, world: World, states: tuple, mode: str,
            guess: float) -> tuple:
  """The 'bounced' function returns how the body rings after the
  hammer's tap for 'mode': its frequency, Hz, and damping ratio (fitted,
  from 'guess' Hz), and the times and values watched (heave: the body's
  centre's height, m; pitch and roll: its turn about the world's y or x
  axis from where it stood, rad)."""
  rest = states[car.chassis].turn
  states = tapped(car, states, mode)
  times, values = [], []
  axis = 1 if mode == 'pitch' else 0
  for count in range(int(round(RING / EVERY))):
    states = world.advancedAll(car.assembly, states, EVERY, count * EVERY)
    chassis = states[car.chassis]
    if (count + 1) * EVERY < SKIP:
      continue
    times.append((count + 1) * EVERY - SKIP)
    values.append(chassis.place[2] if mode == 'heave'
                  else _turnedBy(chassis.turn, rest)[axis])
  frequency, damping = ringOf(times, values, guess)
  return frequency, damping, tuple(times), tuple(values)


def designed(car: CarBuild, states: tuple) -> dict:
  """The 'designed' function returns what the springs and dampers were
  made for: each corner's wheel rate, N/m (its sprung share of the body
  at 'RIDE' Hz), the ride and damping the springs alone were made for
  ('springs': 'RIDE', 'RIDE_DAMPING'), and the heave, pitch and roll
  frequencies, Hz, and damping ratios they give the body standing on its
  tyres ('heave', 'pitch', 'roll': each (Hz, ratio); roll about the
  ground, its weight leaning out with it), and how far it rolls a g,
  deg ('gradient'). Each corner's spring stands on its tyre ('tyre',
  N/m: the road's stiffness at its tread's two edges), the two in
  series; its damper moves only as much as the spring does, its share
  of the two's give, so it damps that squared. (At 1.5 Hz the tyre,
  ten times stiffer than the spring, hardly showed; at 3 Hz, a third
  as stiff, the body heaved 2.69 Hz, 0.33 of critical, where the
  springs alone made 3.00 and 0.50, and rolled 1.28 deg a g where they
  made 0.88; the tyres in series make 2.59, 0.32 and 1.30.)"""
  bodies = car.assembly.bodies
  sprung = sum(bodies[index].mass for index in (car.chassis, car.column,
                                                car.rack))
  body, state = bodies[car.chassis], states[car.chassis]
  inertia = body.inertiaIn(state)
  loads = weighed(car, carWorld(FULL), states)[0]
  unsprung = [bodies[k].mass + bodies[w].mass
              for k, w in zip(car.knuckles, car.wheels)]
  shares = [load / 9.81 - away for load, away in zip(loads, unsprung)]
  scale = sprung / sum(shares)
  omega = 2.0 * math.pi * RIDE
  rates = [share * scale * omega ** 2 for share in shares]
  dampers = [2.0 * RIDE_DAMPING * math.sqrt(rate * share * scale)
             for rate, share in zip(rates, shares)]
  tyre = 2.0 * CAR_ROAD.stiffness
  springs, rates = rates, [rate * tyre / (rate + tyre) for rate in rates]
  dampers = [damper * (tyre / (spring + tyre)) ** 2
             for damper, spring in zip(dampers, springs)]
  middle = state.place
  high = middle[2]
  out = {'rates': tuple(springs), 'springs': (RIDE, RIDE_DAMPING),
         'tyre': tyre}
  stiff, damp = sum(rates), sum(dampers)
  out['heave'] = (math.sqrt(stiff / sprung) / (2.0 * math.pi),
                  damp / (2.0 * math.sqrt(stiff * sprung)))
  for name, arms, moment, leaning in (
          ('pitch', [states[w].place[0] - middle[0] for w in car.wheels],
           inertia[1][1], 0.0),
          ('roll', [0.5 * TRACK] * 4,
           inertia[0][0] + sprung * high ** 2, sprung * 9.81 * high)):
    stiff = sum(rate * arm ** 2 for rate, arm in zip(rates, arms))
    damp = sum(c * arm ** 2 for c, arm in zip(dampers, arms))
    out[name] = (math.sqrt((stiff - leaning) / moment) / (2.0 * math.pi),
                 damp / (2.0 * math.sqrt((stiff - leaning) * moment)))
    if name == 'roll':
      out['gradient'] = math.degrees(sprung * 9.81 * high
                                     / (stiff - leaning))
  return out


def _riseOf(states: tuple, chassis: int, knuckle: int) -> float:
  """Returns how high 'knuckle' is over the chassis in its frame, m."""
  return rotated(conjugate(states[chassis].turn),
                 minus(states[knuckle].place, states[chassis].place))[2]


def pulled(car: CarBuild, world: World, states: tuple,
           share: float) -> dict:
  """The 'pulled' function returns how the car stands pulled sideways
  (toward +y, left) at the body's centre of mass by a cable with
  'share' of the car's weight, after 'PULL' s: 'roll' (deg, its left
  side down counted up) and 'gradient' (deg a g); for each corner (the
  corners' order) 'travel' (mm, bump up), 'force' (its tyre's side
  force, N, left up), 'steer' and 'camber' (how far its rubber has
  steered it, left up, and leaned it, top out up, deg) and 'compliance'
  (deg of steer a kN of side force)."""
  bodies = car.assembly.bodies
  body, chassis = bodies[car.chassis], states[car.chassis]
  weight = 9.81 * sum(each.mass for each in bodies)
  middle = chassis.place
  anchor = (middle[0], middle[1] + CABLE, middle[2])
  cable = Spring(None, anchor, car.chassis, body.centre,
                 share * weight / CABLE, 0.0)
  assembly = Assembly(bodies, car.assembly.connections + (cable,))
  steer(car, 0.0)
  drive(car, states, 0.0, PULL)
  rest = chassis.turn
  before = [(_riseOf(states, car.chassis, k), toeOf(car, states, corner),
             camberOf(car, states, corner))
            for corner, k in enumerate(car.knuckles)]
  now = world.advancedAll(assembly, states, PULL)
  roll = math.degrees(-_turnedBy(now[car.chassis].turn, rest)[0])
  out = {'roll': roll, 'gradient': roll / share, 'corners': []}
  left = rotated(now[car.chassis].turn, (0.0, 1.0, 0.0))
  for corner, (k, w) in enumerate(zip(car.knuckles, car.wheels)):
    rise, toe, camber = before[corner]
    force = dot(world.groundPushOf(bodies[w], now[w]), left)
    steered = math.degrees(toeOf(car, now, corner) - toe)
    out['corners'].append({
      'travel': 1000.0 * (_riseOf(now, car.chassis, k) - rise),
      'force': force, 'steer': steered,
      'camber': math.degrees(camberOf(car, now, corner) - camber),
      'compliance': steered / (force / 1000.0) if abs(force) > 1.0
      else 0.0})
  return out


def benchOf(car: CarBuild, fidelity: Fidelity = FULL) -> dict:
  """The 'benchOf' function returns the bench's findings for 'car' on a
  flat road as faithful as 'fidelity' says: 'loads' and 'front' (the
  scales), 'designed', the bounces ('heave', 'pitch', 'roll': each
  (Hz, damping ratio)) and 'pulled'."""
  world = carWorld(fidelity)
  steer(car, 0.0)
  drive(car, car.states, 0.0, RING)
  states = car.states
  loads, front = weighed(car, world, states)
  design = designed(car, states)
  out = {'loads': loads, 'front': front, 'designed': design}
  for mode in ('heave', 'pitch', 'roll'):
    out[mode] = bounced(car, world, states, mode, design[mode][0])[:2]
  out['pulled'] = pulled(car, world, states, PULL_SHARE)
  return out


def reportOf(found: dict) -> str:
  """The 'reportOf' function returns the bench's findings ('benchOf')
  as lines to read."""
  lines = ['scales (N): ' + ', '.join(
    '%s %.0f' % (name, load) for name, load in zip(NAMES,
                                                   found['loads'])),
    'front share of the weight: %.1f %%' % (100.0 * found['front']),
    'bounce            measured           designed']
  for mode in ('heave', 'pitch', 'roll'):
    (hz, ratio), (wantHz, wantRatio) = found[mode], found['designed'][mode]
    lines.append('  %-6s  %5.2f Hz, %4.2f of critical   %5.2f Hz, %4.2f'
                 % (mode, hz, ratio, wantHz, wantRatio))
  pull = found['pulled']
  lines.append('pulled sideways at %.1f g: body rolls %.2f deg '
               '(%.2f deg a g; the springs alone %.2f)'
               % (PULL_SHARE, pull['roll'], pull['gradient'],
                  found['designed']['gradient']))
  lines.append('  corner        travel mm  side N   steer deg  camber deg'
               '  steer deg/kN')
  for name, corner in zip(NAMES, pull['corners']):
    lines.append('  %-12s  %+8.1f  %+7.0f  %+9.3f  %+10.3f  %+11.4f' % (
      name, corner['travel'], corner['force'], corner['steer'],
      corner['camber'], corner['compliance']))
  return '\n'.join(lines)
