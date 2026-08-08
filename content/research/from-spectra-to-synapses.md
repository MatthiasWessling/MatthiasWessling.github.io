+++
title = 'Neural networks in membrane science: from property prediction to neuromorphic devices'
date = '2026-08-07'
draft = false
summary = 'Overview of neural-network applications in the group: polymer permeability prediction (1994), data-driven design of layer-by-layer ion-separation membranes (Rall), and organic neuromorphic devices based on PEDOT:PSS (Felder).'
abstract = 'Overview of neural-network applications in the group: polymer permeability prediction (1994), data-driven design of layer-by-layer ion-separation membranes (Rall), and organic neuromorphic devices based on PEDOT:PSS (Felder).'
authors = ['Matthias Wessling']
publication = 'Research overview'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/ink-spectra-synapses.png'
image_alt = 'Abstract black-ink drawing of a neural network with spectral and synaptic motifs'
tags = ['neural networks', 'machine learning', 'membranes', 'neuromorphic']
+++

This note summarizes how artificial neural networks have been used in our group, from early structure–property correlation to membrane–process design and, later, to organic neuromorphic hardware. The aim is to document the scientific line of work and the associated theses and papers.

## Polymer permeability from infrared spectra (1994)

In *[Modelling the permeability of polymers: a neural network approach](https://doi.org/10.1016/0376-7388(93)E0168-J)* (*Journal of Membrane Science*, 1994), we examined whether a neural network can map the infrared spectrum of a polymer to its carbon dioxide permeability. The IR spectrum was treated as a high-dimensional input; permeability was the output. The underlying assumption was that sufficient chemical information is encoded in the spectrum for a data-driven mapping, without first writing a full free-volume or solution–diffusion model. The best network investigated showed predictive capability. The work is short and cautious in its claims; its main lasting point is methodological: non-linear membrane–material relationships can be learned from spectroscopic and transport data.

## Data-driven design of layer-by-layer membranes (Rall)

Deniz Rall’s thesis, *[Data-driven development of layer-by-layer nanofiltration membranes and processes](https://publications.rwth-aachen.de/record/804603)*, shifted the question from predicting properties of existing polymers to navigating the fabrication space of layer-by-layer (LbL) ion-separation membranes and embedding that description in process optimization.

In *[Rational design of ion separation membranes](https://doi.org/10.1016/j.memsci.2018.10.013)* (2019), an ANN trained on an extensive LbL dataset predicted salt retention and water flux from synthesis protocols. Local optimization improved permeability; deterministic global multi-objective optimization identified the Pareto front of the retention–permeability trade-off. Hybrid models coupled the network to mechanistic ion transport.

Subsequent papers extended the scale of decision-making. *[Simultaneous rational design of ion separation membranes and processes](https://doi.org/10.1016/j.memsci.2020.117860)* co-designed module synthesis and plant layout. *[Multi-scale membrane process optimization with high-fidelity ion transport models through machine learning](https://doi.org/10.1016/j.memsci.2020.118208)* embedded ANN surrogates in deterministic global optimization so that Nernst–Planck-level transport fidelity could inform plant-scale design without replacing the physics by heuristics alone.

In this phase, neural networks function as surrogates and as components of optimization workflows that connect laboratory synthesis protocols to process performance.

## Organic neuromorphic devices (Felder)

Daniel Felder’s thesis, *[Electrochemical charge transport in organic neuromorphic device networks](https://publications.rwth-aachen.de/record/964209)*, addresses neural networks implemented in soft, mixed ionic–electronic materials rather than only as computational models of membranes.

Organic artificial synapses based on PEDOT:PSS store information as conductance states and operate in aqueous electrolytes. *[Coupled ionic–electronic charge transport in organic neuromorphic devices](https://doi.org/10.1002/adts.202100492)* develops high-resolution transport models of that electrochemistry. The devices exhibit write non-idealities and self-discharge: programmed weights drift over time.

*[Reminding forgetful organic neuromorphic device networks](https://doi.org/10.1088/2634-4386/ac9c8a)* examines network design and reminder pulses as compensation for decay. *[Spiking neural networks compensate for weight drift in organic neuromorphic device networks](https://doi.org/10.1088/2634-4386/accd90)* shows that always-on spiking learning can continuously reinforce forgotten states. The emphasis is algorithm–hardware co-design that accounts for device limitations instead of assuming ideal synapses.

## Summary of roles

| Period | Role of the network | Focus |
|---|---|---|
| 1994 | Surrogate for structure–property maps | Polymer IR spectra → permeability |
| Rall, ~2019–2020 | Surrogate and optimizer in membrane–process design | Synthesis protocols ↔ plant performance |
| Felder, ~2022–2023 | Physical substrate with electrochemical non-idealities | PEDOT:PSS synapses, self-discharge, spiking learning |

Across these stages, the common element is the coupling of transport and soft-matter physics to learning—whether the network predicts membrane properties, guides fabrication and plant design, or is itself realized as a wet electrochemical device.
