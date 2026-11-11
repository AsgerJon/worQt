"""
TestSolver covers 'Solver', solving models with OpenSees in a process
of its own: the answers known by hand come out, the reactions balance
the loads, the elements answer what they are asked, a model OpenSees
refuses raises with its own words and leaves nothing behind, and a
process that ends is replaced.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import multiprocessing
import os
import signal
import time

from worksees import Solver, SolverError, SolverDied

from . import WorkseesTest, cantilever, patch


class TestSolver(WorkseesTest):
  """Tests for 'Solver'."""

  def test_cantilever(self) -> None:
    """The head moves PL³/3EI and turns PL²/2EI; the foot is held by
    the push and its moment."""
    result = self.solver.solve(cantilever())
    sideways, down, turn = result.displacement(2)
    self.assertAlmostEqual(sideways, 1000 * 3 ** 3 / (3 * 200e9 * 1e-4))
    self.assertAlmostEqual(down, 0.0)
    self.assertAlmostEqual(turn, -1000 * 3 ** 2 / (2 * 200e9 * 1e-4))
    rx, ry, moment = result.reaction(1)
    self.assertAlmostEqual(rx, -1000.0, 6)
    self.assertAlmostEqual(ry, 0.0, 6)
    self.assertAlmostEqual(moment, 3000.0, 6)
    for force in result.reaction(2):
      self.assertAlmostEqual(force, 0.0, 6)

  def test_patch(self) -> None:
    """Quads however shaped carry a uniform stress exactly: P / (h t)
    at every point, the right edge moving sigma L / E."""
    result = self.solver.solve(patch(), 'stresses')
    for answer in result.response('stresses'):
      self.assertEqual(len(answer), 12)  # 4 points, 3 stresses each
      for sx, sy, sxy in zip(answer[0::3], answer[1::3], answer[2::3]):
        self.assertAlmostEqual(sx, 10.0, 9)
        self.assertAlmostEqual(sy, 0.0, 9)
        self.assertAlmostEqual(sxy, 0.0, 9)
    for node in (3, 6, 9):
      self.assertAlmostEqual(result.displacement(node)[0], 0.02, 12)

  def test_reactions_balance_loads(self) -> None:
    """What holds the plate balances what pulls it."""
    result = self.solver.solve(patch())
    rx = sum(reaction[0] for reaction in result.reactions)
    ry = sum(reaction[1] for reaction in result.reactions)
    self.assertAlmostEqual(rx, -1.0, 12)
    self.assertAlmostEqual(ry, 0.0, 12)

  def test_responses(self) -> None:
    """The elements answer each query asked, one answer to each, and
    none they were not asked."""
    result = self.solver.solve(patch(), 'stresses', 'strains')
    self.assertEqual(result.queries, ('stresses', 'strains'))
    self.assertEqual(len(result.response('strains')), 4)
    with self.assertRaises(KeyError):
      result.response('forces')

  def test_refused(self) -> None:
    """A model OpenSees refuses raises, naming the command and holding
    what OpenSees said; the next model starts from nothing."""
    model = cantilever()
    model.add('element', 'noSuchElement', 1, 2)
    with self.assertRaises(SolverError) as caught:
      self.solver.solve(model)
    self.assertEqual(caught.exception.command[:3],
                     ('element', 'noSuchElement', 2))
    self.assertIn('noSuchElement', caught.exception.said)
    result = self.solver.solve(cantilever())
    self.assertAlmostEqual(result.displacement(2)[0], 4.5e-4)

  def test_died(self) -> None:
    """A process that ends raises 'SolverDied'; the next model starts a
    new one."""
    self.solver.solve(cantilever())
    self.assertTrue(self.solver.running)
    for child in multiprocessing.active_children():
      os.kill(child.pid, signal.SIGKILL)
    time.sleep(0.5)
    with self.assertRaises(SolverDied):
      self.solver.solve(cantilever())
    self.assertFalse(self.solver.running)
    result = self.solver.solve(cantilever())
    self.assertAlmostEqual(result.displacement(2)[0], 4.5e-4)

  def test_close(self) -> None:
    """Its process starts on the first model and ends on 'close' or with
    its 'with' block."""
    with Solver() as solver:
      self.assertFalse(solver.running)
      solver.solve(cantilever())
      self.assertTrue(solver.running)
    self.assertFalse(solver.running)
    solver.solve(cantilever())
    self.assertTrue(solver.running)
    solver.close()
    self.assertFalse(solver.running)
