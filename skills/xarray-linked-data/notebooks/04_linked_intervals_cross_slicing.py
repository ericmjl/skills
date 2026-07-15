# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pandas",
#     "xarray>=2025.1.0",
#     "wigglystuff==0.5.16",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="medium",
    app_title="Linked Intervals and Cross-Slicing",
)


@app.cell(hide_code=True)
def hero(mo):
    mo.md("""
    <div style="
        background: linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%);
        border-radius: 16px;
        padding: 48px 40px;
        margin: -16px -16px 24px -16px;
    ">
        <div style="font-size: 14px; color: #e94e77; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px;">
            xarray-linked-data &middot; Notebook 4
        </div>
        <h1 style="color: #f0f9ff; font-size: 2.4rem; margin: 0 0 16px 0; line-height: 1.2;">
            Linked Intervals &amp; Cross-Slicing
        </h1>
        <p style="color: #c4a6d8; font-size: 1.1rem; margin: 0; max-width: 640px; line-height: 1.6;">
            Build a DimensionInterval index that links concentration ranges
            to time intervals. Selecting on one dimension automatically
            constrains all others to overlapping values.
        </p>
    </div>
    """)
    return


@app.cell(hide_code=True)
def cell_tour(mo):
    import wigglystuff

    tour = wigglystuff.CellTour(
        steps=[
            {"cell_name": "hero", "title": "Linked Intervals", "description": "DimensionInterval: selecting on one dimension constrains all others."},
            {"cell_name": "dimensioninterval_class", "title": "DimensionInterval Index", "description": "A meta-index that links interval coordinates over a shared continuous dimension."},
            {"cell_name": "build_dose_timecourse", "title": "Dose-Response Data", "description": "Time-course with dose levels administered over sequential windows."},
            {"cell_name": "verify_cross_slicing", "title": "Cross-Slicing", "description": "Selecting on time constrains dose levels and vice versa."},
            {"cell_name": "epoch_demo", "title": "Dose Epoching", "description": "Extract per-dose response windows with a single sel() call."},
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
    import pandas as pd
    import xarray as xr
    from xarray import Index
    from xarray.core.indexes import PandasIndex
    from xarray.core.indexing import IndexSelResult

    return Index, IndexSelResult, PandasIndex, mo, np, pd, xr


@app.cell(hide_code=True)
def intro(mo):
    mo.md(r"""
    ## The problem: linked intervals

    In dose-response time-course experiments, each concentration level is
    administered over a **time window**. Selecting a concentration range
    should automatically constrain the time axis to measurements taken
    during that concentration's administration window.

    A `DimensionInterval` index links multiple interval-typed dimensions
    over a shared continuous dimension. Selecting on any one constrains
    all others to overlapping values.
    """)
    return


@app.cell
def dimensioninterval_class(Index, IndexSelResult, PandasIndex, np, pd):
    from dataclasses import dataclass, field
    from collections import defaultdict

    _MISSING = object()

    def merge_sel_results(results):
        dim_indexers = {}
        drop_coords = []
        for res in results:
            dim_indexers.update(res.dim_indexers)
            drop_coords += res.drop_coords
        return IndexSelResult(dim_indexers, drop_coords=drop_coords)

    @dataclass
    class IntervalDimInfo:
        dim_name: str
        coord_name: str
        interval_index: PandasIndex
        label_indexes: dict = field(default_factory=dict)

    class DimensionInterval(Index):
        """Links multiple interval dimensions over a shared continuous dimension.

        Selecting on any dimension constrains all others to overlapping values.
        """

        def __init__(self, continuous_index, continuous_dim_name, interval_dims,
                     coord_to_dim=None, label_to_dim=None):
            self._continuous_index = continuous_index
            self._continuous_name = continuous_dim_name
            self._interval_dims = interval_dims
            self._coord_to_dim = coord_to_dim or {
                info.coord_name: dn for dn, info in interval_dims.items()
            }
            self._label_to_dim = label_to_dim or {
                ln: dn for dn, info in interval_dims.items() for ln in info.label_indexes
            }

        @classmethod
        def from_variables(cls, variables, *, options):
            vars_by_dim = defaultdict(list)
            interval_coords = {}
            for vi_name, vi_var in variables.items():
                assert vi_var.ndim == 1
                vi_dim = str(vi_var.dims[0])
                vars_by_dim[vi_dim].append((vi_name, vi_var))
                if isinstance(vi_var.dtype, pd.IntervalDtype):
                    interval_coords[vi_name] = vi_dim

            all_dims = list(vars_by_dim.keys())
            int_dim_names = set(interval_coords.values())
            cont_dims = [d for d in all_dims if d not in int_dim_names]
            assert len(cont_dims) == 1, f"Expected 1 continuous dim, got {cont_dims}"
            cont_dim = cont_dims[0]

            cont_name, cont_var = vars_by_dim[cont_dim][0]
            cont_idx = PandasIndex.from_variables({cont_name: cont_var}, options=options)

            interval_dims_dict = {}
            for ic_name, ic_dim in interval_coords.items():
                dim_vars = vars_by_dim[ic_dim]
                int_idx = None
                label_idxs = {}
                for vn, vv in dim_vars:
                    if vn == ic_name:
                        int_idx = PandasIndex.from_variables({vn: vv}, options=options)
                    else:
                        label_idxs[vn] = PandasIndex.from_variables({vn: vv}, options=options)
                interval_dims_dict[ic_dim] = IntervalDimInfo(ic_dim, ic_name, int_idx, label_idxs)

            return cls(cont_idx, cont_dim, interval_dims_dict)

        def create_variables(self, variables):
            idx_vars = {}
            idx_vars.update(self._continuous_index.create_variables(variables))
            for info in self._interval_dims.values():
                idx_vars.update(info.interval_index.create_variables(variables))
                for li_idx in info.label_indexes.values():
                    idx_vars.update(li_idx.create_variables(variables))
            return idx_vars

        @staticmethod
        def _interval_min_max(intervals):
            if isinstance(intervals, pd.IntervalIndex):
                return pd.Interval(intervals[0].left, intervals[-1].right, closed=intervals.closed)
            return intervals

        def sel(self, labels, method=None, tolerance=None):
            results = []
            time_range = None

            for sel_key, sel_value in labels.items():
                if sel_key == self._continuous_name:
                    cont_res = self._continuous_index.sel({sel_key: sel_value}, method=method)
                    results.append(cont_res)
                    indexer = cont_res.dim_indexers[self._continuous_name]
                    if isinstance(indexer, slice):
                        tv = self._continuous_index.index[indexer]
                        time_range = pd.Interval(tv.min(), tv.max(), closed="both")

                elif ((dn := self._coord_to_dim.get(sel_key, _MISSING)) is not _MISSING or
                      (dn := self._label_to_dim.get(sel_key, _MISSING)) is not _MISSING):
                    info = self._interval_dims[dn]
                    sel_idx = info.label_indexes.get(sel_key, info.interval_index)
                    sel_res = sel_idx.sel({sel_key: sel_value}, method=method)
                    results.append(sel_res)
                    indexer = sel_res.dim_indexers[dn]
                    sel_intervals = info.interval_index.index[indexer]
                    interval_range = self._interval_min_max(sel_intervals)
                    if time_range is None:
                        time_range = interval_range
                    else:
                        time_range = pd.Interval(
                            max(time_range.left, interval_range.left),
                            min(time_range.right, interval_range.right),
                            closed=interval_range.closed,
                        )

            if time_range is not None:
                if self._continuous_name not in labels:
                    ts = slice(time_range.left, time_range.right)
                    cont_res = self._continuous_index.sel({self._continuous_name: ts})
                    results.append(cont_res)

                selected_dims = set()
                for sel_key in labels:
                    if sel_key in self._coord_to_dim:
                        selected_dims.add(self._coord_to_dim[sel_key])
                    if sel_key in self._label_to_dim:
                        selected_dims.add(self._label_to_dim[sel_key])

                for id_name, id_info in self._interval_dims.items():
                    if id_name in selected_dims:
                        continue
                    overlaps = id_info.interval_index.index.overlaps(
                        pd.Interval(time_range.left, time_range.right, closed="both")
                    )
                    overlap_idxs = np.where(overlaps)[0]
                    if len(overlap_idxs) > 0:
                        results.append(IndexSelResult({id_name: slice(int(overlap_idxs[0]), int(overlap_idxs[-1]) + 1)}))

            return merge_sel_results(results)

        def should_add_coord_to_array(self, name, var, dims):
            return True

    return (DimensionInterval,)


@app.cell(hide_code=True)
def data_header(mo):
    mo.md("""
    ## Building dose-response time-course data

    We simulate a stepped dose-response experiment: each concentration
    level is administered over a specific time window, and measurements
    are taken continuously throughout.
    """)
    return


@app.cell
def build_dose_timecourse(np, pd, xr):
    # Continuous time axis: 0-240 minutes, 1-min resolution
    time_points = np.arange(0, 240, dtype=float)

    # Dose levels administered in sequence (each over a time window)
    dose_labels = ["baseline", "low", "medium", "high", "washout"]
    dose_intervals = pd.IntervalIndex.from_breaks(
        [0, 30, 80, 140, 200, 240], closed="left"
    )

    # Measurement timepoints within each dose window (offset from dose start)
    meas_labels = [f"window_{mw}" for mw in range(5)]
    meas_intervals = pd.IntervalIndex.from_breaks(
        [10, 45, 95, 155, 210, 235], closed="left"
    )

    # Synthetic signal: baseline + dose-dependent response
    dose_responses = {"baseline": 0.1, "low": 0.5, "medium": 1.2, "high": 2.0, "washout": 0.3}
    signal = np.full(240, 0.1)
    for di_idx, di_label in enumerate(dose_labels):
        mask = (time_points >= dose_intervals[di_idx].left) & (time_points < dose_intervals[di_idx].right)
        signal[mask] = dose_responses[di_label] + np.random.normal(0, 0.05, mask.sum())

    dose_ds = xr.Dataset(
        data_vars={"response": (["time"], signal)},
        coords={
            "time": time_points,
            "dose_intervals": ("dose_level", dose_intervals),
            "dose_level": dose_labels,
            "meas_intervals": ("meas_window", meas_intervals),
            "meas_window": meas_labels,
        },
    )
    print(f"Dose-response time-course: {len(time_points)} time points")
    print(f"Dose levels: {dose_labels}")
    print(f"Windows: {[f'[{iv.left},{iv.right})' for iv in dose_intervals]}")
    return (dose_ds,)


@app.cell
def attach_diminterval(DimensionInterval, dose_ds):
    # Attach DimensionInterval linking time, dose_level, and meas_window
    dose_ds_linked = dose_ds.drop_indexes(["time", "dose_level"]).set_xindex(
        ["time", "dose_intervals", "dose_level", "meas_intervals", "meas_window"],
        DimensionInterval,
    )
    print("DimensionInterval attached. Selecting on any dimension constrains all others.")
    return (dose_ds_linked,)


@app.cell
def verify_cross_slicing(dose_ds_linked, mo, pd):
    # Verify: selecting a time range constrains dose_level to overlapping windows
    time_slice = dose_ds_linked.sel(time=slice(50, 100))
    # Time 50-100 overlaps with "low" [30,80) and "medium" [80,140)
    assert "low" in time_slice.dose_level.values, f"Expected 'low' in dose levels, got {time_slice.dose_level.values}"
    assert "medium" in time_slice.dose_level.values, f"Expected 'medium' in dose levels"

    # Verify: selecting a dose level constrains time to its window
    high_only = dose_ds_linked.sel(dose_level="high")
    # "high" window is [140, 200)
    assert high_only.time.values[0] >= 140, f"Expected time >= 140, got {high_only.time.values[0]}"
    assert high_only.time.values[-1] < 200, f"Expected time < 200, got {high_only.time.values[-1]}"

    # Verify: selecting a dose interval by value constrains everything
    medium_interval = dose_ds_linked.sel(dose_intervals=pd.Interval(80, 140, closed="left"))
    assert "medium" in medium_interval.dose_level.values

    mo.callout(
        mo.md("""
        **Cross-slicing verified:**
        - `sel(time=slice(50, 100))` constrains dose_level to ["low", "medium"]
        - `sel(dose_level="high")` constrains time to [140, 200)
        - `sel(dose_intervals=Interval(80,140))` constrains dose_level to ["medium"]

        Selecting on ANY dimension automatically constrains ALL others.
        """),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def epoching_header(mo):
    mo.md("""
    ## Dose-response epoching

    With linked intervals, extracting a response window around each dose
    change is a single `.sel()` call. No manual time-point tracking.
    """)
    return


@app.cell
def epoch_demo(dose_ds_linked, mo):
    # Extract the medium dose window
    medium_data = dose_ds_linked.sel(dose_level="medium")
    medium_response = medium_data["response"].values
    medium_time = medium_data.time.values

    # Compare mean response per dose level
    dose_means = {}
    for dl in ["baseline", "low", "medium", "high", "washout"]:
        dl_data = dose_ds_linked.sel(dose_level=dl)
        dose_means[dl] = float(dl_data["response"].mean().values)

    # Verify dose means are in expected ranges (synthetic data has known means)
    assert 0.0 < dose_means['baseline'] < 0.3, f"Baseline unexpected: {dose_means['baseline']}"
    assert 1.0 < dose_means['medium'] < 1.4, f"Medium unexpected: {dose_means['medium']}"
    assert 1.8 < dose_means['high'] < 2.2, f"High unexpected: {dose_means['high']}"

    mo.md(
        f"""
        **Dose-response epoching:**

        Mean response by dose level:
        - Baseline: **{dose_means['baseline']:.3f}**
        - Low: **{dose_means['low']:.3f}**
        - Medium: **{dose_means['medium']:.3f}**
        - High: **{dose_means['high']:.3f}**
        - Washout: **{dose_means['washout']:.3f}**

        Each extraction is a single `.sel(dose_level=...)` call. The linked
        interval index handles all time-window constraining automatically.
        """
    )
    return


@app.cell(hide_code=True)
def close(mo):
    mo.md("""
    ---

    ## Summary

    DimensionInterval links interval-typed dimensions over a shared
    continuous axis. It enables **cross-slicing**: selecting on any
    dimension automatically constrains all linked dimensions.

    **Key use cases:**
    - Dose-response time-courses (concentration x time linking)
    - Event-locked experimental windows
    - Hierarchical annotation linking (e.g., words x phonemes x time)

    **Next:** [Notebook 5](05_cross_experiment_datatree.py) covers
    DataTree for heterogeneous multi-assay data.
    """)
    return


if __name__ == "__main__":
    app.run()
