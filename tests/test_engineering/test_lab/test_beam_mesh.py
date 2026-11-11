"""
TestBeamMesh covers 'BeamMesh', the beam on its rig as a solid of
bricks with its bars and stirrups steel through them: its lines meet the
supports, the actuators and their plates, the rows of bars and the bars
across, at most 50 mm along, 60 mm up and 65 mm across; every brick has
its own tensile strength, scattered, but those bearing on a support or
under a plate, elastic; the stirrups stand on the lines nearest them,
none in the gaps; the model holds the whole beam, nothing symmetric
about it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.lab import BeamMesh, Rig, Stirrups

from . import LabTest, standardBeam


class TestBeamMesh(LabTest):
  """Tests for 'BeamMesh'."""

  def mesh(self, stirrups: Stirrups = None) -> BeamMesh:
    """The standard beam on its standard rig, meshed."""
    beam = standardBeam()
    if stirrups is not None:
      beam = beam.withStirrups(stirrups)
    return BeamMesh(beam, Rig.standard(beam), 1)

  def test_lines(self) -> None:
    """The lines meet the ends, the supports, the actuators and their
    plates' ends, the rows of bars and the bars across, no more than
    the most apart."""
    mesh = self.mesh()
    for x in (0.0, 150.0, 1100.0, 1150.0, 1200.0, 2150.0, 3150.0,
              3300.0):
      self.assertTrue(any(abs(line - x) < 1e-9 for line in mesh.xs))
    for y in (0.0, 38.0, 265.0, 300.0):
      self.assertTrue(any(abs(line - y) < 1e-9 for line in mesh.ys))
    for z in (0.0, 38.0, 100.0, 162.0, 200.0):
      self.assertTrue(any(abs(line - z) < 1e-9 for line in mesh.zs))
    for lines, most in ((mesh.xs, 50.0), (mesh.ys, 60.0),
                        (mesh.zs, 65.0)):
      for low, high in zip(lines, lines[1:]):
        self.assertLessEqual(high - low, most + 1e-9)
        self.assertGreater(high - low, 0.0)

  def test_bricks(self) -> None:
    """The whole beam is bricks, each of its own tensile strength,
    within 5 % of fctm."""
    mesh = self.mesh()
    counts = [len(lines) - 1 for lines in (mesh.xs, mesh.ys, mesh.zs)]
    self.assertEqual(mesh.brickCount, counts[0] * counts[1] * counts[2])
    self.assertEqual(len(mesh.strengths), mesh.brickCount)
    fctm = standardBeam().fctm
    for strength in mesh.strengths:
      self.assertLessEqual(abs(strength - fctm), 0.05 * fctm)
    self.assertGreater(len(set(mesh.strengths)), 1)

  def test_stirrups(self) -> None:
    """The stirrups stand on the lines nearest them, within a third of a
    brick, and none in a gap."""
    mesh = self.mesh()
    places = standardBeam().stirrups.places(3300.0)
    self.assertEqual(len(mesh.stirrupPlaces), len(places))
    for stood, place in zip(mesh.stirrupPlaces, places):
      self.assertLessEqual(abs(stood - place), 0.3 * 50.0 + 1e-9)
    gapped = self.mesh(Stirrups(8.0, 150.0, ((200.0, 1100.0),)))
    for x in gapped.stirrupPlaces:
      self.assertFalse(200.0 < x < 1100.0)
    self.assertEqual(self.mesh(Stirrups(0.0, 150.0, ())).stirrupPlaces,
                     ())

  def test_bearing(self) -> None:
    """The bricks bearing on a support and under an actuator's plate are
    elastic; the rest crack."""
    mesh = self.mesh()
    xs, top = mesh.xs, len(mesh.ys) - 2
    support = xs.index(150.0)
    self.assertTrue(mesh.bearing(support - 1, 0))
    self.assertTrue(mesh.bearing(support, 0))
    self.assertFalse(mesh.bearing(support + 1, 0))
    self.assertFalse(mesh.bearing(support, 1))
    self.assertTrue(mesh.bearing(xs.index(1100.0), top))
    self.assertFalse(mesh.bearing(xs.index(1200.0), top))
    model = mesh.model()
    kinds = [part[1] for part in model.parts if part[0] == 'nDMaterial']
    self.assertEqual(len(kinds), mesh.brickCount)
    self.assertIn('ElasticIsotropic', kinds)
    elements = [part[1] for part in model.parts if part[0] == 'element']
    self.assertEqual(elements.count('stdBrick'), mesh.brickCount)

  def test_model(self) -> None:
    """The model has a node to each crossing of the lines and a brick to
    each cell; the driven actuator pushes the middle of its plate on the
    top; the supports' lines are held up across the beam, the pin's
    along too; nothing is held by symmetry."""
    mesh = self.mesh()
    model = mesh.model()
    nodes = len(mesh.xs) * len(mesh.ys) * len(mesh.zs)
    self.assertEqual(model.nodeCount, nodes)
    x, y, z = model.nodes[mesh.driven - 1]
    self.assertEqual((x, y), (1150.0, 300.0))
    self.assertEqual(z, mesh.zs[mesh.middle()])
    fixed = dict(model.fixed)
    held = [node for node, flags in fixed.items() if flags[1]]
    self.assertEqual(len(held), 2 * len(mesh.zs))
    along = [node for node, flags in fixed.items() if flags[0]]
    self.assertEqual(len(along), len(mesh.zs))
    sideways = [node for node, flags in fixed.items() if flags[2]]
    self.assertEqual(len(sideways), 1)
    loads = dict(model.loads)
    total = sum(forces[1] for forces in loads.values())
    self.assertAlmostEqual(total, -2.0)
