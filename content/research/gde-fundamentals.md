+++
title = 'Fundamentals of gas diffusion electrodes'
date = '2026-08-07'
draft = false
summary = 'Overview of fundamental GDE work on wetting, electrowetting, PTFE surface coverage, concurrent saturation states, reaction location at the triple-phase boundary, and related micromodel and continuum approaches.'
abstract = 'Overview of fundamental GDE work on wetting, electrowetting, PTFE surface coverage, concurrent saturation states, reaction location at the triple-phase boundary, and related micromodel and continuum approaches.'
authors = ['Matthias Wessling']
publication = 'Research overview'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/ink-gde.png'
image_alt = 'Abstract black-ink drawing of a porous gas diffusion electrode and triple-phase boundary'
tags = ['gas diffusion electrodes', 'CO2 reduction', 'wetting', 'triple-phase boundary', 'electrowetting', 'modeling', 'microfluidics']
+++

Gas diffusion electrodes (GDEs) supply gaseous reactants (for example CO₂, O₂, or N₂) to a catalyst in contact with liquid electrolyte, thereby relaxing mass-transport limitations of planar electrodes. Performance and stability, however, depend strongly on the gas–liquid–solid triple-phase boundary (TPB) inside a porous, mixed-wetting catalyst layer. Excess flooding favors parasitic hydrogen evolution; insufficient liquid connectivity impairs ionic pathways; applied potential can change wettability. This note summarizes fundamental group work that measures, visualizes, and models that multiphase interface.

## Guiding questions

1. Where does the desired reaction occur inside the electrode?  
2. How does electrolyte enter or leave the catalyst layer under operating potential?  
3. Which structural and surface descriptors (PTFE coverage, pore morphology, mixed wettability) set the accessible gas–liquid interfacial area?

Sebastian Brosch’s thesis, *[Wettability and reaction visualization of electrochemical CO₂ reduction at gas diffusion electrodes](https://publications.rwth-aachen.de/record/1028159)*, and Florian Wiesner’s *[Two-phase flow simulations in gas diffusion electrodes](https://publications.rwth-aachen.de/record/1028896)*, address these questions experimentally and computationally. Continuum modeling by Matthias Heßelmann and coauthors connects wetting states to reactor-relevant metrics.

## Micromodels for operando wetting

Conventional GDEs are optically opaque. *[Micromodel of a Gas Diffusion Electrode Tracks In-Operando Pore-Scale Wetting Phenomena](https://doi.org/10.1002/smll.202204012)* (Kalde, Großeheide, Brosch, Keller, Linkhorst, Wessling, 2022) introduced a microfluidic GDE with multi-scale porosity and heterogeneous wettability, allowing operando observation of the gas–liquid–solid boundary.

*[Fluid distribution in artificially manufactured porous mixed-wetting materials as a model for gas diffusion electrodes](https://doi.org/10.1016/j.ces.2025.121465)* (Brosch, Mager, Linkhorst, Nieken, Wessling, 2025) compared mixed-wetting micromodels with smoothed-particle hydrodynamics simulations. Spatial surface-energy distribution, rather than a single average contact angle, governs fluid placement.

## Electrowetting, reaction location, and weeping

*[Spatio-Temporal Electrowetting and Reaction Monitoring in Microfluidic Gas Diffusion Electrode Elucidates Mass Transport Limitations](https://doi.org/10.1002/smll.202310427)* (Brosch, Wiesner, Decker, Linkhorst, Wessling, 2024) combined a microfluidic GDE surrogate with fluorescence lifetime imaging. Upon polarization, electrowetting caused catalyst-layer flooding and spatially oscillating local pH. The TPB is therefore a dynamical state, not a fixed geometric line.

*[Visualization of CO formation at the triple-phase boundary in gas diffusion electrodes for ecCO2RR](https://doi.org/10.1016/j.chempr.2025.102582)* (Brosch et al., 2025) mapped CO formation across wetting states. The primary reaction location is the TPB, while the active area for CO₂ reduction is larger than a thin-line idealization would suggest. Catalyst-layer wetting affects selectivity together with catalyst identity.

At device scale, *[On the weeping of the GDE cathode during bipolar membrane-based electrochemical CO2 reduction reaction at high current densities](https://doi.org/10.1016/j.cej.2023.145335)* (Wrobel, Kriescher, Keller, Wessling, 2023) quantified GDE permeate at currents up to 300 mA cm⁻². High CO Faraday efficiencies remain possible while weeping rate and bicarbonate saturation increase, treating flooding as a continuous, measurable process.

## PTFE coverage and gas diffusion layer water content

*[Unveiling the Role of PTFE Surface Coverage on Controlling Gas Diffusion Layer Water Content](https://doi.org/10.1021/acsami.4c04641)* (Wiesner, Woodford, Sabharwal, Hesselmann, Wessling, Secanell, 2024) replaced average-contact-angle assumptions with mixed-wettability algorithms on µ-CT and stochastically reconstructed GDLs. PTFE reduces saturation at given capillary pressure; the controlling descriptor is surface coverage and local material identity, not PTFE weight percent alone. Capillary pressure–saturation relations obtained this way feed continuum models. Wiesner’s thesis extends morphological two-phase simulation from reconstructed structures toward generalizable surrogates.

## Continuum models with concurrent wetting states

Many reactor models assume a catalyst layer that is either fully flooded or partially saturated and fully gas-accessible. *[Modeling different wetting states in gas diffusion electrodes for CO2 electrolysis](https://doi.org/10.1016/j.electacta.2025.146699)* (Plischka, Heßelmann, Wessling, Keller, 2025) allows concurrent wetting states that set gas–liquid interfacial area and local rate, using size-modified Nernst–Planck–Poisson transport. *[Simulation-based guidance for improving CO2 reduction on silver gas diffusion electrodes](https://doi.org/10.1002/elsa.202100160)* (Heßelmann, Bräsel, Keller, Wessling, 2023) examined how electrolyte and gas composition, flow, and catalyst-layer properties affect local reactant concentration and pH.

*[Dynamics of the Boundary Layer in Pulsed CO2 Electrolysis](https://doi.org/10.1002/anie.202406924)* (Heßelmann, Felder, Plischka, Linkhorst, Wessling, Keller, 2024) showed that pulsed potential reorganizes the near-electrode microenvironment, including reactant replenishment and carbonate-related dynamics.

## Summary

| Question | Experimental findings | Modeling findings |
|---|---|---|
| Reaction location | CO forms at the TPB over a broader wetting-dependent region than a thin-line model | Concurrent wetting states set interfacial area and rate |
| Performance drift | Electrowetting floods the catalyst layer; pH oscillates; weeping rises with current | Capillary saturation and PTFE coverage control water pathways |
| Design relevance | Mixed wettability and catalyst-layer wetting state, not catalyst chemistry alone | Pore morphology, surface coverage, and local pH/reactant fields |

Taken together, the work treats GDE improvement as a problem of multiphase porous-media physics under electrochemical forcing, in addition to active-site chemistry. Micromodels, FLIM, weeping quantification, PTFE-resolved GDL reconstruction, and continuum models with concurrent wetting states are used to make the triple-phase boundary measurable and therefore designable.
