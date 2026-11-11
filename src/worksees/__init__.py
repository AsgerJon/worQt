"""
The 'worksees' package sets up finite element analyses for OpenSees and
reads back what comes out, OpenSees kept in a process of its own.

- Model: a finite element model in OpenSees's terms, kept as plain
  values: nodes, parts (materials, sections, transforms, elements),
  fixed freedoms and loads.
- Worker: the process OpenSees runs in.
- Solver: solves models linearly with OpenSees, in a process of its own.
- Session: keeps a model in OpenSees and pushes it step by step under
  displacement control, as an actuator pushes a specimen.
- Result: how the nodes moved, what held them, what the elements
  answered.
- SolverError: OpenSees refused a model; SolverDied: its process ended.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._solver_error import SolverError, SolverDied
from ._model import Model
from ._result import Result
from ._worker import Worker
from ._solver import Solver
from ._session import Session

__all__ = (
  'SolverError',
  'SolverDied',
  'Model',
  'Result',
  'Worker',
  'Solver',
  'Session',
)
