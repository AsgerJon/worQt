"""
The jobs a 'Worker' runs in the process OpenSees runs in: 'runJob'
solves a model linearly; 'openSession' builds one to be pushed and
'advanceSession' pushes it a number of steps.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
import tempfile
import time

#  How OpenSees is told to number the freedoms and solve the equations,
#  sparse ('SparseGeneral' is quicker but frees its memory twice when the
#  analysis is set up again); the constraints are held 'Plain' unless
#  nodes are coupled, when they are 'Transformation', which is slower
_EQUATIONS = (
    ('numberer', 'RCM'),
    ('system', 'UmfPack'),
)
#  Linearly, the loads in full in one step
_LINEAR = (
    ('integrator', 'LoadControl', 1.0),
    ('algorithm', 'Linear'),
    ('analysis', 'Static'),
)
#  The ways a step is tried, each with the iterations it is given: the
#  tangent first, then those that cope where it does not
_TRIES = (
    (('Newton',), 50),
    (('KrylovNewton',), 100),
    (('NewtonLineSearch', 0.8), 100),
    (('ModifiedNewton', '-initial'), 500),
)
_PRECISION = 1e-3  # of the step, the least change still iterated on
_LEAST_CHANGE = 1e-10  # iterated on, for a step of nought
_SPLITS = 3  # times a step not made is split in four
_BUDGET = 45.0  # seconds a step may take, split and tried every way
#  The node and freedom a session pushes, in this process
_PUSHED = {}


def quietProcess() -> None:
  """The 'quietProcess' function sends the standard output and error of
  the process nowhere, so OpenSees cannot write past a job into the
  asker's terminal, as it does when its process ends."""
  quiet = os.open(os.devnull, os.O_WRONLY)
  os.dup2(quiet, 1)
  os.dup2(quiet, 2)
  os.close(quiet)


def runJob(commands: tuple, queries: tuple) -> tuple:
  """The 'runJob' function builds a model in OpenSees from its
  'commands', starting from nothing, analyses it linearly and returns
  ('solved', frame, said): the frame of what came out, the elements
  asked each of the 'queries', and what OpenSees said meanwhile; or
  ('refused', command, said) when OpenSees refuses a command."""
  return _heard(_solve, commands, queries)


def openSession(commands: tuple, node: int, freedom: int,
                token: int) -> tuple:
  """The 'openSession' function builds a model in OpenSees from its
  'commands', starting from nothing, to be pushed at 'freedom' of
  'node' by the session 'token' names, and returns ('opened', said), or
  ('refused', command, said) when OpenSees refuses a command."""
  return _heard(_open, commands, node, freedom, token)


def advanceSession(token: int, increment: float, count: int,
                   queries: tuple) -> tuple:
  """The 'advanceSession' function pushes the model the session
  'token' names opened 'count' steps of 'increment' each and returns
  ('advanced', frames, stuck, said): a frame to each step made, the
  elements asked each of the 'queries', and whether a step could not be
  made, which ends the pushing early; or ('refused', command, said) if
  another session has been opened since."""
  return _heard(_advance, token, increment, count, queries)


def _heard(job, *args) -> tuple:
  """Runs 'job' with what OpenSees writes past Python sent to a file of
  its own, and returns what it returns, with what OpenSees said."""
  with tempfile.TemporaryFile() as log:
    saved = _divert(log.fileno())
    try:
      outcome = job(*args)
    finally:
      _restore(saved)
    log.seek(0)
    said = log.read().decode('utf-8', 'replace')
  return (*outcome, said)


def _divert(target: int) -> tuple[int, int]:
  """Sends what is written to the standard output and error to 'target'
  and returns where they went before."""
  sys.stdout.flush()
  sys.stderr.flush()
  saved = os.dup(1), os.dup(2)
  os.dup2(target, 1)
  os.dup2(target, 2)
  return saved


def _restore(saved: tuple[int, int]) -> None:
  """Sends the standard output and error back where they went."""
  sys.stdout.flush()
  sys.stderr.flush()
  for descriptor, original in zip((1, 2), saved):
    os.dup2(original, descriptor)
    os.close(original)


def _constraints(commands: tuple) -> tuple:
  """How the constraints of 'commands' are held: 'Plain', fast, unless
  nodes are coupled, then by 'Transformation'."""
  coupled = any(command[0] == 'equalDOF' for command in commands)
  return ('constraints', 'Transformation' if coupled else 'Plain')


def _opensees():
  """OpenSees, imported here only, in the process it runs in."""
  import openseespy.opensees as ops
  return ops


def _build(commands: tuple) -> tuple | None:
  """Builds the model from nothing; returns the command OpenSees
  refused, if it refused one."""
  ops = _opensees()
  ops.wipe()
  _PUSHED.clear()
  for command in commands:
    try:
      getattr(ops, command[0])(*command[1:])
    except ops.OpenSeesError:
      return command
  return None


def _solve(commands: tuple, queries: tuple) -> tuple:
  """Builds, analyses linearly and reads off the model."""
  refused = _build((*commands, _constraints(commands), *_EQUATIONS,
                    *_LINEAR))
  if refused is not None:
    return 'refused', refused
  ops = _opensees()
  if ops.analyze(1) != 0:
    return 'refused', ('analyze', 1)
  frame = _frame(queries)
  ops.wipe()
  return 'solved', frame


def _open(commands: tuple, node: int, freedom: int, token: int) -> tuple:
  """Builds the model to be pushed at 'freedom' of 'node'."""
  pushing = (('integrator', 'DisplacementControl', node, freedom, 0.0),
             ('test', 'NormDispIncr', 1e-8, 50),
             ('algorithm', 'Newton'),
             ('analysis', 'Static'))
  refused = _build((*commands, _constraints(commands), *_EQUATIONS,
                    *pushing))
  if refused is not None:
    return 'refused', refused
  _PUSHED.update({'node': node, 'freedom': freedom, 'token': token})
  return ('opened',)


def _advance(token: int, increment: float, count: int,
             queries: tuple) -> tuple:
  """Pushes the model opened, a frame to each step made."""
  if _PUSHED.get('token') != token:
    print('another session has been opened in this process since')
    return 'refused', ('advance', increment, count)
  frames = []
  for _ in range(count):
    if not _push(increment, 0, time.monotonic() + _BUDGET):
      return 'advanced', (*frames,), True
    frames.append(_frame(queries))
  return 'advanced', (*frames,), False


def _push(increment: float, depth: int, until: float) -> bool:
  """Makes a step of 'increment', split in four, and those again, up to
  '_SPLITS' times, where it cannot be made whole, giving up once the
  clock passes 'until'; tells whether it was made."""
  if time.monotonic() > until:
    return False
  if _tryStep(increment, until):
    return True
  if depth == _SPLITS:
    return False
  return all(_push(increment / 4, depth + 1, until) for _ in range(4))


def _tryStep(increment: float, until: float) -> bool:
  """Tries a step of 'increment' each of the ways; tells whether one
  made it."""
  ops = _opensees()
  ops.integrator('DisplacementControl', _PUSHED['node'],
                 _PUSHED['freedom'], increment)
  least = max(abs(increment) * _PRECISION, _LEAST_CHANGE)
  for algorithm, iterations in _TRIES:
    if time.monotonic() > until:
      return False
    _set('test', ('NormDispIncr', least, iterations))
    _set('algorithm', algorithm)
    if ops.analyze(1) == 0:
      return True
  return False


def _set(command: str, args: tuple) -> None:
  """Sets the analysis's 'command' to 'args', unless it is so already:
  OpenSees sets its analysis up afresh at each such command."""
  if _PUSHED.get(command) != args:
    getattr(_opensees(), command)(*args)
    _PUSHED[command] = args


def _frame(queries: tuple) -> tuple:
  """What the model is now: (displacements, reactions, responses,
  loadFactor), a tuple to each node, and to each of the 'queries' a
  tuple to each element."""
  ops = _opensees()
  ops.reactions()
  nodes = sorted(ops.getNodeTags())
  elements = sorted(ops.getEleTags())
  displacements = (*[(*ops.nodeDisp(node),) for node in nodes],)
  reactions = (*[(*ops.nodeReaction(node),) for node in nodes],)
  responses = []
  for query in queries:
    args = query if isinstance(query, tuple) else (query,)
    answers = [(*ops.eleResponse(element, *args),) for element in elements]
    responses.append((*answers,))
  return displacements, reactions, (*responses,), ops.getLoadFactor(1)
