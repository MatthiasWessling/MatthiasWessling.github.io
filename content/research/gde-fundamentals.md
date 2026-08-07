+++
title = 'Fundamentals of gas diffusion electrodes'
date = '2026-08-07'
draft = false
summary = 'Why GDEs succeed or fail is decided at the triple-phase boundary: wetting, electrowetting, flooding, PTFE coverage, and concurrent saturation states — made visible in micromodels and captured in continuum theory.'
abstract = 'Why GDEs succeed or fail is decided at the triple-phase boundary: wetting, electrowetting, flooding, PTFE coverage, and concurrent saturation states — made visible in micromodels and captured in continuum theory.'
authors = ['Matthias Wessling']
publication = 'Research note'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/gde-fundamentals-visual.png'
image_alt = 'Cutaway of a gas diffusion electrode showing gas pathways, partial catalyst-layer flooding, and a dynamic triple-phase boundary with local reaction gradients'
tags = ['gas diffusion electrodes', 'CO2 reduction', 'wetting', 'triple-phase boundary', 'electrowetting', 'modeling', 'microfluidics']
+++

A gas diffusion electrode is often introduced as a clever hardware trick: bring gaseous CO₂ (or O₂, or N₂) to a catalyst that sits next to liquid electrolyte, so mass transport no longer throttles the reaction. That description is true — and incomplete.

What actually decides Faraday efficiency, stability, and scale-up is the **gas–liquid–solid triple-phase boundary (TPB)** inside a porous, mixed-wetting catalyst layer. Flood a little too much and hydrogen evolution takes over. Dry out too much and ionic pathways collapse. Apply potential and the wettability itself moves. The fundamental program in our group has been to stop treating that interface as a cartoon line and start measuring, imaging, and modeling it as a living, spatio-temporal object.

## The core questions

Three questions recur across theses and papers:

1. **Where** does the desired reaction actually occur inside the electrode?  
2. **How** does electrolyte invade — or leave — the catalyst layer under operating potential?  
3. **Which** structural and surface descriptors (PTFE coverage, pore morphology, mixed wettability) set the accessible gas–liquid interfacial area?

Sebastian Brosch’s thesis, *[Wettability and reaction visualization of electrochemical CO₂ reduction at gas diffusion electrodes](https://publications.rwth-aachen.de/record/1028159)*, and Florian Wiesner’s *[Two-phase flow simulations in gas diffusion electrodes](https://publications.rwth-aachen.de/record/1028896)*, sit at the experimental and computational poles of those questions. Matthias Heßelmann’s continuum work then reconnects pore-scale wetting states to reactor-relevant performance.

## Act I — Build a GDE you can see into

Conventional GDEs are opaque. Early progress therefore required a surrogate that keeps the chemistry of a silver / Nafion catalyst layer while exposing pore-scale wetting to the microscope.

*[Micromodel of a Gas Diffusion Electrode Tracks In-Operando Pore-Scale Wetting Phenomena](https://doi.org/10.1002/smll.202204012)* (Kalde, Großeheide, Brosch, Keller, Linkhorst, Wessling, 2022) established a microfluidic GDE with multi-scale porosity and heterogeneous wettability. In operando, the gas–liquid–solid boundary can be watched as it forms, moves, and fails — the first systematic window onto why long-term GDE operation so often ends in flooding.

That micromodel language matured into mixed-wetting artificial porous media compared directly to SPH simulations: *[Fluid distribution in artificially manufactured porous mixed-wetting materials as a model for gas diffusion electrodes](https://doi.org/10.1016/j.ces.2025.121465)* (Brosch, Mager, Linkhorst, Nieken, Wessling, 2025). The lesson is methodological and physical: spatial surface-energy distribution, not a single average contact angle, governs fluid placement.

## Act II — Potential changes wettability; wettability relocates the reaction

Charging the electrode is not chemically neutral for the interface. *[Spatio-Temporal Electrowetting and Reaction Monitoring in Microfluidic Gas Diffusion Electrode Elucidates Mass Transport Limitations](https://doi.org/10.1002/smll.202310427)* (Brosch, Wiesner, Decker, Linkhorst, Wessling, 2024) combines the realistic microfluidic GDE with fluorescence lifetime imaging. Upon polarization, electrowetting drives immediate catalyst-layer flooding; local pH then oscillates in space and time. The TPB is not a fixed geometric locus. It is a dynamical state.

The sequel asks the product question directly. *[Visualization of CO formation at the triple-phase boundary in gas diffusion electrodes for ecCO2RR](https://doi.org/10.1016/j.chempr.2025.102582)* (Brosch et al., 2025) maps where CO forms across wetting states. The primary reaction location is indeed the TPB — yet the active area for CO₂ reduction is **far larger than the classical thin-line picture assumed**. Wetting state of the catalyst layer reshapes selectivity as much as catalyst identity does.

At device scale, the same physics appears as weeping. *[On the weeping of the GDE cathode during bipolar membrane-based electrochemical CO2 reduction reaction at high current densities](https://doi.org/10.1016/j.cej.2023.145335)* (Wrobel, Kriescher, Keller, Wessling, 2023) quantifies permeate through the GDE at currents up to 300 mA cm⁻²: Faraday efficiencies for CO can still be high, but weeping rate and bicarbonate saturation climb — flooding as a measurable continuum, not a binary failure mode.

## Act III — Morphology and PTFE: coverage, not slogans

Hydrophobic treatment is the industry’s answer to flooding. Fundamentals demand a sharper statement: **how much PTFE is on the surface, and where?**

*[Unveiling the Role of PTFE Surface Coverage on Controlling Gas Diffusion Layer Water Content](https://doi.org/10.1021/acsami.4c04641)* (Wiesner, Woodford, Sabharwal, Hesselmann, Wessling, Secanell, 2024) replaces the common “average contact angle” assumption with mixed-wettability algorithms on µ-CT and stochastically reconstructed GDLs. PTFE addition lowers saturation at a given capillary pressure — but the controlling variable is surface coverage and local material identity, not a single weight-percent slogan. That result connects fabrication recipes to the capillary pressure–saturation curves that continuum models need.

Wiesner’s broader thesis program — morphological two-phase simulation from reconstructed and µ-CT structures toward generalizable machine-learning surrogates — is the computational counterpart to Brosch’s visualization: predict water content and pathways before the electrode floods on the bench.

## Act IV — Continuum models that allow two wetting worlds at once

Most reactor models still assume a catalyst layer that is either fully flooded (gas impermeable) or partially saturated and fully gas-accessible. Reality is messier: both states can coexist.

*[Modeling different wetting states in gas diffusion electrodes for CO2 electrolysis](https://doi.org/10.1016/j.electacta.2025.146699)* (Plischka, Heßelmann, Wessling, Keller, 2025) builds a continuum GDE model in which concurrent wetting states set the gas–liquid interfacial area and thus the local reaction rate, using size-modified Nernst–Planck–Poisson transport. Earlier guidance work, *[Simulation-based guidance for improving CO2 reduction on silver gas diffusion electrodes](https://doi.org/10.1002/elsa.202100160)* (Heßelmann, Bräsel, Keller, Wessling, 2023), already showed how electrolyte and gas composition, flow, and catalyst-layer properties tune local reactant concentration and pH.

Time-domain operation adds another fundamental lever. *[Dynamics of the Boundary Layer in Pulsed CO2 Electrolysis](https://doi.org/10.1002/anie.202406924)* (Heßelmann, Felder, Plischka, Linkhorst, Wessling, Keller, 2024) shows that pulsing reorganizes the near-electrode microenvironment — reactant replenishment and carbonate management as scheduled dynamics rather than a fixed steady state.

## What “fundamental” means for a GDE

| Question | Experimental answer | Modeling answer |
|---|---|---|
| Where is the reaction? | CO maps to the TPB, but over a broader active wetting region than assumed | Concurrent wetting states set interfacial area and rate |
| Why does performance drift? | Electrowetting floods the CL; pH oscillates; weeping rises with current | Capillary saturation and PTFE coverage control water pathways |
| What should we design? | Mixed wettability and CL wetting state, not catalyst alone | Pore morphology + surface coverage + local pH/reactant fields |

The practical corollary is uncomfortable for catalyst-only narratives. Improving a GDE is first a problem of **multiphase porous-media physics under electrochemical forcing**, and only then a problem of active-site chemistry. Micromodels, FLIM, weeping quantification, PTFE-resolved GDL reconstruction, and continuum models with concurrent wetting states are not accessories to CO₂ electrolysis. They are the fundamentals.

From a microfluidic silver–Nafion surrogate that first showed the invading electrolyte, to CO fluorescence at the TPB and saturation curves that know where the PTFE sits, the thread is the same: **make the triple-phase boundary measurable, then make it designable.**

#GasDiffusionElectrodes
#TriplePhaseBoundary
#Electrowetting
#CO2Electrolysis
#Wetting
#Microfluidics
#TwoPhaseFlow
#ContinuumModeling
#PTFE
#Flooding
