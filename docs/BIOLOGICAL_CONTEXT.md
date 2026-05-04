# Biological Context

## The Biological Question

Cells use electrochemical gradients across their membranes to power essential biological process. In bacteria this gradient is called the proton-motive force (PMF). PMF powers ATP synthesis, flagellar motility, transport, and other essential processes.

This study uses _E. coli_ as a model organism to investigate how the PMF responds to a hyperosmotic shock.

## Why Osmotic Shock Matters

Bacteria often encounter sudden changes in external osmolarity. When the surrounding solution becomes more concentrated, cells experience rapid water efflux, leading to osmotic stress that alters cell volume, turgor pressure, membrane tension, and metabolism. However, there has been a knowledge gap in understanding how this affects cellular bioenergetics.

The key insight here is that osmotic shock not only induces physiological changes in the cell, but also leads to a rapid and reversible loss of the PMF, thereby linking environmental stress to bioenergetics.

## Measuring PMF in bacteria is technically challenging

Unlike in neuroscience, patch-clamp techniques are not feasible in bacterial cells due to their small size. Additionally, in gram-negative bacteria like _E. coli_, the presence of an outer membrane further restricts the application of these techniques, limiting our understanding of bacterial electrophysiology. However, the bacterial flagellar motor can be used as a tool to address this methodological challenge.

## Method 1: Using the bacteria flagellar motor as PMF reporter.

The rotation speed of the flagellar motor increases monotonically with the PMF, allowing changes in PMF to be inferred by measuring rotation speed, which provides a precise, global readout of the cell’s energetic state.

To measure rotation speed, a microscopic bead is attached to a sheared flagellar filament, and its rotation is tracked at high temporal resolution to obtain a readout of the PMF.

## Method 2: TMRM as a membrane potential sensor

We use TMRM to independently verify our bead assay results. If both motor speed and TMRM fluorescence decreases after an osmotic shock, this strengthens the interpretation that the motor slowdown reflects a global drop in membrane potential rather than a motor-specific artifact.

TMRM is a fluorescent dye used as an independent indicator of membrane potential. It follows a Nernstian distribution, where cells with a polarized membrane accumulate more TMRM molecules, resulting in increased fluorescence. When cells become depolarized, less dye accumulates, leading to a decrease in signal. By tracking changes in cellular fluorescence, we can indirectly report changes in membrane potential.

## Accounting for viscosity

Adding sucrose or sorbitol increases the viscosity of the medium. A bead rotating in a
more viscose liquid should slow down even if the motor produces the same torque.

The paper therefore compares the expected decrease in motor speed due to increased viscosity with the observed results. We find that the reduction in rotation speed cannot be fully explained by viscosity alone, supporting the conclusion that the PMF decreases during osmotic shock.

## Testing different experimental conditions

- Sucrose and sorbitol test whether the effect is specific to one osmolyte.
- Sodium phosphate buffer tests whether immediate potassium uptake is required.
- Clockwise-locked motors test whether the response depends on motor rotation
  direction or rotor conformation.
- Sustained-shock adaptation data show that motor speed partially recovers over
  minutes, consistent with cellular adaptation and PMF restoration.
- Cell-area measurements show the physical shrinkage response that accompanies
  the energetic response.

## Main Interpretation

Hyperosmotic shock rapidly depolarizes _E. coli_. The flagellar motor detects
this as a fast motor-speed decrease, TMRM supports the membrane-potential
interpretation, and longer recordings show partial recovery as cells adapt.
