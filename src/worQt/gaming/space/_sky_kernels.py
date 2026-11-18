"""
The Warp kernel 'skyFlown' flies the heavy bodies (user, 2026-11-18:
real gravity, "Only between heavy objects like Terra and the moons";
"PHYSICS MUST BE REAL"): Sol, the planets and the moons, each pulling
every other, one thread for them all (they must move together), a
launch a run of steps of 'SPAN' s, each step's states written out (the
sky's table: '_ephemeris').

Each body is kept from the body it goes round (its parent: Sol is the
origin and moves with nothing, its pull on the others' parents taken
off as theirs on it is). Each step is Wisdom and Holman's, as the
flight's: half a step coasting on the pull between the body and its
parent alone, exactly (Kepler's arc of the two, their G M summed:
'_flight_kernels.drifted'), a kick of every other body's pull on it
less that body's pull on its parent (so Terra feels Luna, and Luna
feels Sol's pull on her less Sol's on Terra), half a step coasting
again. Where one body is from another is summed along the tree from
their nearest common forebear, so Luna's place from Terra is never
taken from Sol and back.

float32 ('feedback: GPU always'), each place and velocity two float32s
(a big part and the small rest, 'pairAdded'): a step's few km on
Terra's 150 million are kept.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import warp as wp

from ._flight_kernels import drifted, pairAdded

wp.config.log_level = wp.LOG_WARNING
wp.set_module_options({'enable_backward': False})

#  A body's four rows in 'states' and in each of the table's rows: its
#  place's big part and rest, its velocity's big part and rest.
PLACE_HI = wp.constant(0)
PLACE_LO = wp.constant(1)
SPEED_HI = wp.constant(2)
SPEED_LO = wp.constant(3)
ROWS = 4


@wp.func
def treeApart(parents: wp.array(dtype=wp.int32),
              depths: wp.array(dtype=wp.int32),
              places: wp.array(dtype=wp.vec3), a: int, b: int) -> wp.vec3:
  """Returns where body 'a' is from body 'b', summed along the tree from
  their nearest common forebear ('places': each body's from its
  parent)."""
  out = wp.vec3(0.0, 0.0, 0.0)
  x = a
  y = b
  while depths[x] > depths[y]:
    out = out + places[x]
    x = parents[x]
  while depths[y] > depths[x]:
    out = out - places[y]
    y = parents[y]
  while x != y:
    out = out + places[x] - places[y]
    x = parents[x]
    y = parents[y]
  return out


@wp.func
def pullOf(mu: float, apart: wp.vec3) -> wp.vec3:
  """Returns the pull toward a body of G M 'mu' 'apart' m away, m/s²."""
  r2 = wp.dot(apart, apart)
  return apart * (mu / (r2 * wp.sqrt(r2)))


@wp.func
def coasted(states: wp.array(dtype=wp.vec3),
            parents: wp.array(dtype=wp.int32),
            mus: wp.array(dtype=wp.float32), count: int,
            dt: float) -> int:
  """Coasts every body but Sol 'dt' s on its pull with its parent alone
  (their G M summed); returns nought."""
  for k in range(1, count):
    row = k * ROWS
    hi = states[row + PLACE_HI]
    lo = states[row + PLACE_LO]
    vhi = states[row + SPEED_HI]
    vlo = states[row + SPEED_LO]
    arc = drifted(hi + lo, vhi + vlo, mus[parents[k]] + mus[k], dt)
    pair = pairAdded(hi, lo, arc[0])
    states[row + PLACE_HI] = pair[0]
    states[row + PLACE_LO] = pair[1]
    pair = pairAdded(vhi, vlo, arc[1])
    states[row + SPEED_HI] = pair[0]
    states[row + SPEED_LO] = pair[1]
  return 0


@wp.kernel
def skyFlown(states: wp.array(dtype=wp.vec3),
             parents: wp.array(dtype=wp.int32),
             depths: wp.array(dtype=wp.int32),
             mus: wp.array(dtype=wp.float32),
             places: wp.array(dtype=wp.vec3),
             kicks: wp.array(dtype=wp.vec3),
             table: wp.array(dtype=wp.vec3), steps: int, dt: float):
  """Flies the bodies 'steps' steps of 'dt' s on from 'states' (each
  body's 'ROWS' rows, from its parent; Sol's nought), writing each
  step's states to its row of 'table' ('ROWS' rows a body); 'places'
  and 'kicks' are scratch, a row a body."""
  count = parents.shape[0]
  for s in range(steps):
    coasted(states, parents, mus, count, 0.5 * dt)
    for k in range(count):
      places[k] = states[k * ROWS + PLACE_HI] + states[k * ROWS + PLACE_LO]
    for b in range(1, count):
      parent = parents[b]
      kick = wp.vec3(0.0, 0.0, 0.0)
      for k in range(count):
        if k != b and k != parent:
          onBody = pullOf(mus[k], treeApart(parents, depths, places, k, b))
          onParent = pullOf(mus[k], treeApart(parents, depths, places, k,
                                              parent))
          kick = kick + onBody - onParent
      kicks[b] = kick
    for b in range(1, count):
      row = b * ROWS
      pair = pairAdded(states[row + SPEED_HI], states[row + SPEED_LO],
                       kicks[b] * dt)
      states[row + SPEED_HI] = pair[0]
      states[row + SPEED_LO] = pair[1]
    coasted(states, parents, mus, count, 0.5 * dt)
    for k in range(count * ROWS):
      table[s * count * ROWS + k] = states[k]
