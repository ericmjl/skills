# Selection and Manipulation of Linked Data

How to read, select, align, and compute across linked xarray variables.
All operations preserve coordinate alignment automatically.

## Table of Contents

1. [Label-based selection (.sel)](#label-based-selection)
2. [Positional selection (.isel)](#positional-selection)
3. [Boolean masking (.where)](#boolean-masking)
4. [Pointwise/vectorized indexing](#pointwise-indexing)
5. [Alignment and joins](#alignment-and-joins)
6. [Computation patterns](#computation-patterns)
7. [Dimension manipulation](#dimension-manipulation)

## Label-based selection

Use `.sel()` to select by coordinate **values**. Everything linked stays
aligned:

```python
# Select a single molecule -- all linked variables update
ds.sel(molecule="mol_007")

# Select a range (slice) -- inclusive on both ends for labels
ds.sel(time_point=slice(6, 24))

# Nearest-neighbor for continuous coordinates
ds.sel(concentration_um=1.5, method="nearest")

# With tolerance -- returns empty if nothing within tolerance
ds.sel(concentration_um=1.5, method="nearest", tolerance=0.1)

# Multiple values (list selection)
ds.sel(condition=["wt", "ko"])

# Datetime selection
ds.sel(time="2025-07")
ds.sel(time=slice("2025-01-01", "2025-06-30"))
```

### Combining selections

```python
# Multi-dimensional selection in one call
ds.sel(molecule="mol_007", condition="ko", time_point=24)

# Selecting on a non-dimension coordinate
ds.sel(channel="fitc")  # if "channel" is a coordinate
```

## Positional selection

Use `.isel()` for integer-position indexing (like NumPy, but by dimension
name):

```python
# First molecule, third replicate
ds.isel(molecule=0, replicate=2)

# Slices
ds.isel(time_point=slice(0, 10))

# Boolean array indexing
train_idx = np.where(ds.train_mask.sel(split_type="random_80_20").values)[0]
ds.isel(molecule=train_idx)
```

**Key difference from NumPy**: xarray indexes by dimension **name**, so order
doesn't matter: `ds.isel(molecule=0, replicate=2)` == `ds.isel(replicate=2, molecule=0)`.

## Boolean masking

Use `.where()` to filter by conditions while keeping the coordinate grid:

```python
# Keep only molecules above a threshold -- NaN for the rest
filtered = ds.where(ds.mean_signal > 5.0)

# Drop the NaN rows entirely
filtered = ds.where(ds.mean_signal > 5.0, drop=True)

# Multiple conditions with bitwise operators
high_affinity = ds.where((ds.kd < 10) & (ds.purity > 0.95), drop=True)

# Using train/test masks
train_data = ds.where(ds.train_mask.sel(split_type="random_80_20"), drop=True)
test_data = ds.where(ds.test_mask.sel(split_type="random_80_20"), drop=True)
```

### Using .isin() for membership filtering

```python
# Filter by membership in a list
qc_passed = ds.where(ds.qc_flag.isin([0, 1]), drop=True)  # flags 0 and 1 are "pass"
```

## Pointwise indexing

Extract values at arbitrary coordinate locations using `DataArray` indexers
with a **shared output dimension**:

```python
# Extract signal at specific (wavelength, time) pairs
wavelengths = xr.DataArray([488, 561, 638], dims="laser")
times = xr.DataArray([0, 12, 24], dims="laser")

# Pointwise: each laser gets its own (wavelength, time) pair
result = ds.sel(wavelength=wavelengths, time=times, method="nearest")
# result has a new "laser" dimension of size 3
```

**Contrast with orthogonal indexing** (list selection = Cartesian product):

```python
# Orthogonal: all combinations of wavelengths x times (3x3 = 9)
result = ds.sel(wavelength=[488, 561, 638], time=[0, 12, 24], method="nearest")
```

Use pointwise when you want paired lookups. Use orthogonal when you want the
full cross-product.

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
coordinate linkage.

### Reductions

```python
# Mean over specific dimensions -- result keeps remaining coords
per_molecule = ds["signal"].mean(dim=["condition", "replicate"])

# Standard deviation
ds["signal"].std(dim="replicate")

# Quantiles
ds["signal"].quantile([0.25, 0.75], dim="replicate")
```

### Groupby (label-space splitting)

```python
# Group by a coordinate value, apply, combine
ds.groupby("condition").mean(dim="replicate")

# Group by bins of a continuous variable
ds.groupby_bins("concentration_um", bins=[0, 1, 10, 100]).mean()

# Custom group labels
season = ds.time.dt.season  # "DJF", "MAM", "JJA", "SON"
ds.groupby(season).mean()
```

### Rolling windows

```python
# Sliding window mean over time
ds["signal"].rolling(time_point=5, center=True).mean()

# Construct window as new dimension (memory-efficient view)
windowed = ds["signal"].rolling(time_point=5).construct("window")
# Now "window" is a new dimension you can reduce over
```

### Resampling (time series)

```python
# Downsample time series
ds.resample(time="6h").mean()

# Upsample with forward-fill
ds.resample(time="1h").ffill()
```

### Weighted reductions

```python
weights = ds["cell_count"] / ds["cell_count"].sum(dim="sample")
weighted_mean = (ds["signal"] * weights).sum(dim="sample")
```

### apply_ufunc (custom functions)

For applying NumPy/SciPy functions across xarray dimensions:

```python
def my_metric(x, axis):
    """Custom reduction over axis."""
    return np.percentile(x, 90, axis=axis)

result = xr.apply_ufunc(
    my_metric,
    ds["signal"],
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
ds = ds.swap_dims({"molecule_index": "molecule_id"})
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
ds = ds.rename_dims({"time_point": "time_hr"})
```

### Merge / concat

```python
# Merge variables that share coordinates
merged = xr.merge([ds_a, ds_b])

# Concatenate along a dimension
combined = xr.concat([ds_batch1, ds_batch2], dim="batch")
```
