"""
The 'worQt.document' package is a generic, relational single-file document
model: one 'Document' is one file. A
'Document' owns 'ValueField's (scalars: a bool, a title) and 'ArrayField's
(ordered collections of 'Member's). A 'Member' - a node, an element, a
paragraph - carries its own 'ValueField' attributes plus 'Reference' and
'ReferenceList' attributes that point at members of *other* array fields by
stable id. Editing anything climbs to the document, which tracks a dirty
flag and a revision and notifies subscribers; saving and loading are atomic
JSON, with references resolved in a second pass.

Nothing here is domain-specific: a FEM model (nodes + elements referencing
nodes), a word processor (paragraphs), or a config file all sit on top of
the same primitives.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._change import Change
from ._observable_list import ObservableList
from ._schema import Schema
from ._value_field import ValueField
from ._reference import Reference
from ._reference_list import ReferenceList
from ._array_field import ArrayField
from ._member import Member
from ._document import Document

__all__ = [
  'Change',
  'ObservableList',
  'Schema',
  'ValueField',
  'Reference',
  'ReferenceList',
  'ArrayField',
  'Member',
  'Document',
]
