+++
title = 'Seeing space and time: Spatio-temporal phenomena in membranes and electrodes'
date = '2026-08-07'
draft = false
summary = 'From stochastic deposit maps to Rayleigh–Bénard heating, overlimiting electroconvection, and operando FLIM: how our group resolves where and when transport, fouling, wetting, and reaction actually happen.'
abstract = 'From stochastic deposit maps to Rayleigh–Bénard heating, overlimiting electroconvection, and operando FLIM: how our group resolves where and when transport, fouling, wetting, and reaction actually happen.'
authors = ['Matthias Wessling']
publication = 'Research note'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/spatio-temporal-phenomena-visual.png'
image_alt = 'Three-stage visual of spatio-temporal membrane science: multibore MRI wetting fronts, microfluidic colloidal deposition trails, and oscillating reaction zones in a gas diffusion electrode'
tags = ['spatio-temporal', 'visualization', 'MRI', 'microfluidics', 'fouling', 'GDE', 'wetting', 'Rayleigh-Bénard', 'electroconvection', 'overlimiting']
+++

Membrane processes are usually reported as numbers that erase space and time: flux, rejection, faradaic efficiency, a single pH. Useful — and incomplete. Fouling does not grow uniformly. Wetting does not advance as a flat front. Reactions in gas diffusion electrodes do not occur “everywhere on the catalyst.” They happen *somewhere*, and that somewhere moves.

Over two decades, our group has treated that “somewhere, and when” as a first-class scientific object. The tools changed — stochastic models, NMR/MRI, electrical impedance, microfluidic micromodels, fluorescence lifetime imaging — but the question stayed the same: **what is the spatio-temporal structure behind the bulk signal?**

## Act I — Heterogeneity is not noise

The early framing was already spatial. In *[Two-dimensional stochastic modeling of membrane fouling](https://doi.org/10.1016/S1383-5866(01)00138-1)* (2001), deposit morphology was not a uniform cake resistance. Diffusion-limited aggregation over an explicit membrane morphology produced local density variations — thinner aggregates above pores, denser layers on flat surfaces — and flux decline regimes that depended on pore size and thickness. Fouling was cast as a *map*, not a scalar.

That habit of mind returns throughout the later work. Average flux decline can hide very different microscopic routes to the same macroscopic loss.

## Act II — Make the map visible: filtration in space and time

Once the question is spatial, instrumentation follows.

**Microfluidics turned pores into theatres.** *[Microfluidic colloid filtration](https://doi.org/10.1038/srep22376)* (2016) opened a pore-scale window on colloidal retention. Coupled CFD–DEM work then asked what the eye cannot quite resolve: adsorption and resuspension pathways, gliding of particles along surfaces, transitions between secondary and primary DLVO minima — *[What are the microscopic events of colloidal membrane fouling?](https://doi.org/10.1016/j.memsci.2018.02.023)* (2018). Soft matter made the temporal structure even sharper. Confocal imaging of microgel cakes showed amorphous and crystalline domains deforming under permeation — *[Direct Observation of Deformation in Microgel Filtration](https://doi.org/10.1038/s41598-019-55516-w)* (2019) — while backwashing revealed cluster resuspension rather than a simple hydraulic reset — *[What are the microscopic events during membrane backwashing?](https://doi.org/10.1016/j.memsci.2020.117886)* (2020).

**Time itself became a measurable texture.** In *[Temporal resistance fluctuations during the initial filtration period of colloidal matter filtration](https://doi.org/10.1016/j.memsci.2024.122988)* (2024), early filtration is not a smooth ramp. Soft microgel cakes show a resistance peak followed by a drop of up to ~50% as the deposit reorganizes — a reminder that start-up dynamics are a different physics from the quasi-steady cake.

**Impedance added an online structural clock.** *[On-line monitoring of cake layer structure during fouling on porous membranes by in situ electrical impedance analysis](https://doi.org/10.1016/j.memsci.2016.01.009)* (2016) extracted cake height and porosity versus time for flat-sheet and hollow-fiber geometries, showing that the same “fouling curve” can hide opposite porosity trends depending on architecture.

## Act III — Modules have geography

Pore-scale insight does not automatically scale to a module. Magnetic resonance imaging made that geography readable without cutting the fiber open.

*[In-situ investigation of wetting patterns in polymeric multibore membranes via magnetic resonance imaging](https://doi.org/10.1016/j.memsci.2020.119026)* (2021) quantified how aqueous fronts invade multibore fibers as a function of flux, packing, axial position, and initial wetting state. Complete wetting can take hours even at high fluxes — a spatio-temporal process, not an instantaneous material property. The chapter *[Magnetic Resonance Imaging of Membrane Filtration Processes](https://doi.org/10.1002/9783527827244.ch9)* (2022) collected this logic across filtration applications.

The module story continues in *[Flow and fouling visualization in modules having multiple multichannel membranes](https://doi.org/10.1016/j.memsci.2025.124205)* (2025): jet-like streams, reverse flows, and recirculation grow with packing density; inner bore channels contribute disproportionately little under fouling. Apparent membrane performance is partly *architecture-induced maldistribution*.

The same MRI instinct crossed into electrochemical separations. *[Visualizing the local ion concentration in electrodialysis cells via magnetic resonance imaging](https://doi.org/10.1016/j.memlet.2025.100094)* (2025) reconstructs copper concentration fields inside an opaque ED module — desalination as a spatial profile, not only as conductivity change.

## Act IV — Heat the membrane: Rayleigh–Bénard as designed instability

Not every spatio-temporal pattern is a defect to be diagnosed. Theresa Lohaus (now Rösener) asked whether temperature could *create* useful near-membrane hydrodynamics.

In *[Feed flow patterns of combined Rayleigh-Bénard convection and membrane permeation](https://doi.org/10.1016/j.memsci.2017.11.061)* (2018) — foreshadowed in *[Strömungsprofil von überlagerter Permeation und Rayleigh-Bénard-Konvektion](https://doi.org/10.1002/cite.201650170)* (2016) — an electrically conductive membrane is heated so that buoyancy-driven Rayleigh–Bénard cells rise from the surface and mix with pressure-driven permeation. Particle image velocimetry and CFD map the mixed-convection patterns; the Richardson number sorts when thermal rolls dominate permeation suction and when the opposite is true. Concentration polarization is attacked by an instability that is *scheduled* by heat input rather than left to chance.

*[Direct membrane heating for temperature induced fouling prevention](https://doi.org/10.1016/j.memsci.2020.118431)* (2020) then turns Joule heating of silicon carbide hollow fibers into an operational lever: continuous heating during cross-flow, heated backwash, and in-place thermal cleaning during yeast filtration. Temperature here is not a background parameter. It rewrites local viscosity, particle–surface interaction, and deposit mobility — fouling control as a spatio-temporal thermal protocol. The thesis *[Temperature modulated membrane transport phenomena](https://publications.rwth-aachen.de/record/774433)* collects this program.

## Act V — Overlimiting currents: electroconvection as living flow

Electrically driven membrane processes have their own native instability. Above the limiting current, the depleted boundary layer does not simply thicken forever. It can break into electroconvective vortices — a classic spatio-temporal phenomenon long visible in chronopotentiometric voltage fluctuations ([*Chronopotentiometry and overlimiting ion transport through monopolar ion exchange membranes*](https://doi.org/10.1016/S0376-7388(99)00134-9), 1999).

*[Morphology and microtopology of cation-exchange polymers and the origin of the overlimiting current](https://doi.org/10.1021/jp068474t)* (2007) showed that surface undulations with spacing comparable to the boundary-layer thickness shorten the plateau and accelerate the onset of electroconvection — geometry as a trigger for when and where vortices appear. Later work made the patterns themselves the measured object. *[Space-Charge breakdown phenomenon and spatio-temporal ion concentration and fluid flow patterns in overlimiting current electrodialysis](https://doi.org/10.1016/j.memsci.2021.119583)* (2021) used direct numerical simulation of a full cation–anion membrane channel to resolve how ion fields and flow co-evolve once space charge breaks down. Felix Stockmeier’s thesis, *[Flow fields in the overlimiting current regime in electrically-driven membrane processes](https://publications.rwth-aachen.de/record/856875)*, pushed further to experimental 3D velocity fields of electroconvection at high temporal and spatial resolution — finally quantifying the vortex geography that bulk *I–V* curves only hint at.

Recent spacer studies close the engineering loop: *[Trade-offs between spacer-induced mixing and electric-field shadowing govern overlimiting electrodialysis performance](https://doi.org/10.1016/j.memsci.2026.125644)* (2026) shows that forced hydrodynamics and electroconvection do not simply add; buoyancy-stable versus unstable orientations and spacer shadowing reshape when overlimiting transport helps or hurts. Rayleigh–Bénard heating and overlimiting electroconvection are cousins: both replace a stagnant diffusion layer with organized, time-dependent flow — one thermal, one electrical.

## Act VI — Control space and time, then watch reactions move

Spatio-temporal phenomena are not only to be observed. They can be engineered.

*[Magnetically Actuable Complex-Shaped Microgels for Spatio-Temporal Flow Control](https://doi.org/10.1002/admt.202300044)* (2023) programs magnetic moments into complex microgels so that external fields set position and rotation — soft impellers that rewrite local flow on demand. Flow control becomes a temporal protocol.

In electrochemical CO₂ reduction, the decisive theatre is the triple-phase boundary inside a gas diffusion electrode. *[Spatio-Temporal Electrowetting and Reaction Monitoring in Microfluidic Gas Diffusion Electrode Elucidates Mass Transport Limitations](https://doi.org/10.1002/smll.202310427)* (2024) combines a realistic microfluidic GDE surrogate with fluorescence lifetime imaging. Charging triggers immediate electrowetting and catalyst-layer flooding, then *spatially oscillating* local pH — the (in)stability of the triple-phase boundary made visible in operando. The sequel in *Chem*, *[Visualization of CO formation at the triple-phase boundary in gas diffusion electrodes for ecCO2RR](https://doi.org/10.1016/j.chempr.2025.102582)* (2025), maps where CO actually forms across wetting states and ties selectivity to the geography of the reaction zone.

Time-domain operation closes the loop. *[Dynamics of the Boundary Layer in Pulsed CO2 Electrolysis](https://doi.org/10.1002/anie.202406924)* (2024) models how alternating potential reorganizes the electrode microenvironment — reactant replenishment and carbonate management as *scheduled* spatio-temporal dynamics rather than a fixed steady state.

## One laboratory habit

Read as a sequence, these papers are not a catalog of methods. They are a progressive refusal to trust the bulk average:

| Scale | What moves in space and time | How we watch / drive |
|---|---|---|
| Pore / cake | Particle adsorption, deformation, cluster release, resistance fluctuations | Microfluidics, confocal, CFD–DEM, impedance |
| Fiber / module | Wetting fronts, shell–lumen communication, maldistribution, local ion fields | MRI |
| Heated membrane | Rayleigh–Bénard rolls mixed with permeation; thermal fouling control | PIV, CFD, Joule-heated SiC fibers |
| Overlimiting ED | Electroconvective vortices, space-charge breakdown, spacer–buoyancy coupling | Chronopotentiometry, DNS, 3D µPTV |
| Soft actuators | Oriented microgels rewriting local flow | Magnetic stop-flow lithography |
| GDE / electrolyzer | Electrowetting, flooding, oscillating pH, moving CO zones, pulsed boundary layers | FLIM micromodels, reaction mapping, dynamic modeling |

The practical consequence is sharp. Cleaning protocols, membrane heating, surface patterning, module packing, catalyst-layer wettability, and pulsed or overlimiting operation all act on *local histories*. If the diagnostic only reports a global number, design optimizes the wrong object.

Spatio-temporal phenomena are therefore not a specialty niche next to “membrane science.” They are membrane science once space and time are allowed back into the description — from a stochastic deposit map in 2001, through heated Rayleigh–Bénard cells and overlimiting electroconvection, to an oscillating triple-phase boundary under potential.

#SpatioTemporal
#MembraneScience
#MRI
#Microfluidics
#Fouling
#RayleighBenard
#DirectMembraneHeating
#Electroconvection
#OverlimitingCurrent
#GasDiffusionElectrodes
#Electrowetting
#OperandoVisualization
#TriplePhaseBoundary
