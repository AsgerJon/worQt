"""
TestTrackDress covers the loop's stage drawn and stood on
('gui._trackdress', 'rail._stage.loopStage'; user, 2026-11-15: "a void
world, like in skyblock, where there is only enough terrain for the
loop de loop"): every quad of the track faces out (its corners' normals
agree with its own); the bed's grass faces the track's up, upside down
at the loop's top; the rails' heads lie level with the centre line, a
gauge apart; the dress is made once; the island lies 5 cm under the
bed, the walker standing on it, clear of the track.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy

from worQt.phys.gui._trackdress import BED_TOP, GAUGE, TrackDress
from worQt.phys.gui._trackdress import trackQuads
from worQt.phys.rail import Ribbon, bend, loopSpan, loopStage, loopTrack
from worQt.phys.rail import straight
from worQt.phys.rail import _stage

from . import PhysTest


class TestTrackDress(PhysTest):
  """Tests for the loop's stage drawn (seconds)."""

  def test_outward(self) -> None:
    """Every quad's own normal (its first triangle's) agrees with its
    corners' normals: none faces in."""
    quads = trackQuads(loopTrack())
    self.assertEqual(set(quads), {'rail', 'sleeper', 'grass', 'dirt'})
    for key, parts in quads.items():
      a, b, c = parts[:, 0, :3], parts[:, 1, :3], parts[:, 2, :3]
      own = numpy.cross(b - a, c - a)
      own /= numpy.linalg.norm(own, axis=1)[:, None]
      given = parts[:, 0, 3:]
      with self.subTest(key=key):
        self.assertGreater(float(numpy.einsum('ij,ij->i', own,
                                              given).min()), 0.9)

  def test_grass_up(self) -> None:
    """The bed's grass faces the track's up: at the loop's top, down in
    the world; on the platforms, up."""
    track = loopTrack()
    grass = trackQuads(track)['grass']
    begins, ends = loopSpan()
    middle = track.frameAt(0.5 * (begins + ends))[0]
    near = numpy.linalg.norm(grass[:, 0, :3] - middle, axis=1).argmin()
    self.assertLess(float(grass[near, 0, 5]), -0.99)
    start = numpy.linalg.norm(grass[:, 0, :3] - track.frameAt(5.0)[0],
                              axis=1).argmin()
    self.assertGreater(float(grass[start, 0, 5]), 0.99)

  def test_rails(self) -> None:
    """On a level straight the rails' heads' tops lie at the centre
    line's height, their middles a gauge apart; the bed's top under it
    by the rail and the sleeper."""
    ribbon = Ribbon((straight(10.0), bend(0.5, 20.0, (0.0, 1.0, 0.0))))
    rails = trackQuads(ribbon)['rail']
    tops = rails[(numpy.abs(rails[:, 0, 5] - 1.0) < 1e-9)
                 & (rails[:, 0, 2] > -0.1)]
    level = tops[tops[:, 0, 0] < 9.0]
    self.assertEqual(len(level), 2 * 36)
    self.assertLess(float(numpy.abs(level[:, :, 2]).max()), 1e-12)
    ys = sorted(set(numpy.round(level[:, :, 1].ravel(), 9)))
    middles = (0.5 * (ys[0] + ys[1]), 0.5 * (ys[2] + ys[3]))
    self.assertNear(middles[1] - middles[0], GAUGE, 1e-9)
    grass = trackQuads(ribbon)['grass']
    flat = grass[grass[:, 0, 0] < 9.0]
    self.assertNear(float(flat[:, :, 2].max()), BED_TOP, 1e-12)

  def test_once(self) -> None:
    """The dress makes its quads once: the same each frame."""
    dress = TrackDress(Ribbon((straight(3.0),)))
    self.assertIs(dress.quads(()), dress.quads(()))

  def test_island(self) -> None:
    """The island's top lies 5 cm under the bed's; the walker stands on
    it, beside the track; its grass and dirt (after the wheelset) are
    bodies of the world."""
    assembly, states = loopStage()
    shape = assembly.bodies[2].shape
    top = states[2].place[2] + max(point[2] for point in shape.points) - (
      assembly.bodies[2].centre[2])
    bed = _stage.DROP + BED_TOP
    self.assertNear(bed - top, 0.05, 1e-9)
    walker = states[0].place
    self.assertNear(walker[2] - assembly.bodies[0].shape.radius, top, 1e-9)
    self.assertGreater(abs(walker[1]), 2.0 + 0.5)
    self.assertEqual(set(assembly.fixed), {2, 3})
