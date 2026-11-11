"""
UniaxialTest is a cylinder's lattice loaded between its platens, step by
step, as a testing machine loads it; CompressionTest crushes it and
TensionTest pulls it apart.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._lattice_base import LatticeBase
from ._phase_num import PhaseNum

_PLATEN = PhaseNum.PLATEN.index


class UniaxialTest(BaseObject):
  """
  UniaxialTest is a cylinder's lattice loaded between its platens, step
  by step, as a testing machine loads it: the bottom platen held, the
  top one moved at a steady rate, shortening the cylinder in a
  'CompressionTest' and lengthening it in a 'TensionTest'. Each cell
  moves as Newton says under the forces of its springs, slowly enough
  that it stays all but in equilibrium; each cell's mass is made just
  enough that a step is stable, and its movement damped against the way
  it goes, as Cundall damps such models. The stress is the mean of the
  forces on the two platens over the width, the strain the platen's
  movement over the height.

  A spring is elastic until its material's strength. Then a crack opens:
  across the face the stress falls as the crack widens, to nought at the
  width that spends the material's fracture energy; a crack that closes
  again bears as before. Along the face the spring holds by cohesion and
  friction, the cohesion lost as the crack opens and as the face slides,
  over the slip that spends its shear fracture energy. The platens never
  let go. Nothing in it is concrete: the stones, the mortar and the bond
  are.

  'advance' takes steps, 'run' takes them to the end: once the stress has
  fallen, cracked, to a third of the 'strength', or the strain reached
  its limit. The 'curve' is the strain and stress every fifty steps; the
  'strength' is the greatest stress, reached at 'strengthStrain' with
  'strengthCracks' faces cracked. 'openings' are how wide each face's
  crack is now, 'slips' how far each has slid, and 'crackSizes' the
  more of the two, in mm.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_direction__ = -1.0  # the way the top platen moves
  __fallback_crossing_strain__ = 2.0e-5  # strain while a wave crosses
  __fallback_start_crossings__ = 4.0  # crossings to get up to speed
  __fallback_strain_limit__ = 5.0e-3
  __fallback_record_steps__ = 50
  __fallback_mass_factor__ = 3.2  # times the least stable mass
  __fallback_damping__ = 0.7
  __fallback_ending_share__ = 0.3  # of the strength: where a test ends
  __fallback_platen_hold__ = 1.0e9  # MPa and N/mm: platens never let go
  __fallback_run_steps__ = 1000  # steps 'run' takes between its checks

  #  Private Variables
  __test_lattice__: LatticeBase | None = None
  __test_materials__: tuple | None = None
  __test_device__: str = 'cpu'
  __test_state__: dict | None = None
  __test_curve__: list | None = None
  __test_step__: int = 0
  __test_strength__: tuple[float, float, int] = (0.0, 0.0, 0)
  __test_finished__: bool = False

  #  Virtual Variables
  lattice: Field[LatticeBase] = Field()
  materials: Field[tuple] = Field()
  device: Field[str] = Field()
  direction: Field[float] = Field()
  rate: Field[float] = Field()
  step: Field[int] = Field()
  strain: Field[float] = Field()
  stress: Field[float] = Field()
  curve: Field[tuple[tuple[float, float], ...]] = Field()
  strength: Field[float] = Field()
  strengthStrain: Field[float] = Field()
  strengthCracks: Field[int] = Field()
  stiffness: Field[float] = Field()
  finished: Field[bool] = Field()
  crackedCount: Field[int] = Field()
  openings: Field[torch.Tensor] = Field()
  slips: Field[torch.Tensor] = Field()
  crackSizes: Field[torch.Tensor] = Field()
  displacements: Field[torch.Tensor] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @lattice.GET
  def _getLattice(self, ) -> LatticeBase:
    """The 'lattice' getter returns the lattice tested."""
    if self.__test_lattice__ is None:
      raise MissingVariable(self, '__test_lattice__', LatticeBase)
    return self.__test_lattice__

  @materials.GET
  def _getMaterials(self, ) -> tuple:
    """The 'materials' getter returns the stone's, the mortar's and the
    bond's materials, as the test has them."""
    if self.__test_materials__ is None:
      raise MissingVariable(self, '__test_materials__', tuple)
    return self.__test_materials__

  @device.GET
  def _getDevice(self, ) -> str:
    """The 'device' getter returns where the test is reckoned: 'cpu' on
    the processor, 'cuda' on a graphics card."""
    return self.__test_device__

  @direction.GET
  def _getDirection(self, ) -> float:
    """The 'direction' getter returns the way the top platen moves: down
    to crush, up to pull apart."""
    return self.__fallback_direction__

  @rate.GET
  def _getRate(self, ) -> float:
    """The 'rate' getter returns the strain each step adds: the crossing
    strain over the steps a wave takes to cross the cylinder, about one
    a spacing."""
    lattice = self.lattice
    crossing = self.__fallback_crossing_strain__
    return crossing * lattice.spacing / lattice.height

  @step.GET
  def _getStep(self, ) -> int:
    """The 'step' getter returns how many steps have been taken."""
    return self.__test_step__

  @strain.GET
  def _getStrain(self, ) -> float:
    """The 'strain' getter returns the strain now, lengthening
    positive: the platen gets up to speed over its first few crossings,
    as a machine starts, so it sends no shock through the cylinder, and
    then moves steadily."""
    rate, ramp = self.rate, self._rampSteps()
    step = self.step
    if step < ramp:
      return self.direction * rate * step * step / (2 * ramp)
    return self.direction * rate * (step - ramp / 2)

  @stress.GET
  def _getStress(self, ) -> float:
    """The 'stress' getter returns the stress last recorded, in MPa,
    tension positive."""
    if self.__test_curve__:
      return self.__test_curve__[-1][1]
    return 0.0

  @curve.GET
  def _getCurve(self, ) -> tuple[tuple[float, float], ...]:
    """The 'curve' getter returns the strain and the stress recorded every
    fifty steps."""
    return (*(self.__test_curve__ or ()),)

  @strength.GET
  def _getStrength(self, ) -> float:
    """The 'strength' getter returns the greatest stress so far, in MPa,
    as a positive number."""
    return self.__test_strength__[0]

  @strengthStrain.GET
  def _getStrengthStrain(self, ) -> float:
    """The 'strengthStrain' getter returns the strain, as a positive
    number, the strength was reached at."""
    return self.__test_strength__[1]

  @strengthCracks.GET
  def _getStrengthCracks(self, ) -> int:
    """The 'strengthCracks' getter returns how many faces had cracked
    when the strength was reached."""
    return self.__test_strength__[2]

  @stiffness.GET
  def _getStiffness(self, ) -> float:
    """The 'stiffness' getter returns the stiffness before cracking, in
    MPa: the stress over the strain where the stress first reached three
    tenths of the strength; nought before there is any."""
    least = 0.3 * self.strength
    for strain, stress in self.curve:
      if least > 0 and abs(stress) >= least and strain:
        return stress / strain
    return 0.0

  @finished.GET
  def _getFinished(self, ) -> bool:
    """The 'finished' getter tells whether the test has reached its
    end."""
    return self.__test_finished__

  @crackedCount.GET
  def _getCrackedCount(self, ) -> int:
    """The 'crackedCount' getter returns how many faces have cracked:
    opened past their strength."""
    state = self._state()
    cracked = (state['reach'] > state['opening']) & state['inner']
    return int(cracked.sum())

  @openings.GET
  def _getOpenings(self, ) -> torch.Tensor:
    """The 'openings' getter returns how wide each face's crack is now,
    in mm; nought for a face uncracked or closed."""
    return self._state()['widths'].to('cpu', torch.float64)

  @slips.GET
  def _getSlips(self, ) -> torch.Tensor:
    """The 'slips' getter returns how far each face has slid along
    itself, all told, in mm."""
    return self._state()['worn'].to('cpu', torch.float64)

  @crackSizes.GET
  def _getCrackSizes(self, ) -> torch.Tensor:
    """The 'crackSizes' getter returns how far each face has given, in
    mm: its crack's opening now, or how far it has slid, whichever is
    the more. A crushed face slides more than it opens: the inclined
    cracks."""
    return torch.maximum(self.openings, self.slips)

  @displacements.GET
  def _getDisplacements(self, ) -> torch.Tensor:
    """The 'displacements' getter returns the movements of the cells and
    the platens now, three to each."""
    return self._state()['moves'].to('cpu', torch.float64)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(LatticeBase, tuple, str)
  def __init__(self, lattice: LatticeBase, materials: tuple,
               device: str, ) -> None:
    if len(materials) != 3:
      raise ValueError('a test needs the stone, the mortar and the bond')
    self.__test_lattice__ = lattice
    self.__test_materials__ = (*materials,)
    self.__test_device__ = device
    self.__test_curve__ = []
    self.__test_state__ = self._prepare()

  @overload(LatticeBase, tuple)
  def __init__(self, lattice: LatticeBase, materials: tuple) -> None:
    self.__init__(lattice, materials, 'cpu')

  @overload(LatticeBase)
  def __init__(self, lattice: LatticeBase) -> None:
    materials = (lattice.stoneMaterial, lattice.mortarMaterial,
                 lattice.bondMaterial)
    self.__init__(lattice, materials, 'cpu')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def advance(self, steps: int) -> None:
    """The 'advance' method takes up to 'steps' steps, fewer if the test
    reaches its end."""
    every = self.__fallback_record_steps__
    for _ in range(steps):
      if self.__test_finished__:
        return
      self._takeStep()
      if self.__test_step__ % every == 0:
        self._record()

  def run(self, ) -> None:
    """The 'run' method takes steps until the test reaches its end."""
    while not self.__test_finished__:
      self.advance(self.__fallback_run_steps__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _state(self, ) -> dict:
    """The tensors the test steps."""
    if self.__test_state__ is None:
      raise MissingVariable(self, '__test_state__', dict)
    return self.__test_state__

  def _rampSteps(self, ) -> float:
    """The steps the platen takes to get up to speed: its first few
    crossings, a crossing about a step to each spacing."""
    lattice = self.lattice
    crossings = self.__fallback_start_crossings__
    return crossings * lattice.height / lattice.spacing

  def _materials(self, ) -> torch.Tensor:
    """Each spring's material as a row: E, ft, Gf, c, mu and GII."""
    stone, mortar, bond = self.materials
    hold = self.__fallback_platen_hold__
    table = torch.tensor([
        [*stone], [*mortar], [*bond], [0.0, hold, hold, hold, 0.0, hold],
    ]).double()
    return table[self.lattice.phases]

  def _prepare(self, ) -> dict:
    """The springs' constants, the masses, and the cells at rest, on the
    device the test runs on: in double precision on the processor, in
    single on a graphics card."""
    lattice = self.lattice
    stone, mortar, _ = self.materials
    rows = self._materials()
    tension, toughness = rows[:, 1], rows[:, 2]
    cohesion, shearToughness = rows[:, 3], rows[:, 5]
    moduli = lattice.moduliOf(stone, mortar)
    stiff = moduli / lattice.distances
    areas = lattice.faceAreas
    count = lattice.bodyMoves * (lattice.nodeCount + 2)
    springs = len(stiff)
    zeros = torch.zeros(springs).double()
    shear = lattice.shearRows
    floats = {
        'stiff': stiff, 'tension': tension, 'friction': rows[:, 4],
        'cohesion': cohesion, 'opening': tension / stiff,
        'width': 2 * toughness / tension,
        'slipWidth': 2 * shearToughness / cohesion,
        'areas': areas, 'normal': lattice.normalRows, 'shear': shear,
        'mass': self._masses(moduli * areas / lattice.distances),
        'moves': torch.zeros(count).double(),
        'speeds': torch.zeros(count).double(),
        'reach': zeros.clone(), 'worn': zeros.clone(),
        'widths': zeros.clone(),
        'slip': torch.zeros(springs, shear.shape[1]).double(),
        'forces': torch.zeros(springs, lattice.dofs.shape[1]).double(),
    }
    device = torch.device(self.device)
    kind = torch.float64 if device.type == 'cpu' else torch.float32
    state = {key: value.to(device, kind) for key, value in floats.items()}
    others = {
        'flat': lattice.dofs.reshape(-1), 'top': lattice.topMask,
        'bottom': lattice.bottomMask, 'inner': lattice.phases != _PLATEN,
    }
    state.update({key: value.to(device) for key, value in others.items()})
    return state

  def _masses(self, stiffness: torch.Tensor) -> torch.Tensor:
    """The mass of each movement of the cells: its springs' 'stiffness'
    summed as Gershgorin bounds it, so the fastest mode is stable at a
    step of one, and some to spare."""
    lattice = self.lattice
    normal, shear = lattice.normalRows.abs(), lattice.shearRows.abs()
    rows = normal * normal.sum(1, True)
    rows = rows + (shear * shear.sum(2, True)).sum(1)
    rows = rows * stiffness[:, None]
    count = lattice.bodyMoves * (lattice.nodeCount + 2)
    sums = torch.zeros(count).double()
    sums.index_add_(0, lattice.dofs.reshape(-1), rows.reshape(-1))
    free = lattice.bodyMoves * lattice.nodeCount
    return sums[:free] / self.__fallback_mass_factor__

  def _takeStep(self, ) -> None:
    """Takes a step: moves the top platen, finds each spring's forces
    from how it stretches and slides, and moves each cell by its
    forces."""
    state = self._state()
    self.__test_step__ += 1
    moves, speeds = state['moves'], state['speeds']
    free = len(state['mass'])
    moves[self.lattice.platenLift] = self.strain * self.lattice.height
    flat, normal, shear = state['flat'], state['normal'], state['shear']
    local = moves[flat].view(len(normal), -1)
    stretch = (normal * local).sum(1)
    slides = (shear * local[:, None]).sum(2)
    stress, along = self._faceStresses(state, stretch, slides)
    areas = state['areas']
    forces = ((stress * areas)[:, None] * normal
              + ((along * areas[:, None])[:, :, None] * shear).sum(1))
    state['forces'] = forces
    total = torch.zeros_like(moves).index_add_(0, flat, forces.view(-1))
    push = -total[:free]
    push = push - self.__fallback_damping__ * push.abs() * torch.sign(
        speeds[:free])
    speeds[:free] += push / state['mass']
    moves[:free] += speeds[:free]

  @staticmethod
  def _faceStresses(state: dict, stretch: torch.Tensor,
                    slides: torch.Tensor, ) -> tuple:
    """
    The stress across each face and along it, each way it slides.
    Across: elastic up to the strength, then falling as the crack
    widens, the crack's widest opening so far setting how much is left;
    a closed crack bears in full. Along: elastic, up to the cohesion
    left, worn by the crack and by sliding, and the friction of the
    pressure across; past that the face slides the way it is pushed.
    """
    stiff, tension = state['stiff'], state['tension']
    reach = torch.maximum(state['reach'], stretch)
    state['reach'] = reach
    cracked = reach > state['opening']
    width = state['width']
    falling = (width - reach) / (width / tension - 1.0 / stiff)
    bound = torch.clamp(torch.minimum(falling, tension), 0.0)
    left = torch.where(cracked, bound / (stiff * reach), 1.0)
    across = torch.where(stretch > 0, stiff * left * stretch,
                         stiff * stretch)
    state['widths'] = torch.where(stretch > 0, (1.0 - left) * stretch, 0.0)
    worn = torch.clamp(1.0 - state['worn'] / state['slipWidth'], 0.0)
    cohesion = state['cohesion'] * left * worn
    holding = torch.clamp(cohesion - state['friction'] * across, 0.0)
    trial = stiff[:, None] * (slides - state['slip'])
    size = trial.norm(2, 1)
    beyond = torch.clamp(size - holding, 0.0)
    share = torch.where(size > 0, beyond / size, 0.0)
    slipped = trial * (share / stiff)[:, None]
    state['slip'] = state['slip'] + slipped
    state['worn'] = state['worn'] + slipped.norm(2, 1)
    return across, trial - stiff[:, None] * slipped

  def _record(self, ) -> None:
    """Records the strain and the stress, keeps the strength, and ends
    the test once it has fallen far enough, or strained far enough."""
    state = self._state()
    forces = state['forces']
    column = self.lattice.liftColumn
    top = forces[state['top'], column].sum().item()
    bottom = forces[state['bottom'], column].sum().item()
    stress = (top - bottom) / 2 / self.lattice.loadedArea
    strain = self.strain
    self.__test_curve__.append((strain, stress))
    if abs(stress) > self.strength:
      self.__test_strength__ = (abs(stress), abs(strain), self.crackedCount)
    if abs(strain) >= self.__fallback_strain_limit__:
      self.__test_finished__ = True
    ending = self.__fallback_ending_share__ * self.strength
    if self.crackedCount and abs(stress) <= ending:
      self.__test_finished__ = True


class CompressionTest(UniaxialTest):
  """
  CompressionTest is a 'UniaxialTest' crushing the cylinder: the top
  platen moved down, steadily, until the cylinder has given out or
  shortened five per mille.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_direction__ = -1.0
  __fallback_crossing_strain__ = 2.0e-5
  __fallback_strain_limit__ = 5.0e-3


class TensionTest(UniaxialTest):
  """
  TensionTest is a 'UniaxialTest' pulling the cylinder apart: the top
  platen moved up, ten times as slowly as in compression, as the
  cylinder gives out at a tenth of the strain, until it has given out or
  lengthened one per mille.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_direction__ = 1.0
  __fallback_crossing_strain__ = 2.0e-6
  __fallback_strain_limit__ = 1.0e-3
