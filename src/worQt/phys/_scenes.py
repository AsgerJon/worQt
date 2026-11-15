"""
Scenes are assemblies ready to run and look at: 'towerOnHexapod', the
54-block tower stacked on the hexapod's platform, on a concrete floor;
'ballsUnderPrism', steel balls on the ground and an oak prism launched
across them; 'outerRingWithBalls', the giant hjulleje's outer ring
standing upright with balls in its groove; 'walkingYard', a yard of
crates, dominoes, balls, a plank and a steel block to walk among;
'walkingRing', the outer ring and its balls to walk round;
'walkingBearing', the hjulleje at a car's size, both rings, the
balls and the plastic spacers between, the inner ring on a hollow
shaft a motor turns by its gears, a walker shrunk to walk through
it; and 'giantBallGiven', 'oakBallGiven', 'carBallGiven', one more
ball put among them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
import random

from ._assembly import Actuator, Assembly, Contact, Drive, Fixed
from ._assembly import HeldStroke, Motor, Tie
from ._body import Body, State
from ._ground import Ground
from ._hexapod import HeldPose, Hexapod
from ._gears import centreOf, prismOf, rootOf, roundOutline, spurGear
from ._shape import Shape, Sphere, boxShape, wedgeShape
from ._turned import innerRing, nuInnerRing, nuOuterRing, onShaft
from ._turned import onShaftOf, outerRing, rollerShape
from ._tyre import TYRE, TyreSkin, steelWheel
from ._vectors import ORIGIN, UNTURNED, Quaternion, Vector, plus
from ._vectors import product
from ._vectors import rotated, turnAbout
from ._walking import Grabber, Walker
from ._world import Fidelity, World

INCH = 0.0254
BLOCK = Body.of(boxShape(3.0 * INCH, 1.0 * INCH, 0.5 * INCH), 700.0)
#  The platform: aluminium, a little wider than the tower's foot (three
#  blocks side by side, 3 inches), on a benchtop hexapod standing on the
#  floor, its middle held at 'TABLE_MIDDLE' at rest.
PLATE = Body.of(boxShape(0.12, 0.12, 0.012), 2700.0)
RIG = Hexapod(0.1, 0.05, 20.0, 20.0, 0.0, -0.006)
TABLE_MIDDLE = (0.0, 0.0, 0.12)
#  The floor: a concrete slab, its top at nought, held still by six legs
#  of its own from a metre under it; blocks meet it with their edges
#  sampled every '_LANDING' m (a box lying on a flat floor rests on its
#  corners alike, and the floor's own edges, far off, meet nothing);
#  damped '_THUD' (s/m): maple dropped a metre flat comes back 0.27 m
#  (gives back half its speed, as wood on concrete), on a corner 0.06 m
#  (the rest goes into its spin).
FLOOR = Body.of(boxShape(2.0, 2.0, 0.1), 2400.0)
FLOOR_RIG = Hexapod(1.0, 0.6, 20.0, 20.0, -1.0, -0.05)
FLOOR_HELD = HeldPose((0.0, 0.0, -0.05))
_LANDING = 0.1
_THUD = 0.3
UP = (0.0, 0.0, 1.0)

#  Blocks stacked by hand are neither made alike nor laid as drawn (the
#  game's blocks are made uneven on purpose): each block's sizes scatter
#  by '_SIZE_SCATTER' (m, one standard deviation), it lies off its place
#  along itself by '_PLACE_SCATTER' (m) and turned about the upright by
#  '_TURN_SCATTER' (rad); neighbours in a layer lie '_GAP' (m) apart and
#  '_GAP_SCATTER' more at random. Draws are cut at three deviations.
_SIZE_SCATTER = 1e-4
_PLACE_SCATTER = 5e-4
_TURN_SCATTER = math.radians(0.5)
_GAP = 1e-4
_GAP_SCATTER = 2e-4


def towerOnHexapod(motion: object, levels: int, spacing: float,
                   seed: int = None, heading: float = 0.0,
                   ) -> tuple[Assembly, tuple[State, ...]]:
  """The 'towerOnHexapod' function returns 'levels' layers of three
  maple blocks, 3 x 1 x 0.5 inches, laid flat, each layer across the
  one below, on the hexapod's platform moving as 'motion' says (the
  tower stacked on it where it is, unturned, at time nought), any two
  touching (wood on wood, the edges sampled every 'spacing' m); and
  how they start, still, each layer a tenth of a millimetre over the
  tallest block below. With 'seed' None every block is made and laid
  as drawn; else as by hand ('_roughLayer'), alike for a seed. The
  tower stands turned 'heading' rad about the platform's upright
  middle, its first layer along x at nought. The bodies: the platform,
  the blocks layer by layer, and last the floor, under the hexapod's
  feet, every block meeting it (wood on concrete)."""
  draw = None if seed is None else random.Random(seed)
  start = motion.at(0.0).state()
  bodies, states = [PLATE], [start]
  bottom = start.place[2] + 0.5 * _thicknessOf(PLATE) + 1e-4
  for level in range(levels):
    if draw is None:
      layer = _layer(level, bottom)
    else:
      layer = _roughLayer(level, bottom, draw)
    for body, state in layer:
      bodies.append(body)
      states.append(_headed(state, heading, start.place))
    bottom = max(state.place[2] + 0.5 * _thicknessOf(body)
                 for body, state in layer) + 1e-4
  count = 3 * levels
  floor = count + 1
  bodies.append(FLOOR)
  states.append(FLOOR_HELD.at(0.0).state())
  contacts = tuple(Contact(a, b, 1e5, 10.0, 0.4, 1e5, 100.0, spacing)
                   for a in range(count + 1)
                   for b in range(a + 1, count + 1))
  landings = tuple(Contact(b, floor, 1e5, _THUD, 0.6, 1e5, 100.0,
                           _LANDING)
                   for b in range(1, count + 1))
  legs = RIG.legs(PLATE, 0, motion) + FLOOR_RIG.legs(FLOOR, floor,
                                                     FLOOR_HELD)
  return (Assembly(tuple(bodies), legs + contacts + landings),
          tuple(states))


def _layer(level: int, bottom: float) -> list[tuple[Body, State]]:
  """Returns layer 'level' as drawn, its underside at 'bottom': three
  blocks side by side, along x on even levels, along y on odd."""
  z = bottom + 0.25 * INCH
  out = []
  for k in range(3):
    offset = (k - 1) * INCH
    if level % 2 == 0:
      out.append((BLOCK, State((0.0, offset, z))))
    else:
      out.append((BLOCK, State((offset, 0.0, z),
                               turnAbout(UP, 0.5 * math.pi))))
  return out


def _roughLayer(level: int, bottom: float,
                draw: random.Random) -> list[tuple[Body, State]]:
  """Returns layer 'level' as by hand, its underside at 'bottom': each
  block made a little off its sizes, laid a little off its place and
  turned, neighbours apart by a little more than each one's reach
  across (its half width as turned, corners and all)."""
  made = []
  for _ in range(3):
    long = 3.0 * INCH + _SIZE_SCATTER * _drawn(draw)
    wide = 1.0 * INCH + _SIZE_SCATTER * _drawn(draw)
    thick = 0.5 * INCH + _SIZE_SCATTER * _drawn(draw)
    turn = _TURN_SCATTER * _drawn(draw)
    reach = 0.5 * wide * math.cos(turn) + 0.5 * long * abs(math.sin(turn))
    along = _PLACE_SCATTER * _drawn(draw)
    made.append((Body.of(boxShape(long, wide, thick), 700.0), thick, turn,
                 reach, along))
  middle = _PLACE_SCATTER * _drawn(draw)
  first = _GAP + _GAP_SCATTER * abs(_drawn(draw))
  last = _GAP + _GAP_SCATTER * abs(_drawn(draw))
  acrosses = (middle - made[1][3] - first - made[0][3], middle,
              middle + made[1][3] + last + made[2][3])
  out = []
  for (body, thick, turn, _, along), across in zip(made, acrosses):
    z = bottom + 0.5 * thick
    if level % 2 == 0:
      out.append((body, State((along, across, z), turnAbout(UP, turn))))
    else:
      out.append((body, State((across, along, z),
                              turnAbout(UP, 0.5 * math.pi + turn))))
  return out


def _headed(state: State, heading: float, middle: tuple) -> State:
  """Returns 'state', laid about the upright through the origin, turned
  'heading' rad about it and moved over to the platform's 'middle'."""
  turn = turnAbout(UP, heading)
  x, y, z = rotated(turn, state.place)
  return State((x + middle[0], y + middle[1], z),
               product(turn, state.turn))


def _drawn(draw: random.Random) -> float:
  """Returns a standard normal draw cut at three deviations."""
  return max(-3.0, min(3.0, draw.gauss(0.0, 1.0)))


def _thicknessOf(body: Body) -> float:
  """Returns how thick a block (or the platform) lying flat is, m."""
  heights = [point[2] for point in body.shape.points]
  return max(heights) - min(heights)


#  The balls and the prism: 80 mm steel balls (2.1 kg), an oak prism 600
#  x 350 x 40 mm (5.9 kg), on the ground ('BALL_GROUND'). Contacts are
#  points: steel on steel and steel on oak, stiffness N/m, damping s/m,
#  grip, bristle N/m and its damping N s/m. The balls lie scattered over
#  '_FIELD' (m, half the length and width), no two closer than '_APART'
#  between their middles.
BALL = Body.of(Sphere(0.04), 7850.0)
PRISM = Body.of(boxShape(0.6, 0.35, 0.04), 700.0)
BALL_GROUND = Ground()
_ON_STEEL = (2e5, 0.5, 0.3, 2e5, 200.0)
_ON_OAK = (2e5, 1.0, 0.5, 2e5, 200.0)
_FIELD = (0.55, 0.28)
_APART = 0.11


def ballsUnderPrism(count: int,
                    seed: int) -> tuple[Assembly, tuple[State, ...]]:
  """The 'ballsUnderPrism' function returns 'count' steel balls lying
  still on the ground, scattered at random as 'seed' says, and the oak
  prism last, launched across them ('prismLaunched'); every ball
  touching every other and the prism; and how they start."""
  draw = random.Random(seed)
  places = []
  for _ in range(5000):
    if len(places) == count:
      break
    x = draw.uniform(-_FIELD[0], _FIELD[0])
    y = draw.uniform(-_FIELD[1], _FIELD[1])
    if all((x - px) ** 2 + (y - py) ** 2 >= _APART ** 2
           for px, py in places):
      places.append((x, y))
  radius = BALL.shape.radius
  sunk = BALL.mass * 9.81 / BALL_GROUND.stiffness
  states = [State((x, y, radius - sunk)) for x, y in places]
  states.append(prismLaunched())
  balls = len(places)
  contacts = tuple(Contact(a, b, *_ON_STEEL)
                   for a in range(balls) for b in range(a + 1, balls))
  contacts += tuple(Contact(a, balls, *_ON_OAK) for a in range(balls))
  return (Assembly((BALL,) * balls + (PRISM,), contacts), tuple(states))


def prismLaunched() -> State:
  """The 'prismLaunched' function returns the prism as it is launched:
  over the near end of the field, 3 cm above the balls, flying along x
  at 1.2 m/s and turning slowly about the upright."""
  top = 2.0 * BALL.shape.radius + 0.03 + 0.02
  return State((-0.3, 0.02, top), (1.0, 0.0, 0.0, 0.0), (1.2, 0.0, 0.0),
               (0.0, 0.0, 0.8))


#  The giant hjulleje's outer ring, as picked on the design page: balls
#  of 400 mm on a pitch circle of 20 m, the groove a gothic arch as the
#  120 degree V it replaces (contact angle 30), its arcs 0.52 of a ball's
#  diameter; the ring 600 mm wide and 500 mm thick from its bore, steel
#  (139 t), standing upright 5 cm clear of the ground, held still. Its
#  steel balls weigh 263 kg; contacts at this size are stiffer: N/m at a
#  point, s/m, grip, bristle N/m and its damping N s/m.
OUTER_RING = Body.of(outerRing(20.0, 0.4, 120.0, 0.52, 0.6, 0.5, 72),
                     7850.0)
GIANT_BALL = Body.of(Sphere(0.2), 7850.0)
RING_GROUND = Ground(1e7, 1.0, 0.5, 1e7, 2e4)
RING_MIDDLE = (0.0, 0.0, 10.59 + 0.05)
RING_UPRIGHT = turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi)
_GIANT_STEEL = (1e8, 0.5, 0.3, 1e8, 2e4)


def outerRingWithBalls(count: int) -> tuple[Assembly, tuple[State, ...]]:
  """The 'outerRingWithBalls' function returns the outer ring standing
  upright (its body first, its axle along y), held still by six legs
  from the ground to its middle, and 'count' balls in its groove at the
  bottom, three degrees apart on the pitch circle, still; every ball
  touching the ring and each other; and how they start."""
  held = HeldPose(RING_MIDDLE, RING_UPRIGHT)
  legs = Hexapod(1.0, 0.6, 20.0, 20.0, 0.0, 0.0).legs(OUTER_RING, 0, held)
  states = [held.at(0.0).state()]
  for j in range(count):
    a = math.radians(-90.0 + 3.0 * (j - 0.5 * (count - 1)))
    arm = rotated(RING_UPRIGHT, (10.0 * math.cos(a), 10.0 * math.sin(a),
                                 0.0))
    states.append(State((RING_MIDDLE[0] + arm[0], RING_MIDDLE[1] + arm[1],
                         RING_MIDDLE[2] + arm[2])))
  bodies = (OUTER_RING,) + (GIANT_BALL,) * count
  contacts = tuple(Contact(a, b, *_GIANT_STEEL)
                   for a in range(len(bodies))
                   for b in range(max(a + 1, 1), len(bodies)))
  return Assembly(bodies, legs + contacts), tuple(states)


#  The yard: packed earth ('YARD_GROUND'), the walker ('WALKER', body
#  nought) and things to grab: a pyramid of six crates 500 mm (20 kg,
#  boards and air taken as one stuff), eight oak dominoes 100 x 400 x
#  800 mm (22 kg) in a row, four boxes 300 mm (5 kg), an oak plank 2.4 m
#  (21 kg), three oak balls 300 mm (10 kg) and a steel block 350 mm (337
#  kg: more than the grabber lifts). Every two touch: wood on wood (and
#  on steel and on the walker), edges sampled every 5 cm: N/m per m,
#  s/m, grip, bristle N/m per m, its damping; a ball's (or the walker's)
#  contacts are points, N/m.
YARD_GROUND = Ground(2e5, 2.0, 0.6, 2e5, 200.0)
WALKER = Walker()
CRATE = Body.of(boxShape(0.5, 0.5, 0.5), 160.0)
DOMINO = Body.of(boxShape(0.1, 0.4, 0.8), 700.0)
BOX = Body.of(boxShape(0.3, 0.3, 0.3), 185.0)
PLANK = Body.of(boxShape(2.4, 0.25, 0.05), 700.0)
WOODEN_BALL = Body.of(Sphere(0.15), 700.0)
STEEL_BLOCK = Body.of(boxShape(0.35, 0.35, 0.35), 7850.0)
_ON_WOOD = (2e5, 2.0, 0.5, 2e5, 200.0, 0.05)
_ROUND_ON_WOOD = (2e5, 2.0, 0.5, 2e5, 400.0)


def walkingYard() -> tuple[Assembly, tuple[State, ...]]:
  """The 'walkingYard' function returns the yard: the walker first,
  standing at the origin, then the crates' pyramid ahead of them along
  x, the dominoes in a row to their right, the boxes, the plank, the
  balls and the steel block about them, all at rest on the ground,
  every two touching; and how they start."""
  ground = YARD_GROUND.stiffness
  placed = [(WALKER.body(), (0.0, 0.0, WALKER.radius))]
  for y, z in ((-0.52, 0.25), (0.0, 0.25), (0.52, 0.25), (-0.26, 0.751),
               (0.26, 0.751), (0.0, 1.252)):
    placed.append((CRATE, (5.0, y, z)))
  for k in range(8):
    placed.append((DOMINO, (1.5 + 0.5 * k, -2.5, 0.4)))
  for x, y in ((2.5, 1.5), (3.0, 2.2), (-1.5, 2.0), (1.2, -1.0)):
    placed.append((BOX, (x, y, 0.15)))
  placed.append((PLANK, (2.0, 3.5, 0.025)))
  for x, y in ((1.5, 0.6), (-1.0, -1.2), (3.5, -1.0)):
    placed.append((WOODEN_BALL, (x, y, 0.15)))
  placed.append((STEEL_BLOCK, (-2.5, 0.0, 0.175)))
  bodies, states = [], []
  for body, (x, y, z) in placed:
    corners = 1.0 if isinstance(body.shape, Sphere) else 4.0
    sunk = body.mass * 9.81 / (corners * ground) if z < 0.5 else 0.0
    bodies.append(body)
    states.append(State((x, y, z - sunk)))
  contacts = []
  for a in range(len(bodies)):
    for b in range(a + 1, len(bodies)):
      rounds = isinstance(bodies[a].shape, Sphere) or isinstance(
          bodies[b].shape, Sphere)
      law = _ROUND_ON_WOOD if rounds else _ON_WOOD
      contacts.append(Contact(a, b, *law))
  return Assembly(tuple(bodies), tuple(contacts)), tuple(states)


#  The ring to walk round: the outer ring held upright as in
#  'outerRingWithBalls', its plane across the walker's way, on a
#  concrete apron ('APRON': its giant balls sink 2.6 mm); the walker
#  first, the ring second, giant balls in its groove at the bottom and
#  more lying on the apron before it. The walker's ball on steel: N/m at
#  a point, s/m, grip, bristle N/m, its damping. 'RING_GRABBER' holds
#  with 8000 N (the balls weigh 2580) and pulls with 5000 N: a ball is
#  lifted off the apron at 9 m/s² and swung with what is left; the
#  walker standing under it is pressed down by its weight (gripping the
#  harder), yanked by what swings it sideways past their grip.
APRON = Ground(1e6, 1.0, 0.6, 1e6, 5e3)
RING_GRABBER = Grabber(10.0, 5000.0, 6.0, 1.0, 8000.0, 0.1, 3000.0, 4.0)
_WALKER_ON_STEEL = (1e6, 1.0, 0.5, 1e6, 2e3)


def walkingRing(count: int,
                loose: int) -> tuple[Assembly, tuple[State, ...]]:
  """The 'walkingRing' function returns the walker (first) standing 6
  m before the outer ring (second; upright, its axle along y, held
  still by six legs from the apron to its middle), 'count' giant balls
  in its groove packed at the bottom (a millimetre apart, so they rest
  there) and 'loose' more on the apron 2 m before it, a metre and a
  third apart, all still; every two touching; and how they start."""
  held = HeldPose(RING_MIDDLE, RING_UPRIGHT)
  legs = Hexapod(1.0, 0.6, 20.0, 20.0, 0.0, 0.0).legs(OUTER_RING, 1, held)
  walker = WALKER.body()
  radius = GIANT_BALL.shape.radius
  states = [State((0.0, -6.0, WALKER.radius
                   - walker.mass * 9.81 / APRON.stiffness)),
            held.at(0.0).state()]
  apart = 2.0 * math.asin((radius + 5e-4) / 10.0)
  for j in range(count):
    a = -0.5 * math.pi + apart * (j - 0.5 * (count - 1))
    arm = rotated(RING_UPRIGHT, (10.0 * math.cos(a), 10.0 * math.sin(a),
                                 0.0))
    states.append(State((RING_MIDDLE[0] + arm[0], RING_MIDDLE[1] + arm[1],
                         RING_MIDDLE[2] + arm[2])))
  sunk = GIANT_BALL.mass * 9.81 / APRON.stiffness
  for k in range(loose):
    states.append(State((4.0 / 3.0 * (k - 0.5 * (loose - 1)), -2.0,
                         radius - sunk)))
  bodies = (walker, OUTER_RING) + (GIANT_BALL,) * (count + loose)
  contacts = tuple(Contact(a, b, *(_WALKER_ON_STEEL if a == 0 else
                                   _GIANT_STEEL))
                   for a in range(len(bodies))
                   for b in range(a + 1, len(bodies)))
  return Assembly(bodies, legs + contacts), tuple(states)


def giantBallGiven(assembly: Assembly, states: tuple[State, ...],
                   state: State) -> tuple[Assembly, tuple[State, ...]]:
  """The 'giantBallGiven' function returns 'assembly' in 'states' (the
  walker first) with one more giant ball, last, in 'state', touching
  every body (steel on steel, the walker on steel)."""
  return _ballGiven(assembly, states, GIANT_BALL, state, _GIANT_STEEL,
                    _WALKER_ON_STEEL)


def oakBallGiven(assembly: Assembly, states: tuple[State, ...],
                 state: State) -> tuple[Assembly, tuple[State, ...]]:
  """The 'oakBallGiven' function returns 'assembly' in 'states' (the
  walker first) with one more oak ball, last, in 'state', touching every
  body."""
  return _ballGiven(assembly, states, WOODEN_BALL, state, _ROUND_ON_WOOD,
                    _ROUND_ON_WOOD)


def _ballGiven(assembly: Assembly, states: tuple[State, ...], ball: Body,
               state: State, law: tuple,
               walkerLaw: tuple) -> tuple[Assembly, tuple[State, ...]]:
  """Returns 'assembly' in 'states' with 'ball' added last in 'state',
  touching the walker (body nought) by 'walkerLaw' and every other body
  by 'law'."""
  count = len(assembly.bodies)
  contacts = tuple(Contact(other, count,
                           *(walkerLaw if other == 0 else law))
                   for other in range(count))
  return (Assembly(assembly.bodies + (ball,),
                   assembly.connections + contacts),
          tuple(states) + (state,))


#  The hjulleje at a car's size, a four-point ball bearing as a wheel
#  hub's, on the design page's form (contact angle 30, gothic arches of
#  0.52 of a ball): balls 12.7 mm (1/2 in) on a 64 mm pitch circle, the
#  rings 18 mm wide and 9 mm thick from their faces (outside 88 mm, bore
#  40 mm), steel; between each two balls a spacer, a PA66 (polyamide)
#  ball 12.2 mm, a hair smaller so it carries no load (it rolls against
#  its neighbours, turning the other way). The outer ring is held by the
#  lab's rig (six legs, drawn), the inner ring pressed on its shaft (it
#  turns on the balls with it). Contacts are each pair's Hertz stiffness
#  at the loads here, made straight (Hertz stiffens with load), then
#  taken a hundredth as stiff ('_SOFTER', below): steel on steel 1.2e7
#  N/m (a ball's share of the ring, its shaft and gear, 411 g, 0.8 N, on
#  a groove of 0.52; 1e7 for the ring alone, 0.3 N, before the shaft),
#  PA66 on steel 3e5 (E 3 GPa against 210); greased, grip 0.1 (the
#  spacers none: below); steel rings nearly true (damping 0.1 s/m), PA66
#  dead (1). Bristles as stiff (Mindlin's 0.8 rounded up) and damped
#  near critical.
CAR_PITCH, CAR_BALL, CAR_SPACER = 0.064, 0.0127, 0.0122
CAR_OUTER = Body.of(outerRing(CAR_PITCH, CAR_BALL, 120.0, 0.52, 0.018,
                              0.009, 72), 7850.0)
CAR_INNER = Body.of(innerRing(CAR_PITCH, CAR_BALL, 120.0, 0.52, 0.018,
                              0.009, 72), 7850.0)
CAR_BALL_BODY = Body.of(Sphere(0.5 * CAR_BALL), 7850.0)
CAR_SPACER_BODY = Body.of(Sphere(0.5 * CAR_SPACER), 1140.0)
#  Softer than steel: a hundredth of Hertz's stiffness (user, 2026-11-13:
#  "what about softer balls then?", "send it"): as stiff, the balls rang
#  so fast the window's world had to step every 16 us; a hundredth as
#  stiff, every 143 us (the balls ring ten times slower), a simulated
#  second computed in 2.6 s against 12.2 (1.7 in the window's longer
#  runs: 59 % of real time; the reference's 4.0 against 18), the bearing
#  alike (the shaft 1.993 rad/s against 1.990, the gears 1.9323 against
#  1.9337, the balls' orbit 1.0022 of rolling against 1.0003), the shaft
#  sunk 27 um on its balls against 0.3 (to a walker 32 mm tall, as 1.5 mm
#  to a person: unseen; the walker passes 45 um under the hole's floor
#  and its own radius). The bristles a hundredth as stiff too, damped a
#  tenth as hard (alike near critical); the pushes' damping (per speed,
#  times the push) as it was: a knock rebounds as before.
_SOFTER = 100.0
_STEEL_ON_STEEL = (1.2e7 / _SOFTER, 0.1, 0.1, 1.2e7 / _SOFTER,
                   100.0 / math.sqrt(_SOFTER))
#  The spacers slide without friction (user, 2026-11-13: "what if we
#  agreed the balls and the plastic spacers were friction free?"): a
#  spacer rolling against the balls turns the other way to them, so it
#  can only slide on the rings, and its rubbing was all the bearings'
#  drag (the shaft at 85 % of the motor's free speed and slowing, 1.7
#  rad/s to 1.4 in 2.4 s; frictionless, 2.00 steady, the balls' orbit as
#  rolling has it). The balls keep their grip: frictionless too, they
#  stopped going round (0 % of rolling), the rings sliding under them.
_PA66_ON_STEEL = (3e5 / _SOFTER, 1.0, 0.0, 3e5 / _SOFTER,
                  10.0 / math.sqrt(_SOFTER))
#  The outer ring as it stands: pressed into its housing (user,
#  2026-11-13, of a plate it was bolted to: "what the fuck is this
#  frame"), one solid with it, a pillow block's: steel 8 mm thick round
#  the ring (52 mm out), as wide; the housing on its pedestal
#  ('CAR_PEDESTAL'). Its middle 100 mm over the floor (user, 2026-11-13:
#  "elevate the rings above the ground so that the connections between
#  the rings become more clear"): the housing's bottom 48 mm up, held
#  by its pedestal's cheeks; under the shaft between the two bearings
#  80 mm clear, room for the shrunk walker (32 mm tall) to walk beneath
#  it and see it join them (it stood 58 mm up, the housing's bottom
#  6 mm over the floor, sunk 4 mm into the pedestal's foot).
CAR_HOUSED = Body.of(outerRing(CAR_PITCH, CAR_BALL, 120.0, 0.52, 0.018,
                               0.017, 72), 7850.0)
CAR_MIDDLE = (0.0, 0.0, 0.1)

#  The bearing's shaft (user, 2026-11-13: "put a hollow shaft that is
#  tall enough for the player to walk through. in one end put teeth
#  outside of the shaft and put a motor with a tooth wheel to drive"):
#  steel, the inner ring pressed on it as one solid ('onShaft'), its
#  wall 2 mm round a hole of 36.3 mm (the walker shrunk to stand 32 mm
#  tall walks through it), reaching 'SHAFT_FRONT' before the ring's
#  middle (toward the walker) and 'SHAFT_BACK' behind it: 930 g with
#  both bearings' inner rings ('BEARING_APART'). Near its back end its
#  gear ('CAR_GEAR'): 31 teeth at module 1.5, 'GEAR_WIDTH' wide, cut on
#  a band pressed and keyed on, one with the
#  shaft (a tie at its middle and three 2 mm rods in the shaft's wall,
#  its key: '_keyed'). Beside it the motor's pinion ('CAR_PINION'), 16
#  teeth (none in common with 31: each tooth meets every one of the
#  gear's in turn), its axle 'GEAR_CENTRE' from the shaft's (0.1 mm of
#  play), on the motor's output shaft (a tie at its middle and two rods
#  across the shaft's stub at the housing's face: a bearing, turning
#  freely about its axle, '_outputShaft'); the motor ('CAR_MOTOR') a
#  steel can 22 mm across on its pedestal, part of the world, its 'Motor'
#  twisting the pinion as a motor twists its rotor ('motorTorque':
#  'MOTOR_STALL' standing, nought at 'MOTOR_FREE', the speed that turns
#  the ring at 2 rad/s; 6 mN m, up to speed in a third of a second with
#  the long shaft, 930 g), the housing taking the twist back. The teeth
#  meet as greased steel ('_MESH': grip 0.1, damped as the grease's film
#  squeezed between them, near half of critical at the motor's most;
#  their edges sampled every 3 mm, three points across a face: every
#  millimetre cost half again as much, and turned them as true), but
#  softer than steel teeth are: 3e5 N/m per m of face against a real
#  mesh's 1.4e10 (its bristles 0.8 of it, as Mindlin's), so they need no
#  shorter steps than the balls (a contact's steps are bound as if a
#  face lay flat on the other, and the gear's 31 teeth end in one plane:
#  stiff as steel they took steps 23 times shorter; at 3e5 the pinion's
#  bound is 0.86 of a ball's, the gear's 0.77: a hundredth, as the balls
#  were softened, is what keeps it so); standing against the motor's
#  stall, 0.5 N on a tooth, they give 0.14 mm at the gear's pitch circle
#  (3 um at 3e7, steel 7 nm), 0.35 degrees of the gear's turn: to the
#  walker as 8 mm to a person, unseen. Before the shaft's front end a
#  steel ramp ('CAR_RAMP', 1:3)
#  up to its hole's floor, 'RAMP_GAP' clear of it, part of the world
#  (the ground is the shrunk walker's, as soft to steel as the apron is
#  to a boulder: it would sink). The bodies after the
#  walker, in order: the outer ring, the shaft, the gear, the motor, its
#  pinion, the ramp, the pedestal, then the balls and spacers from
#  'FIRST_BALL'. Seen, every support is solid (user, 2026-11-13: "what
#  the fuck are thus disgusting struts ... Just make but solid ... this
#  instead"): the ring's housing and pedestal, the motor's pedestal, the
#  pinion's stub shaft, the ramp's wedge; the rods that hold them
#  still (rigid: they hold them as the floor would) are not drawn.
SHAFT_INSIDE = CAR_INNER.shape.bounds()[0] - 0.002
#  Two bearings carry the shaft, as a beam on a pin and a roller (user,
#  2026-11-13: "this is only one of the tow bearings, is it the pinned
#  or rolled? in any case, let's length the shaft and add the other
#  bearing"): the first, at nought, the pinned (locating) one, its
#  housing held every way; the second 'BEARING_APART' before it, toward
#  the walker, the roller (floating) one, its housing held but free to
#  slide along the axle ('_floating': as a shaft's length grows with the
#  heat, so it is never squeezed between them). Alike, both four-point
#  ball bearings; the shaft through both, their inner rings on it.
SHAFT_FRONT, SHAFT_BACK, BEARING_APART = 0.25, 0.075, 0.2
CAR_SHAFT = Body.of(onShaft(CAR_INNER.shape, SHAFT_INSIDE, SHAFT_FRONT,
                            SHAFT_BACK, (0.0, BEARING_APART)), 7850.0)
MODULE, GEAR_TEETH, PINION_TEETH, GEAR_WIDTH = 1.5e-3, 31, 16, 0.006
GEAR_AT = -(SHAFT_BACK - 0.003 - 0.5 * GEAR_WIDTH)
GEAR_CENTRE = centreOf(MODULE, GEAR_TEETH, PINION_TEETH, 1e-4)
CAR_GEAR = Body.of(spurGear(MODULE, GEAR_TEETH, GEAR_WIDTH,
                            CAR_INNER.shape.bounds()[0] - 1.5e-4, 0.0, 3,
                            0), 7850.0)
MOTOR_RADIUS, MOTOR_LENGTH = 0.011, 0.02
MOTOR_AT = -(SHAFT_BACK + 0.005 + 0.5 * MOTOR_LENGTH)
#  The pinion on its output shaft: its stub, 3 mm round, solid from the
#  pinion back to the motor's face ('_PINION_BACK', in its own frame),
#  turning with it.
_PINION_ROOT = rootOf(MODULE, PINION_TEETH)
_PINION_BACK = MOTOR_AT + 0.5 * MOTOR_LENGTH - GEAR_AT
CAR_PINION = Body.of(spurGear(MODULE, PINION_TEETH, GEAR_WIDTH,
                              _PINION_ROOT - 1.25e-4, _PINION_ROOT, 3, 32)
                     .joined(prismOf(roundOutline(0.003, 16), _PINION_BACK,
                                     -0.5 * GEAR_WIDTH)), 7850.0)
#  The motor: its can, and under it a solid steel pedestal down to the
#  floor (its own y is up), 16 mm across and 18 mm along the axle.
CAR_MOTOR = Body.of(prismOf(roundOutline(MOTOR_RADIUS, 32),
                            -0.5 * MOTOR_LENGTH, 0.5 * MOTOR_LENGTH).joined(
  boxShape(0.016, CAR_MIDDLE[2] - 0.0085, 0.018).moved(
    (0.0, -0.5 * (CAR_MIDDLE[2] + 0.0075), 0.0), UNTURNED)), 7850.0)
MOTOR_STALL, MOTOR_FREE = 6e-3, 2.0 * GEAR_TEETH / PINION_TEETH
_MESH = (3e7 / _SOFTER, 20.0, 0.1, 2.4e7 / _SOFTER,
         1e4 / math.sqrt(_SOFTER), 3e-3)
_KEY, _STUB = 0.002, 0.004
RAMP_GAP, RAMP_WIDTH, RAMP_LIFT = 1e-3, 0.024, 5e-4
_RAMP_HIGH = CAR_MIDDLE[2] - SHAFT_INSIDE - RAMP_LIFT
CAR_RAMP = Body.of(wedgeShape(3.0 * _RAMP_HIGH, RAMP_WIDTH, _RAMP_HIGH),
                   7850.0)
#  The pedestal the housing sits in, a pillow block's foot, steel, as
#  wide as the housing: a foot 140 mm long and 9.5 mm high (0.5 mm over
#  the floor) and a cheek either side rising from it to 20 degrees under
#  the axle, meeting the housing along a chord within its 8 mm of wall
#  (clear of the ring's bore); in the world's frame, its legs hidden.
_FOOT, _CHEEK_TOP, _CHEEK_LOW = 0.010, math.radians(-20.0), math.radians(
  -60.0)


def _pedestalShape() -> Shape:
  """Returns the pedestal: its foot and its two cheeks, each a solid
  of its own (in x and z, through the housing's width along y)."""
  rim, middle = CAR_HOUSED.shape.bounds()[1], CAR_MIDDLE[2]
  upper = (rim * math.cos(_CHEEK_TOP), middle + rim * math.sin(_CHEEK_TOP))
  lower = (rim * math.cos(_CHEEK_LOW), middle + rim * math.sin(_CHEEK_LOW))
  cheek = ((lower[0], _FOOT), (0.06, _FOOT), (0.054, upper[1]), upper,
           lower)
  half = 0.009
  upright = turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi)
  shape = prismOf(((-0.07, 0.0005), (0.07, 0.0005), (0.07, _FOOT),
                   (-0.07, _FOOT)), -half, half).moved(ORIGIN, upright)
  for side in (1.0, -1.0):
    outline = tuple((side * x, z) for x, z in cheek)
    if side < 0.0:
      outline = outline[::-1]
    shape = shape.joined(prismOf(outline, -half, half).moved(ORIGIN,
                                                               upright))
  return shape


CAR_PEDESTAL = Body.of(_pedestalShape(), 7850.0)
FIRST_BALL = 10
#  The floating bearing as it truly is, a cylindrical roller bearing of
#  type NU (user, 2026-11-13: "both bearings appear identicial, but one
#  is meant to be the pinned and the other roller?", then "yes"): as
#  big as the ball bearing (its housing alike, bore 40 mm, 18 mm wide),
#  'ROLLERS' steel rollers 'ROLLER' across and as long on the same
#  64 mm pitch circle, full complement (no cage: they fill the circle,
#  0.11 mm apart there, each rolling against its neighbours); the
#  outer ring's raceway between two ribs 'NU_RIB_WIDTH' wide reaching
#  'NU_RIB' in (each 1 mm from the rollers' ends), one solid with its
#  housing as the pinned one's; the inner ring a plain cylinder, no
#  ribs, pressed on the shaft beside the pinned one's: the rollers run
#  on it wherever it lies along them, so the shaft slides through this
#  bearing as it grows with heat, the pinned bearing locating it; its
#  housing part of the world as the pinned one's (the hidden rods that
#  let a ball bearing's housing slide, '_floating', gone). Radial play
#  'ROLLER_PLAY' a side. The rollers from 'FIRST_ROLLER', after the
#  pinned bearing's balls and spacers.
ROLLER, ROLLERS, ROLLER_PLAY = 0.011, 18, 5e-6
NU_RIB, NU_RIB_WIDTH = 0.0025, 0.0025
CAR_ROLLER = Body.of(rollerShape(ROLLER, ROLLER, 48), 7850.0)
NU_HOUSED = Body.of(nuOuterRing(CAR_PITCH, ROLLER, ROLLER_PLAY, 0.018,
                                CAR_HOUSED.shape.bounds()[1], NU_RIB,
                                NU_RIB_WIDTH, 72), 7850.0)
NU_INNER = nuInnerRing(CAR_PITCH, ROLLER, ROLLER_PLAY, 0.018,
                       CAR_INNER.shape.bounds()[0], 72)
CAR_SHAFT_NU = Body.of(onShaftOf((CAR_INNER.shape, NU_INNER), SHAFT_INSIDE,
                                 SHAFT_FRONT, SHAFT_BACK,
                                 (0.0, BEARING_APART)), 7850.0)
FIRST_ROLLER = FIRST_BALL + 16
#  Roller on roller: neighbours turn the same way, so where they touch
#  their faces rub opposite ways: sliding on an oil film, grip 0.03
#  (greased steel's 0.1 held them, static friction locking each to the
#  next: they skidded on their raceways, orbiting at 0.90 of rolling,
#  the shaft held to half its speed, 1.0 rad/s; as a real full
#  complement bearing runs hotter and slower than a caged one, but not
#  so). Its stiffness and damping as the balls' (the springs' world
#  does not step rollers: the small steps take only its grip).
_ROLLER_ON_ROLLER = (_STEEL_ON_STEEL[0], _STEEL_ON_STEEL[1], 0.03,
                     _STEEL_ON_STEEL[3], _STEEL_ON_STEEL[4])
#  The bodies standing still, part of the world ('Fixed'; held by legs
#  of six rods each before, rigid, as still, but 30 of the 46 rules the
#  world kept every step): the pinned bearing's housing, the motor, the
#  ramp and the two pedestals; with the roller bearing, its housing too
#  ('STILL_ROLLER').
STILL = (1, 4, 6, 7, 9)
STILL_ROLLER = (1, 4, 6, 7, 8, 9)
#  How faithfully the bearing's world is stepped live: its contacts'
#  steps twice the reference's ('Fidelity.contacts'), alike to it (the
#  motor's run: ring, gears, balls' orbit, to 0.1 %; four times lost
#  it, the balls as stiff as steel), and the ground's swing twice (the
#  balls softened, the walker's own bounce on the floor set the step,
#  91 us, before the balls' 143; at twice, 167: the balls set it, the
#  walk through the shaft alike to 1 um): a simulated second computed
#  in 2.6 s against the reference's 4.0 (3.5 at the ground's swing as
#  the reference's).
BEARING_FIDELITY = Fidelity(2.0, False, 2.0)
#  The bearing's world in small steps ('SmallSteps', user, 2026-11-13:
#  "speed first, let's go!"): 0.125 ms, one pass each: the shaft at its
#  motor's 2 rad/s (1.994), the gears 31/16 (1.00004), the balls' orbit
#  as rolling has it (1.0006), the shaft 17 um sunk on its balls (39
#  before a ball pressed on its still ring gave not at all to the shaft:
#  shock propagation, 'pushApart'; at 0.25 ms 146, too deep for the walk
#  through its hole; four passes there sank 38 but the shaft dipped to
#  1.75 rad/s, unexplained).
SMALL_BEARING = 1.25e-4


def froudeOf(law: tuple, scale: float) -> tuple:
  """The 'froudeOf' function returns the contact law 'law' (stiffness,
  damping s/m, grip, bristle, its damping) as it must be in a world
  shrunk to 'scale' to swing alike under the same gravity (as
  'Walker.scaled'): stiffnesses times its square, damping (per speed)
  over its root, bristle damping times its power 2.5."""
  stiffness, damping, grip, bristle, bristleDamping = law
  return (stiffness * scale ** 2, damping / math.sqrt(scale), grip,
          bristle * scale ** 2, bristleDamping * scale ** 2.5)


def groundAt(scale: float) -> Ground:
  """The 'groundAt' function returns 'APRON' as the ground of a world
  shrunk to 'scale' ('froudeOf'): a walker so shrunk stands on it as
  on the apron (a steel ball fallen on it sinks as a boulder would)."""
  return Ground(*froudeOf(tuple(APRON)[:5], scale),
                APRON.relaxation * scale)


def walkingBearing(scale: float, roller: bool = False
                   ) -> tuple[Assembly, tuple[State, ...]]:
  """The 'walkingBearing' function returns the walker shrunk to 'scale'
  ('Walker.scaled') first, standing before the ramp up into the shaft;
  the pinned bearing's outer ring in its housing (upright, its axle
  along y), the inner rings on their shaft (free, on the balls), its
  gear (keyed on), the motor, its pinion (on its output shaft, its teeth
  among the gear's), the ramp, the pedestal the housing sits in, the
  floating bearing's housing and its pedestal; then, from
  'FIRST_BALL', the pinned bearing's balls and spacers in turn round
  the pitch circle from the bottom, as many as fit; then the floating
  bearing's: with 'roller', the NU bearing's rollers from
  'FIRST_ROLLER' ('ROLLERS' round the circle from the bottom, their
  axes along the axle; its housing part of the world: 'STILL_ROLLER';
  stepped only in small steps, 'SmallSteps': the springs' world meets a
  turned solid with balls only), else a ball bearing alike to the
  pinned one in a housing held to slide along the axle ('_floating';
  'STILL'); all still. The motor's drive twists nought until set
  ('runMotor'). Every ball, spacer and roller touches both its rings
  and its neighbours, the gear the pinion, the walker every body (its
  law shrunk as it is). And how they start."""
  walker = WALKER.scaled(scale)
  body = walker.body()
  held = HeldPose(CAR_MIDDLE, RING_UPRIGHT)
  ground = groundAt(scale)
  pedestal = State(CAR_PEDESTAL.centre)
  apart = (0.0, -BEARING_APART, 0.0)
  housing = NU_HOUSED if roller else CAR_HOUSED
  shaft = CAR_SHAFT_NU if roller else CAR_SHAFT
  second = _placedOn(housing, (0.0, 0.0, BEARING_APART), RING_UPRIGHT)
  secondPedestal = State(plus(CAR_PEDESTAL.centre, apart))
  motor = _placedOn(CAR_MOTOR, (GEAR_CENTRE, 0.0, MOTOR_AT), RING_UPRIGHT)
  pinion = _placedOn(CAR_PINION, (GEAR_CENTRE, 0.0, GEAR_AT),
                     product(RING_UPRIGHT, turnAbout(
                       (0.0, 0.0, 1.0), math.pi / PINION_TEETH)))
  low = (0.0, -(SHAFT_FRONT + RAMP_GAP + 1.5 * _RAMP_HIGH), RAMP_LIFT)
  ramp = State(plus(low, CAR_RAMP.centre))
  states = [State((0.0, low[1] - 1.5 * _RAMP_HIGH - 0.05, walker.radius
                   - body.mass * 9.81 / ground.stiffness)),
            held.at(0.0).state(),
            _placedOn(shaft, (0.0, 0.0, 0.0), RING_UPRIGHT),
            _placedOn(CAR_GEAR, (0.0, 0.0, GEAR_AT), RING_UPRIGHT),
            motor, pinion, ramp, pedestal, second, secondPedestal]
  bodies = [body, CAR_HOUSED, shaft, CAR_GEAR, CAR_MOTOR, CAR_PINION,
            CAR_RAMP, CAR_PEDESTAL, housing, CAR_PEDESTAL]
  pitch = 0.5 * CAR_PITCH
  count = int(math.pi * CAR_PITCH / (CAR_BALL + CAR_SPACER + 2e-4))
  for along in ((0.0,) if roller else (0.0, BEARING_APART)):
    for j in range(2 * count):
      a = -0.5 * math.pi + math.pi * j / count
      arm = rotated(RING_UPRIGHT, (pitch * math.cos(a),
                                   pitch * math.sin(a), along))
      states.append(State(plus(CAR_MIDDLE, arm)))
      bodies.append(CAR_SPACER_BODY if j % 2 else CAR_BALL_BODY)
  if roller:
    for j in range(ROLLERS):
      a = -0.5 * math.pi + 2.0 * math.pi * j / ROLLERS
      states.append(_placedOn(CAR_ROLLER, (
        pitch * math.cos(a), pitch * math.sin(a), BEARING_APART),
        RING_UPRIGHT))
      bodies.append(CAR_ROLLER)
  walking = froudeOf(_WALKER_ON_STEEL, scale)
  contacts = [Contact(0, other, *walking)
              for other in range(1, len(bodies))]
  contacts.append(Contact(3, 5, *_MESH))
  rings = ((FIRST_BALL, 1),) if roller else ((FIRST_BALL, 1),
                                              (FIRST_BALL + 2 * count, 8))
  for first, ring in rings:
    for j in range(2 * count):
      one = first + j
      law = _PA66_ON_STEEL if j % 2 else _STEEL_ON_STEEL
      contacts += [Contact(ring, one, *law), Contact(2, one, *law)]
      following = first + (j + 1) % (2 * count)
      contacts.append(Contact(min(one, following), max(one, following),
                              *_PA66_ON_STEEL))
  if roller:
    for j in range(ROLLERS):
      one = FIRST_ROLLER + j
      following = FIRST_ROLLER + (j + 1) % ROLLERS
      contacts += [Contact(8, one, *_STEEL_ON_STEEL),
                   Contact(2, one, *_STEEL_ON_STEEL),
                   Contact(min(one, following), max(one, following),
                           *_ROLLER_ON_ROLLER)]
  links = (tuple(Fixed(index)
                 for index in (STILL_ROLLER if roller else STILL))
           + _keyed() + _outputShaft()
           + (Motor(4, 5, (0.0, 0.0, 1.0), Drive()),)
           + (() if roller else _floating(8)))
  return Assembly(tuple(bodies), links + tuple(contacts)), tuple(states)


#  The bearing in the void (user, 2026-11-13: "let's have the
#  simulation in the void. We spawn in a little platform and the ball
#  bearing floats. if we fall down we just spawn back on the
#  platform"): no ground; where the pedestals stood, two platforms,
#  aluminium 10 mm thick and 200 mm across (to the walker as 110 m), the
#  first under the walker's start and the ramp's foot (its top where
#  the floor was), the second behind the shaft's back end, its top level
#  with the hole's floor, to step out onto; the bearings' housings, the
#  motor (its can alone, 'CAR_MOTOR_CAN') and the ramp float where they
#  stood, part of the world as before.
CAR_MOTOR_CAN = Body.of(prismOf(roundOutline(MOTOR_RADIUS, 32),
                                -0.5 * MOTOR_LENGTH, 0.5 * MOTOR_LENGTH),
                        7850.0)
_DECK = 0.01


def voidBearing(scale: float) -> tuple[Assembly, tuple[State, ...]]:
  """The 'voidBearing' function returns 'walkingBearing' with its
  roller bearing ('roller') in the void: no ground under it (step it
  with none), the motor its can alone, and in the pedestals' places
  (7 and 9) the two platforms: the first from 0.1 m behind the walker's
  start to 20 mm under the ramp's foot, its top at nought; the second
  from just behind the shaft's back end 0.25 m on, its top level with
  the hole's floor; both 0.2 m across, part of the world."""
  assembly, states = walkingBearing(scale, True)
  bodies, states = list(assembly.bodies), list(states)
  foot = -(SHAFT_FRONT + RAMP_GAP + 3.0 * _RAMP_HIGH)
  start, end = states[0].place[1] - 0.1, foot + 0.02
  front = Body.of(boxShape(0.2, end - start, _DECK), 2700.0)
  floor = CAR_MIDDLE[2] - SHAFT_INSIDE
  back = Body.of(boxShape(0.2, 0.25, _DECK), 2700.0)
  bodies[4] = CAR_MOTOR_CAN
  states[4] = _placedOn(CAR_MOTOR_CAN, (GEAR_CENTRE, 0.0, MOTOR_AT),
                        RING_UPRIGHT)
  bodies[7], states[7] = front, State((0.0, 0.5 * (start + end),
                                       -0.5 * _DECK))
  bodies[9], states[9] = back, State((0.0, SHAFT_BACK + 0.005 + 0.125,
                                      floor - 0.5 * _DECK))
  return (Assembly(tuple(bodies), assembly.connections), tuple(states))


def _placedOn(body: Body, at: Vector, turn: Quaternion) -> State:
  """Returns 'body' still, its own frame's origin at 'at' in the
  bearing's (its middle, its axle along z), turned 'turn'."""
  origin = plus(CAR_MIDDLE, rotated(RING_UPRIGHT, at))
  return State(plus(origin, rotated(turn, body.centre)), turn)


def _floating(index: int) -> tuple:
  """Returns how the roller (floating) bearing's housing, body
  'index', is held: five rods 10 mm long from the world, every one
  square to the axle (two along x, two along y and one across, at its
  middle and its face), so it can neither move across nor turn any way,
  but slides along the axle as the shaft takes it."""
  rim, face, rod = CAR_HOUSED.shape.bounds()[1], 0.009, 0.01
  ends = (((rim, 0.0, 0.0), (rod, 0.0, 0.0)),
          ((0.0, rim, 0.0), (0.0, rod, 0.0)),
          ((-rim, 0.0, 0.0), (0.0, rod, 0.0)),
          ((rim, 0.0, face), (rod, 0.0, 0.0)),
          ((0.0, rim, face), (0.0, rod, 0.0)))
  out = []
  for point, away in ends:
    world = plus(CAR_MIDDLE, rotated(RING_UPRIGHT, (
      point[0] + away[0], point[1] + away[1], BEARING_APART + point[2])))
    out.append(Actuator(None, world, index, point, HeldStroke(rod)))
  return tuple(out)


def _keyed() -> tuple:
  """Returns how the gear is held on the shaft, one with it: a tie at
  its middle and three rods '_KEY' long in the shaft's wall, one across
  (it turns with the shaft) and two along (it stands square on it)."""
  r = CAR_INNER.shape.bounds()[0] - 0.001
  return (Tie(2, (0.0, 0.0, GEAR_AT), 3, (0.0, 0.0, 0.0)),
          Actuator(2, (r, -_KEY, GEAR_AT), 3, (r, 0.0, 0.0),
                   HeldStroke(_KEY)),
          Actuator(2, (0.0, r, GEAR_AT - _KEY), 3, (0.0, r, 0.0),
                   HeldStroke(_KEY)),
          Actuator(2, (-r, 0.0, GEAR_AT - _KEY), 3, (-r, 0.0, 0.0),
                   HeldStroke(_KEY)))


def _outputShaft() -> tuple:
  """Returns the motor's output shaft, the pinion's bearing: a tie at
  the pinion's middle and two rods '_STUB' long across the shaft's stub
  at the housing's face, so the pinion turns about its axle and no
  other way."""
  face = 0.5 * MOTOR_LENGTH
  stub = (0.0, 0.0, MOTOR_AT + face - GEAR_AT)
  return (Tie(4, (0.0, 0.0, GEAR_AT - MOTOR_AT), 5, (0.0, 0.0, 0.0)),
          Actuator(4, (_STUB, 0.0, face), 5, stub, HeldStroke(_STUB)),
          Actuator(4, (0.0, _STUB, face), 5, stub, HeldStroke(_STUB)))


def carBallGiven(scale: float, assembly: Assembly, states: tuple[State, ...],
                 state: State) -> tuple[Assembly, tuple[State, ...]]:
  """The 'carBallGiven' function returns 'assembly' in 'states' (the
  walker, shrunk to 'scale', first) with one more of the car bearing's
  steel balls, last, in 'state', touching every body (steel on steel,
  the walker by its law shrunk as it is)."""
  return _ballGiven(assembly, states, CAR_BALL_BODY, state, _STEEL_ON_STEEL,
                    froudeOf(_WALKER_ON_STEEL, scale))


#  The wheel (user, 2026-11-12: "the world where the car wheel is the
#  size the bearing currently is, roughly", then "maybe the wheel should
#  be the size of the player"): the car's 205/55 R16 ('TYRE') on its
#  steel wheel, ET 40, on a stand on the road. The knuckle is a steel
#  block, 90 x 100 x 120 mm, held by six drawn legs ('KNUCKLE_RIG'); the
#  wheel's hub runs in 120 mm from the disc to its face. The bearing in
#  it is the stand-in the bearing's world made ready ("magic"): a ball
#  joint at the knuckle's middle and two held rods at its face, so the
#  hub turns freely about its axle and no other way (that world found
#  it stiff, 0.12 um under the ring's weight, and nearly free). On the
#  road the axle is held 'WHEEL_DROP' lower than the tyre's unloaded
#  radius, so the tyre carries ~3.6 kN (rubber on dry asphalt, 'ROAD':
#  1e6 N/m and a bristle as stiff at each lump, grip 1); on a lift
#  ('WHEEL_LIFT', a drop below nought) it hangs 3 cm clear, free to be
#  spun (user: "mount it to something and bring it to rotate with the
#  gravity gun").
ROAD = Ground(1e6, 0.5, 1.0, 1e6, 500.0)
WHEEL_BODY = Body.of(steelWheel(TYRE, 0.04, 0.12, 48), 7850.0)
KNUCKLE = Body.of(boxShape(0.09, 0.1, 0.12), 7850.0)
KNUCKLE_RIG = Hexapod(0.05, 0.035, 20.0, 20.0, 0.0, -0.06)
WHEEL_DROP = 0.018
WHEEL_LIFT = -0.03
#  How far out (along -y) the tyre's middle is from the knuckle's.
WHEEL_OUT = 0.17
#  A steel ball of 60 mm (0.89 kg) given on asking; on the tyre, the
#  wheel or the knuckle by '_STEEL_ON_TYRE'.
PEBBLE = Body.of(Sphere(0.03), 7850.0)
_STEEL_ON_TYRE = (1e6, 0.5, 0.8, 1e6, 200.0)
#  How long the tyre is let settle on the road as the wheel is built, s.
_SETTLE = 0.6


@functools.lru_cache(maxsize=4)
def walkingWheel(scale: float,
                 drop: float) -> tuple[Assembly, tuple[State, ...]]:
  """The 'walkingWheel' function returns the walker shrunk to 'scale'
  ('Walker.scaled') first, standing out before the wheel, the knuckle
  second (held by 'KNUCKLE_RIG' with the axle 'drop' m lower than the
  tyre's unloaded radius: 'WHEEL_DROP' on the road, 'WHEEL_LIFT' on a
  lift), the wheel third (on the knuckle's bearing, its axle along y),
  then the tyre's lumps; the walker touching every body (its law shrunk
  as it is); and how they start: the tyre settled ('_SETTLE' s, its
  lumps that would be under the road set on it), all but still.
  Remembered."""
  walker = WALKER.scaled(scale)
  body = walker.body()
  axle = 0.5 * TYRE.outside - drop
  middle = (0.0, 0.0, axle)
  held = HeldPose(middle, UNTURNED)
  legs = KNUCKLE_RIG.legs(KNUCKLE, 1, held)
  origin = (0.0, -WHEEL_OUT, axle)
  wheel = State(plus(origin, rotated(RING_UPRIGHT, WHEEL_BODY.centre)),
                RING_UPRIGHT)
  face = 0.05
  bearing = (Tie(1, (0.0, 0.0, 0.0), 2, (0.0, 0.0, -WHEEL_OUT)),
             Actuator(1, (0.035, -face, 0.0), 2, (0.0, 0.0, -0.12),
                      HeldStroke(0.035)),
             Actuator(1, (0.0, -face, 0.035), 2, (0.0, 0.0, -0.12),
                      HeldStroke(0.035)))
  node = TYRE.node()
  bodies = (body, KNUCKLE, WHEEL_BODY) + (node,) * TYRE.nodes
  walking = froudeOf(_WALKER_ON_STEEL, scale)
  contacts = tuple(Contact(0, other, *walking)
                   for other in range(1, len(bodies)))
  assembly = Assembly(bodies, legs + bearing + TYRE.springsOf(2, 3)
                      + contacts)
  lumps = tuple(State((lump.place[0], lump.place[1],
                       max(lump.place[2], TYRE.lump)), lump.turn)
                for lump in TYRE.statesOn(WHEEL_BODY, wheel))
  states = ((State((0.0, -0.75, walker.radius
                    - body.mass * 9.81 / ROAD.stiffness)),
             held.at(0.0).state(), wheel) + lumps)
  settled = World((0.0, 0.0, -9.81), 1e-3, ROAD).advancedAll(
      assembly, states, _SETTLE)
  return assembly, settled


def wheelSkin() -> TyreSkin:
  """The 'wheelSkin' function returns how the wheel's tyre looks in
  'walkingWheel' (the wheel third, its lumps from the fourth on), its
  tread 160 mm across; 'hitOf' it to grab or punt the tyre."""
  return TyreSkin(TYRE, WHEEL_BODY, 2, 3, 0.16)


def wheelBallGiven(scale: float, assembly: Assembly,
                   states: tuple[State, ...],
                   state: State) -> tuple[Assembly, tuple[State, ...]]:
  """The 'wheelBallGiven' function returns 'assembly' in 'states' (the
  walker, shrunk to 'scale', first) with one more 'PEBBLE', last, in
  'state', touching every body ('_STEEL_ON_TYRE', the walker by its law
  shrunk as it is)."""
  return _ballGiven(assembly, states, PEBBLE, state, _STEEL_ON_TYRE,
                    froudeOf(_WALKER_ON_STEEL, scale))


#  The small steps' proofs (user, 2026-11-13: "build it": the touches
#  kept as rules, 'SmallSteps'): a steel ball 50 mm across (514 g)
#  resting in a groove of two steel plates meeting at 'GROOVE_ANGLE'
#  either side of upright (90 degrees between them); the same ball
#  rolling down a steel ramp of 'RAMP_ANGLE' from 'RAMP_START' up it
#  (rolling, not sliding, it speeds up at 5/7 of g times the slope's
#  sine); a tower of oak blocks 100 mm on a side on the floor, each
#  turned 45 degrees on the one under it (each touching its neighbours
#  along their edges' middles, none edge on edge). Their contacts'
#  springs steel's on steel at the ball's weight (Hertz, ~2e7 N/m) and
#  the yard's on wood, so the springs' world ('World') steps them too.
PROOF_BALL = Body.of(Sphere(0.025), 7850.0)
PROOF_PLATE = Body.of(boxShape(0.2, 0.08, 0.01), 7850.0)
PROOF_RAMP = Body.of(boxShape(0.2, 1.0, 0.02), 7850.0)
PROOF_BLOCK = Body.of(boxShape(0.1, 0.1, 0.1), 700.0)
GROOVE_ANGLE, RAMP_ANGLE = math.radians(45.0), math.radians(20.0)
RAMP_START = 0.4
_STEEL_PROOF = (2e7, 0.1, 0.5, 2e7, 1000.0)


def ballInGroove() -> tuple[Assembly, tuple[State, ...]]:
  """The 'ballInGroove' function returns 'PROOF_BALL' (first) resting
  still in the groove of two 'PROOF_PLATE's along x, part of the world,
  their tops meeting at the origin, each 'GROOVE_ANGLE' from level;
  the ball touching each plate's top, neither pressed."""
  r, a = PROOF_BALL.shape.radius, GROOVE_ANGLE
  half, thick = 0.04, 0.005
  states = [State((0.0, 0.0, r / math.cos(a)))]
  for side in (1.0, -1.0):
    states.append(State((0.0, side * (half * math.cos(a)
                                      + thick * math.sin(a)),
                         half * math.sin(a) - thick * math.cos(a)),
                        turnAbout((1.0, 0.0, 0.0), side * a)))
  links = (Fixed(1), Fixed(2), Contact(0, 1, *_STEEL_PROOF),
           Contact(0, 2, *_STEEL_PROOF))
  return (Assembly((PROOF_BALL, PROOF_PLATE, PROOF_PLATE), links),
          tuple(states))


def ballOnRamp() -> tuple[Assembly, tuple[State, ...]]:
  """The 'ballOnRamp' function returns 'PROOF_BALL' (first) still on
  'PROOF_RAMP' (part of the world, its middle at the origin, rising
  along y at 'RAMP_ANGLE'), 'RAMP_START' up it from its middle, touching
  it, not pressed."""
  r, a = PROOF_BALL.shape.radius, RAMP_ANGLE
  normal = (0.0, -math.sin(a), math.cos(a))
  along = (0.0, math.cos(a), math.sin(a))
  lift = 0.01 + r
  ball = State(tuple(lift * n + RAMP_START * u
                     for n, u in zip(normal, along)))
  ramp = State(ORIGIN, turnAbout((1.0, 0.0, 0.0), a))
  return (Assembly((PROOF_BALL, PROOF_RAMP),
                   (Fixed(1), Contact(0, 1, *_STEEL_PROOF))),
          (ball, ramp))


def twistedTower(levels: int, twist: float = 0.25 * math.pi
                 ) -> tuple[Assembly, tuple[State, ...]]:
  """The 'twistedTower' function returns 'levels' of 'PROOF_BLOCK' on
  the floor (stand them on 'YARD_GROUND'), the lowest first, each
  turned 'twist' (45 degrees; nought: stacked true, edge on edge) about
  the upright from the one under it, standing still, touching, none
  pressed; each touches the one over it as oak on oak."""
  states = tuple(State((0.0, 0.0, 0.05 + 0.1 * k),
                       turnAbout((0.0, 0.0, 1.0), twist * k))
                 for k in range(levels))
  contacts = tuple(Contact(k, k + 1, *_ON_WOOD) for k in range(levels - 1))
  return Assembly((PROOF_BLOCK,) * levels, contacts), states
