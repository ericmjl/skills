# Selection and Manipulation of Linked Data

How to read, select, align, and compute across linked xarray variables.
All operations preserve coordinate alignment automatically -- the running
examples use the molecule-characterization vocabulary from the notebooks
(`molecule`, `target`, `cell_line`, `ec50_nm`, `concentration_nm`, `time_min`).

## Table of Contents

1. [Label-based selection (.sel)](#label-based-selection)
2. [Coordinate retention after `.sel()` (gotcha)](#coordinate-retention)
3. [Positional selection (.isel)](#positional-selection)
4. [Boolean masking (.where)](#boolean-masking)
5. [Pointwise / vectorized indexing](#pointwise-indexing)
6. [Selection on a DataTree](#datatree-selection)
7. [Selection through custom indexes](#custom-index-selection)
8. [Alignment and joins](#alignment-and-joins)
9. [Computation patterns](#computation-patterns)
10. [Dimension manipulation](#dimension-manipulation)

## Label-based selection

Use `.sel()` to select by coordinate **values**. Everything linked stays
aligned:

```python
# Select a single molecule -- all linked variables update
ds.sel(molecule="LNP_007")

# Select a range (slice) -- inclusive on both ends for labels
ds.sel(time_min=slice(6, 24))

# Nearest-neighbor for continuous coordinates (e.g. a dose-response curve)
ds.sel(concentration_nm=1.5, method="nearest")

# With tolerance -- returns empty if nothing within tolerance
ds.sel(concentration_nm=1.5, method="nearest", tolerance=0.1)

# Multiple values (list selection = orthogonal/Cartesian product)
ds.sel(target=["EGFR", "HER2"])
```

> The notebooks store time as a **float** axis (`time_min`, `time_s`,
> `rel_time`), not a `DatetimeIndex`. Datetime-style selection
> (`ds.sel(time="2025-07")`) only works on datetime coordinates; for float
> time use slices or `method="nearest"` as above.

### Combining selections

```python
# Multi-dimensional selection in one call
ds.sel(molecule="LNP_007", target="EGFR", cell_line="HEPG2")
```

## Coordinate retention after `.sel()`

**The most important gotcha when building boolean masks from selections.**

`.sel(dim="value")` returns a DataArray that **still carries `dim` as a scalar
coordinate**, even though you selected a single value. When you then combine
several such results into one boolean mask with `&` / `|` or feed them to
`.where()`, xarray tries to align those leftover coordinates and you get
silent misalignment or a size/broadcasting conflict.

Strip the leftover coordinate with `.drop_vars()` (or extract `.values`) before
using a `.sel()` result in a compound mask:

```python
# WRONG -- leftover `target` / `cell_line` coords can misalign inside the mask
mask = (ds.ec50_nm.sel(target="EGFR") < 8) & (ds.uptake.sel(cell_line="HEPG2") > 40)

# RIGHT -- .drop_vars() removes the retained scalar coordinate
mask = (
    (ds.ec50_nm.sel(target="EGFR").drop_vars("target") < 8)
    & (ds.uptake.sel(cell_line="HEPG2").drop_vars("cell_line") > 40)
)
ds.where(mask, drop=True)
```

Equivalently, drop down to a plain NumPy array with `.values`, which carries
no xarray metadata at all. This is the pattern both Notebooks 1 and 5 use for
their cross-assay queries.

## Positional selection

Use `.isel()` for integer-position indexing (like NumPy, but by dimension
name):

```python
# First molecule, third replicate
ds.isel(molecule=0, replicate=2)

# Slices
ds.isel(time_min=slice(0, 10))

# Boolean array indexing (extract molecule ids from a train mask, then select)
train_mask = ds.train_mask.sel(split_type="random_80_20")
train_mols = list(train_mask.molecule.values[train_mask.values])
campaign.sel(molecule=train_mols)  # propagate the split across the tree
```

**Key difference from NumPy**: xarray indexes by dimension **name**, so order
doesn't matter: `ds.isel(molecule=0, replicate=2)` == `ds.isel(replicate=2, molecule=0)`.

## Boolean masking

Use `.where()` to filter by conditions while keeping the coordinate grid:

```python
# Keep only potent molecules -- NaN for the rest
filtered = ds.where(ds.ec50_nm < 10)

# Drop the NaN rows entirely
filtered = ds.where(ds.ec50_nm < 10, drop=True)

# Multiple conditions (apply the .drop_vars() rule above to each .sel())
high_affinity = ds.where(
    (ds.kd_nm.sel(target="EGFR").drop_vars("target") < 10)
    & (ds.hplc_purity_percent > 95),
    drop=True,
)
```

### Using .isin() for membership filtering

```python
# Filter by membership in a list
qc_passed = ds.where(ds.qc_flag.isin([0, 1]), drop=True)  # flags 0 and 1 are "pass"
```

## Pointwise indexing

Extract values at arbitrary coordinate locations using `DataArray` indexers
with a **shared output dimension** (point-wise -- each pair is one output
row):

```python
# Probe several molecules at several concentrations, paired 1:1
molecules = xr.DataArray(["LNP_003", "LNP_007", "LNP_012"], dims="query")
conc = xr.DataArray([0.1, 1.0, 10.0], dims="query")

result = ds.sel(molecule=molecules, concentration_nm=conc, method="nearest")
# result has a new "query" dimension of size 3
```

**Contrast with orthogonal indexing** (list selection = Cartesian product):

```python
# Orthogonal: all combinations of molecules x concentrations (3x3 = 9)
result = ds.sel(molecule=["LNP_003", "LNP_007", "LNP_012"],
                concentration_nm=[0.1, 1.0, 10.0], method="nearest")
```

Use pointwise when you want paired lookups. Use orthogonal when you want the
full cross-product.

> **Transform-backed coordinates require the DataArray-indexer form.** A
> `CoordinateTransformIndex` (e.g. mass-spec m/z) only supports point-wise
> indexing -- pass `xr.DataArray([value], dims="...")` with `method="nearest"`.
> A bare scalar can raise `TypeError`. See
> [custom-indexes.md](custom-indexes.md).

## Selection on a DataTree

When linked data lives in a `DataTree`, `.sel()` propagates to **every node**
in one call -- the single most important selection capability in this skill:

```python
# Slice all assay nodes for one molecule at once
tree.sel(molecule="LNP_007")

# Or a list (train/test split, or the hits from a cross-assay query)
tree.sel(molecule=hit_molecules)
```

To work with a single node's `Dataset`, use the **`.ds` attribute** (never a
`"/ds"` path suffix, which raises `KeyError`):

```python
dls = tree["/characterization/dls"].ds      # path syntax
dls = tree.characterization.dls.ds          # dot syntax (equivalent)

# per-node selection on incompatible grids
dls_hits = tree["/characterization/dls"].ds.sel(molecule=hit_molecules)
```

A cross-assay query pulls criteria from several nodes, builds one mask, then
re-selects each node by the hit molecules:

```python
derived = tree["/derived"].ds
criteria = (
    derived.ec50_nm_mean.sel(target="EGFR").drop_vars("target") < max_ec50
) & (
    derived.uptake_pct.sel(cell_line="HEPG2").drop_vars("cell_line") > min_uptake
)
hits = list(derived.where(criteria, drop=True).molecule.values)
dls_hits = tree["/characterization/dls"].ds.sel(molecule=hits)
```

See [cross-experiment-linking.md](cross-experiment-linking.md) for the full
DataTree workflow (flat vs deep trees, coordinate inheritance).

## Selection through custom indexes

Three of the notebooks install custom indexes that change what `.sel()` does.
This doc covers the default (`PandasIndex`) case; the custom-index semantics
are documented in [custom-indexes.md](custom-indexes.md):

- **PeriodicIndex** (Notebook 2): `ds.sel(angle=370, method="nearest")` wraps
  to 10 degrees instead of failing.
- **CoordinateTransform** (Notebook 2): `da.sel(depth_nm=500, ...)` queries by
  a *derived* physical coordinate; the index runs the reverse transform.
- **NDIndex** (Notebook 3): `ds.sel(abs_time=7.5, method="nearest")` selects
  on an N-D derived coordinate spanning multiple dimensions.
- **DimensionInterval** (Notebook 4): selecting on one interval dimension
  constrains all linked intervals (`ds.sel(dose_level="high")`).

## Alignment and joins

When combining xarray objects, they are automatically aligned by shared
coordinates. Control the join behavior:

| Join type | Behavior |
|-----------|----------|
| `"inner"` | Intersection of labels (default for arithmetic) |
| `"outer"` | Union of labels; fills missing with NaN |
| `"left"` | Labels of the left object |
| `"right"` | Labels of the right object |
| `"exact"` | Raises `ValueError` if labels differ |

```python
# Explicit alignment
a_aligned, b_aligned = xr.align(ds_a, ds_b, join="inner")

# Override default join for arithmetic
with xr.set_options(arithmetic_join="outer"):
    result = ds_a + ds_b
```

### Debugging alignment issues

If you get unexpected NaNs after combining, check alignment:

```python
# Verify coordinates match exactly
xr.align(ds_a, ds_b, join="exact")  # raises if mismatch

# Compare coordinate values
print(ds_a.molecule.values)
print(ds_b.molecule.values)
```

## Computation patterns

Replace for-loops with xarray's built-in computation patterns that preserve
coordinate linkage. The notebooks lean on reductions over named dimensions:

```python
# Mean over specific dimensions -- result keeps the remaining coords
per_molecule = ds["od450"].mean(dim=["replicate"])

# Standard deviation / median over replicates
ds["od450"].std(dim="replicate")
ds["uptake_pct_positive"].median(dim="replicate")

# Posterior summaries via NumPy on .values (draw dimension)
ec50_post = ds.ec50_nm_posterior.sel(target="EGFR").values  # (draw,)
median = np.median(ec50_post)
ci = np.percentile(ec50_post, [3, 97])
```

### Rolling windows

```python
# Sliding window mean over a float time axis
ds["dls_diameter_nm"].rolling(time_min=5, center=True).mean()

# Construct window as new dimension (memory-efficient view)
windowed = ds["signal"].rolling(time_min=5).construct("window")
```

### Groupby

```python
# Group by a coordinate value, apply, combine
ds.groupby("target").mean(dim="replicate")

# Group by bins of a continuous variable
ds.groupby_bins("concentration_nm", bins=[0, 1, 10, 100]).mean()
```

> **Datetime-only operations.** `resample(...)` and `.dt.season` require a
> `DatetimeIndex`. The notebooks use **float** time axes (`time_min`,
> `time_s`), so those operations don't apply directly -- bin with
> `groupby_bins` or resample manually. If your data does have a datetime
> coordinate, the usual forms work: `ds.resample(time="6h").mean()` and
> `ds.groupby(ds.time.dt.season).mean()`.

### apply_ufunc (custom functions)

For applying NumPy/SciPy functions across xarray dimensions:

```python
def top_decile(x, axis):
    """90th percentile reduction over axis."""
    return np.percentile(x, 90, axis=axis)

result = xr.apply_ufunc(
    top_decile,
    ds["od450"],
    input_core_dims=[["replicate"]],
    output_core_dims=[[]],
    vectorize=True,
)
```

## Dimension manipulation

### Stack / unstack

Combine multiple dimensions into one (MultiIndex):

```python
# Stack molecule + replicate into a single "sample" dimension
stacked = ds.stack(sample=("molecule", "replicate"))
# stacked.sample is a MultiIndex

# Unstack back
unstacked = stacked.unstack("sample")
```

### Swap dimensions

```python
# Make a non-dimension coordinate into the dimension coordinate
ds = ds.swap_dims({"molecule_index": "molecule"})
```

### Expand / squeeze

```python
# Add a new singleton dimension
ds = ds.expand_dims("batch")  # size-1 "batch" dimension

# Remove singleton dimensions
ds = ds.squeeze()  # removes all size-1 dims
```

### Rename

```python
ds = ds.rename({"old_name": "new_name"})
ds = ds.rename_dims({"time_min": "time_hr"})
```

### Merge / concat

```python
# Merge variables that share coordinates
merged = xr.merge([ds_a, ds_b])

# Concatenate along a dimension
combined = xr.concat([ds_batch1, ds_batch2], dim="batch")
```
