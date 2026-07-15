# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "xarray>=2025.1.0",
#     "wigglystuff==0.5.16",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium", app_title="NDIndex and Time-Locking")


@app.cell(hide_code=True)
def hero(mo):
    mo.md("""
    <div style="
        background: linear-gradient(135deg, #0d1117 0%, #1a3a2e 50%, #0d4f3c 100%);
        border-radius: 16px;
        padding: 48px 40px;
        margin: -16px -16px 24px -16px;
    ">
        <div style="font-size: 14px; color: #2ee4a0; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px;">
            xarray-linked-data &middot; Notebook 3
        </div>
        <h1 style="color: #f0f9ff; font-size: 2.4rem; margin: 0 0 16px 0; line-height: 1.2;">
            N-D Derived Coordinates &amp; Time-Locking
        </h1>
        <p style="color: #8fcfab; font-size: 1.1rem; margin: 0; max-width: 640px; line-height: 1.6;">
            Build NDIndex for coordinates spanning multiple dimensions.
            Time-lock experimental measurements to dosing events across trials.
        </p>
    </div>
    """)
    return


@app.cell(hide_code=True)
def cell_tour(mo):
    import wigglystuff

    tour = wigglystuff.CellTour(
        steps=[
            {"cell_name": "hero", "title": "N-D Derived Coordinates", "description": "Coordinates spanning multiple dimensions need a custom index."},
            {"cell_name": "ndindex_class", "title": "NDIndex", "description": "An Index subclass that searches N-D arrays for value lookups."},
            {"cell_name": "build_trial_data", "title": "Trial Data", "description": "Absolute time computed from trial onset + relative time (2-D coordinate)."},
            {"cell_name": "verify_ndindex", "title": "Selection Verified", "description": "sel(abs_time=245) finds the right trial and relative time."},
            {"cell_name": "timelock_build", "title": "Time-Locking", "description": "Multiple event-locked coordinates registered under one NDIndex."},
            {"cell_name": "timelock_verify", "title": "Events Verified", "description": "Select relative to dose or response events -- no data duplication."},
            {"cell_name": "epoch_demo", "title": "Epoching", "description": "Extract windows around events and average across trials."},
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
    from xarray import Index
    from xarray.core.indexing import IndexSelResult
    from xarray.core.variable import Variable

    return Index, IndexSelResult, Variable, mo, np, xr


@app.cell(hide_code=True)
def intro(mo):
    mo.md(r"""
    ## The problem: N-D derived coordinates

    In trial-based experiments, absolute time is computed from two 1-D
    coordinates: trial onset time + relative time within the trial.
    The result is a **2-D coordinate** `abs_time(trial, rel_time)`.

    xarray's default `PandasIndex` only handles 1-D coordinates. An `NDIndex`
    enables `ds.sel(abs_time=7.5)` against the 2-D array.

    This pattern enables **time-locking**: selecting data relative to
    arbitrary events (dose administration, stimulus onset, response time)
    without reshaping or duplicating data.
    """)
    return


@app.cell
def ndindex_class(Index, IndexSelResult, Variable, np):
    class NDIndex(Index):
        """Index for N-D derived coordinates (ndim >= 2).

        Enables label-based selection on coordinates that span multiple
        dimensions, e.g. abs_time(trial, rel_time).
        """

        def __init__(self, nd_coords, slice_method="bounding_box"):
            self._nd_coords = nd_coords
            self._slice_method = slice_method

        @classmethod
        def from_variables(cls, variables, *, options):
            slice_method = (
                options.get("slice_method", "bounding_box") if options else "bounding_box"
            )
            nd_coords = {}
            for nd_name, nd_var in variables.items():
                if nd_var.ndim < 2:
                    raise ValueError(
                        f"NDIndex requires ndim >= 2, got '{nd_name}' with ndim={nd_var.ndim}"
                    )
                nd_coords[nd_name] = (nd_var.dims, nd_var.values)
            return cls(nd_coords, slice_method=slice_method)

        def create_variables(self, variables):
            return {
                nd_name: Variable(nd_dims, nd_vals)
                for nd_name, (nd_dims, nd_vals) in self._nd_coords.items()
            }

        def sel(self, labels, method=None, tolerance=None):
            dim_indexers = {}
            for nd_name, (nd_dims, nd_values) in self._nd_coords.items():
                if nd_name not in labels:
                    continue
                nd_value = labels[nd_name]
                if isinstance(nd_value, slice):
                    nd_start = nd_value.start if nd_value.start is not None else nd_values.min()
                    nd_stop = nd_value.stop if nd_value.stop is not None else nd_values.max()
                    in_range = (nd_values >= nd_start) & (nd_values <= nd_stop)
                    for dim_i, dim_name in enumerate(nd_dims):
                        reduce_axes = tuple(j for j in range(nd_values.ndim) if j != dim_i)
                        has_match = np.any(in_range, axis=reduce_axes)
                        match_idxs = np.where(has_match)[0]
                        dim_indexers[dim_name] = slice(int(match_idxs[0]), int(match_idxs[-1]) + 1)
                else:
                    if method == "nearest":
                        flat_idx = int(np.argmin(np.abs(nd_values - float(nd_value))))
                    else:
                        matches = np.flatnonzero(nd_values == nd_value)
                        if len(matches) == 0:
                            raise KeyError(f"Value {nd_value} not found in {nd_name}")
                        flat_idx = int(matches[0])
                    indices = np.unravel_index(flat_idx, nd_values.shape)
                    for dim_name, dim_idx in zip(nd_dims, indices):
                        dim_indexers[dim_name] = slice(int(dim_idx), int(dim_idx) + 1)
            return IndexSelResult(dim_indexers)

        def isel(self, indexers):
            new_coords = {}
            for nd_name, (nd_dims, nd_values) in self._nd_coords.items():
                idx_tuple = []
                new_dims_list = []
                for dim_name in nd_dims:
                    if dim_name in indexers:
                        idx_val = indexers[dim_name]
                        idx_tuple.append(idx_val)
                        if not isinstance(idx_val, (int, np.integer)):
                            new_dims_list.append(dim_name)
                    else:
                        idx_tuple.append(slice(None))
                        new_dims_list.append(dim_name)
                new_values = nd_values[tuple(idx_tuple)]
                if new_values.ndim >= 2:
                    new_coords[nd_name] = (tuple(new_dims_list), new_values)
            if not new_coords:
                return None
            return NDIndex(new_coords, slice_method=self._slice_method)

        def should_add_coord_to_array(self, name, var, dims):
            return True

    return (NDIndex,)


@app.cell(hide_code=True)
def trial_header(mo):
    mo.md("""
    ## Building trial-based experimental data

    We simulate a dosing time-course study: multiple trials, each with
    a continuous measurement over relative time. The absolute time of
    each measurement is `trial_onset + rel_time`.
    """)
    return


@app.cell
def build_trial_data(np, xr):
    # 10 trials, each with 50 time points (0 to 49 seconds relative)
    n_trials = 10
    n_rel_times = 50
    rel_times = np.arange(n_rel_times, dtype=float)  # 0, 1, 2, ... 49 seconds

    # Each trial starts at a different onset time
    trial_onsets = np.arange(n_trials) * 100.0  # trial 0 at t=0, trial 1 at t=100, etc.

    # Compute 2-D absolute time coordinate
    abs_time = trial_onsets[:, None] + rel_times[None, :]  # shape (trial, rel_time)

    # Synthetic measurement: oscillating signal with trial-specific amplitude
    trial_amplitudes = np.random.uniform(0.5, 2.0, n_trials)
    signal = np.zeros((n_trials, n_rel_times))
    for trial_i in range(n_trials):
        signal[trial_i] = trial_amplitudes[trial_i] * np.sin(rel_times * 0.3) + np.random.normal(0, 0.1, n_rel_times)

    trial_ds = xr.Dataset(
        data_vars={"signal": (["trial", "rel_time"], signal)},
        coords={
            "trial": [f"trial_{trial_j:02d}" for trial_j in range(n_trials)],
            "rel_time": rel_times,
            "trial_onset": ("trial", trial_onsets),
            "abs_time": (["trial", "rel_time"], abs_time),
        },
    )
    print(f"Trial data: {n_trials} trials x {n_rel_times} time points")
    print(f"Trial onsets: {trial_onsets}")
    print(f"abs_time range: {abs_time.min():.0f} - {abs_time.max():.0f} seconds")
    return rel_times, trial_ds, trial_onsets


@app.cell
def attach_ndindex(NDIndex, trial_ds):
    # Register the 2-D abs_time coordinate under NDIndex
    trial_ds_indexed = trial_ds.set_xindex(["abs_time"], NDIndex)
    print("NDIndex attached. Now sel(abs_time=...) works on the 2-D coordinate.")
    return (trial_ds_indexed,)


@app.cell
def verify_ndindex(mo, trial_ds_indexed):
    # Verify: sel(abs_time=250) should find trial=2 (onset=200), rel_time=50... wait
    # trial_onsets = [0, 100, 200, ...], so abs_time=250 -> trial=2, rel_time=50
    # But rel_time goes 0..49, so rel_time=50 doesn't exist. Let's pick 245.
    # trial=2 (onset=200), rel_time=45 -> abs_time=245
    result = trial_ds_indexed.sel(abs_time=245, method="nearest")
    assert result.trial.values == "trial_02", f"Expected trial_02, got {result.trial.values}"
    assert result.rel_time.values == 45, f"Expected rel_time=45, got {result.rel_time.values}"

    # Verify with a value in trial 5: onset=500, abs_time=530 -> rel_time=30
    result2 = trial_ds_indexed.sel(abs_time=530, method="nearest")
    assert result2.trial.values == "trial_05", f"Expected trial_05, got {result2.trial.values}"
    assert result2.rel_time.values == 30, f"Expected rel_time=30, got {result2.rel_time.values}"

    mo.callout(
        mo.md("""
        **NDIndex verified:**
        - `sel(abs_time=245)` -> trial_02, rel_time=45 (200+45=245)
        - `sel(abs_time=530)` -> trial_05, rel_time=30 (500+30=530)
        """),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def timelock_header(mo):
    mo.md("""
    ## Time-locking to events

    The real power: define **multiple event-locked coordinates** and
    register them all under one NDIndex. Then you can select data relative
    to any event without reshaping.
    """)
    return


@app.cell
def timelock_build(NDIndex, np, rel_times, trial_ds, trial_onsets):
    # Define dosing events: dose_time is when the drug was administered in each trial
    # Dose happens at rel_time=10 in each trial
    dose_rel_times = np.full(len(trial_onsets), 10.0)

    # dose_locked: time relative to dose administration
    dose_locked = (
        rel_times[None, :] - dose_rel_times[:, None]
    )  # shape (trial, rel_time)

    # Also define a "response" event at rel_time=25
    response_rel_times = np.full(len(trial_onsets), 25.0)
    response_locked = rel_times[None, :] - response_rel_times[:, None]

    timelock_ds = trial_ds.assign_coords(
        {
            "dose_locked": (["trial", "rel_time"], dose_locked),
            "response_locked": (["trial", "rel_time"], response_locked),
        }
    )

    # Register all 2-D coords under one NDIndex
    timelock_ds = timelock_ds.set_xindex(
        ["abs_time", "dose_locked", "response_locked"], NDIndex
    )
    print("Time-locked coordinates registered:")
    print("  abs_time: absolute time from experiment start")
    print(
        "  dose_locked: time relative to dose administration (0 = dose moment)"
    )
    print(
        "  response_locked: time relative to response event (0 = response moment)"
    )
    return (timelock_ds,)


@app.cell
def timelock_verify(mo, timelock_ds):
    # Select data 5 seconds AFTER dose in each trial
    post_dose = timelock_ds.sel(dose_locked=5, method="nearest")
    # dose_locked=5 means rel_time - 10 = 5, so rel_time = 15
    assert post_dose.rel_time.values == 15, f"Expected rel_time=15, got {post_dose.rel_time.values}"

    # Select data 3 seconds BEFORE response in each trial
    pre_response = timelock_ds.sel(response_locked=-3, method="nearest")
    # response_locked=-3 means rel_time - 25 = -3, so rel_time = 22
    assert pre_response.rel_time.values == 22, f"Expected rel_time=22, got {pre_response.rel_time.values}"

    # Slice: -5 to +10 seconds around dose
    dose_window = timelock_ds.sel(dose_locked=slice(-5, 10))
    # dose_locked=-5 -> rel_time=5, dose_locked=10 -> rel_time=20
    assert dose_window.rel_time.values[0] == 5, f"Expected first rel_time=5"
    assert dose_window.rel_time.values[-1] == 20, f"Expected last rel_time=20"

    mo.callout(
        mo.md("""
        **Time-locking verified:**
        - `sel(dose_locked=5)` -> rel_time=15 (5s after dose at t=10)
        - `sel(response_locked=-3)` -> rel_time=22 (3s before response at t=25)
        - `sel(dose_locked=slice(-5, 10))` -> rel_time 5 to 20

        The same data can be queried relative to **any** event without duplication.
        """),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def epoching_header(mo):
    mo.md("""
    ## Epoching: averaging across trials

    Time-locking enables epoching -- extracting a window around an event
    and averaging across trials. This is the standard analysis for
    event-related potentials (ERPs) in neuroscience and dosing studies.
    """)
    return


@app.cell
def epoch_demo(mo, timelock_ds):
    # Extract -10 to +20 second window around dose
    epoch = timelock_ds.sel(dose_locked=slice(-10, 20))
    # Average signal across trials
    avg_signal = epoch["signal"].mean(dim="trial")
    # The dose_locked coordinate is now the x-axis
    dose_locked_axis = epoch.dose_locked.mean(dim="trial").values

    # Compare pre-dose vs post-dose variance (synthetic data: no dose effect expected)
    pre_dose_var = epoch["signal"].where(epoch.dose_locked < 0).var(dim=["trial", "rel_time"]).values
    post_dose_var = epoch["signal"].where(epoch.dose_locked >= 0).var(dim=["trial", "rel_time"]).values

    mo.md(
        f"""
        **Epoching result** (-10s to +20s around dose):

        - Window size: {epoch.sizes['rel_time']} time points
        - Trials averaged: {epoch.sizes['trial']}
        - Pre-dose signal variance: **{pre_dose_var:.4f}**
        - Post-dose signal variance: **{post_dose_var:.4f}**

        The same `dose_locked` coordinate enables clean epoch extraction and
        trial-averaging without manual time-point alignment.
        """
    )
    return


@app.cell(hide_code=True)
def close(mo):
    mo.md("""
    ---

    ## Summary

    NDIndex enables selection on **N-dimensional derived coordinates**:
    values computed from other coordinates that span multiple dimensions.

    **Key use case: time-locking** -- the same data can be queried relative
    to any event (dose, stimulus, response) by registering multiple locked
    coordinates under one NDIndex. No reshaping, no duplication.

    **Next:** [Notebook 4](04_linked_intervals_cross_slicing.py) covers
    DimensionInterval for linked interval cross-slicing.
    """)
    return


if __name__ == "__main__":
    app.run()
