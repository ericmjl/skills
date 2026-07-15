---
name: xarray-linked-data
description: >-
  Design, build, and manipulate xarray data structures for highly linked,
  multi-dimensional data where measurements, derived estimates, and model
  outputs share coordinates and must stay synchronized. Use when: structuring
  laboratory/experimental/multi-assay data in xarray (Dataset or DataTree);
  designing coordinate systems for linked data; writing custom xarray indexes
  (custom Index subclasses, CoordinateTransforms, interval-based or N-D
  derived coordinate indexes); selecting/aligning/computing across linked
  xarray variables; linking data across experiments through shared
  coordinates or custom indexes; reading or manipulating xarray objects to
  help a user accomplish analysis goals; converting scattered CSV/Parquet/HDF5
  workflows into unified xarray datasets. Covers: progressive data
  accumulation, coordinate design, sel/isel/where/align, groupby/rolling/
  coarsen/resample, Dataset vs DataTree, custom index patterns
  (PeriodicIndex, RangeIndex, CoordinateTransform, NDIndex,
  DimensionInterval), and cross-experiment linking.
license: MIT
---

# Xarray Linked Data

Xarray is the natural home for highly linked data: measurements, derived
estimates, features, and model outputs sharing coordinates and staying
synchronized through selection, computation, and storage.

## When to use this skill

- Designing xarray data structures for multi-dimensional, multi-assay data
- Linking data from different experiments through shared coordinates
- Writing custom xarray indexes (when default PandasIndex is insufficient)
- Reading/manipulating xarray to accomplish analysis goals
- Converting scattered-file workflows into unified coordinate-aligned datasets

## Core mental model

```
Experiment Design          xarray Structure
─────────────────          ────────────────
Samples/subjects    →      dimension coordinates (e.g. molecule_id, sample)
Experimental factors →     dimension coordinates (e.g. treatment, time_point)
Raw measurements    →      data variables (e.g. expression_level, intensity)
Derived estimates   →      data variables (e.g. ec50, kd, effect_estimate)
Features            →      data variables along a feature dimension
Splits/assignments  →      boolean mask variables along a split_type dimension
Physical units      →      coordinate attrs or CoordinateTransform indexes
```

**Key principle:** every piece of data knows its own coordinates. When you
slice, everything stays aligned. No manual index-matching across files.

## Quick reference

### Design data structures

Read [references/data-structure-design.md](references/data-structure-design.md)
for full guidance.

```python
# Progressive accumulation: start with raw data, add layers
ds = xr.Dataset(
    {"expression": (["molecule", "treatment", "replicate"], raw_data)},
    coords={
        "molecule": mol_ids,
        "treatment": ["control", "low", "high"],
        "replicate": ["r1", "r2", "r3"],
    },
)
# Add derived estimates — auto-aligned by coordinates
ds = ds.assign({"ec50": (["molecule"], ec50_estimates)})
# Add features along a new dimension
ds = ds.assign({"features": (["molecule", "feature"], feat_matrix)})
```

**When to use Dataset vs DataTree:**
- **Dataset**: all variables share compatible dimensions/coordinates
- **DataTree**: variables live on different grids (different resolutions,
  different assay types with incompatible shapes); use tree nodes with
  coordinate inheritance

### Select and manipulate

Read [references/selection-and-manipulation.md](references/selection-and-manipulation.md)
for full guidance.

```python
# Label-based selection — everything stays aligned
train = ds.where(ds.train_mask.sel(split_type="random_80_20"), drop=True)

# Pointwise indexing with shared dimension
targets = ds.sel(
    molecule=xr.DataArray(["mol_3", "mol_7"], dims="query"),
    method="nearest",
)

# Alignment with explicit join type
aligned_a, aligned_b = xr.align(ds_a, ds_b, join="inner")
```

### Build custom indexes

Read [references/custom-indexes.md](references/custom-indexes.md) for full
guidance, including complete reference implementations.

When default `PandasIndex` (1-D monotonic labels) is insufficient, build a
custom index. Three patterns, escalating complexity:

1. **`Index` subclass + hand-written `sel`** — for custom selection logic
   (periodic/wrapping coordinates, domain-specific nearest-neighbor)
2. **`CoordinateTransform` subclass** — for coordinate mappings with
   `forward`/`reverse` (pixel to physical, lazy z-stacks, nonlinear warps)
3. **Meta-index** — wraps other indexes for linked multi-coordinate selection
   (interval cross-slicing, N-D derived coordinates)

```python
# Register a custom index
ds = ds.drop_indexes("angle").set_xindex("angle", PeriodicIndex, period=360.0)
```

### Link across experiments

Read [references/cross-experiment-linking.md](references/cross-experiment-linking.md)
for full guidance.

```python
# DataTree for multi-assay hierarchy
tree = xr.DataTree.from_dict({
    "/characterization/dls": dls_ds,
    "/characterization/hplc": hplc_ds,
    "/bioassays/elisa": elisa_ds,
    "/bioassays/flow_cytometry": flow_ds,
})
# Shared molecule_id coordinate inherited across nodes
```

## Reference notebooks

Self-verifying marimo notebooks with synthetic data covering diverse assay
domains (cargo delivery, binding assays, cell-based assays, genomics,
functional readouts, analytical chemistry). Run each with `uv run`:

| Notebook | Topic |
|----------|-------|
| [01_linked_data_design.py](notebooks/01_linked_data_design.py) | Progressive accumulation linking 6 assay domains by molecule_id |
| [02_periodic_and_transform_indexes.py](notebooks/02_periodic_and_transform_indexes.py) | PeriodicIndex + CoordinateTransform (flow cytometry, microscopy, mass spec) |
| [03_ndindex_time_locking.py](notebooks/03_ndindex_time_locking.py) | NDIndex for N-D derived coordinates, time-locking to dosing events |
| [04_linked_intervals_cross_slicing.py](notebooks/04_linked_intervals_cross_slicing.py) | DimensionInterval for concentration x time interval linking |
| [05_cross_experiment_datatree.py](notebooks/05_cross_experiment_datatree.py) | DataTree hierarchy, cross-experiment queries |

## API instability note

Custom indexes are an **experimental** xarray feature (since v2022.06.0).
The API may change without deprecation notice. Pin xarray versions in
notebooks and check the [official docs](https://docs.xarray.dev/en/stable/internals/how-to-create-custom-index.html)
for current API.

## Key references

- [xarray custom index how-to](https://docs.xarray.dev/en/stable/internals/how-to-create-custom-index.html)
- [Ian Hunt-Isaak's linked-indexes](https://ianhuntisaak.com/xarray-linked-indexes/) -- DimensionInterval, NDIndex
- [xarray-tutorial: why-an-index](https://tutorial.xarray.dev/intermediate/indexing/why-an-index.ipynb) -- PeriodicIndex, CoordinateTransform examples
- [xarray-indexes gallery](https://xarray-indexes.readthedocs.io/) -- NDPointIndex (KD-tree/Ball-tree)
