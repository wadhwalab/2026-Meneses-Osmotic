# Glossary

**Adaptation**: Recovery or adjustment after the initial shock. In this study,
motor speed partly recovers during sustained osmotic stress.

**Baseline**: The pre-shock period used as the reference for normalization.
Values are often expressed relative to this period.

**Bead assay**: An experiment where a small bead is attached to a bacterial
flagellar filament so motor rotation can be measured by tracking bead motion.

**CCW / CW**: Counterclockwise and clockwise rotation directions of the
flagellar motor.

**Cell area**: The two-dimensional area of a segmented cell in microscope
images. It is reported in pixels in the curated data.

**Depolarization**: A reduction in membrane potential. In this study,
depolarization means the electrical component of PMF decreases after osmotic
shock.

**DFF / DeltaF/F0**: A baseline-normalized fluorescence change. A value of `0`
means no change from baseline; negative values mean fluorescence decreased.

**DeltaA/A0**: A baseline-normalized area change. Negative values mean the cell
area decreased relative to its pre-shock baseline.

**Frame**: One image or time point in an image sequence. For bead data, `frame`
preserves the 300 Hz reference used by earlier analysis code.

**Hyperosmotic shock**: A sudden increase in the concentration of solutes
outside the cell. Water tends to leave the cell, and the cell experiences
osmotic stress.

**Manifest**: A metadata table that explains where each data trace lives and
what condition it belongs to.

**Membrane potential**: The electrical voltage difference across the cell
membrane. It is a major component of PMF under these experimental conditions.

**Osmolarity**: A measure of total solute concentration in a solution. Larger
osmolarity differences mean stronger osmotic shocks.

**Osmolyte**: A solute added to change osmolarity, such as sucrose or sorbitol.

**Parquet**: A compact table file format used for the canonical time-series
data. It is efficient for computation but less familiar than CSV.

**PMF, proton motive force**: The electrochemical gradient that stores energy
across the bacterial inner membrane. It powers the flagellar motor and other
cellular processes.

**SE / SEM, standard error of the mean**: A measure of uncertainty in a mean
trace. It is often shown as a shaded band around a population-average line.

**Shock period**: The time window when cells are exposed to the hyperosmotic
medium.

**Stator**: The motor component that conducts ions and generates torque.

**Tau**: A fitted timescale. Smaller tau means a faster change; larger tau means
a slower change.

**TMRM**: Tetramethylrhodamine methyl ester, a fluorescent dye used here as a
membrane-potential indicator.

**Track ID**: Identifier for one tracked cell in fluorescence or cell-area data.

**Viscosity**: A measure of how resistant a fluid is to flow. Higher viscosity
makes bead rotation harder, so viscosity must be considered when interpreting
motor-speed changes.

**Viscosity correction**: An estimate of how much motor speed should decrease
from increased fluid viscosity alone. Any additional slowdown points to a
biological change such as reduced PMF.
