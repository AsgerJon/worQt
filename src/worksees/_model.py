"""
Model is a finite element model in the terms OpenSees builds one in,
kept as plain values until a 'Solver' hands it over.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

#  The commands of the parts OpenSees numbers by kind, the number put in
#  after the kind: element('quad', 1, ...), nDMaterial('Elastic...', 1, ...)
_NUMBERED = ('uniaxialMaterial', 'nDMaterial', 'section', 'geomTransf',
             'beamIntegration', 'element')
#  The commands filling the fiber section added last
_FIBERS = ('patch', 'layer', 'fiber')


class Model(BaseObject):
  """
  Model is a finite element model in the terms OpenSees builds one in,
  kept as plain values, in whatever consistent units its maker uses:
  'dimensions' of space and 'freedoms' at each node (OpenSees's 'ndm'
  and 'ndf'); the 'nodes', numbered from 1 in the order added; the
  'parts', the materials, sections, transforms, integrations and
  elements, each numbered from 1 within its command; the freedoms
  'fixed' at the nodes and those 'coupled' between them; and the
  'loads' on them, one load case applied in full. It
  never touches OpenSees: 'commands' writes it out as the calls OpenSees
  takes, and a 'Solver' makes them.

  'addNode' adds a node at its coordinates and returns its number. 'add'
  adds a part, its number put in after its kind as OpenSees has it, and
  returns that number:
  'add('nDMaterial', 'ElasticIsotropic', E, nu)' and
  'add('element', 'quad', 1, 2, 3, 4, t, 'PlaneStress', material)'.
  'fix' fixes freedoms of a node, 1 fixed and 0 free, adding to those
  fixed there already; 'couple' makes freedoms of one node follow those
  of another, as a pin or a roller between two parts does; 'addLoad'
  adds forces at a node to those on it. 'addFibers' fills the fiber
  section added last: 'addFibers('patch', 'rect', concrete, 20, 1, -h /
  2, -b / 2, h / 2, b / 2)' and 'addFibers('layer', 'straight', steel,
  3, area, y, -z, y, z)'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __model_shape__: tuple[int, int] | None = None
  __model_nodes__: list[tuple[float, ...]] | None = None
  __model_parts__: list[tuple] | None = None
  __model_counts__: dict[str, int] | None = None
  __model_fixed__: dict[int, tuple[int, ...]] | None = None
  __model_loads__: dict[int, tuple[float, ...]] | None = None
  __model_couplings__: list[tuple[int, int, tuple[int, ...]]] | None = None

  #  Virtual Variables
  dimensions: Field[int] = Field()
  freedoms: Field[int] = Field()
  nodes: Field[tuple[tuple[float, ...], ...]] = Field()
  parts: Field[tuple[tuple, ...]] = Field()
  fixed: Field[tuple[tuple[int, tuple[int, ...]], ...]] = Field()
  loads: Field[tuple[tuple[int, tuple[float, ...]], ...]] = Field()
  coupled: Field[tuple[tuple[int, int, tuple[int, ...]], ...]] = Field()
  nodeCount: Field[int] = Field()
  elementCount: Field[int] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getShape(self, ) -> tuple[int, int]:
    if self.__model_shape__ is None:
      raise MissingVariable(self, '__model_shape__', tuple)
    return self.__model_shape__

  @dimensions.GET
  def _getDimensions(self, ) -> int:
    """The 'dimensions' getter returns the dimensions of space, 'ndm'."""
    return self._getShape()[0]

  @freedoms.GET
  def _getFreedoms(self, ) -> int:
    """The 'freedoms' getter returns the freedoms at each node, 'ndf'."""
    return self._getShape()[1]

  @nodes.GET
  def _getNodes(self, ) -> tuple[tuple[float, ...], ...]:
    """The 'nodes' getter returns the coordinates of the nodes, the
    first node's first."""
    return (*self.__model_nodes__,)

  @parts.GET
  def _getParts(self, ) -> tuple[tuple, ...]:
    """The 'parts' getter returns the parts as the commands making them,
    in the order added."""
    return (*self.__model_parts__,)

  @fixed.GET
  def _getFixed(self, ) -> tuple[tuple[int, tuple[int, ...]], ...]:
    """The 'fixed' getter returns each node fixed with its freedoms, 1
    fixed and 0 free, by node."""
    return (*sorted(self.__model_fixed__.items()),)

  @loads.GET
  def _getLoads(self, ) -> tuple[tuple[int, tuple[float, ...]], ...]:
    """The 'loads' getter returns each node loaded with its forces, by
    node."""
    return (*sorted(self.__model_loads__.items()),)

  @coupled.GET
  def _getCoupled(self, ) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    """The 'coupled' getter returns each coupling: the node followed,
    the node following and the freedoms, counted from 1, in the order
    added."""
    return (*self.__model_couplings__,)

  @nodeCount.GET
  def _getNodeCount(self, ) -> int:
    """The 'nodeCount' getter returns how many nodes there are."""
    return len(self.__model_nodes__)

  @elementCount.GET
  def _getElementCount(self, ) -> int:
    """The 'elementCount' getter returns how many elements there are."""
    return self.__model_counts__.get('element', 0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d, %d): %d nodes, %d elements"""
    return infoSpec % (type(self).__name__, self.dimensions, self.freedoms,
                       self.nodeCount, self.elementCount)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, dimensions: int, freedoms: int) -> None:
    if dimensions not in (1, 2, 3):
      raise ValueError('a model has 1, 2 or 3 dimensions, not %d'
                       % dimensions)
    if freedoms < 1:
      raise ValueError('a node has at least 1 freedom, not %d' % freedoms)
    self.__model_shape__ = (dimensions, freedoms)
    self.__model_nodes__ = []
    self.__model_parts__ = []
    self.__model_counts__ = {}
    self.__model_fixed__ = {}
    self.__model_loads__ = {}
    self.__model_couplings__ = []

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addNode(self, *coordinates: float) -> int:
    """The 'addNode' method adds a node at its 'coordinates', one to each
    dimension, and returns its number."""
    if len(coordinates) != self.dimensions:
      infoSpec = """a node takes %d coordinates, not %d"""
      raise ValueError(infoSpec % (self.dimensions, len(coordinates)))
    self.__model_nodes__.append((*map(float, coordinates),))
    return self.nodeCount

  def add(self, command: str, kind: str, *args) -> int:
    """The 'add' method adds a part of 'kind' by the OpenSees 'command'
    making it, its number put in after its kind, and returns that
    number, counted within its command."""
    if command not in _NUMBERED:
      infoSpec = """'add' adds parts by %s, not by '%s'"""
      raise ValueError(infoSpec % (', '.join(_NUMBERED), command))
    number = self.__model_counts__.get(command, 0) + 1
    self.__model_counts__[command] = number
    self.__model_parts__.append((command, kind, number, *args))
    return number

  def addFibers(self, command: str, *args) -> None:
    """The 'addFibers' method fills the fiber section added last with a
    'patch', a 'layer' or a 'fiber' of the material numbered in
    'args'."""
    if command not in _FIBERS:
      infoSpec = """a fiber section is filled by %s, not by '%s'"""
      raise ValueError(infoSpec % (', '.join(_FIBERS), command))
    last = self.__model_parts__[-1] if self.__model_parts__ else ('',)
    if last[:2] != ('section', 'Fiber') and last[0] not in _FIBERS:
      raise ValueError('fibers fill a fiber section, added last')
    self.__model_parts__.append((command, *args))

  def couple(self, followed: int, following: int, *freedoms: int) -> None:
    """The 'couple' method makes the 'freedoms' of the node 'following',
    counted from 1, follow those of the node 'followed'."""
    self._checkNode(followed)
    self._checkNode(following)
    if followed == following:
      raise ValueError('a node cannot follow itself')
    if not freedoms or any(not 1 <= f <= self.freedoms for f in freedoms):
      infoSpec = """the freedoms coupled are among 1 to %d, not %r"""
      raise ValueError(infoSpec % (self.freedoms, freedoms))
    self.__model_couplings__.append((followed, following, (*freedoms,)))

  def fix(self, node: int, *flags: int) -> None:
    """The 'fix' method fixes freedoms of 'node', one flag to each, 1
    fixed and 0 free, adding to those fixed there already."""
    self._checkNode(node)
    self._checkCount('flags', flags)
    for flag in flags:
      if flag not in (0, 1):
        raise ValueError('a freedom is fixed, 1, or free, 0, not %r' % flag)
    had = self.__model_fixed__.get(node, (0,) * self.freedoms)
    self.__model_fixed__[node] = (*map(max, had, flags),)

  def addLoad(self, node: int, *forces: float) -> None:
    """The 'addLoad' method adds 'forces' at 'node', one to each
    freedom, to those on it already."""
    self._checkNode(node)
    self._checkCount('forces', forces)
    had = self.__model_loads__.get(node, (0.0,) * self.freedoms)
    summed = [a + float(b) for a, b in zip(had, forces)]
    self.__model_loads__[node] = (*summed,)

  def commands(self, ) -> tuple[tuple, ...]:
    """The 'commands' method writes the model out as the calls OpenSees
    takes to build it, each a command and its arguments: the model, its
    nodes, its parts, what is fixed, and its loads under a pattern of
    its own."""
    lines = [('model', 'basic', '-ndm', self.dimensions,
              '-ndf', self.freedoms)]
    lines += [('node', number, *coordinates)
              for number, coordinates in enumerate(self.nodes, 1)]
    lines += self.parts
    lines += [('fix', node, *flags) for node, flags in self.fixed]
    lines += [('equalDOF', followed, following, *freedoms)
              for followed, following, freedoms in self.coupled]
    lines += [('timeSeries', 'Linear', 1), ('pattern', 'Plain', 1, 1)]
    lines += [('load', node, *forces) for node, forces in self.loads]
    return (*lines,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _checkNode(self, node: int) -> None:
    """Raises unless 'node' is the number of a node."""
    if not 1 <= node <= self.nodeCount:
      infoSpec = """there is no node %r: the nodes are 1 to %d"""
      raise ValueError(infoSpec % (node, self.nodeCount))

  def _checkCount(self, name: str, values: tuple) -> None:
    """Raises unless 'values' has one to each freedom."""
    if len(values) != self.freedoms:
      infoSpec = """a node takes %d %s, not %d"""
      raise ValueError(infoSpec % (self.freedoms, name, len(values)))
