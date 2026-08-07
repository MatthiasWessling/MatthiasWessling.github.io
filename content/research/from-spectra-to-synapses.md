+++
title = 'My journey with AI: From spectra to synapses'
date = '2026-08-07'
draft = false
summary = 'Three decades of neural networks in our group: from predicting polymer permeability, through designing ion-separation membranes and plants, to building forgetful organic hardware that learns.'
abstract = 'Three decades of neural networks in our group: from predicting polymer permeability, through designing ion-separation membranes and plants, to building forgetful organic hardware that learns.'
authors = ['Matthias Wessling']
publication = 'Research note'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/neural-networks-arc-visual.png'
image_alt = 'Three-stage visual: infrared spectra feeding a neural net, layered nanofiltration membranes with optimization curves, and an organic neuromorphic synapse'
tags = ['neural networks', 'machine learning', 'membranes', 'neuromorphic']
+++

In 1994 we asked a question that still feels modern: can a neural network read the chemistry of a polymer from its infrared spectrum and predict how fast carbon dioxide will permeate through it?

That short communication in the *Journal of Membrane Science* — *[Modelling the permeability of polymers: a neural network approach](https://doi.org/10.1016/0376-7388(93)E0168-J)* — was modest in length and cautious in claims. The best network we tried did show predictive capability. Looking back, the real contribution was not a spectacular correlation coefficient. It was a bet: that the non-linear relationships membrane scientists care about might be learnable from data long before we had the vocabulary of “machine learning for materials.”

Thirty years later, that bet has branched into two very different futures in our group. One uses neural networks as *design tools* for membranes and processes. The other turns soft matter and ion transport into *physical* neural networks. Deniz Rall and Daniel Felder each carried one of those futures to a PhD — and together they tell a story of how far the idea can travel.

## Act I — Predict: chemistry as a signal

The 1994 paper treated an IR spectrum as a high-dimensional input and permeability as the output. The assumption was simple and radical: enough chemical information is encoded in the spectrum that a network can map it to transport without writing down a full free-volume or solution–diffusion model first.

That framing — soft matter as a coded signal, transport as a decodeable response — never really left our work. What changed was the ambition of the decode.

## Act II — Design: Deniz Rall and the learnable membrane

Deniz Rall’s thesis, *[Data-driven development of layer-by-layer nanofiltration membranes and processes](https://publications.rwth-aachen.de/record/804603)*, flipped the early question. Instead of predicting properties of *existing* polymers, he asked whether an artificial neural network could navigate the *fabrication* space of layer-by-layer ion-separation membranes — and then sit inside process optimization.

In *[Rational design of ion separation membranes](https://doi.org/10.1016/j.memsci.2018.10.013)* (2019), an ANN trained on an extensive LbL dataset predicted salt retention and water flux from synthesis protocols. Local optimization improved permeability; deterministic global multi-objective optimization traced the Pareto front of the retention–permeability trade-off. Hybrid models then coupled the network to mechanistic ion transport, giving physical insight rather than a black box.

The sequel papers pushed the scale further. *[Simultaneous rational design of ion separation membranes and processes](https://doi.org/10.1016/j.memsci.2020.117860)* co-designed module synthesis and plant layout. *[Multi-scale membrane process optimization with high-fidelity ion transport models through machine learning](https://doi.org/10.1016/j.memsci.2020.118208)* embedded ANN surrogates in deterministic global optimization so that nano-scale Nernst–Planck fidelity could inform plant-scale economics — without collapsing everything into heuristics.

The intellectual move is clear. Neural networks stopped being a curiosity for correlation and became a bridge across scales: from coating baths to Pareto fronts to process flowsheets. Where the 1994 paper asked “can we predict?”, Rall’s work asked “can we *decide*?”

## Act III — Embody: Daniel Felder and forgetful hardware

Daniel Felder’s thesis, *[Electrochemical charge transport in organic neuromorphic device networks](https://publications.rwth-aachen.de/record/964209)*, asks a different question still: what if the neural network is not only a model *of* soft matter, but is *made of* it?

Organic artificial synapses based on PEDOT:PSS store information as conductance states and process it in parallel, in aqueous electrolytes — closer to biology than silicon crossbars, and native to a membrane and soft-matter laboratory. In *[Coupled ionic–electronic charge transport in organic neuromorphic devices](https://doi.org/10.1002/adts.202100492)*, high-resolution transport models (with Deniz Rall among the coauthors) made that electrochemistry explicit.

But organic synapses forget. Parasitic reactions drive self-discharge; programmed weights drift. Felder’s answer was not to wish the non-ideality away. It was algorithm–hardware co-design.

*[Reminding forgetful organic neuromorphic device networks](https://doi.org/10.1088/2634-4386/ac9c8a)* showed how reminder pulses and network architecture can compensate for decay — and how surprisingly long a small classifier can stay accurate even while weights wander. *[Spiking neural networks compensate for weight drift in organic neuromorphic device networks](https://doi.org/10.1088/2634-4386/accd90)* went further: always-on spiking learning does not merely tolerate self-discharge; it can *use* continuous relearning to reinforce forgotten states. Forgetfulness becomes a feature of the learning regime rather than only a defect of the device.

Here the arc closes with a twist. We began by using neural networks to understand membranes. We ended by using membrane science — mixed ionic–electronic conductors, electrolytes, charge-transport modeling — to understand neural networks as physical objects.

## One laboratory, three meanings of “neural”

Read together, the three chapters are not a straight line of “better AI.” They are a change in what the network *is*:

| Era | Role of the network | Object of care |
|---|---|---|
| 1994 | Surrogate for unknown structure–property maps | Polymer spectra → permeability |
| Rall ~2019–2020 | Surrogate and optimizer inside membrane–process design | Synthesis protocols ↔ plant performance |
| Felder ~2022–2023 | Physical substrate whose imperfections reshape algorithms | PEDOT:PSS synapses, spikes, drift |

What ties them is a laboratory habit: treat transport and soft matter as first-class citizens of computation. Spectra encode chemistry. Layer-by-layer protocols encode ion selectivity. Conductance states encode synaptic weight — until electrochemistry rewrites them.

That habit is why this story belongs on a membrane-science website, not only on a machine-learning one. Neural networks entered our work as a mathematical tool. They stayed because membranes and ion conductors keep offering new places for learning to happen — in models, in process design, and finally in devices that forget and relearn in wet, soft hardware.

From spectra to synapses, the question never really was whether neural networks belong in membrane science. It was how far we were willing to let the membrane into the network.

#NeuralNetworks
#MachineLearning
#MembraneScience
#LayerByLayer
#NeuromorphicComputing
#OrganicElectronics
#IonTransport
#AlgorithmHardwareCoDesign
