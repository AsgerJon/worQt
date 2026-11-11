"""
TestModel covers 'Model', a finite element model in OpenSees's terms
kept as plain values: nodes numbered in the order added, parts numbered
within their command, freedoms fixed and loads adding up at a node, and
the commands OpenSees takes to build it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worksees import Model

from . import WorkseesTest, cantilever


class TestModel(WorkseesTest):
  """Tests for 'Model'."""

  def test_shape(self) -> None:
    """It has 1, 2 or 3 dimensions and at least a freedom at a node."""
    model = Model(2, 3)
    self.assertEqual(model.dimensions, 2)
    self.assertEqual(model.freedoms, 3)
    with self.assertRaises(ValueError):
      Model(4, 3)
    with self.assertRaises(ValueError):
      Model(2, 0)

  def test_nodes_numbered(self) -> None:
    """Nodes are numbered from 1 in the order added, a coordinate to
    each dimension."""
    model = Model(2, 2)
    self.assertEqual(model.addNode(0.0, 0.0), 1)
    self.assertEqual(model.addNode(1, 2), 2)
    self.assertEqual(model.nodes, ((0.0, 0.0), (1.0, 2.0)))
    self.assertEqual(model.nodeCount, 2)
    with self.assertRaises(ValueError):
      model.addNode(1.0, 2.0, 3.0)

  def test_parts_numbered_by_command(self) -> None:
    """Parts are numbered from 1 within their command, the number put in
    after their kind."""
    model = Model(2, 2)
    for x in (0.0, 1.0, 2.0):
      model.addNode(x, 0.0)
    self.assertEqual(model.add('uniaxialMaterial', 'Elastic', 1e3), 1)
    self.assertEqual(model.add('uniaxialMaterial', 'Elastic', 2e3), 2)
    self.assertEqual(model.add('element', 'truss', 1, 2, 0.1, 2), 1)
    self.assertEqual(model.add('element', 'truss', 2, 3, 0.1, 1), 2)
    self.assertEqual(model.parts[1], ('uniaxialMaterial', 'Elastic', 2,
                                      2e3))
    self.assertEqual(model.parts[3], ('element', 'truss', 2, 2, 3, 0.1,
                                      1))
    self.assertEqual(model.elementCount, 2)

  def test_add_takes_numbered_parts_only(self) -> None:
    """Nodes, fixes and loads have their own methods; 'add' refuses
    them."""
    model = Model(2, 2)
    with self.assertRaises(ValueError):
      model.add('node', 1, 0.0, 0.0)

  def test_fixes_add_up(self) -> None:
    """Freedoms fixed at a node add to those fixed there already."""
    model = Model(2, 2)
    model.addNode(0.0, 0.0)
    model.fix(1, 1, 0)
    model.fix(1, 0, 1)
    self.assertEqual(model.fixed, ((1, (1, 1)),))
    with self.assertRaises(ValueError):
      model.fix(1, 2, 0)
    with self.assertRaises(ValueError):
      model.fix(1, 1)
    with self.assertRaises(ValueError):
      model.fix(2, 1, 1)

  def test_loads_add_up(self) -> None:
    """Forces at a node add to those on it already."""
    model = Model(2, 2)
    model.addNode(0.0, 0.0)
    model.addLoad(1, 1.0, 2.0)
    model.addLoad(1, 0.5, -2.0)
    self.assertEqual(model.loads, ((1, (1.5, 0.0)),))
    with self.assertRaises(ValueError):
      model.addLoad(1, 1.0)

  def test_fibers(self) -> None:
    """A fiber section added last is filled by patches, layers and
    fibers; nothing else is."""
    model = Model(2, 3)
    concrete = model.add('uniaxialMaterial', 'Elastic', 30000.0)
    with self.assertRaises(ValueError):
      model.addFibers('patch', 'rect', concrete, 10, 1, -1, -1, 1, 1)
    section = model.add('section', 'Fiber')
    model.addFibers('patch', 'rect', concrete, 10, 1, -1, -1, 1, 1)
    model.addFibers('layer', 'straight', concrete, 2, 0.1, -0.8, -0.8,
                    -0.8, 0.8)
    self.assertEqual(model.parts[1], ('section', 'Fiber', section))
    self.assertEqual(model.parts[2][:2], ('patch', 'rect'))
    self.assertEqual(model.parts[3][:2], ('layer', 'straight'))
    with self.assertRaises(ValueError):
      model.addFibers('node', 1)
    self.assertEqual(model.add('beamIntegration', 'Legendre', section, 2),
                     1)

  def test_couple(self) -> None:
    """Freedoms of one node are made to follow those of another, the
    couplings written out after the fixes."""
    model = Model(2, 3)
    model.addNode(0.0, 0.0)
    model.addNode(0.0, 1.0)
    model.fix(1, 1, 1, 1)
    model.couple(1, 2, 1, 2)
    self.assertEqual(model.coupled, ((1, 2, (1, 2)),))
    commands = model.commands()
    self.assertEqual(commands[4], ('equalDOF', 1, 2, 1, 2))
    with self.assertRaises(ValueError):
      model.couple(1, 1, 1)
    with self.assertRaises(ValueError):
      model.couple(1, 2, 4)
    with self.assertRaises(ValueError):
      model.couple(1, 3, 1)

  def test_commands(self) -> None:
    """It writes itself out as the calls OpenSees takes: the model, the
    nodes, the parts, the fixes and the loads under a pattern."""
    commands = cantilever().commands()
    self.assertEqual(commands[0], ('model', 'basic', '-ndm', 2, '-ndf', 3))
    self.assertEqual(commands[1], ('node', 1, 0.0, 0.0))
    self.assertEqual(commands[2], ('node', 2, 0.0, 3.0))
    self.assertEqual(commands[3], ('geomTransf', 'Linear', 1))
    self.assertEqual(commands[4][:3], ('element', 'elasticBeamColumn', 1))
    self.assertEqual(commands[5], ('fix', 1, 1, 1, 1))
    self.assertEqual(commands[6:8], (('timeSeries', 'Linear', 1),
                                     ('pattern', 'Plain', 1, 1)))
    self.assertEqual(commands[8], ('load', 2, 1000.0, 0.0, 0.0))
