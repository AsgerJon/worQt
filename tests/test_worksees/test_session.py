"""
TestSession covers 'Session', keeping a model in OpenSees and pushing it
step by step under displacement control, as an actuator pushes a
specimen: each step moves the node pushed by the increment, and the load
factor is what holds it there; a session may share a worker's process,
which keeps going after it, and a session opened after another there
leaves that one refused.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worksees import Session, SolverError, Worker

from . import WorkseesTest, bar


class TestSession(WorkseesTest):
  """Tests for 'Session'."""

  def test_pushed(self) -> None:
    """Each step moves the node pushed by the increment, held by E A u
    / L."""
    with Session(bar(), 2, 1) as session:
      results = session.advance(0.01, 5)
      self.assertEqual(len(results), 5)
      self.assertEqual(session.steps, 5)
      self.assertFalse(session.stuck)
      for step, result in enumerate(results, 1):
        self.assertAlmostEqual(result.displacement(2)[0], 0.01 * step)
        self.assertAlmostEqual(result.loadFactor, 10.0 * step)
        self.assertAlmostEqual(result.reaction(1)[0], -10.0 * step)
      more = session.advance(0.01, 2)
      self.assertAlmostEqual(more[-1].loadFactor, 70.0)
      self.assertEqual(session.steps, 7)

  def test_pushed_back(self) -> None:
    """A step back moves the node back, and the factor with it."""
    with Session(bar(), 2, 1) as session:
      session.advance(0.02, 2)
      back = session.advance(-0.01, 1)
      self.assertAlmostEqual(back[0].displacement(2)[0], 0.03)
      self.assertAlmostEqual(back[0].loadFactor, 30.0)

  def test_held(self) -> None:
    """A step of nought holds the node where it is, the factor with
    it."""
    with Session(bar(), 2, 1) as session:
      session.advance(0.01, 3)
      held = session.advance(0.0, 2)
      self.assertEqual(len(held), 2)
      self.assertAlmostEqual(held[-1].displacement(2)[0], 0.03)
      self.assertAlmostEqual(held[-1].loadFactor, 30.0)

  def test_queries(self) -> None:
    """The elements answer what they are asked at each step."""
    with Session(bar(), 2, 1) as session:
      results = session.advance(0.01, 2, 'axialForce')
      self.assertAlmostEqual(results[1].response('axialForce')[0][0], 20.0)

  def test_refused(self) -> None:
    """A node or freedom that is not there is refused before OpenSees is
    asked; a command OpenSees refuses, when the session is made."""
    with self.assertRaises(ValueError):
      Session(bar(), 3, 1)
    with self.assertRaises(ValueError):
      Session(bar(), 2, 2)
    model = bar()
    model.add('element', 'noSuchElement', 1, 2)
    with self.assertRaises(SolverError) as caught:
      Session(model, 2, 1)
    self.assertIn('noSuchElement', caught.exception.said)

  def test_shared_worker(self) -> None:
    """Sessions given a worker share its process, which keeps going
    after them; the one opened last there is the one pushed, the one
    before refused."""
    worker = Worker()
    try:
      first = Session(bar(), 2, 1, worker)
      first.advance(0.01, 1)
      second = Session(bar(), 2, 1, worker)
      with self.assertRaises(SolverError):
        first.advance(0.01, 1)
      self.assertAlmostEqual(second.advance(0.01, 2)[-1].loadFactor, 20.0)
      first.close()
      second.close()
      self.assertTrue(worker.running)
    finally:
      worker.close()
    self.assertFalse(worker.running)

  def test_own_worker(self) -> None:
    """A session given no worker has a process of its own, ended when
    it is closed."""
    session = Session(bar(), 2, 1)
    self.assertTrue(session.ownsWorker)
    self.assertTrue(session.worker.running)
    session.close()
    self.assertFalse(session.worker.running)
