"""
Result is what a 'Solver' found for a 'Model': how its nodes moved, what
held them, and what its elements answered.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable


class Result(BaseObject):
  """
  Result is what a 'Solver' found for a 'Model', in the model's units:
  the 'displacements' and the 'reactions', a tuple to each node, one
  value to each freedom, the first node's first; the 'queries' the
  elements were asked, and for each, their answers in 'response'; and
  what OpenSees 'said' meanwhile; and the 'loadFactor' the loads were
  applied by, 1 for a linear solve, and for a step pushed by a
  'Session' the factor holding the pushed node where it was pushed to.
  'displacement' and 'reaction' take a node by its number.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __result_nodes__: tuple[tuple, tuple] | None = None
  __result_answers__: dict[str, tuple] | None = None
  __result_said__: str = ''
  __result_factor__: float = 1.0

  #  Virtual Variables
  displacements: Field[tuple[tuple[float, ...], ...]] = Field()
  reactions: Field[tuple[tuple[float, ...], ...]] = Field()
  queries: Field[tuple[str | tuple, ...]] = Field()
  said: Field[str] = Field()
  loadFactor: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getNodes(self, ) -> tuple[tuple, tuple]:
    if self.__result_nodes__ is None:
      raise MissingVariable(self, '__result_nodes__', tuple)
    return self.__result_nodes__

  @displacements.GET
  def _getDisplacements(self, ) -> tuple[tuple[float, ...], ...]:
    """The 'displacements' getter returns how each node moved."""
    return self._getNodes()[0]

  @reactions.GET
  def _getReactions(self, ) -> tuple[tuple[float, ...], ...]:
    """The 'reactions' getter returns the force holding each node, nought
    where nothing is fixed."""
    return self._getNodes()[1]

  @queries.GET
  def _getQueries(self, ) -> tuple[str | tuple, ...]:
    """The 'queries' getter returns what the elements were asked."""
    return (*self.__result_answers__,)

  @loadFactor.GET
  def _getLoadFactor(self, ) -> float:
    """The 'loadFactor' getter returns the factor the loads were applied
    by."""
    return self.__result_factor__

  @said.GET
  def _getSaid(self, ) -> str:
    """The 'said' getter returns what OpenSees said while solving."""
    return self.__result_said__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(tuple, tuple, tuple, float, tuple, str)
  def __init__(self, displacements: tuple, reactions: tuple,
               responses: tuple, loadFactor: float, queries: tuple,
               said: str, ) -> None:
    if len(queries) != len(responses):
      raise ValueError('one response to each query')
    self.__result_nodes__ = (displacements, reactions)
    self.__result_answers__ = dict(zip(queries, responses))
    self.__result_factor__ = loadFactor
    self.__result_said__ = said

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def displacement(self, node: int) -> tuple[float, ...]:
    """The 'displacement' method returns how the node numbered 'node'
    moved."""
    return self.displacements[self._index(node)]

  def reaction(self, node: int) -> tuple[float, ...]:
    """The 'reaction' method returns the force holding the node numbered
    'node'."""
    return self.reactions[self._index(node)]

  def response(self, query: str | tuple) -> tuple[tuple[float, ...], ...]:
    """The 'response' method returns what each element answered to
    'query', the first element's first."""
    if query not in self.__result_answers__:
      infoSpec = """the elements were not asked %r, only %s"""
      asked = ', '.join("'%s'" % (name,) for name in self.queries)
      raise KeyError(infoSpec % (query, asked or 'nothing'))
    return self.__result_answers__[query]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _index(self, node: int) -> int:
    """The index of the node numbered 'node'."""
    if not 1 <= node <= len(self.displacements):
      infoSpec = """there is no node %r: the nodes are 1 to %d"""
      raise ValueError(infoSpec % (node, len(self.displacements)))
    return node - 1
