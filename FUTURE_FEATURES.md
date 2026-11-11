# Future features

Applications and features planned on top of worQt, each described
precisely enough to build and to test. They are planned by user journey,
not by technology: a feature is done when its journey works for someone
who has never seen the tool, with no manual.

## AsgerBim

AsgerBim is a planned civil-engineering CAD/BIM application built on
worQt: one central project model, with drawings, analyses and views made
from it. Its first feature is the site.

## Feature 1: the site

### Why it comes first

A civil engineer's work does not start from a blank canvas, and not even
from the architect's project. It starts from the site: the ground nature
left, and the services the site-servicing contractors brought to it. The
ground decides whether a basement is cheap or a watertight tank, whether
the building stands on footings or on piles, and where on the plot it
should go. The architect's project can only be envisioned properly on
top of it.

### Terms

- **Byggemodning**: site servicing. Roads, sewers, water, power and
  district heating brought to the plot. A 'byggemodnet grund' is a
  serviced plot.
- **Muld**: topsoil. The organic surface layer, stripped under buildings.
- **OSBL** ('overside af bæredygtigt lag'): the top of the bearing
  stratum, the first layer able to carry foundations.
- **Funderingsniveau**: founding level, where a footing actually sits.
- **Grundvandsspejl**: the groundwater table.
- **Landmåler**: the surveyor. AsgerBim uses this one name for the role,
  licensed land surveyor ('landinspektør') or not.
- **Kote**: a level, a height in DVR90.
- **Matrikel**: a cadastral plot.
- **Lokalplan**: the local plan, with the building envelope, heights and
  use.
- **Skråfoto**: an oblique aerial photo.

### Coordinates

Plan positions are ETRS89 / UTM zone 32N (EPSG:25832) and heights DVR90
(EPSG:5799). Everything imported is transformed to these on the way in,
and the transformation is recorded with the data. Heights in the old DNN
datum are recognised and converted, never taken as DVR90.

### Sources

**Public.** Free; most need a free Dataforsyningen token. Each source's
current licence terms are checked before it is used.

- **Danmarks Højdemodel** (SDFI): the terrain model on a 0.4 m grid, and
  the classified point cloud (ground, vegetation, buildings).
- **Orthophotos** (SDFI): the aerial photo draped on the terrain.
- **Skråfoto** (SDFI): oblique aerial photos of all of Denmark from four
  directions plus straight down, served by a STAC API with camera
  metadata. The main imagery for reconstruction. Released as free data in
  2018; the current licence wording is not yet verified.
- **Matrikelkortet**: plot boundaries.
- **Plandata.dk**: the local plan.
- **GEUS Jupiter**: boreholes with their layer logs.
- **GEUS soil maps**: surface geology.
- **HIP** (Hydrologisk Informations- og Prognosesystem): modelled depth
  to the groundwater near the surface.
- **Danmarks Miljøportal**: soil contamination mapping.
- **LER 2.0**: buried pipes and cables, delivered on request for an area,
  under its conditions.
- **Mapillary**: crowd-sourced street-level photos with positions, under
  an open licence (CC BY-SA), with an API.

Google Street View and other Google Maps imagery are not used. Their
terms forbid bulk download, caching and building 3D models from them.
They may be looked at by eye, never fed to the tool.

**Bespoke, paid for each project.**

- **The landmåler's delivery**: topographic survey (LandXML, DXF with
  feature codes), point clouds (LAS/LAZ), drone orthophotos (GeoTIFF),
  and photos from a camera on the GNSS rover pole, tagged with RTK
  positions to the centimetre. It includes the levels of the service
  connections at the boundary, invert levels of sewers among them. Rovers
  with cameras already exist (Leica GS18 I, for one). AsgerBim imports
  what landmålere already deliver and invents no format.
- **The geotechnical report**: boreholes, their logs and groundwater
  observations. Where it has data, it replaces the estimates.

**The engineer's own.**

- **Phone photos**, with the position and compass direction from their
  EXIF data, uploaded by scanning a QR code shown on screen. No app.

### What the tool builds

1. **The surface**: the terrain with the aerial photo, sharpened by
   reconstruction from photographs (photogrammetry or Gaussian
   splatting). The reconstruction is registered to the terrain model,
   which gives it coordinates and scale.
2. **The ground below**: layers from the borehole logs, and interpolated
   surfaces for the base of the topsoil, the top of the bearing stratum
   and the groundwater table. Each carries its uncertainty, which grows
   with the distance to the nearest borehole and with the borehole's age
   and quality.
3. **Features**: pipes, cables and connection points with their levels,
   boundary markers, manholes, trees and neighbouring buildings. They come
   from LER, the cadastre, the point cloud and the landmåler, plus
   suggestions recognised in photos.
4. **Quantities**: the topsoil to strip, cut and fill, the excavation and
   the soil to cart away. They update as data arrives.

### What AI does

- **Reconstruction**: photographs become a 3D surface.
- **Recognition**: a vision model suggests features it sees in photos: a
  manhole, a boundary stake, a tree, a crack in a neighbour's façade,
  standing water or reeds that hint at high groundwater. These are
  suggestions only; the engineer confirms or rejects each one. Confirmed
  photos of neighbouring buildings double as the record of their
  condition before construction.
- **Reading**: borehole logs ('LER, sandet, gruset, brun (moræne)'),
  geotechnical report PDFs and utility deliveries become structured
  layers and features.

AI never generates site data. Everything shown comes from a source.

### UX rules

1. **Realism only where measured.** The surface may be photo-real where
   photographs and the terrain model agree. Nothing below ground is ever
   invented: it stays fogged until a borehole, a utility record or a
   survey says otherwise.
2. **Fog of war.** The unknown is fogged. Each source lifts the fog to
   its own accuracy: public terrain to about a decimetre, phone photos to
   about a metre, the landmåler to a few centimetres. A borehole lifts it
   around itself, fading with distance.
3. **Provenance everywhere.** Hovering any surface, layer or feature shows
   where it came from, when, and how accurate it is: 'terrain: DHM 2023',
   'texture: photo 2026-11-05 14:02', 'layer: borehole DGU 123.456'.
4. **Every fog has someone who can lift it, and the tool writes their
   brief**: the landmåler (what to survey, photograph and level), the
   geotechnician (where to bore, favouring the heaviest future loads) and
   the engineer (where to look).
5. **Photos sit on the map** where they were taken, each with its view
   cone. Parts of the site no photo has seen stay fogged.
6. **No dialogs for problems.** Problems show in the site itself.
7. **Mouse first, every action echoed as text** in a Vidget, as a line
   that could have been typed instead.
8. **Nothing is ever lost.** Every import and every decision can be
   undone, and is kept.
9. **Data for the public is taken freely; data about people is held as
   little as possible.** No personal data beyond what a delivery
   requires.

### The journey: "the plot"

An engineer who has never seen AsgerBim:

1. Opens it. A map of Denmark, with one invitation: find your plot, by
   address, by cadastral number or by clicking.
2. Picks a plot. The terrain rises in 3D under the aerial photo. The plot
   boundary and the local plan's building envelope stand on it, with the
   neighbouring buildings around. Buried pipes and cables show as lines
   in the ground.
3. Nearby boreholes stand as columns showing their layers. The top of
   the bearing stratum and the groundwater table appear as surfaces under
   the terrain: clear near the boreholes, fogged further away, with a note
   on how far to trust them ('nearest boring 38 m away, from 1974').
4. The tool shows what is still unknown, and offers the briefs that would
   lift it.
5. Photos arrive (from the phone, from the landmåler, from Mapillary) and
   land where they were taken. The surface sharpens, and recognised
   features appear as suggestions.
6. The quantities update as the data arrives.
7. A geotechnical report or a landmåler's delivery lifts more fog, and
   everything it changed is highlighted, like a revision.

### Done when

- The journey runs as one scripted 'WidgetTest' on a real test site:
  the gestures above, with assertions of what is shown at each beat.
  Tests run on recorded real data for the test sites, never on live
  network calls. Recorded data stays out of git unless its licence allows
  it.
- A civil engineer who has never seen AsgerBim completes the journey
  unaided.

### Development data

- **Real sites only.** No synthetic or AI-generated site data, not even
  during development.
- **Nobody goes outside to collect it.** Test sites are chosen where the
  photography already exists.
- **A test site has** good skråfoto coverage, Mapillary photos at street
  level, boreholes within about 100 m and, ideally, a municipal plot sale
  that published its geotechnical report and servicing plan.
- **At least two sites**: an easy one (flat, dry, the bearing stratum
  near the surface) and a hard one (a slope, high groundwater, old fill).

### Out of scope

- The architect's project landing on the site. That is the next feature,
  with KIT's open 'AC20-Institute-Var-2' IFC model as its first
  architect's project.
- Structural analysis, drawings and construction phases.
- Helping architects, a separate product for later.

### Open questions

- Which test sites.
- The current licence terms of each source: skråfoto, the conditions of
  LER 2.0, Mapillary's attribution.
- Where AsgerBim lives: its own repository, depending on worQt?
- The 3D viewer (pyvista/VTK, Qt Quick 3D or other), and how Gaussian
  splats are drawn in it.
- Which reconstruction tools, and where they run.
- Which vision and language models, and whether they run locally.

## Three-cushion: a computer opponent

Potential plans, nothing decided (2026-11-07). Searching shots on the
real engine is costly: one shot played to rest takes it 0.35-0.6 s,
nine tenths of it in the contacts stepped through, so a few hundred
candidates take some 20 s a think on 8 cores. Two ways round it:

- **A learned shot finder.** A compute project, run once: reinforcement
  learning against the real engine teaches a small model which shots
  are good from a layout, and at play time a shot finder proposes and
  ranks shots the way a chess engine does. The training is costly; the
  player that comes out of it could be small.
- **A crude prediction engine.** Far cheaper than the real one: exact
  cloth phases, collisions as instant pushes, the cushions as a few
  adjustable parameters. A training run fits those parameters until it
  predicts the real engine's outcomes well, and the opponent searches
  shots with it.

Either way the skill would sit in the opponent's hand rather than its
brain: errors in aim, tip and speed by level, so it misses differently
each time.

## Billiards: balls with height

Noted 2026-11-11, for later. The engine keeps every ball on the cloth:
a push up on a ball is dropped and the slate takes it. Height for balls
(an airborne state, a hop, landing on the slate) would bring in, as
honestly as the rest (the user: the rare edge case done right is what
makes it immersive, "we are not gonna be like" a game that leaves it
out or crashes on it):

- **Keglebillard, a ball meeting a lying pin.** A pin on its side is
  about 20 mm high, a third of the ball; its push on the ball leans
  some 30 degrees up, so a ball rides up it, or at speed hops over,
  where the engine now has it shove the pin as a wall would. Lying pins
  block a carom a little more often than on a real table.
- **Three-cushion, jumps.** A fast ball with heavy top spin can leave
  the table (the user); a ball can leave the slate off a cushion's nose
  or another ball.
- **An elevated cue** (massé, swerve), struck down into the ball.
