"""
Reading is what the instruments read at a cycle of a beam test;
LabEvent is something that happened to the beam on the way.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple


class Reading(NamedTuple):
  """
  Reading is what is read at a 'step', a cycle of the control, of a beam
  test, 'time' seconds in, up positive as the transducers under the
  beam read: the control's 'command' and its 'feedback', the reading of
  the transducer it reads, in mm; the 'stroke' of the actuator driven,
  how far it has moved up, in mm, less than nought pushing down; the
  'forces' each actuator puts on the beam, in kN, less than nought
  pushing down, and their total, 'force'; each transducer's reading, in
  mm, in 'transducers'; how far the underside's middle has moved down
  at each line of the mesh along the beam, in mm, for drawing it, in
  'deflections'; each 'cells' of the beam's face, a column of bricks
  across it, its greatest principal strain in the plane of the face,
  tension positive, the direction that pulls in, in radians from along
  the beam, and its least principal strain; and the greatest strains
  of the 'bottomBars' and the 'topBars' in each stretch of the mesh
  along the beam, and of each of the 'stirrups'.
  """

  step: int
  time: float
  command: float
  feedback: float
  stroke: float
  forces: tuple[float, ...]
  force: float
  transducers: tuple[float, ...]
  deflections: tuple[float, ...]
  cells: tuple[tuple[float, float, float], ...]
  bottomBars: tuple[float, ...]
  topBars: tuple[float, ...]
  stirrups: tuple[float, ...]


class LabEvent(NamedTuple):
  """
  LabEvent is something that happened to the beam during a test: its
  'name', such as 'first crack', at which 'step', the driven actuator's
  'stroke' and the total 'force', up positive, and 'where' along the
  beam, in mm from its left end.
  """

  name: str
  step: int
  stroke: float
  force: float
  where: float
