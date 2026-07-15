# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy==2.5.1",
#     "pandas==3.0.3",
#     "xarray==2026.7.0",
#     "scipy==1.18.0",
#     "matplotlib",
#     "wigglystuff==0.5.16",
#     "plotly==6.9.0",
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
            {"cell_name": "dose_timecourse_plot", "title": "The Data, Visualized", "description": "Stepped dose-response over time -- dose windows (solid) and offset measurement windows (dotted) sharing the time axis."},
            {"cell_name": "verify_cross_slicing", "title": "Cross-Slicing", "description": "Selecting on time constrains dose levels and vice versa."},
            {"cell_name": "crossslice_query", "title": "Explorer Controls", "description": "Pick which dimension to slice on."},
            {"cell_name": "crossslice_plot", "title": "Linked Dimensions Constrain", "description": "Watch selecting one axis highlight the surviving dose levels and measurement windows."},
            {"cell_name": "epoch_demo", "title": "Dose-Response Fit", "description": "Extract per-dose windows with one .sel() call, then fit a sigmoidal dose-response curve."},
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
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from scipy.optimize import curve_fit


    return (
        Index,
        IndexSelResult,
        PandasIndex,
        curve_fit,
        go,
        make_subplots,
        mo,
        np,
        pd,
        xr,
    )


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

    # Synthetic signal: baseline + dose-dependent response.
    # Seeded RNG for reproducible renders (matches nb03).
    rng = np.random.default_rng(42)
    dose_responses = {"baseline": 0.1, "low": 0.5, "medium": 1.2, "high": 2.0, "washout": 0.3}
    signal = np.full(240, 0.1)
    for di_idx, di_label in enumerate(dose_labels):
        mask = (time_points >= dose_intervals[di_idx].left) & (time_points < dose_intervals[di_idx].right)
        signal[mask] = dose_responses[di_label] + rng.normal(0, 0.05, mask.sum())

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


@app.cell(hide_code=True)
def dose_timecourse_plot(dose_ds, go, mo, np):
    _time = np.asarray(dose_ds.time.values, dtype=float)
    _resp = np.asarray(dose_ds.response.values, dtype=float)
    _dose_labels = list(np.asarray(dose_ds.dose_level.values).astype(str))
    _dose_iv = np.asarray(dose_ds.dose_intervals.values)
    _meas_iv = np.asarray(dose_ds.meas_intervals.values)
    _meas_labels = list(np.asarray(dose_ds.meas_window.values).astype(str))

    _palette = ["#5b6478", "#c4a6d8", "#e94e77", "#7c3aed", "#3a5a40"]
    _ink = "#f0f9ff"

    _fig = go.Figure()
    _fig.add_trace(go.Scatter(
        x=_time, y=_resp, mode="lines",
        line=dict(color="#9aa5b8", width=2),
        name="response",
        hovertemplate="t=%{x:.0f} min<br>response=%{y:.2f}<extra></extra>",
    ))
    # dose administration windows (solid band, labelled at top)
    for _lab, _iv, _col in zip(_dose_labels, _dose_iv, _palette):
        _fig.add_vrect(
            x0=float(_iv.left), x1=float(_iv.right),
            fillcolor=_col, opacity=0.18, layer="below", line_width=0,
        )
        _fig.add_annotation(
            x=(float(_iv.left) + float(_iv.right)) / 2, y=_resp.max() * 1.10,
            text=_lab, showarrow=False, font=dict(size=10, color=_col),
        )
    # measurement windows (dashed bracket along the bottom)
    for _lab, _iv in zip(_meas_labels, _meas_iv):
        _fig.add_shape(
            type="line", x0=float(_iv.left), x1=float(_iv.right),
            y0=0, y1=0, layer="below",
            line=dict(color="#8ab4d8", width=2, dash="dot"),
        )
        _fig.add_annotation(
            x=(float(_iv.left) + float(_iv.right)) / 2, y=-0.06,
            text=_lab.replace("window_", "w"), showarrow=False,
            textangle=-90, font=dict(size=8, color="#8ab4d8"),
        )

    _fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)", font=dict(color=_ink, size=12),
        margin=dict(l=45, r=20, t=24, b=55), height=380, showlegend=False,
        xaxis=dict(title="time (min)", range=[-4, 244]),
        yaxis=dict(title="response", range=[-0.12, _resp.max() * 1.22]),
    )

    mo.vstack([
        _fig,
        mo.md(
            "A stepped dose-response: each concentration is administered over a "
            "sequential time window (solid shaded band, labelled above), and response "
            "is measured continuously. The **measurement windows** (dotted brackets "
            "below) are deliberately offset from the dose windows. The `DimensionInterval` "
            "index links all three axes -- `time`, `dose_level`, `meas_window` -- over the "
            "shared continuous `time` dimension."
        ),
    ])

    return


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
    # "high" window is [140, 200). Pandas label-slicing is end-inclusive, so the
    # right boundary point (t=200) is carried along -- the selection spans [140, 200].
    assert high_only.time.values[0] >= 140, f"Expected time >= 140, got {high_only.time.values[0]}"
    assert high_only.time.values[-1] <= 200, f"Expected time <= 200, got {high_only.time.values[-1]}"

    # Verify: selecting a dose interval by value constrains everything
    medium_interval = dose_ds_linked.sel(dose_intervals=pd.Interval(80, 140, closed="left"))
    assert "medium" in medium_interval.dose_level.values

    mo.callout(
        mo.md("""
        **Cross-slicing verified:**
        - `sel(time=slice(50, 100))` constrains dose_level to ["low", "medium"]
        - `sel(dose_level="high")` constrains time to the high window [140, 200]
        - `sel(dose_intervals=Interval(80,140,closed="left"))` constrains dose_level to ["medium"]

        Selecting on ANY dimension automatically constrains ALL others.
        """),
        kind="success",
    )

    return


@app.cell(hide_code=True)
def crossslice_query(dose_ds_linked, mo):
    _dose_levels = list(dose_ds_linked.dose_level.values)
    _windows = list(dose_ds_linked.meas_window.values)

    sel_mode = mo.ui.radio(
        ["by dose level", "by time window", "by measurement window"],
        value="by dose level",
        label="Slice on ONE dimension",
    )
    dose_pick = mo.ui.dropdown(_dose_levels, value="medium", label="dose level")
    time_pick = mo.ui.range_slider(0, 240, value=[50, 100], step=5, label="time window (min)")
    win_pick = mo.ui.dropdown(_windows, value="window_2", label="measurement window")

    mo.vstack([
        mo.md("### Cross-slicing explorer"),
        mo.md(
            "The `DimensionInterval` index links `time`, `dose_level`, and `meas_window`. "
            "Select on **any one** and the others automatically constrain to overlapping "
            "values -- no manual bookkeeping."
        ),
        sel_mode,
        mo.hstack([dose_pick, time_pick, win_pick], gap=1),
    ])

    return dose_pick, sel_mode, time_pick, win_pick


@app.cell(hide_code=True)
def crossslice_plot(
    dose_ds_linked,
    dose_pick,
    go,
    mo,
    np,
    sel_mode,
    time_pick,
    win_pick,
):
    _mode = sel_mode.value

    if _mode == "by dose level":
        _subset = dose_ds_linked.sel(dose_level=dose_pick.value)
        _on = f"dose_level = <b>{dose_pick.value}</b>"
    elif _mode == "by time window":
        _t0, _t1 = time_pick.value
        _subset = dose_ds_linked.sel(time=slice(_t0, _t1))
        _on = f"time = <b>[{_t0}, {_t1}]</b> min"
    else:
        _subset = dose_ds_linked.sel(meas_window=win_pick.value)
        _on = f"meas_window = <b>{win_pick.value}</b>"

    _full_time = np.asarray(dose_ds_linked.time.values, dtype=float)
    _full_resp = np.asarray(dose_ds_linked.response.values, dtype=float)
    _sel_time = np.atleast_1d(np.asarray(_subset.time.values, dtype=float))
    _mask = np.isin(_full_time, _sel_time)

    _surv_dose = list(np.atleast_1d(np.asarray(_subset.dose_level.values)).astype(str))
    _surv_win = list(np.atleast_1d(np.asarray(_subset.meas_window.values)).astype(str))

    _dose_labels = list(np.asarray(dose_ds_linked.dose_level.values).astype(str))
    _dose_iv = np.asarray(dose_ds_linked.dose_intervals.values)

    _accent, _pale, _ink = "#e94e77", "#c4a6d8", "#f0f9ff"
    _fig = go.Figure()
    _fig.add_trace(go.Scatter(
        x=_full_time, y=_full_resp, mode="lines",
        line=dict(color="#39465a", width=1.5),
        name="full time-course", hoverinfo="skip",
    ))
    if _mask.any():
        _fig.add_trace(go.Scatter(
            x=_full_time[_mask], y=_full_resp[_mask], mode="lines",
            line=dict(color=_accent, width=3),
            name="cross-slice", hovertemplate="t=%{x:.0f}<br>response=%{y:.2f}<extra></extra>",
        ))
    for _lab, _iv in zip(_dose_labels, _dose_iv):
        _alive = _lab in _surv_dose
        _fig.add_vrect(
            x0=float(_iv.left), x1=float(_iv.right),
            fillcolor=_accent if _alive else "#241a2e",
            opacity=0.16 if _alive else 0.5, layer="below", line_width=0,
        )
        _fig.add_annotation(
            x=(float(_iv.left) + float(_iv.right)) / 2, y=_full_resp.max() * 1.06,
            text=_lab, showarrow=False, font=dict(size=9, color=_ink if _alive else "#7a6b8a"),
        )
    _fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)", font=dict(color=_ink, size=12),
        margin=dict(l=45, r=20, t=30, b=45), height=400,
        showlegend=False,
        xaxis=dict(title="time (min)", range=[-4, 244]),
        yaxis=dict(title="response", range=[0, _full_resp.max() * 1.15]),
    )

    _n_sel = int(_mask.sum())

    def _cards(on, surv_d, surv_w, n_sel):
        def _row(nm, val, color):
            return (
                f'<div style="flex:1;min-width:140px;background:#10171f;border:1.5px solid {color}33;'
                f'border-radius:10px;padding:12px 14px;">'
                f'<div style="color:{color};font-size:9.5px;text-transform:uppercase;letter-spacing:1.1px;font-weight:700;">{nm}</div>'
                f'<div style="color:{_ink};font-size:17px;font-weight:700;margin:3px 0 2px;font-family:ui-monospace,monospace;">{val}</div>'
                f'</div>'
            )
        return (
            f'<div style="font-family:-apple-system,system-ui,sans-serif;">'
            f'<div style="color:{_ink};font-size:13px;margin:2px 0 11px;">Selected {on} &rarr; {n_sel} time points survive the cross-slice.</div>'
            f'<div style="display:flex;gap:10px;flex-wrap:wrap;">'
            f'{_row("surviving dose levels", ", ".join(surv_d) or chr(8212), _accent)}'
            f'{_row("surviving meas windows", ", ".join(surv_w) or chr(8212), _pale)}'
            f'</div></div>'
        )

    mo.vstack([
        _fig,
        mo.Html(_cards(_on, _surv_dose, _surv_win, _n_sel)),
    ])

    return


@app.cell(hide_code=True)
def epoching_header(mo):
    mo.md("""
    ## Dose-response epoching

    With linked intervals, extracting a response window around each dose
    change is a single `.sel()` call. No manual time-point tracking.
    """)
    return


@app.cell(hide_code=True)
def epoch_demo(curve_fit, dose_ds_linked, go, make_subplots, mo, np):
    # Each dose window is a single .sel() away -- the linked index does the bookkeeping.
    _order = ["baseline", "low", "medium", "high", "washout"]
    _conc_map = {"baseline": 0.01, "low": 1.0, "medium": 10.0, "high": 100.0, "washout": 0.0}

    _dose_means = {}
    for _dl in _order:
        _dose_means[_dl] = float(dose_ds_linked.sel(dose_level=_dl)["response"].mean().values)

    # Sanity: the synthetic dose ladder is recovered via linked-interval selection.
    assert 0.0 < _dose_means["baseline"] < 0.3
    assert 1.0 < _dose_means["medium"] < 1.4
    assert 1.8 < _dose_means["high"] < 2.2

    # Sigmoidal dose-response over the ascending ladder (washout excluded -- it is a
    # return-to-baseline, not a dose step). Floor is fixed to the baseline response,
    # leaving 3 free parameters for 4 points (well-determined fit).
    _ascend = ["baseline", "low", "medium", "high"]
    _x = np.array([_conc_map[_d] for _d in _ascend], dtype=float)
    _y = np.array([_dose_means[_d] for _d in _ascend], dtype=float)
    _floor = _y[0]

    def _sigmoid(_xv, top, ec50, hill):
        return _floor + (top - _floor) / (1.0 + (ec50 / _xv) ** hill)

    _popt, _ = curve_fit(
        _sigmoid, _x, _y, p0=[_y[-1], 3.0, 1.0],
        bounds=([1.0, 0.01, 0.1], [3.0, 100.0, 5.0]), maxfev=20000,
    )
    _top, _ec50, _hill = _popt
    assert 0.01 <= _ec50 <= 100.0, f"EC50 out of range: {_ec50}"

    _full_time = np.asarray(dose_ds_linked.time.values, dtype=float)
    _full_resp = np.asarray(dose_ds_linked.response.values, dtype=float)
    _dose_labels = list(np.asarray(dose_ds_linked.dose_level.values).astype(str))
    _dose_iv = np.asarray(dose_ds_linked.dose_intervals.values)

    _accent, _pale, _ink = "#e94e77", "#c4a6d8", "#f0f9ff"
    _fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Dose schedule (linked windows)", "Dose-response fit"),
        horizontal_spacing=0.14,
    )
    _fig.add_trace(
        go.Scatter(
            x=_full_time, y=_full_resp, mode="lines",
            line=dict(color="#39465a", width=1.5), name="response",
            hovertemplate="t=%{x:.0f}<br>response=%{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )
    for _lab, _iv in zip(_dose_labels, _dose_iv):
        _cx = (float(_iv.left) + float(_iv.right)) / 2
        _fig.add_vrect(
            x0=float(_iv.left), x1=float(_iv.right), row=1, col=1,
            fillcolor="#241a2e", opacity=0.6, layer="below", line_width=0,
        )
        _fig.add_trace(
            go.Scatter(
                x=[_cx], y=[_dose_means[_lab]], mode="markers",
                marker=dict(color=_accent, size=9, line=dict(color=_ink, width=1)),
                name=_lab, showlegend=False,
                hovertemplate=f"{_lab}<br>mean=%{{y:.2f}}<extra></extra>",
            ),
            row=1, col=1,
        )
    _x_smooth = np.logspace(-2, 2.2, 200)
    _fig.add_trace(
        go.Scatter(
            x=_x, y=_y, mode="markers",
            marker=dict(color=_accent, size=11, line=dict(color=_ink, width=1.5)),
            name="observed mean", legendgroup="dr",
        ),
        row=1, col=2,
    )
    _fig.add_trace(
        go.Scatter(
            x=_x_smooth, y=_sigmoid(_x_smooth, *_popt), mode="lines",
            line=dict(color=_pale, width=2.5), name="fit", legendgroup="dr",
        ),
        row=1, col=2,
    )
    _fig.add_vline(x=_ec50, line=dict(color=_accent, dash="dash", width=1.5), row=1, col=2)
    _fig.add_annotation(
        x=_ec50, y=float(_sigmoid(np.array([_ec50]), *_popt)[0]), row=1, col=2,
        text=f"EC50 \u2248 {_ec50:.1f}", showarrow=True, arrowhead=2,
        font=dict(color=_accent, size=11), ax=40, ay=-30,
    )
    _fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)", font=dict(color=_ink, size=12),
        margin=dict(l=48, r=20, t=54, b=48), height=400, showlegend=False,
    )
    _fig.update_xaxes(title_text="time (min)", row=1, col=1)
    _fig.update_xaxes(title_text="concentration (nM)", type="log", row=1, col=2)
    _fig.update_yaxes(title_text="response", row=1, col=1)
    _fig.update_yaxes(title_text="response", row=1, col=2)

    mo.vstack([
        _fig,
        mo.md(
            f"**One `.sel(dose_level=...)` per window** extracts each epoch via the linked "
            f"`DimensionInterval` -- no manual time indexing. Fitting a sigmoidal "
            f"dose-response (floor fixed at baseline) to the ascending ladder recovers "
            f"EC50 \u2248 **{_ec50:.1f} nM** (Hill \u2248 {_hill:.2f}, ceiling {_top:.2f}). "
            f"`washout` is excluded from the fit -- it is a return-to-baseline, not a dose step."
        ),
    ])

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
