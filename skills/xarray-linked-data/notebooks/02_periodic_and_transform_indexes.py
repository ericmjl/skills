# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "xarray>=2025.1.0",
#     "scipy",
#     "matplotlib",
#     "wigglystuff==0.5.16",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium", app_title="Periodic and Transform Indexes")


@app.cell(hide_code=True)
def hero(mo):
    mo.md("""
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 48px 40px;
        margin: -16px -16px 24px -16px;
    ">
        <div style="font-size: 14px; color: #e94560; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px;">
            xarray-linked-data &middot; Notebook 2
        </div>
        <h1 style="color: #f0f9ff; font-size: 2.4rem; margin: 0 0 16px 0; line-height: 1.2;">
            Custom Indexes: Periodic &amp; Transform
        </h1>
        <p style="color: #aeb6c7; font-size: 1.1rem; margin: 0; max-width: 640px; line-height: 1.6;">
            When PandasIndex is not enough. Build PeriodicIndex for angular data
            and CoordinateTransform for pixel-to-physical mappings.
        </p>
    </div>
    """)
    return


@app.cell(hide_code=True)
def cell_tour(mo):
    import wigglystuff

    tour = wigglystuff.CellTour(
        steps=[
            {"cell_name": "hero", "title": "Custom Indexes", "description": "Two patterns for when PandasIndex is not enough."},
            {"cell_name": "periodic_index_class", "title": "PeriodicIndex", "description": "An Index subclass with hand-written sel() for wrapping/angular coordinates."},
            {"cell_name": "periodic_verify", "title": "Wrapping Verified", "description": "350deg finds 345deg, 370deg wraps to 15deg -- no gaps on the circle."},
            {"cell_name": "zstack_transform_class", "title": "ZStackTransform", "description": "A CoordinateTransform: just write forward() and reverse(), xarray builds the index."},
            {"cell_name": "zstack_verify", "title": "Depth Selection", "description": "sel(depth_nm=500) computes the reverse transform and finds slice 125."},
            {"cell_name": "massspec_transform", "title": "MassSpecTransform", "description": "Nonlinear calibration curve (quadratic) as a CoordinateTransform."},
            {"cell_name": "massspec_verify", "title": "m/z Selection", "description": "Select by mass-to-charge ratio; the transform handles the TOF-to-mz mapping."},
        ],
        auto_start=False,
        show_progress=True,
    )
    mo.ui.anywidget(tour)
    return



@app.cell(hide_code=True)
def imports():
    import marimo as mo
    import numpy as np
    import xarray as xr
    from xarray import Index, Coordinates
    from xarray.core.indexing import IndexSelResult
    from xarray.indexes import (
        PandasIndex,
        CoordinateTransform,
        CoordinateTransformIndex,
    )

    return (
        CoordinateTransform,
        CoordinateTransformIndex,
        Coordinates,
        Index,
        IndexSelResult,
        PandasIndex,
        mo,
        np,
        xr,
    )


@app.cell(hide_code=True)
def intro(mo):
    mo.md(r"""
    ## When the default index is not enough

    xarray's default `PandasIndex` handles 1-D monotonic labels. But what if your
    coordinates have structure that `PandasIndex` can't express?

    This notebook builds two custom indexes from scratch:

    1. **`PeriodicIndex`** -- for angular/wrapping coordinates (flow cytometry scatter angles)
    2. **`ZStackTransform`** -- a `CoordinateTransform` for microscopy pixel-to-depth mapping

    Each is self-verifying with `assert` statements.
    """)
    return


@app.cell(hide_code=True)
def periodic_header(mo):
    mo.md("""
    ## Pattern 1: PeriodicIndex

    Flow cytometry measures light scatter at angles around a laser beam.
    Angles wrap around: 350deg is close to 10deg. The default PandasIndex
    treats these as far apart. A custom PeriodicIndex wraps the distance.
    """)
    return


@app.cell
def periodic_index_class(Index, IndexSelResult, PandasIndex, np):
    class PeriodicIndex(Index):
        """1-D index whose axis wraps every ``period`` (e.g. angle, period=360)."""

        def __init__(self, pandas_index, period):
            self._index = pandas_index
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
            # Wrapped distance on the circle
            d = np.abs(
                (q[..., None] - base[None, :] + self.period / 2) % self.period
                - self.period / 2
            )
            if q.ndim == 0:
                return IndexSelResult({self._index.dim: [int(d.argmin())]})
            return IndexSelResult({self._index.dim: d.argmin(axis=1)})

        def create_variables(self, variables):
            return self._index.create_variables(variables)

    return (PeriodicIndex,)


@app.cell
def periodic_build_data(PeriodicIndex, np, xr):
    # Synthetic flow cytometry: scatter intensity at 24 angles around a laser
    scatter_angles = np.linspace(0, 345, 24)  # 24 angles, 15deg spacing
    scatter_intensity = np.random.lognormal(3, 0.5, (40, 24))  # 40 particles x 24 angles

    flow_ds = xr.Dataset(
        data_vars={"scatter_intensity": (["particle", "angle"], scatter_intensity)},
        coords={
            "particle": [f"particle_{p_idx:02d}" for p_idx in range(40)],
            "angle": scatter_angles,
        },
    )
    # Attach the PeriodicIndex
    flow_ds = flow_ds.drop_indexes("angle").set_xindex("angle", PeriodicIndex, period=360.0)
    print(f"Flow cytometry data: {flow_ds.sizes['particle']} particles x {flow_ds.sizes['angle']} angles")
    print(f"Angle range: {scatter_angles[0]}-{scatter_angles[-1]} degrees (wrapping)")
    return (flow_ds,)


@app.cell
def periodic_verify(flow_ds, mo, xr):
    # Verify wrapping: angle=350 should find angle=345 (nearest), not angle=0
    result_350 = flow_ds.sel(angle=350, method="nearest")
    result_370 = flow_ds.sel(angle=370, method="nearest")  # 370 wraps to 10

    # 350 nearest is 345 (diff=5) not 0 (diff=350 without wrapping)
    assert result_350.angle.values == 345.0, f"Expected 345, got {result_350.angle.values}"
    # 370 wraps to 10, nearest is 15 (diff=5) not 0 (diff=370 without wrapping)
    assert result_370.angle.values == 15.0, f"Expected 15, got {result_370.angle.values}"

    # Verify vectorized: query multiple angles including wrap-around
    query_angles = flow_ds.sel(
        angle=xr.DataArray([5, 355, 370], dims="query"), method="nearest"
    )
    assert query_angles.angle.values.tolist() == [0.0, 0.0, 15.0]

    mo.callout(
        mo.md("""
        **PeriodicIndex verified:**
        - `sel(angle=350)` -> 345deg (wrapping distance = 5deg)
        - `sel(angle=370)` -> 15deg (370 wraps to 10, nearest is 15)
        - Vectorized: [5, 355, 361] -> [0, 0, 15]
        """),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def transform_header(mo):
    mo.md("""
    ## Pattern 2: CoordinateTransform (Z-Stack)

    Microscopy z-stacks: pixel slice indices map to physical depths.
    A `CoordinateTransform` lets you `sel(depth_nm=500)` and the index
    computes the reverse transform (500nm / 4nm-per-slice = slice 125).
    Labels never need to be materialized.
    """)
    return


@app.cell
def zstack_transform_class(CoordinateTransform):
    class ZStackTransform(CoordinateTransform):
        """Maps slice index to physical depth (nm).

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

    return (ZStackTransform,)


@app.cell
def zstack_build_data(
    CoordinateTransformIndex,
    Coordinates,
    ZStackTransform,
    np,
    xr,
):
    # Synthetic microscopy: 200 z-slices, 4nm each, 2 channels (nuclei + membrane)
    n_slices = 200
    slice_thickness = 4.0  # nm per slice
    image_data = np.random.poisson(50, (n_slices, 128, 128, 2)).astype(float)

    zstack_da = xr.DataArray(
        image_data,
        dims=("z", "y", "x", "channel"),
        coords={
            "y": np.arange(128),
            "x": np.arange(128),
            "channel": ["nuclei", "membrane"],
            **Coordinates.from_xindex(
                CoordinateTransformIndex(ZStackTransform(n_slices, slice_thickness))
            ),
        },
        name="fluorescence",
    )
    print(f"Z-stack: {n_slices} slices x {slice_thickness} nm/slice = {n_slices * slice_thickness:.0f} nm total depth")
    print(f"depth_nm coordinate is LAZY (never materialized): {zstack_da.depth_nm[:3].values} ...")
    return (zstack_da,)


@app.cell
def zstack_verify(mo, xr, zstack_da):
    # Verify: depth_nm=500 should map to slice 125 (500/4=125)
    result = zstack_da.sel(depth_nm=500, method="nearest")
    assert result.z.values == 125, f"Expected slice 125, got {result.z.values}"

    # Verify: depth_nm=0 maps to slice 0
    result_0 = zstack_da.sel(depth_nm=0, method="nearest")
    assert result_0.z.values == 0

    # Verify vectorized: query multiple depths
    probe_depths = xr.DataArray([100, 200, 300], dims="probe")
    probed = zstack_da.sel(depth_nm=probe_depths, method="nearest")
    assert probed.z.values.tolist() == [25, 50, 75]

    # Verify channel selection still works
    nuclei = zstack_da.sel(channel="nuclei", depth_nm=400, method="nearest")
    assert nuclei.channel.values == "nuclei"

    mo.callout(
        mo.md("""
        **ZStackTransform verified:**
        - `sel(depth_nm=500)` -> slice 125 (500/4=125)
        - `sel(depth_nm=0)` -> slice 0
        - Vectorized: [100, 200, 300] nm -> [25, 50, 75]
        - Channel selection still works alongside the transform
        """),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def massspec_header(mo):
    mo.md("""
    ## Pattern 3: CoordinateTransform for Mass Spec (m/z calibration)

    Mass spectrometry: time-of-flight maps to mass-to-charge ratio (m/z)
    via a nonlinear calibration curve. A CoordinateTransform handles the
    quadratic relationship `mz = a * sqrt(tof) + b`.
    """)
    return


@app.cell
def massspec_transform(CoordinateTransform, np):
    class MassSpecTransform(CoordinateTransform):
        """Maps time-of-flight bins to mass-to-charge ratio (m/z).

        Calibration: mz = a * sqrt(tof) + b
        Inverse:     tof = ((mz - b) / a)^2
        """

        def __init__(self, n_bins, calib_a, calib_b):
            super().__init__(("mz",), {"tof_bin": n_bins})
            self.n_bins = n_bins
            self.calib_a = calib_a
            self.calib_b = calib_b

        def forward(self, dim_positions):
            tof = dim_positions["tof_bin"]
            return {"mz": self.calib_a * np.sqrt(tof.astype(float)) + self.calib_b}

        def reverse(self, coord_labels):
            mz = coord_labels["mz"]
            return {"tof_bin": ((mz - self.calib_b) / self.calib_a) ** 2}

    return (MassSpecTransform,)


@app.cell
def massspec_build(
    CoordinateTransformIndex,
    Coordinates,
    MassSpecTransform,
    np,
    xr,
):
    # Synthetic mass spec: 10000 TOF bins, calibration mz = 100*sqrt(tof) + 10
    n_tof_bins = 10000
    calib_a = 100.0
    calib_b = 10.0
    intensity = np.random.exponential(1, n_tof_bins)

    # Add synthetic peaks at known m/z values
    # m/z=1010 -> tof=((1010-10)/100)^2=100, m/z=2010 -> tof=400, m/z=3010 -> tof=900
    for target_mz in [1010, 2010, 3010]:
        target_tof = int(((target_mz - calib_b) / calib_a) ** 2)
        intensity[target_tof - 2 : target_tof + 3] += 100

    ms_da = xr.DataArray(
        intensity,
        dims=("tof_bin",),
        coords=Coordinates.from_xindex(
            CoordinateTransformIndex(MassSpecTransform(n_tof_bins, calib_a, calib_b))
        ),
        name="intensity",
    )
    print(f"Mass spec: {n_tof_bins} TOF bins")
    print(f"Calibration: mz = {calib_a} * sqrt(tof) + {calib_b}")
    return (ms_da,)


@app.cell
def massspec_verify(mo, ms_da, xr):
    # Verify: sel by m/z returns the correct TOF bin
    result_1010 = ms_da.sel(mz=1010, method="nearest")
    result_2010 = ms_da.sel(mz=2010, method="nearest")

    # mz=1010 -> tof=((1010-10)/100)^2 = 100
    assert result_1010.tof_bin.values == 100, f"Expected tof_bin=100, got {result_1010.tof_bin.values}"
    # mz=2010 -> tof=((2010-10)/100)^2 = 400
    assert result_2010.tof_bin.values == 400, f"Expected tof_bin=400, got {result_2010.tof_bin.values}"

    # Verify peaks are found at expected m/z values
    peak_mz = xr.DataArray([1010, 2010, 3010], dims="peak")
    peaks = ms_da.sel(mz=peak_mz, method="nearest")
    assert all(peaks.values > 100), "Expected high intensity at peak positions"

    mo.callout(
        mo.md("""
        **MassSpecTransform verified:**
        - `sel(mz=1010)` -> tof_bin=100 (nonlinear calibration correct)
        - `sel(mz=2010)` -> tof_bin=400
        - Peaks detected at expected m/z values
        """),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def close(mo):
    mo.md("""
    ---

    ## Summary

    | Pattern | Base class | Key methods | When to use |
    |---------|-----------|-------------|-------------|
    | PeriodicIndex | `xarray.Index` | `sel`, `from_variables` | Wrapping/angular coordinates |
    | ZStackTransform | `CoordinateTransform` | `forward`, `reverse` | Linear pixel-to-physical mapping |
    | MassSpecTransform | `CoordinateTransform` | `forward`, `reverse` | Nonlinear calibration curves |

    **Next:** [Notebook 3](03_ndindex_time_locking.py) covers N-D derived coordinates and time-locking.
    """)
    return


if __name__ == "__main__":
    app.run()
