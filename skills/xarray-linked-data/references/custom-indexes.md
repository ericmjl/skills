# Custom Indexes for Linked Data

When xarray's default `PandasIndex` (1-D monotonic labels) is insufficient,
build a custom index. This reference covers the three patterns, complete
reference implementations, and when to use each.

## Table of Contents

1. [When to build a custom index](#when-to-build)
2. [The Index API surface](#api-surface)
3. [Pattern 1: Index subclass (PeriodicIndex)](#pattern-1)
4. [Pattern 2: CoordinateTransform (RangeIndex, z-stack)](#pattern-2)
5. [Pattern 3: Meta-index (RasterIndex)](#pattern-3)
6. [N-D derived coordinates (NDIndex)](#ndindex)
7. [Linked intervals (DimensionInterval)](#dimensioninterval)
8. [Registration and usage](#registration)
9. [Gotchas](#gotchas)

## When to build

The default `PandasIndex` handles 1-D monotonic labels. Build a custom index
when:

- Coordinates have **periodic/wrapping topology** (angles, phases)
- Coordinates are **derived** from other coordinates (absolute time = trial
  onset + relative time)
- You need **linked selection** across multiple coordinates (selecting on one
  constrains others)
- Coordinates need a **nonlinear transform** (pixel to physical units, lens
  distortion)
- The coordinate axis is **too large to materialize** (exabyte-scale imaging)
- You need **N-dimensional coordinate lookup** (2-D spatial coordinates)

## API surface

Every custom index inherits from `xarray.Index`. The only **required** method
is `from_variables`. Everything else is optional but determines what
operations the index supports.

```python
from xarray import Index
from xarray.core.indexing import IndexSelResult


class MyIndex(Index):
    # REQUIRED: xarray calls this to build the index from coordinates
    @classmethod
    def from_variables(cls, variables, *, options):
        # variables: dict of {name: Variable}
        # options: dict from set_xindex(..., option_key=value)
        # validate inputs, then construct
        return cls(...)

    # OPTIONAL: needed for .sel() support
    def sel(self, labels, method=None, tolerance=None) -> IndexSelResult:
        # labels: {coord_name: query_value}
        # return IndexSelResult(dim_indexers={dim: positions})
        ...

    # OPTIONAL: keep index alive after .isel(); default = drop
    def isel(self, indexers):
        ...

    # OPTIONAL: expose index data as coords (avoid duplication)
    def create_variables(self, variables):
        ...

    # OPTIONAL: alignment trio (all three required together)
    def equals(self, other): ...
    def join(self, other, how="inner"): ...
    def reindex_like(self, other): ...
```

### IndexSelResult

```python
IndexSelResult(
    dim_indexers,     # REQUIRED: {dim_name: positional_indexer}
    indexes={},       # new indexes to install in result
    variables={},     # new variables to install in result
    drop_coords=[],   # coord names to drop
    drop_indexes=[],  # index names to drop
    rename_dims={},   # {old_dim: new_dim}
)
```

For meta-indexes combining results from multiple sub-indexes, use
`xarray.core.indexing.merge_sel_results`:

```python
from xarray.core.indexing import merge_sel_results

results = [sub_index.sel(...) for sub_index in self._sub_indexes]
return merge_sel_results(results)
```

## Pattern 1: Index subclass

Use when you need **custom selection logic** on 1-D coordinates with
non-standard structure.

### Reference: PeriodicIndex

For angular/wrapping coordinates (flow cytometry scatter angles, circular
genomics positions, rotational microscopy stages):

```python
import numpy as np
from xarray import Index
from xarray.core.indexing import IndexSelResult
from xarray.indexes import PandasIndex


class PeriodicIndex(Index):
    """1-D index whose axis wraps every ``period`` (e.g. angle, period=360)."""

    def __init__(self, pandas_index, period):
        self._index = pandas_index  # a PandasIndex holding the labels
        self.period = period

    @classmethod
    def from_variables(cls, variables, *, options):
        return cls(
            PandasIndex.from_variables(variables, options={}),
            options["period"],
        )

    def sel(self, labels, method=None, tolerance=None):
        (name, label), = labels.items()
        base = self._index.index.to_numpy()
        q = np.asarray(label, dtype=float)
        if q.ndim == 0:
            d = np.abs((float(q) - base + self.period / 2) % self.period - self.period / 2)
            return IndexSelResult({self._index.dim: [int(d.argmin())]})
        d = np.abs((q[:, None] - base[None, :] + self.period / 2) % self.period - self.period / 2)
        pos = d.argmin(axis=1)
        return IndexSelResult({self._index.dim: pos})

    def create_variables(self, variables):
        return self._index.create_variables(variables)
```

### Usage

```python
ds = ds.drop_indexes("angle").set_xindex("angle", PeriodicIndex, period=360.0)
ds.sel(angle=370)  # wraps to angle=10
ds.sel(angle=np.array([-10, 0, 370]))  # vectorized wrapping
```

## Pattern 2: CoordinateTransform

Use when you have a **coordinate mapping** between index space and world
space. Just write `forward` and `reverse`; xarray builds the index.

### Reference: CoordinateTransform z-stack

For microscopy/imaging where pixel positions map to physical depths:

```python
import numpy as np
from xarray import Coordinates
from xarray.indexes import CoordinateTransform, CoordinateTransformIndex


class ZStackTransform(CoordinateTransform):
    """Maps slice index to physical depth (nm or um).

    forward: slice_index -> depth_nm
    reverse: depth_nm -> slice_index
    """

    def __init__(self, n_slices, slice_thickness_nm):
        super().__init__(("depth_nm",), {"z": n_slices})
        self.n_slices = n_slices
        self.slice_thickness_nm = slice_thickness_nm

    def forward(self, dim_positions):
        return {"depth_nm": dim_positions["z"] * self.slice_thickness_nm}

    def reverse(self, coord_labels):
        return {"z": coord_labels["depth_nm"] / self.slice_thickness_nm}
```

### Usage

```python
# Build a DataArray with a lazy depth coordinate (labels never materialized)
da = xr.DataArray(
    image_data,  # shape (z, y, x)
    dims=("z", "y", "x"),
    coords=Coordinates.from_xindex(
        CoordinateTransformIndex(ZStackTransform(n_slices=200, slice_thickness_nm=4.0))
    ),
)

# Select by physical depth -- xarray computes the reverse transform
da.sel(depth_nm=500.0, method="nearest")  # finds slice 125 (500/4=125)
da.sel(depth_nm=xr.DataArray([100, 200, 300], dims="probe"), method="nearest")
```

### Built-in RangeIndex

For regular axes too large to store, use xarray's built-in `RangeIndex`:

```python
from xarray import Coordinates
from xarray.indexes import RangeIndex

z = Coordinates.from_xindex(RangeIndex.arange(0.0, 2e9 * 4.0, 4.0, dim="z"))["z"]
# 2 billion entries, only 3 numbers stored (start, stop, step)
```

## Pattern 3: Meta-index

Use when you need to **link multiple coordinates** under one index that
delegates to sub-indexes.

### Reference: RasterIndex

Links two 1-D coordinates (x, y) under one index for 2-D selection:

```python
from xarray import Index
from xarray.core.indexes import PandasIndex
from xarray.core.indexing import merge_sel_results


class RasterIndex(Index):
    """Links x and y coordinates for 2-D raster selection."""

    def __init__(self, xy_indexes):
        assert len(xy_indexes) == 2
        self._xy_indexes = xy_indexes

    @classmethod
    def from_variables(cls, variables, *, options):
        assert len(variables) == 2
        xy_indexes = {
            k: PandasIndex.from_variables({k: v}, options=options)
            for k, v in variables.items()
        }
        return cls(xy_indexes)

    def create_variables(self, variables):
        idx_vars = {}
        for idx in self._xy_indexes.values():
            idx_vars.update(idx.create_variables(variables))
        return idx_vars

    def sel(self, labels):
        results = []
        for k, idx in self._xy_indexes.items():
            if k in labels:
                results.append(idx.sel({k: labels[k]}))
        return merge_sel_results(results)
```

## NDIndex

For **N-dimensional derived coordinates** -- coordinates that span multiple
dimensions (e.g., absolute time computed from trial onset + relative time).

### Problem solved

A 2-D coordinate like `abs_time(trial, rel_time)` cannot be indexed by the
default `PandasIndex` (which requires 1-D). `NDIndex` enables
`ds.sel(abs_time=7.5)` against an N-D array.

### Reference implementation (simplified)

```python
import numpy as np
from xarray import Index
from xarray.core.indexing import IndexSelResult
from xarray.core.variable import Variable


class NDIndex(Index):
    """Index for N-D derived coordinates (ndim >= 2)."""

    def __init__(self, nd_coords, slice_method="bounding_box"):
        self._nd_coords = nd_coords  # {name: (dims, values)}

    @classmethod
    def from_variables(cls, variables, *, options):
        slice_method = options.get("slice_method", "bounding_box") if options else "bounding_box"
        nd_coords = {}
        for name, var in variables.items():
            if var.ndim < 2:
                raise ValueError(f"NDIndex requires ndim >= 2, got {name} with ndim={var.ndim}")
            nd_coords[name] = (var.dims, var.values)
        return cls(nd_coords, slice_method=slice_method)

    def create_variables(self, variables):
        return {name: Variable(dims, vals) for name, (dims, vals) in self._nd_coords.items()}

    def sel(self, labels, method=None, tolerance=None):
        dim_indexers = {}
        for name, (dims, values) in self._nd_coords.items():
            if name not in labels:
                continue
            value = labels[name]
            if isinstance(value, slice):
                start = value.start if value.start is not None else values.min()
                stop = value.stop if value.stop is not None else values.max()
                in_range = (values >= start) & (values <= stop)
                for i, dim in enumerate(dims):
                    axes = tuple(j for j in range(values.ndim) if j != i)
                    has = np.any(in_range, axis=axes)
                    idxs = np.where(has)[0]
                    dim_indexers[dim] = slice(int(idxs[0]), int(idxs[-1]) + 1)
            else:
                if method == "nearest":
                    flat_idx = int(np.argmin(np.abs(values - float(value))))
                else:
                    matches = np.flatnonzero(values == value)
                    if len(matches) == 0:
                        raise KeyError(f"Value {value} not found in {name}")
                    flat_idx = int(matches[0])
                indices = np.unravel_index(flat_idx, values.shape)
                for dim, idx in zip(dims, indices):
                    dim_indexers[dim] = slice(int(idx), int(idx) + 1)
        return IndexSelResult(dim_indexers)

    def isel(self, indexers):
        new_coords = {}
        for name, (dims, values) in self._nd_coords.items():
            idx_tuple = []
            new_dims = []
            for dim in dims:
                if dim in indexers:
                    idx_tuple.append(indexers[dim])
                    if not isinstance(indexers[dim], (int, np.integer)):
                        new_dims.append(dim)
                else:
                    idx_tuple.append(slice(None))
                    new_dims.append(dim)
            new_values = values[tuple(idx_tuple)]
            if new_values.ndim >= 2:
                new_coords[name] = (tuple(new_dims), new_values)
        if not new_coords:
            return None  # drop index when all coords become 1-D
        return NDIndex(new_coords, slice_method=self._slice_method)

    def should_add_coord_to_array(self, name, var, dims):
        return True
```

### Usage: time-locking to events

```python
# Trial-based data: signal(trial, rel_time)
# abs_time = trial_onset + rel_time (2-D derived coordinate)
ds = ds.assign_coords(
    abs_time=(["trial", "rel_time"], trial_onsets[:, None] + rel_times[None, :]),
    stim_locked=(["trial", "rel_time"], ds.rel_time - ds.stim_onset),  # relative to stim
)

# Register N-D coords under NDIndex
ds = ds.set_xindex(["abs_time", "stim_locked"], NDIndex)

# Select by absolute time -- finds the right (trial, rel_time)
ds.sel(abs_time=7.5, method="nearest")

# Select relative to stimulus onset across all trials
window = ds.sel(stim_locked=slice(-0.5, 1.0))  # -0.5s to +1.0s around stim
```

For the full implementation with slice methods and edge-case handling, see
Ian Hunt-Isaak's [linked_indices library](https://github.com/ianhi/xarray-linked-indexes).

## DimensionInterval

For **linked interval coordinates** -- multiple interval-typed dimensions
over a shared continuous dimension, where selecting on one constrains all
others.

### Problem solved

Speech data: `time` is continuous; `word_intervals` and `phoneme_intervals`
are both interval-indexed and overlap hierarchically. Selecting on time
should constrain both words and phonemes to overlapping ranges.

### Setup

```python
import pandas as pd
from linked_indices import DimensionInterval

word_intervals = pd.IntervalIndex.from_breaks([0, 40, 80, 120], closed="left")
phoneme_intervals = pd.IntervalIndex.from_breaks([0, 20, 40, 60, 80, 100, 120], closed="left")

ds = ds.drop_indexes(["time", "word", "phoneme"]).set_xindex(
    ["time", "word_intervals", "phoneme_intervals", "word", "phoneme"],
    DimensionInterval,
)
```

### Cross-slicing

```python
ds.sel(time=slice(30, 70))           # constrains word AND phoneme
ds.sel(word_intervals=60)            # picks word [40,80); constrains time + phoneme
ds.sel(phoneme_intervals=70)         # picks phoneme [60,80); constrains time + word
```

### Onset/duration format

```python
ds = ds.drop_indexes(["time", "word"]).set_xindex(
    ["time", "word_onset", "word_duration", "word"],
    DimensionInterval,
    onset_duration_coords={"word": ("word_onset", "word_duration")},
)
```

For the full implementation, see
[linked_indices](https://github.com/ianhi/xarray-linked-indexes).

## Registration

Two ways to attach a custom index:

### On an existing object

```python
# Drop default indexes first, then attach custom index
ds = ds.drop_indexes("angle").set_xindex("angle", PeriodicIndex, period=360.0)

# For multi-coordinate indexes
ds = ds.drop_indexes(["x", "y"]).set_xindex(["x", "y"], RasterIndex)
```

### At construction time (CoordinateTransform only)

```python
from xarray import Coordinates
from xarray.indexes import CoordinateTransformIndex

coords = Coordinates.from_xindex(
    CoordinateTransformIndex(ZStackTransform(n_slices=200, slice_thickness_nm=4.0))
)
da = xr.DataArray(data, dims=("z", "y", "x"), coords=coords)
```

### Inspecting installed indexes

```python
ds.xindexes  # pretty-prints index -> coords mapping
```

## Gotchas

1. **Experimental API**: Custom indexes may change without deprecation.
   Pin xarray versions.

2. **Must `drop_indexes` before re-installing**: `set_xindex` will not
   overwrite an existing custom index silently.

3. **`isel` not implemented -> index dropped**: If you skip `isel()`,
   positional selection loses the index. Always implement `isel` if you want
   the index to survive subsetting.

4. **Slice selection returns bounding boxes**: For N-D indexes, slice queries
   return the smallest rectangle containing matches -- may include cells
   outside the requested range. Filter with `.where()` afterwards:
   ```python
   result = ds.sel(abs_time=slice(2.5, 7.5))
   mask = (result.abs_time >= 2.5) & (result.abs_time <= 7.5)
   filtered = result.where(mask)
   ```

5. **Two indexes on one shared dimension cannot co-select**: Allowed to
   exist; cannot be used in the same `.sel()` call.

6. **`from_variables` must validate**: The method receives arbitrary
   `{name: Variable}` -- assert shape/dim/count constraints yourself.

7. **`create_variables` only for array-like data**: Tree-based indexes
   (KD-tree) cannot expose their structure as coordinate variables.

8. **`NDIndex` vs `NDPointIndex`**: Different problems. `NDIndex` = value
   lookup in N-D array (structured data with derived coords). `NDPointIndex`
   = spatial nearest-neighbor in point clouds (unstructured data).
