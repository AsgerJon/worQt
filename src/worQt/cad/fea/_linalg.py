"""
A tiny, dependency-free linear-algebra helper for the FEA solver: a dense
matrix-vector product and Gaussian elimination with partial pivoting. No
numpy, so the 'fea' core stays pure Python like the rest of the model, and
the systems a hand-built truss produces are small enough that it is fine.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass

__pivot_eps__ = 1e-12  # a pivot below this counts as singular


def matVec(matrix: list, vector: list) -> list:
  """The product 'matrix' * 'vector' as a new list."""
  out = []
  for row in matrix:
    out.append(sum(row[j] * vector[j] for j in range(len(vector))))
  return out


def solveLinear(matrix: list, vector: list) -> list:
  """
  Solve 'matrix' * x = 'vector' and return x, by Gaussian elimination with
  partial pivoting. 'matrix' must be square. A near-zero pivot raises
  'ValueError' - for a truss that means an unconstrained or mechanism-like
  system with no unique solution.
  """
  size = len(vector)
  if not size:
    return []
  rows = [list(matrix[i]) + [vector[i]] for i in range(size)]  # augmented
  for col in range(size):
    pivot = col
    for candidate in range(col + 1, size):
      if abs(rows[candidate][col]) > abs(rows[pivot][col]):
        pivot = candidate
    if abs(rows[pivot][col]) < __pivot_eps__:
      info = 'singular system: the structure is a mechanism or unconstrained'
      raise ValueError(info)
    rows[col], rows[pivot] = rows[pivot], rows[col]
    for target in range(col + 1, size):
      factor = rows[target][col] / rows[col][col]
      if factor:
        for cursor in range(col, size + 1):
          rows[target][cursor] -= factor * rows[col][cursor]
  solution = [0.0] * size
  for row in range(size - 1, -1, -1):
    total = rows[row][size]
    for cursor in range(row + 1, size):
      total -= rows[row][cursor] * solution[cursor]
    solution[row] = total / rows[row][row]
  return solution
