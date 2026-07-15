# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "xarray>=2025.1.0",
#     "wigglystuff==0.5.16",
#     "plotly==6.9.0",
#     "pymc==6.1.0",
#     "arviz==1.2.0",
#     "matplotlib==3.11.0",
#     "numpyro==0.21.0",
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
            {"cell_name": "build_trial_data", "title": "Trial Data", "description": "Absolute time from trial onset + relative time (2-D), with a realistic post-dose response baked in."},
            {"cell_name": "verify_controls", "title": "2-D Selection", "description": "Drag abs_time -- one scalar resolves to a single cell in the trial x rel_time grid."},
            {"cell_name": "verify_ndindex", "title": "Resolution", "description": "The selected abs_time decomposes into trial + rel_time (onset + offset)."},
            {"cell_name": "timelock_build", "title": "Time-Locking", "description": "Multiple event-locked coordinates registered under one NDIndex."},
            {"cell_name": "timelock_controls", "title": "Explore", "description": "Drag the sliders -- the ruler plot re-labels each instant in every coordinate."},
            {"cell_name": "timelock_verify", "title": "Point + Window", "description": "A point (dashed) and a window (band) traced across three event-locked rulers."},
            {"cell_name": "epoch_demo", "title": "Bayesian Epoching", "description": "Epoch around the dose event, fit a hierarchical PyMC model, and store the posterior back -- the N-D index carries it along."},
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
    import plotly.graph_objects as go
    import pymc as pm
    import xarray as xr
    import arviz as az
    from plotly.subplots import make_subplots
    from xarray import Index
    from xarray.core.indexing import IndexSelResult
    from xarray.core.variable import Variable

    return Index, IndexSelResult, Variable, go, make_subplots, mo, np, pm, xr


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


@app.cell(hide_code=True)
def build_trial_data(np, xr):
    # 10 trials, each with 50 time points (0 to 49 seconds relative)
    n_trials = 10
    n_rel_times = 50
    rel_times = np.arange(n_rel_times, dtype=float)  # 0, 1, 2, ... 49 seconds

    # Each trial starts at a different onset time
    trial_onsets = np.arange(n_trials) * 100.0  # trial 0 at t=0, trial 1 at t=100, etc.

    # Compute 2-D absolute time coordinate
    abs_time = trial_onsets[:, None] + rel_times[None, :]  # shape (trial, rel_time)

    # Seeded RNG so the demo is reproducible across runs
    rng = np.random.default_rng(42)

    # Baseline physiology: slow oscillation with trial-specific amplitude & phase
    trial_amplitudes = rng.uniform(0.4, 1.2, n_trials)
    trial_phases = rng.uniform(0, 2 * np.pi, n_trials)

    # Post-dose pharmacodynamic response: the drug is dosed at rel_time=10.
    # Response rises after dosing, peaks ~dose+12s, then decays -- an Emax-style
    # bump whose magnitude varies trial-to-trial (the effect we want to recover).
    dose_time = 10.0
    peak_offset = 12.0
    response_width = 6.0
    response_amps = rng.uniform(1.5, 3.5, n_trials)

    signal = np.zeros((n_trials, n_rel_times))
    for trial_i in range(n_trials):
        baseline = trial_amplitudes[trial_i] * np.sin(rel_times * 0.25 + trial_phases[trial_i])
        pd_response = response_amps[trial_i] * np.exp(
            -0.5 * ((rel_times - (dose_time + peak_offset)) / response_width) ** 2
        )
        # Pharmacokinetic delay: no response before the dose is administered
        pd_response = np.where(rel_times >= dose_time, pd_response, 0.0)
        noise = rng.normal(0, 0.15, n_rel_times)
        signal[trial_i] = baseline + pd_response + noise

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
    print(f"Dose administered at rel_time={dose_time:.0f}s in every trial")
    return rel_times, trial_ds, trial_onsets


@app.cell(hide_code=True)
def attach_ndindex(NDIndex, trial_ds):
    # Register the 2-D abs_time coordinate under NDIndex
    trial_ds_indexed = trial_ds.set_xindex(["abs_time"], NDIndex)
    print("NDIndex attached. Now sel(abs_time=...) works on the 2-D coordinate.")
    return (trial_ds_indexed,)


@app.cell(hide_code=True)
def verify_controls(mo):
    # Interactive control for 2-D abs_time selection.
    abs_slider = mo.ui.slider(0, 949, value=245, step=1, label="abs_time (s)")
    mo.vstack([
        mo.md("**Drag abs_time** &mdash; watch a single scalar resolve to one cell in the (trial &times; rel_time) grid."),
        abs_slider,
    ])

    return (abs_slider,)


@app.cell(hide_code=True)
def verify_ndindex(abs_slider, go, mo, trial_ds_indexed):
    # One scalar abs_time -> one cell in the 2-D (trial x rel_time) field.
    sel = trial_ds_indexed.sel(abs_time=abs_slider.value, method="nearest")
    sel_trial = str(sel.trial.values.item())
    sel_rt = int(sel.rel_time.values.item())
    sel_abs = int(round(float(sel.abs_time.values.item())))
    trial_idx = int(sel_trial.split("_")[1])
    onset = trial_idx * 100
    assert onset + sel_rt == sel_abs, f"arithmetic check failed: {onset}+{sel_rt} != {sel_abs}"

    abs_grid = trial_ds_indexed.abs_time.values
    trial_labels = [str(t) for t in trial_ds_indexed.trial.values]
    _v_rel_times = trial_ds_indexed.rel_time.values

    _vfig = go.Figure(
        go.Heatmap(
            z=abs_grid,
            x=_v_rel_times,
            y=trial_labels,
            colorscale=[[0, "#0d1117"], [0.45, "#133326"], [1, "#2ee4a0"]],
            colorbar=dict(title="abs_time", thickness=10, len=0.85),
            hovertemplate="trial=%{y}<br>rel_time=%{x}<br>abs_time=%{z}<extra></extra>",
        )
    )
    _vfig.add_trace(
        go.Scatter(
            x=[sel_rt],
            y=[sel_trial],
            mode="markers+text",
            marker=dict(size=20, color="rgba(0,0,0,0)", line=dict(width=3, color="#e94e77"), symbol="circle"),
            text=[f"{sel_abs}"],
            textposition="top center",
            textfont=dict(color="#e94e77", size=11, family="monospace"),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    _vfig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)",
        font=dict(color="#f0f9ff", size=12),
        margin=dict(l=70, r=20, t=40, b=50),
        height=380,
        xaxis=dict(title="rel_time (s)", dtick=10),
        yaxis=dict(title="trial", autorange="reversed"),
    )


    def _cards(asked, resolved, trial_label, rt, onset_v):
        mint, pale, ink = "#2ee4a0", "#8fcfab", "#f0f9ff"
        items = [
            ("abs_time", f"{resolved}s", f"you dragged to {asked}", mint, True),
            ("trial", trial_label, f"onset {onset_v}s", pale, False),
            ("rel_time", f"{rt}s", "into that trial", pale, False),
        ]
        ch = []
        for name, val, phrase, color, active in items:
            bg = "#0f2a20" if active else "#10171f"
            border = color if active else "#1f2a24"
            glow = f"box-shadow:0 0 0 1px {color}33;" if active else ""
            ch.append(
                f'<div style="flex:1;min-width:0;background:{bg};border:1.5px solid {border};'
                f'border-radius:10px;padding:13px 16px;{glow}">'
                f'<div style="color:{color};font-size:10px;text-transform:uppercase;letter-spacing:1.2px;font-weight:700;">{name}</div>'
                f'<div style="color:{ink};font-size:23px;font-weight:700;margin:3px 0 2px;font-family:ui-monospace,monospace;">{val}</div>'
                f'<div style="color:{pale};font-size:11px;">{phrase}</div></div>'
            )
        eq = (
            f"<code style='color:{mint};'>{onset_v} + {rt} = {resolved}</code>"
            f" &nbsp;&mdash; the scalar is the <b>sum</b> of the two underlying indices."
        )
        lead = (
            f"abs_time = <b style='color:{mint};'>{resolved}s</b> is one cell: "
            f"<b style='color:{ink};'>{trial_label}</b> at <b style='color:{ink};'>rel_time {rt}</b>."
        )
        return (
            f'<div style="font-family:-apple-system,system-ui,sans-serif;">'
            f'<div style="color:{ink};font-size:13px;margin:2px 0 11px;">{lead}</div>'
            f'<div style="display:flex;gap:12px;margin-bottom:11px;">{"".join(ch)}</div>'
            f'<div style="font-size:11.5px;color:{pale};">{eq}</div>'
            f"</div>"
        )


    mo.vstack([
        _vfig,
        mo.Html(_cards(abs_slider.value, sel_abs, sel_trial, sel_rt, onset)),
    ])

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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def timelock_controls(mo):
    # Interactive controls for event-locked selection.
    coord = mo.ui.radio(
        options=["dose_locked", "response_locked"],
        value="dose_locked",
        label="query coordinate (0 = the event moment)",
    )
    rt_slider = mo.ui.slider(0, 49, value=15, step=1, label="rel_time (s)")
    win = mo.ui.range_slider(-10, 39, value=[-5, 10], step=1, label="dose_locked window (s)")
    mo.vstack([
        mo.md("**Drag to explore** &mdash; the rulers below re-label the same instant in every event coordinate."),
        mo.hstack([coord, rt_slider], wrap=True),
        win,
    ])

    return coord, rt_slider, win


@app.cell(hide_code=True)
def timelock_verify(coord, mo, rt_slider, timelock_ds, win):
    # One plot, two queries: a point (dashed guide) and a window (band) on the same rulers.
    offset = 10 if coord.value == "dose_locked" else 25
    locked_val = rt_slider.value - offset
    sel_point = timelock_ds.sel(**{coord.value: locked_val}, method="nearest")
    resolved_rt = int(sel_point.rel_time.values.item())
    assert resolved_rt == rt_slider.value, (
        f"NDIndex mismatch: sel({coord.value}={locked_val}) gave rel_time={resolved_rt}, expected {rt_slider.value}"
    )

    w_lo, w_hi = win.value
    sliced = timelock_ds.sel(dose_locked=slice(w_lo, w_hi))
    rt_lo, rt_hi = int(sliced.rel_time.values[0]), int(sliced.rel_time.values[-1])
    assert rt_lo == w_lo + 10, f"Expected rel_time start {w_lo+10}, got {rt_lo}"
    assert rt_hi == w_hi + 10, f"Expected rel_time end {w_hi+10}, got {rt_hi}"


    def _rulers_svg(rt_sel, active_name, r_lo, r_hi):
        mint, pale, ink, pink = "#2ee4a0", "#8fcfab", "#f0f9ff", "#e94e77"
        W, H, ML, MR = 760, 340, 140, 44
        sc = (W - ML - MR) / 49
        x = lambda rt: ML + rt * sc
        rows = [("rel_time", 120, pale, lambda rt: rt, None),
                ("dose_locked", 210, mint, lambda rt: rt - 10, 10),
                ("response_locked", 300, pink, lambda rt: rt - 25, 25)]
        active_i = {"rel_time": 0, "dose_locked": 1, "response_locked": 2}[active_name]
        ticks = [0, 10, 20, 30, 40, 49]
        parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:760px">',
                 f'<rect width="{W}" height="{H}" fill="#0d1117" rx="12"/>',
                 f'<text x="{ML}" y="34" fill="{mint}" font-size="14" font-weight="700">Same axis, three coordinate systems</text>',
                 f'<text x="{ML}" y="55" fill="{pale}" font-size="11.5" font-family="ui-monospace,monospace">point (dashed) + window (band) re-labeled per event</text>']
        bx0, bx1 = x(r_lo), x(r_hi)
        parts.append(f'<rect x="{bx0:.1f}" y="108" width="{bx1-bx0:.1f}" height="204" fill="{mint}" opacity="0.12" rx="3"/>')
        parts.append(f'<line x1="{bx0:.1f}" y1="108" x2="{bx0:.1f}" y2="312" stroke="{mint}" stroke-width="1.3" opacity="0.6"/>')
        parts.append(f'<line x1="{bx1:.1f}" y1="108" x2="{bx1:.1f}" y2="312" stroke="{mint}" stroke-width="1.3" opacity="0.6"/>')
        cx = x(rt_sel)
        parts.append(f'<line x1="{cx:.1f}" y1="112" x2="{cx:.1f}" y2="312" stroke="{pink}" stroke-width="1.6" stroke-dasharray="5 4" opacity="0.9"/>')
        for i, (label, yc, color, fn, evt) in enumerate(rows):
            dim = 1.0 if i == active_i else 0.45
            parts.append(f'<line x1="{x(0):.1f}" y1="{yc}" x2="{x(49):.1f}" y2="{yc}" stroke="{color}" stroke-width="2.5" opacity="{dim}"/>')
            parts.append(f'<text x="{ML-18}" y="{yc+4}" fill="{color}" font-size="12" text-anchor="end" font-weight="600" opacity="{dim}">{label}</text>')
            for t in ticks:
                tx = x(t)
                parts.append(f'<line x1="{tx:.1f}" y1="{yc-5}" x2="{tx:.1f}" y2="{yc+5}" stroke="{color}" stroke-width="1" opacity="{dim}"/>')
                parts.append(f'<text x="{tx:.1f}" y="{yc+18}" fill="{ink}" font-size="9.5" text-anchor="middle" font-family="ui-monospace,monospace" opacity="{dim}">{fn(t)}</text>')
            if evt is not None:
                ex = x(evt)
                parts.append(f'<circle cx="{ex:.1f}" cy="{yc}" r="4.5" fill="{color}" opacity="{dim}"/>')
            parts.append(f'<circle cx="{cx:.1f}" cy="{yc}" r="5.5" fill="{pink}" stroke="#0d1117" stroke-width="1.5"/>')
        parts.append("</svg>")
        return "".join(parts)


    def _phrase(v, event):
        if v == 0:
            return f"at the {event}"
        return f"{abs(v)}s {'after' if v > 0 else 'before'} {event}"


    def _readout_html(rt, coord_name, dose_v, resp_v, lo, hi, npts):
        mint, pale, ink, pink = "#2ee4a0", "#8fcfab", "#f0f9ff", "#e94e77"
        cards = [
            ("rel_time", f"{rt}s", "into each trial", pale, coord_name == "rel_time"),
            ("dose_locked", f"{dose_v}s", _phrase(dose_v, "dose"), mint, coord_name == "dose_locked"),
            ("response_locked", f"{resp_v}s", _phrase(resp_v, "response"), pink, coord_name == "response_locked"),
        ]
        card_html = []
        for name, val, phrase, color, active in cards:
            bg = "#0f2a20" if active else "#10171f"
            border = color if active else "#1f2a24"
            glow = f"box-shadow:0 0 0 1px {color}33;" if active else ""
            card_html.append(
                f'<div style="flex:1;min-width:0;background:{bg};border:1.5px solid {border};border-radius:10px;'
                f'padding:13px 16px;{glow}">'
                f'<div style="color:{color};font-size:10px;text-transform:uppercase;letter-spacing:1.2px;font-weight:700;">{name}</div>'
                f'<div style="color:{ink};font-size:23px;font-weight:700;margin:3px 0 2px;font-family:ui-monospace,monospace;">{val}</div>'
                f'<div style="color:{pale};font-size:11px;">{phrase}</div>'
                f"</div>"
            )
        lead = (
            f"You picked the moment <b style='color:{mint};'>{rt}s</b> into every trial."
            f" It goes by three names &mdash; the same instant, referenced from each event:"
        )
        foot = (
            f"<span style='color:{pale};'>the query: "
            f"<code style='color:{mint};'>timelock_ds.sel({coord_name}={rt - (10 if coord_name=='dose_locked' else 25)})</code></span>"
            f" &nbsp;&middot;&nbsp; <span style='color:{pale};'>window: "
            f"<b style='color:{ink};'>{lo}&ndash;{hi}s</b> into each trial ({npts} pts)</span>"
        )
        return (
            f'<div style="font-family:-apple-system,system-ui,sans-serif;">'
            f'<div style="color:{ink};font-size:13px;margin:2px 0 11px;">{lead}</div>'
            f'<div style="display:flex;gap:12px;margin-bottom:12px;">{"".join(card_html)}</div>'
            f'<div style="font-size:11.5px;">{foot}</div>'
            f"</div>"
        )


    n_pts = sliced.sizes["rel_time"]
    eq_dose = resolved_rt - 10
    eq_resp = resolved_rt - 25
    mo.vstack([
        mo.Html(_rulers_svg(resolved_rt, coord.value, rt_lo, rt_hi)),
        mo.Html(_readout_html(resolved_rt, coord.value, eq_dose, eq_resp, rt_lo, rt_hi, n_pts)),
    ])

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


@app.cell(hide_code=True)
def epoch_demo(go, make_subplots, mo, np, pm, timelock_ds, xr):

    # Extract a -10s to +20s window locked to dose administration.
    # The NDIndex + dose_locked coordinate do all the alignment -- no manual indexing.
    epoch = timelock_ds.sel(dose_locked=slice(-10, 20))

    sig = epoch["signal"].values                       # (trial, rel_time)
    dl = epoch.dose_locked.mean(dim="trial").values    # 1-D time-locked axis
    rel_time_epoch = epoch.rel_time.values
    n_trial, n_t = sig.shape

    # --- Hierarchical Bayesian dose-response ---
    # Each trial gets its own baseline and response amplitude, partially pooled
    # toward population hyperpriors (non-centered parameterization for clean
    # sampling). We report the population curve with full uncertainty.
    with pm.Model() as dose_model:
        d = pm.Data("dose_locked", dl)
        # Population level
        mu_baseline = pm.Normal("mu_baseline", 0, 1)
        sigma_baseline = pm.HalfNormal("sigma_baseline", 1)
        mu_amp = pm.HalfNormal("mu_amp", 2)
        sigma_amp = pm.HalfNormal("sigma_amp", 1)
        peak = pm.Normal("peak", 10, 5)          # peak time relative to dose (s)
        width = pm.HalfNormal("width", 8)        # response spread (s)
        # Trial level (non-centered)
        bl_off = pm.Normal("bl_off", 0, 1, shape=n_trial)
        baseline_t = pm.Deterministic("baseline", mu_baseline + bl_off * sigma_baseline)
        amp_off = pm.Normal("amp_off", 0, 1, shape=n_trial)
        amp = pm.Deterministic("amp", mu_amp + amp_off * sigma_amp)
        # Gaussian response bump over the locked axis
        bump = pm.math.exp(-0.5 * ((d[None, :] - peak) / width) ** 2)
        mu = baseline_t[:, None] + amp[:, None] * bump
        sigma = pm.HalfNormal("sigma", 1)
        pm.Normal("obs", mu=mu, sigma=sigma, observed=sig)
        idata = pm.sample(draws=1000, tune=1000, chains=4, target_accept=0.9,
                          random_seed=42, progressbar=False, nuts_sampler="numpyro")

    # --- Posterior population dose-response curve ---
    post = idata.posterior
    mu_bl = post["mu_baseline"].values.reshape(-1)
    mu_a = post["mu_amp"].values.reshape(-1)
    pk = post["peak"].values.reshape(-1)
    wd = post["width"].values.reshape(-1)
    n_draws = mu_bl.size
    curves = mu_bl[:, None] + mu_a[:, None] * np.exp(
        -0.5 * ((dl[None, :] - pk[:, None]) / wd[:, None]) ** 2
    )
    curve_med = np.median(curves, axis=0)
    ci_lo, ci_hi = np.percentile(curves, [3, 97], axis=0)
    peak_med = float(np.median(pk))
    amp_med = float(np.median(mu_a))

    # --- Store the posterior back into the Dataset under a `draw` dim ---
    # Now any NDIndex selection on dose_locked / abs_time carries the posterior
    # along automatically -- the closed loop.
    posterior_da = xr.DataArray(
        curves, dims=["draw", "rel_time"],
        coords={"draw": np.arange(n_draws), "rel_time": rel_time_epoch},
    )
    epoch = epoch.assign(posterior_response=posterior_da)
    peek = epoch.sel(dose_locked=5, method="nearest")
    peek_med = float(peek.posterior_response.median())

    mint = "#2ee4a0"
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("All trials (dose-locked)", "Bayesian population response"),
        horizontal_spacing=0.12,
    )
    # Panel A: every trial as a thin line
    for t_idx in range(n_trial):
        fig.add_trace(
            go.Scatter(
                x=dl, y=sig[t_idx], mode="lines",
                line=dict(color=mint, width=1), opacity=0.3, showlegend=False,
                hovertemplate=f"t=%{{x:.0f}}s<br>signal=%{{y:.2f}}<extra>trial {t_idx}</extra>",
            ),
            row=1, col=1,
        )
    # Panel B: posterior median + 94% credible band
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([dl, dl[::-1]]),
            y=np.concatenate([ci_hi, ci_lo[::-1]]),
            fill="toself", fillcolor="rgba(46, 228, 160, 0.18)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip",
            name="94% credible band", legendgroup="bayes",
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=dl, y=curve_med, mode="lines",
            line=dict(color=mint, width=3), name="Posterior median", legendgroup="bayes",
        ),
        row=1, col=2,
    )
    for col in (1, 2):
        fig.add_vline(x=0, line=dict(color="#e94e77", dash="dash", width=1.5), row=1, col=col)
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13, 17, 23, 0.6)", font=dict(color="#f0f9ff", size=12),
        margin=dict(l=50, r=20, t=54, b=50), height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="time relative to dose (s)", row=1, col=1)
    fig.update_xaxes(title_text="time relative to dose (s)", row=1, col=2)
    fig.update_yaxes(title_text="signal", row=1, col=1)
    fig.update_yaxes(title_text="signal", row=1, col=2)

    mo.vstack([
        fig,
        mo.md(f"""
        **Hierarchical model recovered the dose response with full uncertainty.**
        Posterior median peak **{peak_med:.1f}s** after dose, response amplitude
        **{amp_med:.2f}** -- trial-level amplitudes partially pool toward this
        population estimate. The posterior is stored back into the Dataset under a
        `draw` dimension: `epoch.sel(dose_locked=5)` returns {n_draws} posterior
        draws (median **{peek_med:.2f}**) -- the custom N-D index carries the
        Bayesian estimate along with the raw data.
        """),
    ])

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
