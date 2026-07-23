# Data Structure Design for Linked Data

How to map real-world experimental data onto xarray dimensions, coordinates,
and data variables so that everything stays linked through shared coordinates.

## Table of Contents

1. [Core principle: coordinates are the linkage](#core-principle)
2. [Design workflow](#design-workflow)
3. [Progressive accumulation](#progressive-accumulation)
4. [Dataset vs DataTree](#dataset-vs-datatree)
5. [Coordinate design patterns](#coordinate-design-patterns)
6. [Metadata and units](#metadata-and-units)
7. [Storage formats](#storage-formats)

## Core principle

Every data variable in a Dataset shares the same coordinate registry. When
you select, compute, or store, xarray keeps everything aligned by coordinate
**names and values** -- not array positions. This eliminates manual
index-matching across files.

```
Dimension:  molecule (50)    treatment (3)    replicate (3)
                │                │                │
    ┌───────────┼────────────────┼────────────────┤
    │ expression_level   (molecule, treatment, replicate)
    │ ec50               (molecule,)
    │ features           (molecule, feature)
    │ train_mask         (molecule, split_type)
    └─────────────────────────────────────────────────
```

All four data variables are linked through the shared `molecule` coordinate.
Selecting `molecule="mol_7"` propagates to all variables automatically.

## Design workflow

### Step 1: Identify entities and factors

List the things you measure and the experimental factors:

```python
# Entities (what you measure on)
molecules = [f"mol_{i:03d}" for i in range(1, 51)]  # 50 candidate molecules

# Experimental factors (conditions you vary)
treatments = ["control", "low_dose", "high_dose"]
replicates = ["r1", "r2", "r3"]
time_points = [0, 2, 6, 12, 24, 48]  # hours
```

### Step 2: Assign dimensions and coordinates

Each entity/factor becomes a dimension with a coordinate:

```python
coords = {
    "molecule": molecules,
    "treatment": treatments,
    "replicate": replicates,
    "time_point": time_points,
}
```

### Step 3: Create the base Dataset with raw measurements

```python
shape = (len(molecules), len(treatments), len(replicates), len(time_points))
ds = xr.Dataset(
    {"signal": (list(coords.keys()), np.random.lognormal(2, 1, shape))},
    coords=coords,
)
```

### Step 4: Progressively add derived data

```python
# Per-molecule estimates (1-D, aligned by molecule)
ds = ds.assign({"mean_signal": ds["signal"].mean(dim=["treatment", "replicate", "time_point"])})

# Features along a new dimension
ds = ds.assign({"features": (["molecule", "feature"], feature_matrix)})
ds = ds.assign_coords(feature=["mw", "logp", "hbd", "hba", "tps"])
```

## Progressive accumulation

Build incrementally -- start with raw data, add layers as analysis develops:

```
Stage 1: Raw measurements    →  ds = xr.Dataset({"raw": ...})
Stage 2: Derived estimates   →  ds = ds.assign({"ec50": ..., "kd": ...})
Stage 3: Computed features   →  ds = ds.assign({"features": ...})
Stage 4: Model outputs       →  ds = ds.assign({"predictions": ..., "train_mask": ...})
Stage 5: Uncertainty         →  ds = ds.assign({"ec50_posterior": (["molecule", "target", "draw"], samples)})
```

Each stage reuses the same coordinates. No re-alignment needed.

### Storing uncertainty inline (a `draw` dimension)

A powerful pattern: store the full posterior from a Bayesian fit (PyMC/ArviZ)
as an extra `draw` dimension aligned to the same coordinates as the point
estimates. Selecting a molecule then carries its uncertainty along for free.
Keep posteriors that belong to different assays in separate `Dataset`s or
DataTree nodes so their `draw` dimensions don't collide.

```python
n_draws = trace.posterior.sizes["chain"] * trace.posterior.sizes["draw"]
ds = ds.assign(
    {"ec50_nm": (["molecule", "target"], ec50_estimates),  # point estimate
     "ec50_nm_posterior": (["molecule", "target", "draw"], ec50_full_post)},
).assign_coords(draw=np.arange(n_draws))

# selecting a molecule carries the whole posterior with it
ds.sel(molecule="LNP_007").ec50_nm_posterior  # (target, draw)
```

### Full example

```python
import numpy as np
import xarray as xr

# Stage 1: Raw expression data
ds = xr.Dataset(
    {"expression": (["gene", "condition", "replicate"], np.random.lognormal(5, 1, (100, 3, 3)))},
    coords={
        "gene": [f"gene_{i}" for i in range(100)],
        "condition": ["wt", "ko", "rescue"],
        "replicate": ["a", "b", "c"],
    },
)

# Stage 2: Fold-change estimates (aligned by gene + condition)
mean_expr = ds["expression"].mean(dim="replicate")
wt_expr = mean_expr.sel(condition="wt")
ds = ds.assign({"log2fc": np.log2(mean_expr / wt_expr)})

# Stage 3: Features
ds = ds.assign(
    {"gc_content": (["gene"], np.random.uniform(0.3, 0.7, 100)),
     "length": (["gene"], np.random.randint(500, 5000, 100))}
)

# Stage 4: Splits
train_mask = np.random.rand(100) > 0.2
ds = ds.assign(
    {"train_mask": (["gene"], train_mask),
     "test_mask": (["gene"], ~train_mask)}
)
```

## Dataset vs DataTree

### When to use Dataset

All data variables share **compatible** dimensions and coordinates. This is
the common case -- you can put everything in one flat Dataset.

### When to use DataTree

Data variables live on **incompatible** grids (different shapes, different
resolutions, different coordinate systems). DataTree keeps them in one
object with tree-structured organization and coordinate inheritance.

```python
import xarray as xr

# Different assays with incompatible shapes
dls_ds = xr.Dataset(
    {"hydrodynamic_diameter_nm": (["molecule", "replicate"], dls_data)},  # (50, 3)
    coords={"molecule": mol_ids, "replicate": ["r1", "r2", "r3"]},
)
hplc_ds = xr.Dataset(
    {"purity_percent": (["molecule", "peak"], hplc_data)},  # (50, 12) -- 12 HPLC peaks
    coords={"molecule": mol_ids, "peak": [f"peak_{i}" for i in range(12)]},
)

# These can't go in one Dataset (different non-molecule dims)
# Use DataTree instead:
tree = xr.DataTree.from_dict({
    "/": xr.Dataset(coords={"molecule": mol_ids}),  # root with shared coord
    "/characterization/dls": dls_ds,
    "/characterization/hplc": hplc_ds,
})
```

DataTree provides:
- **Coordinate inheritance**: with a `"/"` root, child nodes inherit the
  root's coordinates (the `molecule` defined once at root is visible in every
  child -- no duplication)
- **Path-based access**: get the `Dataset` at a node with the `.ds` attribute
  -- `tree["/characterization/dls"].ds` (dot form works too:
  `tree.characterization.dls.ds`). Note: `tree["/characterization/dls/ds"]`
  is **wrong** -- it looks for a child node literally named `"ds"` and raises
  `KeyError`.
- **Tree-wide selection**: `tree.sel(molecule="mol_007")` propagates to every
  node in one call (see [cross-experiment-linking.md](cross-experiment-linking.md))
- **Independent grids**: each node keeps its own dims

### Flat vs deep DataTree

There are two shapes, for two situations (Notebooks 1 and 5 contrast them
directly):

- **Flat tree** (no `"/"` root): sibling nodes each independently carry the
  shared coordinate. Use when assays have mostly **compatible** dimensions and
  you just want them grouped.
- **Deep tree** (with a `"/"` root that defines the shared coordinate): children
  **inherit** the root's coordinates. Use when assays live on **incompatible**
  grids and forcing one `Dataset` would broadcast to huge NaN-filled arrays.

```python
# Flat (Notebook 1): siblings each carry `molecule` independently
campaign = xr.DataTree.from_dict({
    "/analytical": ds_stage1,
    "/binding": ds_stage2,
})

# Deep (Notebook 5): root defines `molecule` once, children inherit it
campaign = xr.DataTree.from_dict({
    "/": xr.Dataset(coords={"molecule": mol_ids}),
    "/characterization/dls": dls_ds,
})
```

## Coordinate design patterns

### Pattern: Categorical dimension coordinate

For experimental factors with discrete levels:

```python
coords = {"channel": ["fitc", "pe", "apc", "percp"]}
```

### Pattern: Continuous dimension coordinate

For quantitative axes (time, concentration, wavelength):

```python
coords = {
    "time_hr": np.linspace(0, 48, 25),  # 0-48 hours, 2h spacing
    "concentration_um": np.logspace(-3, 2, 12),  # 1nM to 100uM, log-spaced
}
```

### Pattern: Non-dimension coordinate

For derived/auxiliary coordinates that share a dimension but aren't the index:

```python
# "abs_time" is a 2-D non-dimension coordinate derived from trial + rel_time
ds = ds.assign_coords(
    abs_time=(["trial", "time_point"], trial_onsets[:, None] + rel_times[None, :])
)
```

### Pattern: Multi-index (stacked coordinates)

When multiple factors define a single dimension:

```python
ds = ds.stack(sample=("molecule", "batch", "replicate"))
# Now ds.sample is a MultiIndex of (molecule, batch, replicate)
```

### Pattern: Feature dimension

Store a feature matrix with named features:

```python
ds = ds.assign(
    {"features": (["molecule", "feature"], feat_matrix)}
).assign_coords(feature=["mw", "logp", "hbd", "hba", "tps", "charge"])
```

### Pattern: Boolean mask dimension

Store train/test splits as masks along a split dimension:

```python
ds = ds.assign(
    {"train_mask": (["molecule", "split_type"], train_masks)}
).assign_coords(split_type=["random_80_20", "scaffold_split", "temporal_split"])
```

## Metadata and units

Store units and provenance in `attrs`:

```python
ds["expression"].attrs = {
    "units": "RPKM",
    "description": "Reads per kilobase per million",
    "assay": "RNA-seq",
    "protocol": "polyA_enriched_v2",
}
ds.attrs = {
    "title": "Multi-assay molecule characterization",
    "created": "2025-07-15",
    "lab": "Molecular Sciences",
}
```

For physical coordinates that need transformation (pixel to micrometers), use
a `CoordinateTransform` custom index -- see
[custom-indexes.md](custom-indexes.md).

## Storage formats

### Zarr (recommended for linked data)

Cloud-native, chunked, preserves all coordinates and metadata:

```python
ds.to_zarr("s3://bucket/experiment.zarr", mode="w")
ds = xr.open_zarr("s3://bucket/experiment.zarr")
```

**Gotcha**: Zarr has limited dtype support (no `U8` strings on some
versions). Use object arrays or encode strings as bytes if needed.

### DataTree + Zarr (hierarchical)

```python
tree.to_zarr("s3://bucket/multi_assay.zarr")
tree = xr.open_datatree("s3://bucket/multi_assay.zarr")
```

### NetCDF

Traditional format, good for single Datasets:

```python
ds.to_netcdf("experiment.nc")
ds = xr.open_dataset("experiment.nc")
```
