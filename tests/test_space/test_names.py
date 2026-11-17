"""
TestNames covers the space package's names: no class defines a method
twice and no module a function twice (the second hides the first
without a word: the window's '_seen' for the Grav-Gun's sight was so
hidden by its '_seen' for the eye, and the gun raised every frame it was
held up).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import ast
from pathlib import Path

import worQt.gaming.space as space

from . import SpaceTest


class TestNames(SpaceTest):
  """Tests for the space package's names."""

  def test_once(self) -> None:
    """Every method of a class and every function of a module is
    defined once (a property's setter aside)."""
    twice = []
    for path in sorted(Path(space.__file__).parent.glob('*.py')):
      tree = ast.parse(path.read_text(encoding='utf-8'))
      bodies = [('', tree.body)] + [
        (node.name + '.', node.body) for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)]
      for owner, body in bodies:
        names = set()
        for item in body:
          if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
          if any(isinstance(d, ast.Attribute) and d.attr in (
              'setter', 'deleter') for d in item.decorator_list):
            continue
          if item.name in names:
            twice.append('%s:%d %s%s' % (path.name, item.lineno, owner,
                                         item.name))
          names.add(item.name)
    self.assertEqual(twice, [])
