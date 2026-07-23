# Cross-Experiment Linking

How to link data from different experiments, assays, or modalities through
shared coordinates and custom indexes.

## Table of Contents

1. [The linking problem](#the-linking-problem)
2. [Pattern: shared coordinate in one Dataset](#shared-coordinate-dataset)
3. [Pattern: DataTree for heterogeneous assays](#datree-heterogeneous)
4. [Pattern: custom index for cross-experiment selection](#custom-index-cross)
5. [Pattern: merge and concat](#merge-concat)
6. [Real-world example: molecule characterization campaign](#real-world)

## The linking problem

A research program measures the same molecules across multiple assays:

- **Analytical chemistry**: DLS (size), zeta potential, HPLC (purity), MS (MW)
- **Binding assays**: ELISA (KD), BLI (kon/koff), SPR (affinity)
- **Cell-based assays**: flow cytometry (uptake), viability, potency
- **Functional readouts**: EC50/IC50, efficacy, dose-response
- **Genomics**: target expression, off-target profiling

Each assay produces data with its own shape and coordinate structure, but all
share the entity being characterized (e.g. `molecule`).

The challenge: keep all this data linked so queries like "find molecules with
DLS size < 100nm AND ELISA KD < 10nM AND flow cytometry uptake > 50%" work
without manual index-matching.

## Pattern: shared coordinate in one Dataset

When all assays can be expressed with compatible dimensions, put everything
in one Dataset:

```python
ds = xr.Dataset(coords={"molecule": mol_ids})

# Analytical chemistry
ds = ds.assign({
    "hydrodynamic_diameter_nm": (["molecule", "replicate"], dls_data),
    "zeta_potential_mv": (["molecule", "replicate"], zeta_data),
    "purity_percent": (["molecule"], hplc_purity),
})

# Binding
ds = ds.assign({
    "kd_nm": (["molecule", "target"], kd_data),
    "kon_per_ms": (["molecule", "target"], kon_data),
})

# Cell-based
ds = ds.assign({
    "uptake_percent": (["molecule", "cell_line", "replicate"], uptake_data),
    "ec50_um": (["molecule", "cell_line"], ec50_data),
})

# Query across all assays -- one line.
# NOTE: .drop_vars() after .sel() strips the leftover coordinate so the
# single-indexer results align cleanly inside the combined boolean mask.
promising = ds.where(
    (ds.hydrodynamic_diameter_nm.mean("replicate") < 100)
    & (ds.kd_nm.sel(target="EGFR").drop_vars("target") < 10)
    & (ds.uptake_percent.sel(cell_line="HEPG2").drop_vars("cell_line").mean("replicate") > 50),
    drop=True,
)
```

**When this works**: all data variables can share the `molecule` dimension
plus per-assay sub-dimensions (replicate, target, cell_line, etc.).

**When this breaks**: assays produce fundamentally incompatible shapes (e.g.
HPLC chromatograms with 1000 peaks per molecule vs. scalar EC50 values). Use
DataTree instead.

## Pattern: DataTree for heterogeneous assays

When assays produce data on incompatible grids, use `DataTree` -- each assay
is a tree node, sharing common coordinates via inheritance:

```python
import xarray as xr

# Root with shared `molecule` coordinate
root = xr.Dataset(coords={"molecule": mol_ids})

# Each assay is a node with its own dims
dls_ds = xr.Dataset(
    {"diameter_nm": (["molecule", "replicate", "time_s"], dls_timeseries)},
    coords={"molecule": mol_ids, "replicate": ["r1", "r2", "r3"], "time_s": np.linspace(0, 300, 100)},
)

hplc_ds = xr.Dataset(
    {"signal_au": (["molecule", "retention_min"], hplc_chromatograms)},
    coords={"molecule": mol_ids, "retention_min": np.linspace(0, 30, 1500)},
)

elisa_ds = xr.Dataset(
    {"od450": (["molecule", "concentration_nm", "replicate"], elisa_data)},
    coords={
        "molecule": mol_ids,
        "concentration_nm": np.logspace(-1, 3, 12),
        "replicate": ["r1", "r2", "r3"],
    },
)

flow_ds = xr.Dataset(
    {"fluorescence": (["molecule", "cell_line", "event"], flow_events)},
    coords={
        "molecule": mol_ids,
        "cell_line": ["HEPG2", "HEK293", "primary"],
        "event": np.arange(10000),
    },
)

tree = xr.DataTree.from_dict({
    "/": root,
    "/characterization/dls": dls_ds,
    "/characterization/hplc": hplc_ds,
    "/bioassays/elisa": elisa_ds,
    "/bioassays/flow_cytometry": flow_ds,
})
```

### Accessing nodes

Get the `Dataset` at a node with the **`.ds` attribute** -- never subscript a
`"/ds"` path suffix (that looks for a child node literally named `"ds"` and
raises `KeyError`):

```python
# Path syntax -- .ds attribute returns the Dataset
tree["/characterization/dls"].ds
tree["/bioassays/binding"].ds

# Dot syntax (equivalent)
tree.characterization.dls.ds

# Both return the same data
assert tree["/characterization/dls"].ds.equals(tree.characterization.dls.ds)
```

### Tree-wide selection

The headline feature: one `.sel()` propagates to **every** node. No manual
index-matching across assays.

```python
# Slice all nodes for one molecule in a single call
tree.sel(molecule="LNP_007")

# Or a list of molecules (e.g. train/test split, or cross-assay query hits)
tree.sel(molecule=hit_molecules)
```

### Coordinate inheritance (deep tree)

When the tree has a `"/"` root, child nodes **inherit** the root's coordinates.
The `molecule` coordinate defined once at the root is visible in every child
without duplication:

```python
assert (tree["/characterization/dls"].ds.molecule.values == tree.ds.molecule.values).all()
```

> **Flat vs deep:** a *flat* tree (no `"/"` root) has each sibling carry
> `molecule` independently -- fine for mostly-compatible assays. A *deep* tree
> (root defines the shared coordinate) is for **incompatible** grids where one
> `Dataset` would broadcast to huge NaN-filled arrays. See
> [data-structure-design.md](data-structure-design.md).

## Pattern: custom index for cross-experiment selection

When experiments share a derived relationship (e.g. dose-response curves
measured at different time points), use a custom index to link selection
across experiment boundaries.

### Example: concentration-time linking

Dose-response data measured at multiple time points. The concentration axis
and time axis are linked: selecting a concentration range should constrain
the time axis to measurements taken at that concentration.

```python
# Build a DimensionInterval linking concentration and time
ds = ds.drop_indexes(["time_hr", "concentration_um"]).set_xindex(
    ["time_hr", "concentration_intervals", "time_intervals", "concentration_um"],
    DimensionInterval,
)

# Select a concentration window -- time auto-constrained
ds.sel(concentration_intervals=100)  # all data at ~100uM, across time
```

## Pattern: merge and concat

### Merge: combine datasets sharing coordinates

```python
# Two datasets with different variables but same molecules
analytical = xr.Dataset({"diameter": (["molecule"], dls), ...})
biological = xr.Dataset({"ec50": (["molecule"], ec50), ...})

# Merge by shared molecule coordinate
combined = xr.merge([analytical, biological])
# Now both diameter and ec50 are in one Dataset, aligned by molecule
```

### Concat: stack datasets along a new dimension

```python
# Multiple batches, same assays
batch1 = xr.Dataset({"ec50": (["molecule"], ec50_batch1)}, ...)
batch2 = xr.Dataset({"ec50": (["molecule"], ec50_batch2)}, ...)

# Concatenate along batch dimension
all_batches = xr.concat([batch1, batch2], dim="batch")
# Assign batch labels
all_batches = all_batches.assign_coords(batch=["batch_1", "batch_2"])
```

### Alignment during merge/concat

```python
# Inner join (intersection of molecules) -- default
combined = xr.merge([analytical, biological])  # only molecules in both

# Outer join (union, NaN for missing)
combined = xr.merge([analytical, biological], join="outer")

# Exact join (error if mismatch)
combined = xr.merge([analytical, biological], join="exact")
```

## Real-world example: molecule characterization campaign

A full multi-assay molecule characterization campaign, organized as a
DataTree with progressive accumulation:

```python
# Root: molecule registry
root = xr.Dataset(
    coords={
        "molecule": [f"mol_{i:03d}" for i in range(50)],
        "batch": ["batch_a", "batch_b"],
    },
    data_vars={
        "smiles": (["molecule"], smiles_strings),
        "mw_da": (["molecule"], molecular_weights),
    },
)

# Analytical characterization node
analytical = xr.Dataset(
    {
        # DLS: diameter timeseries (size stability)
        "dls_diameter_nm": (["molecule", "batch", "time_min"], dls_data),
        # HPLC: purity
        "purity_percent": (["molecule", "batch"], purity),
        # MS: observed mass
        "observed_mass_da": (["molecule"], masses),
    },
    coords={
        "molecule": mol_ids,
        "batch": ["batch_a", "batch_b"],
        "time_min": np.linspace(0, 60, 30),
    },
)

# Bioassay node
bioassay = xr.Dataset(
    {
        # ELISA: dose-response OD readings
        "od450": (["molecule", "target", "concentration_nm", "replicate"], elisa_data),
        # Flow cytometry: per-event fluorescence
        "uptake_mfi": (["molecule", "cell_line", "event"], flow_data),
    },
    coords={
        "molecule": mol_ids,
        "target": ["EGFR", "HER2", "CD20"],
        "concentration_nm": np.logspace(-1, 3, 8),
        "replicate": ["r1", "r2", "r3"],
        "cell_line": ["HEPG2", "HEK293"],
        "event": np.arange(5000),
    },
)

# Derived estimates node
derived = xr.Dataset(
    {
        # 4PL fit results
        "ec50_um": (["molecule", "target", "cell_line"], ec50_estimates),
        "ec50_std": (["molecule", "target", "cell_line"], ec50_stds),
        "hill_coefficient": (["molecule", "target"], hill_coeffs),
        # Bayesian KD estimates
        "kd_nm": (["molecule", "target"], kd_means),
        "kd_nm_hdi_3pct": (["molecule", "target"], kd_lower),
        "kd_nm_hdi_97pct": (["molecule", "target"], kd_upper),
    },
    coords={
        "molecule": mol_ids,
        "target": ["EGFR", "HER2", "CD20"],
        "cell_line": ["HEPG2", "HEK293"],
    },
)

# Build tree
tree = xr.DataTree.from_dict({
    "/": root,
    "/characterization": analytical,
    "/bioassays/raw": bioassay,
    "/bioassays/derived": derived,
})

# Cross-assay query (.drop_vars() keeps the two .sel() results aligned)
promising_molecules = derived.where(
    (derived.ec50_um.sel(target="EGFR").drop_vars("target") < 1.0)
    & (derived.kd_nm.sel(target="EGFR").drop_vars("target") < 10),
    drop=True,
).molecule.values

# Pull analytical data for those molecules (.ds attribute, then .sel)
analytical_promising = tree["/characterization"].ds.sel(molecule=promising_molecules)
```
