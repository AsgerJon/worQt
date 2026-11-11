"""
The 'worQt.gaming.billiards' package is billiards, three-cushion
carambole first: the table and its balls, needing no Qt;
'worQt.gaming.billiards.gui' shows them in 3D.

- CaromTable: the shape of a three-cushion table, its spots and
  diamonds, and the balls as a game opens.
- Ball: a ball on the table, its name, where it lies and how it is
  turned.
- turnOf, STILL, Turn: turns as unit quaternions, and the turn that
  leaves a ball as it is.
- Cloth: the felt, moving a single ball over it exactly: sliding,
  rolling, spinning in place, still.
- Cushion, Carom: how the cushions push back, Mathavan et al.'s (2010)
  cushion with the user's squaring past where it holds, and how two
  balls meet, every value adjustable; mathavanRebound, their rigid
  cushion, the reference.
- Motion: the balls on the table, over the cloth exactly, through
  their hits on the cushions and on each other step by step; 'played'
  also logs each contact as it begins, a 'Touch', the cushions named
  as in 'CUSHIONS'; 'glided' and 'collided' are its pieces, a 'Glide'
  on the cloth and the steps through hits, 'Hits', which a 'Recorder'
  runs on sample by sample.
- Recorder, Recording, Stretch, STATE, PIN_STATE: a shot played at
  once and sampled, streamed a stretch at a time, and shown from the
  samples, keglebillard's pins with the balls.
- Trails, ribbonMesh: the way each ball of a shot went, as far as it is
  shown, and the flat ribbon it is drawn with on the cloth.
- Trench, Trenches, trenchMesh: the way ball 1 sets off along the aim
  and ball 2's after it meets it, to a cushion, a ball or its rest, as
  a shot sends them, and the trench they are drawn with on the cloth.
- Room, TABLES: the billiard room the game opens in, both tables in it,
  walked first person: kept on the floor, out of the walls and tables,
  near a table to play there.
- ShotWorker: shots played in a process of their own, streamed back.
- KeglePin, PROFILE: a keglebillard pin's shape and mass, toppling.
- PinField, PinContacts: the pins as rigid bodies on the cloth, knocked
  over by balls and each other, credited to the ball that set them going.
- KegleGame: a keglebillard game as it is played, shot by shot, the
  game loop: the match, how the balls lie for each shot, the call.
- KegleMotion, KegleHits, KegleRecorder, ZONE: keglebillard's balls and
  pins moved together, through their hits stepped in one compiled
  kernel, and a shot of them played at once and sampled.
- KegleTable, KegleShot, Streak, KegleCall, KegleReferee, KegleMatch,
  DISTANCES: keglebillard, the second game, as Den Danske Billard
  Union's rules have it: the table with pockets, pins and spots, the
  referee's calls, and the match to a distance of 200 to 800.
- Cue: the stick, just another cushion, one that moves: striking a ball
  at a point on its face, squirting it off the stick's line; 'sent'
  sends it along a line as a player aims.
- Unfolded, Crossing, Hit, Fan: the table unfolded, every cushion a
  mirror into a copy of it; English as an arc across the copies, where
  it crosses a cushion's line; where it first meets a ball; and the fan
  of where the two may go then.
- Rules, Shot, Call, Referee: three-cushion judged as the FFB's Code
  sportif carambole has it; 'FROZEN', how near is touching.
- Match, PHASES: a match between two players, the lag, innings, runs,
  the equalizing inning, sets.
- prismMesh, tableMeshes, diamondMesh: the table's cushions, woodwork
  and diamonds as triangles, after the tables of Søren Søgaard.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._carom_table import STILL, Turn, turnOf, Ball, CaromTable
from ._cloth import Cloth
from ._cushion import Cushion
from ._mathavan import mathavanRebound
from ._carom import Carom
from ._motion import CUSHIONS, Touch, Glide, Hits, Motion
from ._recorder import STATE, PIN_STATE, Stretch, Recording, Recorder
from ._trails import Trails, ribbonMesh
from ._trenches import Trench, Trenches, trenchMesh
from ._room import TABLES, Room
from ._shot_worker import ShotWorker
from ._cue import Cue
from ._unfolded import Crossing, Hit, Fan, Run, Unfolded
from ._referee import FROZEN, Rules, Shot, Call, Referee
from ._match import PHASES, Match
from ._kegle_table import KegleTable
from ._kegle_pin import PROFILE, KeglePin
from ._kegle_pins import PinContacts, PinField
from ._kegle_motion import ZONE, KegleMotion, KegleHits, KegleRecorder
from ._kegle_referee import PIN_POINTS, RED_POINTS, KegleShot, Streak
from ._kegle_referee import KegleCall, KegleReferee
from ._kegle_match import DISTANCES, KEGLE_PHASES, KegleMatch
from ._kegle_game import KegleGame
from ._table_shapes import prismMesh, tableMeshes, diamondMesh
from ._table_shapes import latheMesh

__all__ = (
  'STILL',
  'Turn',
  'turnOf',
  'Ball',
  'CaromTable',
  'Cloth',
  'Cushion',
  'mathavanRebound',
  'Carom',
  'CUSHIONS',
  'Touch',
  'Glide',
  'Motion',
  'Hits',
  'STATE',
  'PIN_STATE',
  'Stretch',
  'Recording',
  'Recorder',
  'Trails',
  'ribbonMesh',
  'Trench',
  'TABLES',
  'Room',
  'Trenches',
  'trenchMesh',
  'ShotWorker',
  'Cue',
  'Crossing',
  'Hit',
  'Fan',
  'Run',
  'Unfolded',
  'FROZEN',
  'Rules',
  'Shot',
  'Call',
  'Referee',
  'PHASES',
  'Match',
  'KegleTable',
  'PROFILE',
  'KeglePin',
  'PinContacts',
  'PinField',
  'ZONE',
  'KegleMotion',
  'KegleHits',
  'KegleRecorder',
  'PIN_POINTS',
  'RED_POINTS',
  'KegleShot',
  'Streak',
  'KegleCall',
  'KegleReferee',
  'DISTANCES',
  'KEGLE_PHASES',
  'KegleMatch',
  'KegleGame',
  'prismMesh',
  'tableMeshes',
  'diamondMesh',
  'latheMesh',
)
