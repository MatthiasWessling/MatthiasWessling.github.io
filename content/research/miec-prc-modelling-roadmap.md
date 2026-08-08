+++
title = 'Modelling roadmap: MIEC, physical reservoir computing, and emergence in soft matter'
date = '2026-08-08'
draft = false
summary = 'Inventory and progress map of local coding campaigns that treat permeable soft matter—mixed ionic–electronic beads, colloidal assemblies, pore networks and ionic circuits—as physical reservoirs whose constitutive state stores and transforms history.'
abstract = 'Inventory and progress map of local coding campaigns that treat permeable soft matter—mixed ionic–electronic beads, colloidal assemblies, pore networks and ionic circuits—as physical reservoirs whose constitutive state stores and transforms history.'
authors = ['Matthias Wessling']
publication = 'Research overview'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/ink-miec-prc-roadmap.png'
image_alt = 'Abstract black-ink drawing of porous beads, a contact network, a readout waveform, and soft colloidal trails'
tags = ['MIEC', 'physical reservoir computing', 'soft matter', 'information materials', 'emergence', 'pore network', 'PEDOT:PSS', 'modelling roadmap']
+++

This note maps the modelling and coding activity underway for *information materials*: soft, permeable systems whose transport, charge and contacts co-evolve so that recent input is retained as distributed physical state and can be read out linearly—physical reservoir computing (PRC). The scientific centre is mixed ionic–electronic conductors (MIEC), especially porous PEDOT:PSS:PEI beads and networks (PERMEAC), flanked by soft-matter colloidal reservoirs and electrokinetic pore-network substrates. Related experimental and materials context appears in *[PEDOT:PSS](/research/pedot/)*, *[neural networks to neuromorphic devices](/research/from-spectra-to-synapses/)*, and *[spatio-temporal phenomena](/research/spatio-temporal-phenomena/)*.

Progress percentages below are **engineering–scientific maturity estimates** toward reproducible, evidence-tagged PRC claims on that substrate—not completion of the wider PERMEAC vision. Evidence language follows the lab stack: *validated*, *smoke-tested*, *invalid* (do not cite), *proposed*.

## Scientific question

Can **physical materials** act as reservoir computers—fixed nonlinear dynamics driven by an input, with only a **linear readout** trained—and can that capacity be *designed* through chemistry, geometry and contact topology?

| Axis | Role |
|---|---|
| Constitutive state | Ion occupancy, oxidation fraction, double-layer charge, phase/order parameters |
| Architecture | Bead / film / fiber; pore networks; contact graphs; coupled colloidal ensembles |
| Computation | Memory (lag-*k*), NARMA, chaotic forecasting; ridge readout; multi-seed statistics |
| Failure mode to avoid | *Physical hallucination*: consistent, documented conclusions not grounded in correct physics or protocol |

## Programme map

Five early PRC tracks (July 2026 synthesis) plus later electrokinetic and ionic-circuit arms:

| Cluster | Local campaigns | Links forward to |
|---|---|---|
| **Framing** | ERC Modelling overview; PERMEAC B1/B2 writing | All tracks |
| **MIEC / Permeac** | Charge bead 2 (v1–v4); Charge bead + RC transfer | Silberstein crosswalk; PERMEAC proposal |
| **Soft-matter emergence** | Connected Bell (Dzubiella); Connected RC Bechinger; Colloidal RC 2 (swarmalator) | Network-of-reservoirs; metrics hygiene |
| **Ionic networks & circuits** | Gupta PNM; Mani–Alizadeh EKRC; Silberstein Ionics; Electroshock LMM | Bead-bed / motif design; packed-bed RC |
| **Substrate tools (idle)** | spnpFoam; Lovamap; Pore size; Wagner polymer LAMMPS | Future digital twins |

## Progress by coding project

Degree of progress is given as a percentage of a *research-ready* PRC campaign on that substrate (validated physics or published benchmark where applicable, multi-seed RC metrics, evidence registry, honest invalidation of failed claims). Sibling checkouts of the same science line are collapsed.

| Project (local folder) | Role | Progress | Evidence tier | Status |
|---|---|---|---|---|
| **Charge distribution bead 2 liquid reservoir computing** | Primary MIEC PDE → chemistry → geometries → topology-first `ContactGraph` (v1–v4) | **80%** | Lag-5 **validated** (median NRMSE ≈ 0.30, 20/20 seeds); MG claims **invalid** | Warm — canonical Track A |
| **Charge distribution bead** | Parallel MIEC bead + Da×τ regime maps; Dzubiella→MIEC transfer harness | **70%** | v1 PDE **validated**; RC transfer Stage 0–1 documented | Warm — sibling of bead 2 |
| **Connected RC Bechinger** | Active-colloid RC (Zenodo port); network-of-reservoirs ablations | **85%** | Lorenz R² ≈ 0.97–0.98 sim+exp **validated**; pre-v3 MG **invalid** | Warm — strongest soft-matter benchmark |
| **Connected Bell Dzubiealla** | Göth–Dzubiella colloids + connected ESN bead grids | **65%** | Tier-1 physics + lag-5 **validated**; N=72 **smoke**; ring +7% MC **smoke** | Warm — *de facto* Dzubiella home |
| **Charge Distribution Beads as RC based on Dzubiealla learnings** / **Bell with backgroundDzubiealla** | Sibling Dzubiella forks + transfer roadmaps | **60%** | Same science line as Connected Bell; treat as archives | Warm archive — do not score separately for science |
| **Gupta 2024 Network model ionic transport** | Henrique/Gupta transmission-line PNM; printed-electrode motifs; MC / NARMA | **75%** | Spine A closed; Spine B freeze trend **validated** with protocol caveats | Active/warm — strongest PNM–RC line |
| **Multi-scale porous media Mani Alizadeh** | Alizadeh–Mani multi-scale electrokinetic PNM → RC datasets | **55%** | Smoke RC + Fig campaigns progressing; full paper match partial | Active — validated-smoke → research-ready |
| **Silberstein ionic complexity hierarchical ciruits** | OpenModelica Ionics ladders/motifs as PRC; NARMA / GA | **50%** | NARMA foothold **smoke**; multi-seed / GA still required | Active |
| **Electroshock RC Bazant Mani** | 1D leaky-membrane packed-bed (Dydek–Bazant) + multi-electrode RC | **40%** | Analytics / I–V **smoke**; figure digitization open | Warm early bridge |
| **Colloidal reservoir computing 2** | Swarmalator sandbox for cheap (J,K) RC maps | **35%** | Pipeline works; 2/36 pairs beat baseline | Prototype sandbox |
| **Bipo EquivCir Modelling** | Bipolar-membrane EIS equivalent-circuit sweeps | **25%** | Nyquist OAT prototype; not yet PRC | Micro-project |
| **Chronopotentiometry for multi-ion mixtures** | Sand / two-ion membrane chronopotentiometry roadmap | **15%** | Classical scripts; MoL solver **proposed** | Exploration |
| **ERC Modelling overview** | Cross-repo PhD programme summary + scorecard | **90%** *(docs)* | Mature synthesis (2026-07-13); needs Gupta/Mani/Silberstein refresh | Hub |
| **Reservoir Computing Bootcamp** | Digital ESN curriculum (metrics hygiene) | **95%** *(curriculum)* | Teaching notebooks mature | Reference literacy |
| **MOOC Intelligent Physical Systems** | Course spine: dynamics → PRC → transport-as-computation | **40%** | Modules scaffolded; materials curation ongoing | Education |
| **Permeac - editing** / **ERC Permeac Writing** | ERC Part B1/B2 emergence synopsis and proposal text | **70%** *(writing)* | Active Aug 2026; claim↔workspace maps | Writing |
| **robjwags DiscreteDynamicPolymerModeling** | Wagner mesoscale dynamic elastomers/gels (LAMMPS) | **10%** *(local)* | Upstream mature; not wired into RC | Adjacent reference |
| **spnpFoam** / **Lovamap** / **Pore size and retention** | SNPP CFD, void→PNM geometry, UF retention | **20%** | Useful substrate tools; not current PRC campaigns | Reference |

### How to read the percentages

| Band | Meaning |
|---|---|
| **≥75%** | Research-ready core: reproducible physics or published benchmark + multi-seed RC with evidence tags |
| **50–74%** | Strong campaign culture; some claims still smoke-tested or incomplete |
| **25–49%** | Working pipeline / validated-smoke physics; PRC claims thin or early |
| **&lt;25%** | Exploration, roadmap, or unused reference tool |

## Roadmap — Immediate / Medium / Long-term

### Immediate

- [ ] Refresh the ERC Modelling overview scorecard with Gupta PNM, Mani–Alizadeh, Electroshock and Silberstein (post–2026-07-13).
- [ ] Consolidate Dzubiella forks to one canonical checkout for citation (Connected Bell) and mark siblings as archives.
- [ ] Promote one MIEC nonlinear task (τ-matched NARMA or fair MG with correct `dt`) beyond lag-5 memory.
- [ ] Finish Silberstein multi-seed landscape before motif-GA scientific claims.
- [ ] Digitize Dydek figures and close Electroshock analytics→RC segment ablation.

### Medium

- [ ] Cross-platform ranking table at the **metrics layer only** (shared NRMSE / R² / memory capacity; no merged ODE stacks).
- [ ] Couple Connected Bell grids to full Dzubiella physics (or retire synthetic-only claims).
- [ ] Quantitative Mani–Alizadeh paper-figure overlays; license-safe packaging.
- [ ] Explicit MIEC bead ↔ Silberstein Ionics crosswalk campaigns (shared tasks, shared evidence tags).
- [ ] Wire Wagner polymer bond-exchange dynamics into an RC metrics harness if soft mechanical memory is in scope.

### Long-term

- [ ] Experiment-matched 3D bead-bed / contact-network digital twin for PERMEAC.
- [ ] Heterogeneous network-of-reservoirs claims that survive shuffle controls and multi-task stats.
- [ ] Optical / acoustic strands of PERMEAC, if retained in the proposal, need dedicated codes—not yet present as modelling campaigns.
- [ ] Publication packages that separate **validated**, **smoke-tested** and **invalid** artefacts in SI.

## What was achieved vs not

**Achieved.** Multi-material PRC programme with working code, reproduced published benchmarks (Bechinger Lorenz; Dzubiella Tier-1 physics), MIEC v1–v4 lag-5 memory, mature journal/evidence culture, and first honest cross-platform comparisons. Pore-network (Gupta, Mani–Alizadeh) and hierarchical ionic-circuit (Silberstein) arms extend the substrate beyond colloids and single beads.

**Not achieved.** Publication-grade Mackey–Glass on physical substrates; reliable scale-up of Dzubiella RC to large *N*; experiment-matched 3D MIEC assemblies; optical/acoustic modelling strands; polymer bond-memory RC. Cross-platform “which material computes best” rankings remain readout-dependent.

**Operating doctrine.** Failures (wrong presets, leaky globals, one-line generator bugs, trivial MG with missing `dt`) were as informative as successes. Evidence tagging and subprocess isolation are deliverables of the programme, not bureaucracy.

## Reading order

| Priority | Document | Local project |
|---|---|---|
| 1 | `docs/phd_programme_summary.md` | ERC Modelling overview |
| 2 | `docs/phd_introductory_paper.md` | Connected RC Bechinger |
| 3 | `docs/lessons_learned_RC_history.md` | Dzubiella / Connected Bell line |
| 4 | `docs/project_history_and_validation.tex` | Charge distribution bead 2 |
| 5 | `docs/lessons_learned_mackey_glass_sim.md` | Connected RC Bechinger |
| 6 | `version_4/docs/reference/lessons_synthesis.md` | Charge distribution bead 2 |

## Scope note

Folders under `~/Coding` devoted to crawling, bibliography tooling, ChemE LCA, DFG evaluation Monte Carlo, or generic LAMMPS dumps are **out of scope** for this roadmap. Neuroscience literacy (NEURON, Brian2, Würzburger notes) is conceptual adjacency only. This page inventories **modelling campaigns** for MIEC, PRC and emergence in soft information materials as of August 2026.
