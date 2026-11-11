"""
The 'worQt.gaming.pusher' package is a two-level coin pusher
('skubbe-maskinen'), honest and in 3D: coins dropped down a chute onto
the moving shelf, pushed off it onto the table and off the table into
the tray, back to the player; solid side walls, nothing kept. The coins
are rigid 20-krone coins, stacking, sliding, rolling and tipping, played
by a solver of our own compiled by Warp. It needs no Qt;
'worQt.gaming.pusher.gui' plays it.

- Coin: a coin's shape and weight, the 20-krone coin by default.
- CoinWorld: coins among the boxes and edges of a cabinet, a frame at a
  time. Box, Edge: those parts.
- Cabinet: the machine's shape, how its pusher moves, its parts.
- Machine: the machine running and the player's purse; PURSE, MACHINE,
  TRAY and AWAY say where a coin is.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._coin import Coin
from ._coin_world import Box, Edge, CoinWorld
from ._cabinet import Cabinet
from ._machine import Machine, PURSE, MACHINE, TRAY, AWAY

__all__ = (
  'Coin',
  'Box',
  'Edge',
  'CoinWorld',
  'Cabinet',
  'Machine',
  'PURSE',
  'MACHINE',
  'TRAY',
  'AWAY',
)
