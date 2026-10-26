+++
title = 'Simulating membrane fouling: from DLA to pore-scale dynamics'
date = '2026-10-25'
draft = false
summary = 'Fouling as deposit architecture that redirects transport—from stochastic morphology on explicit pores to CFD–DEM of colloidal events, soft-cake history, multi-pore communication and particle shape—with evidence boundaries and complementary simulation literature.'
abstract = 'Fouling as deposit architecture that redirects transport—from stochastic morphology on explicit pores to CFD–DEM of colloidal events, soft-cake history, multi-pore communication and particle shape—with evidence boundaries and complementary simulation literature.'
authors = ['Matthias Wessling']
publication = 'Research overview'
publication_year = '2026'
paper_url = ''
featured = true
image = '/images/blog/ink-dla-membrane-fouling.png'
image_alt = 'Abstract black-ink drawing of DLA filter-cake growth on a membrane pore under crossflow'
tags = ['fouling', 'simulation', 'DLA', 'CFD-DEM', 'colloids', 'pore-scale', 'crossflow', 'backwashing', 'clogging', 'soft cakes']
+++

Membrane fouling is often reduced to a resistance that grows with time. That description is useful for process control, but it does not answer *where* particles stick, *how* a deposit redirects permeation, or *whether* cleaning reverses the same microscopic pathway. Group work on fouling simulation treats deposit location, shape, cohesion and local flow as part of the scientific problem: transport creates structure, and structure subsequently redirects transport. The line runs from early stochastic aggregation on an explicit membrane geometry to particle-resolved CFD–DEM of deposition, resuspension, soft-cake rearrangement, multi-pore communication and shape-dependent clogging. Later findings belong to the named author teams, not to a single investigator alone.

This note draws on an Undermind workspace overview of the group lineage and on a deep search that situates complementary pore-scale simulation literature (stochastic/Monte Carlo, CFD–DEM, LBM–DEM, communicating pores, shape effects). Claims are kept within the evidence boundaries of each study.

## Guiding questions

1. When flux decline looks similar in bulk, which microscopic deposit architectures are compatible with the observation?
2. How do DLVO, hydrophilicity and local hydrodynamics select adsorption versus resuspension at a pore?
3. Does backwashing reverse fouling as a hydraulic reset, or as cluster-scale multiphase dynamics?
4. How do neighboring pores communicate through shared deposits under crossflow?
5. How do soft-cake history and particle shape change clogging relative to hard spheres?

## Stochastic deposit morphology (2001)

*[Two-dimensional stochastic modeling of membrane fouling](https://doi.org/10.1016/S1383-5866(01)00138-1)* (Wessling, 2001) adapted diffusion-limited aggregation to particles depositing on an explicit membrane cross-section with a defined pore. Particles performed random walks (optionally biased for permeation or crossflow) and stuck with assigned membrane and aggregate sticking probabilities. Local resistance was estimated from Poiseuille scaling on the evolving pore diameter; cake and pore contributions were summed to relative flux.

Two results remain durable. First, aggregate density differed above pores versus flat regions, so flux decline was a spatially resolved morphological process rather than a single resistance term. Second, a linear inverse-flux–time relation—conventionally read as pore blocking—could appear in the simulation even when the deposit had not yet blocked the pore. Familiar curve shape alone is therefore not a reliable mechanism diagnosis. The model stated its own limits: sequential arrival, simplified flow bias, no deposit permeation, and eventual complete pore closure. It efficiently linked idealized morphology to filtration outcomes; it was not an experimentally validated quantitative predictor.

## Pore-scale colloidal events and backwash (Lohaus)

Johannes Lohaus advanced the problem from stochastic stickiness to resolved particle–fluid mechanics. *[What are the microscopic events of colloidal membrane fouling?](https://doi.org/10.1016/j.memsci.2018.02.023)* (Lohaus, Pérez, Wessling, 2018) used CFD–DEM in microfluidic pore-like geometries with particle–particle and particle–wall DLVO interactions. Simulations resolved capture in a secondary DLVO minimum, collision-assisted transition into the primary minimum, edge adsorption, downstream gliding, and cluster re-entrainment with possible re-attachment inside the pore structure. Inner pore geometry thus becomes an active cause of fouling behavior, not only a hydraulic boundary.

Evidence boundaries matter. Agreement with experiment was stronger for geometries with inner structure than for straight channels; fouling kinetics were faster in simulation than in experiment; smooth walls likely overestimated gliding; and the secondary-to-primary transition was inferred rather than directly imaged. Particle concentrations in the simulations were much higher than in the comparison experiments.

*[What are the microscopic events during membrane backwashing?](https://doi.org/10.1016/j.memsci.2020.117886)* (Lohaus, Stockmeier, Surray, Lölsberg, Wessling, 2020) paired pore-scale microfluidic visualization with CFD–DEM under reverse flow. Cleaning acts on clusters and bridges: they can break, remain partly attached, or rotate into lower-drag positions that shield material from the flow. Backwash is therefore not fouling run backward, and single-particle detachment models miss the structure being cleaned. Particle–membrane interaction dominated simulated backwash efficiency relative to particle–particle interactions. The experiment visualized seven pores while the simulation represented one pore at elevated concentration—quantitative experiment–model closure remained limited.

The thesis *[Multiphase dynamics of colloidal deposition and resuspension at membranes](https://publications.rwth-aachen.de/record/843415)* (2021) summarizes that program. *[On the balance of hydrophilicity and electrostatic interactions during particle filtration and backwash at microfiltration pores](https://doi.org/10.1016/j.memsci.2023.121640)* (Kalde, Lohaus, Musholt, Wessling, 2023) adds hydrophilicity versus electrostatics as competing wall boundary conditions for both filtration and cleaning.

## Soft-cake history (Lüken)

*[Particle movements provoke avalanche-like compaction in soft colloid filter cakes](https://doi.org/10.1038/s41598-021-92119-w)* (Lüken, Stüwe, Lohaus, Linkhorst, Wessling, 2021) imaged PEG microgel cakes and compared compression with CFD–DEM. During buildup, single-particle motion can trigger avalanche-like network rearrangements. Under pressure cycling, irreversible packing (void filling) is distinguishable from elastic deformation that recovers on relaxation. Compression therefore leaves structural memory in the cake. The study did **not** measure flux or cake resistance; the proposed link from internal rearrangement to filtration performance remains a clear next experiment—structure and permeation in the same campaign.

## Communicating pores and particle shape (Bräsel)

Berinike Bräsel extended the discrete picture from single-pore events to communicating pores and non-spherical particles. *[Evolution of particle deposits at communicating membrane pores during crossflow filtration](https://doi.org/10.1016/j.memsci.2023.121977)* (Bräsel, Yoo, Huber, Wessling, Linkhorst, 2023) simulated four rectangular pores sharing a crossflow channel (CFD–DEM, monodisperse spheres). Crossflow shaped where deposits formed (pore intrusion at low shear/high TMP versus back-entrance accumulation at higher shear); TMP affected compaction and resistance to removal; agglomerates at upstream pores could create dead zones that altered fouling at neighbors. Flux declined faster at higher TMP; high crossflow produced fluctuating recovery when agglomerates detached. Limits: four-pore domain (so local events exaggerate flux fluctuations), short simulated times (~80 ms), spherical monodisperse particles, and interaction parameters that promote agglomerates.

*[Transport and clogging dynamics of flexible rods in pore constrictions](https://doi.org/10.1039/d4sm00734d)* (Bräsel, Geiger, Linkhorst, Wessling, 2024) validated CFD–DEM for flexible rods: flexibility, confinement, approach angle and rod-to-pore size jointly shape trajectories and mechanical sieving. This is a single-particle mechanical-clogging study—not yet collective fouling, colloidal adhesion or cleaning. *[Shape-dependent fouling dynamics in a crossflow model pore system](https://doi.org/10.1016/j.memsci.2025.124849)* (Bräsel, Linkhorst, Wessling, 2025) extends shape into crossflow model pores; detailed mechanism claims await wider abstract/full-text use in secondary synthesis. The thesis *[Multidimensional filtration dynamics based on numerical insights from single-pore to multi-pore simulations](https://publications.rwth-aachen.de/record/1016404)* (2025) frames the program as narrowing the gap between pore-scale events and macroscopic filtration.

## Conceptual thread and evidence boundaries

| Stage | Representation | What becomes observable | Evidence boundary |
|---|---|---|---|
| Stochastic / DLA (2001) | Aggregate growth on explicit membrane geometry | Morphology–flux coupling; non-unique mechanism from flux curves | Idealized 2D sequential walks; not a quantitative plant predictor |
| CFD–DEM fouling (2018) | Discrete colloids + continuum fluid + DLVO | Adsorption, collision-assisted capture, gliding, cluster re-entrainment | Qualitative kinetics; smooth walls; high simulated concentration |
| CFD–DEM backwash (2020) | Reverse flow, cluster release/reorientation | Cleaning as multiphase dynamics, not a lumped reset | Few pores imaged vs one simulated; limited quantitative match |
| Soft cakes (2021) | Imaging + CFD–DEM of microgel cakes | Avalanche rearrangements; irreversible vs elastic compression | Structure observed; flux/resistance not measured |
| Multi-pore crossflow (2023) | Communicating pores under shear | Pore-to-pore deposit coupling; TMP vs crossflow roles | Small domain, short time, spheres only |
| Shape / flexibility (2024–2025) | Rods and shape-resolved fouling | Mechanical clogging pathways beyond spheres | Single-particle / model-pore stage; collective mixtures open |

This is not a simple “DLA was replaced by CFD–DEM” story. Stochastic models efficiently explore deposit statistics and flux evolution; particle-resolved models make specific forces and events testable. Both levels remain useful when assumptions and validation limits are explicit.

## Complementary simulation landscape

A deep search seeded on the papers above returned a dense complementary literature in the same conceptual lineage—methods that resolve deposit morphology or particle-level events rather than lumped cake correlations alone. Selected anchors:

- **Stochastic / Monte Carlo cake structure:** *[Cake Structure in Dead-End Membrane Filtration: Monte Carlo Simulations](https://doi.org/10.1089/109287502320963373)* (Kim & Hoek, 2002); *[A Stochastic Collision-Attachment-Based Monte Carlo Simulation of Colloidal Fouling](https://doi.org/10.1021/acs.est.0c04165)* (Liu et al., 2020) on foulant–clean-membrane versus foulant–fouled-membrane transitions and metastable flux.
- **Collective clogging and permeability fluctuations:** *[Collective dynamics of flowing colloids during pore clogging](https://doi.org/10.1039/c4sm00869c)* (Agbangla, Bacchin, Climent, 2014)—bridging, jamming and DLVO-dependent aggregate morphology at pore entrances.
- **Fouling–backwash cycles in dead-end microfiltration:** Ando and coauthors’ direct simulation of particulate flow and pore-size effects on fouling and backwash ([2010](https://doi.org/10.1252/jcej.10we031); [2012](https://doi.org/10.1016/J.MEMSCI.2011.11.051)).
- **Communicating / parallel pores:** *[Growth of clogs in parallel microchannels](https://doi.org/10.1103/PhysRevFluids.3.104301)* (Sauret et al., 2018)—coupled aggregate growth after stochastic clogging events.
- **Non-spherical cakes and CFD–DEM / LBM–DEM:** *[DEM-CFD study of the filter cake formation process due to non-spherical particles](https://doi.org/10.1016/j.partic.2020.01.003)* (Deshpande, Antonyuk, Iliev, 2020); *[LBM-DEM simulation of particle deposition and resuspension of pre-deposited dynamic membrane](https://doi.org/10.1016/j.powtec.2022.117637)* (Song et al., 2022); related microchannel fouling CFD–DEM ([Trofa et al., 2019](https://doi.org/10.1016/J.CEJ.2018.09.207)).
- **High-resolution pore clogging and erosion:** *[Mechanisms of Pore-Clogging Using a High-Resolution CFD-DEM Colloid Transport Model](https://doi.org/10.1007/s11242-024-02072-1)* (Liu, Shikhov, Arns, 2024); *[Clogging at pore scale and pressure-induced erosion](https://doi.org/10.1103/PhysRevFluids.3.074302)* (Jager, Mendoza, Herrmann, 2018).

These works do not replace the group lineage; they supply independent tests of bridging/jamming, parallel-pore coupling, shape-resolved cakes, cyclic cleaning and reduced-order upscaling—the natural citation set for contrast and complementarity.

## Challenges ahead

The central open problem is **predictive closure across scales**: turning resolved particle events into forecasts of flux, rejection, cleaning and cycle life without refitting to each case.

| Challenge | What needs resolving | A useful next test |
|---|---|---|
| Realistic geometry and flow | Ideal pores, smooth walls, coarse meshes | Couple measured 3D pore geometry with flow-resolved particle tracking and imaged deposit locations |
| Physicochemical realism | DLVO-only or omitted adhesion; soft/patchy surfaces | Independent surface/particle characterization; sensitivity to chemistry and ionic strength |
| From structure to performance | Rearrangement and compression not yet tied to measured resistance | Time-resolved deposit structure **and** permeation in one experiment |
| Fouling–cleaning cycles | Residual cluster structure as the next cycle’s initial condition | Repeated filtration/backwash with tracked residual architecture |
| Many pores and long times | Small domains exaggerate fluctuations | Pore-network or reduced models informed by particle-resolved runs, tested on larger arrays |
| Polydisperse, non-spherical, deformable foulants | Spherical monodisperse limits | Multi-particle mixtures of flexible/soft particles vs controlled model-pore clogging maps |
| Uncertainty and transfer | Contact and adhesion parameters poorly constrained | Report parameter uncertainty; predict on independent geometries/conditions |

## Assessment

The contribution of this program is a progression in what membrane fouling models are expected to explain. The early work made deposit morphology explicit and warned against inferring mechanism from flux curves alone. Later collaborative work resolved colloidal deposition and re-entrainment, treated backwashing as a collective structural process, and expanded the frame to soft cakes, interacting pores and flexible particles. The open frontier is quantitative prediction under realistic chemistry, geometry, particle diversity and repeated operation—demonstrated against independent experiments, not only fitted cases.

Related experimental and module-scale visualization of fouling as a distributed state is collected in *[Spatio-temporal phenomena in membranes and electrodes](/research/spatio-temporal-phenomena/)*. Source synthesis: Undermind workspace [Simulating membrane fouling: DLA to pore-scale](https://app.undermind.ai/projects/ca6d2978-e0eb-44ff-8d3c-99cb128d17a8) ([overview](https://app.undermind.ai/projects/ca6d2978-e0eb-44ff-8d3c-99cb128d17a8?path=/Matthias%20Wessling%20and%20membrane%20fouling%20modeling); [deep search](https://app.undermind.ai/projects/ca6d2978-e0eb-44ff-8d3c-99cb128d17a8?path=/Pore-scale%20fouling%20simulation%20beyond%20DLA%20CFD-DEM)).
