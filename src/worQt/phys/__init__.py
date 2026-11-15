"""
The 'worQt.phys' package is the physics lab's own physics, made,
examined and tested here: the reference a port to C++ is held to. In m,
kg, N and s, z up; plain Python floats, every sum written out; no Qt.

- Shape: the outside of a solid, any solid, a closed surface of
  triangles, and its volume, centre and moments; 'boxShape',
  'cylinderShape' and 'wedgeShape' make three.
- Body, State: a rigid body, its mass, centre, inertia and shape; where
  it is and how it moves, its six degrees of freedom.
- Ground: the flat ground, pushing back where a body's points press
  into it, holding them by bristles as friction does.
- Tie, Weld, Spring, Damper, Assembly: bodies tied together at a point
  on each by a cord of no length, holding the points together, the
  bodies turning freely about them; bodies welded into one new rigid
  body; a coil spring, and a dashpot, between points on two bodies; an
  actuator, a rigid rod whose length its stroke sets, with whatever
  force it takes (HeldStroke, SineStroke); a contact, letting two bodies
  touch, rest one on the other, slide; bodies put together so.
- World: gravity, the ground, and bodies stepped on through time, alone
  or put together, the ties' pulls and actuators' pushes read off.
- SmallSteps: a world stepped as GPUs step games', its touches kept as
  rules in small steps, all at once, in float32 (so far balls, convex
  shapes, the ground, grip); 'ballInGroove', 'ballOnRamp',
  'twistedTower' its proofs.
- Books, Stored, Grease, Sleep: the energy a run gains and loses, line
  by line; the energy held at a moment; random shaking, its work
  booked; bodies at rest let sleep.
- Hexapod, LegStroke, HeldPose, SwayingPose, PoseAt: a test rig, a
  moving platform on six actuators, its legs' strokes worked out from
  the motion it is to make.
- Walker, Grabber: a person walking among the bodies (a ball where
  their feet are, rolled by their legs), and a tool in their hands that
  pulls a body in, holds it before their eyes and punts it away.
- Tyre, TyreSkin: a car's tyre built from what it is made of (its belt
  and tread as lumps, held to the rim by laced rubber springs) on its
  steel wheel, and how it looks as it gives.
- Motor, Drive: a motor twisting one body against another, its drive
  set between runs (a torque, a servo, a brake).
- carBuilt, drive, steer: the car, four wheels on suspensions of their
  own, steered through a column, a motor in each bearing.
- Terrain, track: the ground shaped (heights on a grid), and the car's
  track.
- The vectors and turns, as plain tuples.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._vectors import Vector, Matrix, Quaternion
from ._vectors import ORIGIN, UNTURNED, IDENTITY, AXES
from ._vectors import plus, minus, scaled, dot, cross, norm
from ._vectors import applied, transposed, matrixProduct
from ._vectors import product, conjugate, normalised, turnAbout, rotated
from ._vectors import matrixOf, turnOf, solved
from ._shape import Shape, Sphere, boxShape, cylinderShape, wedgeShape
from ._poke import driven, hitOf, motorTorque, poked, reachOf
from ._poke import rotorSpinOf, runMotor
from ._turned import Turned, innerRing, onShaft, outerRing
from ._turned import nuInnerRing, nuOuterRing, onShaftOf, rollerOf
from ._turned import rollerShape
from ._gears import centreOf, spurGear
from ._tyre import TYRE, Tyre, TyreSkin, steelWheel
from ._body import Body, State
from ._ground import Ground
from ._assembly import Tie, Weld, Spring, Damper, Actuator, Contact
from ._assembly import Drag, Drive, Fixed, Motor
from ._assembly import ATMOSPHERE, Air, CordLine, Crowd, Tyre
from ._assembly import BrakeLine, Bush, DiscBrake, Hinge, Slide
from ._assembly import FourthWall, GearMesh, Housed, RackAndPinion
from ._assembly import TurnPoint
from ._assembly import HUMP_ROOM, Hump, Humps, Ram
from ._assembly import Assembly
from ._assembly import HeldStroke, SineStroke
from ._books import Books, Stored, Grease, Sleep
from ._world import FULL, LIVE, Fidelity, World
from ._small_steps import SmallSteps
from ._scenes import ballsUnderPrism, outerRingWithBalls, prismLaunched
from ._scenes import froudeOf, groundAt, towerOnHexapod, walkingBearing
from ._scenes import walkingRing
from ._scenes import walkingYard
from ._scenes import ballInGroove, ballOnRamp, twistedTower
from ._scenes import voidBearing
from ._hub import rearHub, hubShape, spindleShape, cageShape
from ._scenes import ROAD, walkingWheel, wheelBallGiven, wheelSkin
from ._car import CAR_ROAD, CarBuild, camberOf, carBuilt, carWheel
from ._car import carWorld, drive, speedOf, steer, steeringOf, toeOf
from ._car import carPlaced, ovalWorld, trackWorld
from ._terrain import Terrain, track
from ._car import wheelSpinOf
from ._scenes import carBallGiven, giantBallGiven, oakBallGiven
from ._walking import Walker, Grabber, wantedOf, flyingOf
from ._hexapod import PoseAt, HeldPose, SwayingPose, LegStroke, Hexapod

__all__ = (
  'Vector',
  'Matrix',
  'Quaternion',
  'ORIGIN',
  'UNTURNED',
  'IDENTITY',
  'AXES',
  'plus',
  'minus',
  'scaled',
  'dot',
  'cross',
  'norm',
  'applied',
  'transposed',
  'matrixProduct',
  'product',
  'conjugate',
  'normalised',
  'turnAbout',
  'rotated',
  'matrixOf',
  'turnOf',
  'solved',
  'Shape',
  'Sphere',
  'Turned',
  'outerRing',
  'innerRing',
  'onShaft',
  'centreOf',
  'spurGear',
  'TYRE',
  'Tyre',
  'TyreSkin',
  'steelWheel',
  'hitOf',
  'poked',
  'reachOf',
  'driven',
  'motorTorque',
  'rotorSpinOf',
  'runMotor',
  'boxShape',
  'cylinderShape',
  'wedgeShape',
  'Body',
  'State',
  'Ground',
  'Tie',
  'Drive',
  'Motor',
  'Fixed',
  'Drag',
  'ATMOSPHERE',
  'Air',
  'CordLine',
  'Crowd',
  'Tyre',
  'BrakeLine',
  'Bush',
  'DiscBrake',
  'Hinge',
  'Slide',
  'FourthWall',
  'TurnPoint',
  'GearMesh',
  'Housed',
  'RackAndPinion',
  'Ram',
  'Hump',
  'Humps',
  'HUMP_ROOM',
  'CAR_ROAD',
  'CarBuild',
  'camberOf',
  'carBuilt',
  'carWheel',
  'carWorld',
  'drive',
  'speedOf',
  'steer',
  'steeringOf',
  'toeOf',
  'wheelSpinOf',
  'trackWorld',
  'ovalWorld',
  'carPlaced',
  'Terrain',
  'track',
  'Weld',
  'Spring',
  'Damper',
  'Actuator',
  'Contact',
  'HeldStroke',
  'SineStroke',
  'Assembly',
  'Books',
  'Stored',
  'Grease',
  'Sleep',
  'World',
  'Fidelity',
  'FULL',
  'LIVE',
  'SmallSteps',
  'ballInGroove',
  'ballOnRamp',
  'twistedTower',
  'towerOnHexapod',
  'ballsUnderPrism',
  'outerRingWithBalls',
  'prismLaunched',
  'walkingYard',
  'walkingRing',
  'walkingBearing',
  'ROAD',
  'walkingWheel',
  'wheelBallGiven',
  'wheelSkin',
  'froudeOf',
  'groundAt',
  'giantBallGiven',
  'oakBallGiven',
  'carBallGiven',
  'Walker',
  'Grabber',
  'wantedOf',
  'flyingOf',
  'PoseAt',
  'HeldPose',
  'SwayingPose',
  'LegStroke',
  'Hexapod',
)
