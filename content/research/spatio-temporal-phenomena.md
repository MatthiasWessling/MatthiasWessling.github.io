+++
title = 'Spatio-temporal phenomena in membranes and electrodes'
date = '2026-08-07'
draft = false
summary = 'Overview of work on spatial and temporal structure in fouling, wetting, module hydrodynamics, membrane heating, overlimiting electroconvection, and gas diffusion electrodes, with associated visualization and modeling methods.'
abstract = 'Overview of work on spatial and temporal structure in fouling, wetting, module hydrodynamics, membrane heating, overlimiting electroconvection, and gas diffusion electrodes, with associated visualization and modeling methods.'
authors = ['Matthias Wessling']
publication = 'Research overview'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/ink-spatio-temporal.png'
image_alt = 'Abstract black-ink drawing of fluid convection rolls and a membrane line'
tags = ['spatio-temporal', 'visualization', 'MRI', 'microfluidics', 'fouling', 'GDE', 'wetting', 'Rayleigh-Bénard', 'electroconvection', 'overlimiting']
+++

Membrane and electrochemical processes are often summarized by bulk quantities such as flux, rejection, Faraday efficiency, or a single pH. Those metrics are necessary but do not resolve where and when transport, deposition, wetting, or reaction occur. This note collects group work that treats spatial and temporal structure as part of the scientific problem, using stochastic models, microfluidics, impedance, MRI, fluorescence lifetime imaging, and continuum or discrete simulations.

## Fouling as a spatially heterogeneous process

*[Two-dimensional stochastic modeling of membrane fouling](https://doi.org/10.1016/S1383-5866(01)00138-1)* (2001) described deposit morphology with diffusion-limited aggregation over an explicit membrane geometry. Local aggregate density varied (for example above pores versus flat regions), and flux decline depended on pore size and thickness. Fouling was formulated as a spatially resolved process rather than a single resistance term. Later work consistently returns to the point that similar bulk flux decline can arise from different microscopic pathways.

## Pore-scale filtration: visualization and simulation

*[Microfluidic colloid filtration](https://doi.org/10.1038/srep22376)* (2016) provided a pore-scale experimental platform for colloidal retention. Coupled CFD–DEM studies examined adsorption, resuspension, and DLVO-related transitions — *[What are the microscopic events of colloidal membrane fouling?](https://doi.org/10.1016/j.memsci.2018.02.023)* (2018). Soft-matter systems added temporal structure: confocal imaging of microgel cakes showed deformation of amorphous and crystalline domains under permeation — *[Direct Observation of Deformation in Microgel Filtration](https://doi.org/10.1038/s41598-019-55516-w)* (2019) — and backwashing was resolved as cluster resuspension rather than a simple hydraulic reset — *[What are the microscopic events during membrane backwashing?](https://doi.org/10.1016/j.memsci.2020.117886)* (2020).

*[Temporal resistance fluctuations during the initial filtration period of colloidal matter filtration](https://doi.org/10.1016/j.memsci.2024.122988)* (2024) showed that early filtration of soft microgels is not a monotonic resistance ramp: a peak can be followed by a substantial drop as the deposit reorganizes. Start-up dynamics therefore differ from quasi-steady cake behavior.

*[On-line monitoring of cake layer structure during fouling on porous membranes by in situ electrical impedance analysis](https://doi.org/10.1016/j.memsci.2016.01.009)* (2016) extracted cake height and porosity versus time for flat-sheet and hollow-fiber geometries, illustrating that architecture can reverse porosity trends that look similar when only flux is recorded.

## Module-scale wetting, flow, and ion fields

*[In-situ investigation of wetting patterns in polymeric multibore membranes via magnetic resonance imaging](https://doi.org/10.1016/j.memsci.2020.119026)* (2021) quantified aqueous invasion of multibore fibers as a function of flux, packing, axial position, and initial wetting state. Complete wetting can require hours even at high fluxes. Related MRI applications are summarized in *[Magnetic Resonance Imaging of Membrane Filtration Processes](https://doi.org/10.1002/9783527827244.ch9)* (2022).

*[Flow and fouling visualization in modules having multiple multichannel membranes](https://doi.org/10.1016/j.memsci.2025.124205)* (2025) reported jet-like streams, reverse flows, and recirculation that intensify with packing density, with reduced contribution of inner bore channels under fouling. Module architecture therefore contributes to apparent membrane performance through maldistribution.

*[Visualizing the local ion concentration in electrodialysis cells via magnetic resonance imaging](https://doi.org/10.1016/j.memlet.2025.100094)* (2025) reconstructed copper concentration fields inside an opaque electrodialysis module, treating desalination as a spatially resolved concentration profile.

## Membrane heating and Rayleigh–Bénard convection

Theresa Lohaus (Rösener) examined temperature as a controlled driver of near-membrane hydrodynamics. In *[Feed flow patterns of combined Rayleigh-Bénard convection and membrane permeation](https://doi.org/10.1016/j.memsci.2017.11.061)* (2018), preceded by *[Strömungsprofil von überlagerter Permeation und Rayleigh-Bénard-Konvektion](https://doi.org/10.1002/cite.201650170)* (2016), an electrically conductive membrane was heated to induce buoyancy-driven convection that mixes with pressure-driven permeation. PIV and CFD were used to map mixed-convection regimes; the Richardson number separates thermal-roll-dominated from permeation-dominated conditions.

*[Direct membrane heating for temperature induced fouling prevention](https://doi.org/10.1016/j.memsci.2020.118431)* (2020) applied Joule heating of silicon carbide hollow fibers during yeast filtration (continuous heating, heated backwash, in-place cleaning). Temperature then acts on local viscosity, particle–surface interaction, and deposit mobility. The thesis *[Temperature modulated membrane transport phenomena](https://publications.rwth-aachen.de/record/774433)* documents this program.

## Overlimiting currents and electroconvection

Above the limiting current, depleted boundary layers can develop electroconvective vortices. Chronopotentiometric voltage fluctuations already indicated hydrodynamic instability in *[Chronopotentiometry and overlimiting ion transport through monopolar ion exchange membranes](https://doi.org/10.1016/S0376-7388(99)00134-9)* (1999).

*[Morphology and microtopology of cation-exchange polymers and the origin of the overlimiting current](https://doi.org/10.1021/jp068474t)* (2007) showed that surface undulations with spacing comparable to the boundary-layer thickness shorten the plateau and promote earlier electroconvection. *[Space-Charge breakdown phenomenon and spatio-temporal ion concentration and fluid flow patterns in overlimiting current electrodialysis](https://doi.org/10.1016/j.memsci.2021.119583)* (2021) used direct numerical simulation of a cation–anion membrane channel to resolve coupled ion and flow fields after space-charge breakdown. Felix Stockmeier’s thesis, *[Flow fields in the overlimiting current regime in electrically-driven membrane processes](https://publications.rwth-aachen.de/record/856875)*, reported experimental 3D velocity fields of electroconvection.

*[Trade-offs between spacer-induced mixing and electric-field shadowing govern overlimiting electrodialysis performance](https://doi.org/10.1016/j.memsci.2026.125644)* (2026) examined how spacer geometry and buoyancy orientation interact with overlimiting transport. Thermal Rayleigh–Bénard mixing and electrical electroconvection are related in outcome: both replace a stagnant diffusion layer with organized, time-dependent flow.

## Flow control and gas diffusion electrodes

*[Magnetically Actuable Complex-Shaped Microgels for Spatio-Temporal Flow Control](https://doi.org/10.1002/admt.202300044)* (2023) used programmed magnetic moments in complex microgels to set orientation and rotation under external fields, providing local flow control on demand.

For electrochemical CO₂ reduction, *[Spatio-Temporal Electrowetting and Reaction Monitoring in Microfluidic Gas Diffusion Electrode Elucidates Mass Transport Limitations](https://doi.org/10.1002/smll.202310427)* (2024) combined a microfluidic GDE surrogate with fluorescence lifetime imaging. Polarization induced electrowetting and catalyst-layer flooding, followed by spatially oscillating local pH. *[Visualization of CO formation at the triple-phase boundary in gas diffusion electrodes for ecCO2RR](https://doi.org/10.1016/j.chempr.2025.102582)* (2025) mapped CO formation across wetting states. *[Dynamics of the Boundary Layer in Pulsed CO2 Electrolysis](https://doi.org/10.1002/anie.202406924)* (2024) modeled boundary-layer reorganization under pulsed potential. A more detailed GDE overview is given in *[Fundamentals of gas diffusion electrodes](/research/gde-fundamentals/)*.

## Overview by scale

| Scale | Phenomena | Methods |
|---|---|---|
| Pore / cake | Deposition, deformation, resuspension, resistance fluctuations | Microfluidics, confocal, CFD–DEM, impedance |
| Fiber / module | Wetting fronts, maldistribution, local ion fields | MRI |
| Heated membrane | Rayleigh–Bénard rolls with permeation; thermal fouling control | PIV, CFD, Joule-heated SiC fibers |
| Overlimiting ED | Electroconvection, space-charge breakdown, spacer–buoyancy coupling | Chronopotentiometry, DNS, 3D µPTV |
| Soft actuators | Oriented microgels for local flow | Magnetic stop-flow lithography |
| GDE | Electrowetting, flooding, oscillating pH, reaction location, pulsing | FLIM micromodels, reaction mapping, dynamic modeling |

The practical implication is that cleaning, heating, patterning, packing, catalyst-layer wettability, and pulsed or overlimiting operation act on local, time-dependent states. Bulk averages alone are often insufficient for mechanism assignment or design.
