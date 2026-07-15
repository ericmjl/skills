# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy==2.5.1",
#     "xarray==2026.7.0",
#     "scipy",
#     "matplotlib",
#     "wigglystuff==0.5.16",
#     "plotly==6.9.0",
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
            {"cell_name": "hero", "title": "Custom Indexes", "description": "Two patterns for when PandasIndex is not enough: an Index subclass and a CoordinateTransform."},
            {"cell_name": "periodic_index_class", "title": "PeriodicIndex", "description": "An Index subclass with hand-written sel() for wrapping/angular coordinates."},
            {"cell_name": "periodic_verify", "title": "Wrapping Verified", "description": "350\u00b0 finds 345\u00b0, 370\u00b0 wraps to 15\u00b0 \u2014 no gaps on the circle."},
            {"cell_name": "periodic_plot", "title": "Try it: drag past 360\u00b0", "description": "Polar view \u2014 drag the query angle across the seam and watch PeriodicIndex resolve the true nearest neighbour, versus a plain no-wrap index."},
            {"cell_name": "zstack_transform_class", "title": "ZStackTransform", "description": "A CoordinateTransform: just write forward() and reverse(), xarray builds the index."},
            {"cell_name": "zstack_verify", "title": "Depth Selection", "description": "sel(depth_nm=500) computes the reverse transform and finds slice 125."},
            {"cell_name": "zstack_plot", "title": "Try it: scan the depth", "description": "The depth_nm axis is never stored \u2014 drag it and watch the z-slice materialise on demand."},
            {"cell_name": "massspec_transform", "title": "MassSpecTransform", "description": "A nonlinear calibration (mz = 100\u00b7\u221atof + 10) expressed as a CoordinateTransform."},
            {"cell_name": "massspec_verify", "title": "m/z Selection", "description": "Select by mass-to-charge; the transform inverts the nonlinear TOF\u2194mz mapping. (CoordinateTransformIndex needs a DataArray indexer + method='nearest'.)"},
            {"cell_name": "massspec_plot", "title": "Try it: query a mass", "description": "Data is stored as TOF bins, queried as m/z \u2014 drag to resolve any mass to its bin via the \u221a calibration."},
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
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return (
        CoordinateTransform,
        CoordinateTransformIndex,
        Coordinates,
        Index,
        IndexSelResult,
        PandasIndex,
        go,
        make_subplots,
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
        - `sel(angle=350)` -> 345\u00b0 (wrapping distance = 5\u00b0)
        - `sel(angle=370)` -> 15\u00b0 (370 wraps to 10, nearest is 15)
        - Vectorized: [5, 355, 370] -> [0, 0, 15]
        """),
        kind="success",
    )

    return


@app.cell(hide_code=True)
def periodic_query(mo):
    angle_query = mo.ui.slider(
        0, 720, value=355, step=5,
        label="Query angle (\u00b0) \u2014 drag past 360\u00b0 to trigger wrapping",
    )
    mo.vstack([
        mo.md("**Drag the query angle.** Past 360\u00b0 a plain index cannot cope; the `PeriodicIndex` wraps it onto the circle (0\u201345\u00b0, every 15\u00b0) and finds the true nearest neighbour."),
        angle_query,
    ])

    return (angle_query,)


@app.cell(hide_code=True)
def periodic_plot(angle_query, flow_ds, go, mo, np):
    _q = angle_query.value
    _qmod = _q % 360
    _resolved = flow_ds.sel(angle=_q, method="nearest")
    _res_angle = float(np.asarray(_resolved.angle.values).reshape(-1)[0])
    _dd = abs(_qmod - _res_angle)
    _wrap_dist = float(min(_dd, 360 - _dd))

    _angles = flow_ds.angle.values
    _mean_int = flow_ds.scatter_intensity.mean("particle").values
    _naive_idx = int(np.argmin(np.abs(_angles - _q)))
    _naive_angle = float(_angles[_naive_idx])
    _naive_dist = float(abs(_q - _naive_angle))
    _disagree = not np.isclose(_naive_angle, _res_angle)

    _pfig = go.Figure()
    _pfig.add_trace(go.Barpolar(
        r=_mean_int,
        theta=_angles,
        marker=dict(
            color=["#e94560" if np.isclose(a, _res_angle) else "#39465a" for a in _angles],
            line=dict(color="#0d1117", width=1),
        ),
        hovertemplate="angle=%{theta:.0f}\u00b0<br>mean scatter=%{r:.1f}<extra></extra>",
        name="mean scatter (40 particles)",
    ))
    _pfig.add_trace(go.Scatterpolar(
        r=[0.0, float(_mean_int.max()) * 1.10],
        theta=[_qmod, _qmod],
        mode="lines+markers+text",
        line=dict(color="#f0f9ff", width=2, dash="dot"),
        marker=dict(size=9, color="#f0f9ff"),
        text=[None, f"ask {_q}\u00b0"],
        textposition="top center",
        textfont=dict(color="#f0f9ff", size=11),
        hoverinfo="skip",
        showlegend=False,
    ))
    _pfig.update_layout(
        template="plotly_dark",
        polar=dict(
            bgcolor="rgba(13,17,23,0.6)",
            angularaxis=dict(rotation=90, direction="clockwise", dtick=45, tickfont=dict(size=9)),
            radialaxis=dict(showticklabels=True, tickfont=dict(size=9), gridcolor="#2a3340"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0f9ff", size=12),
        margin=dict(l=30, r=30, t=20, b=20),
        height=430,
        showlegend=False,
    )


    def _cards(q, qmod, resolved, wdist, naive_a, naive_d, disagree):
        accent, pale, ink = "#e94560", "#d98a96", "#f0f9ff"
        if disagree:
            items = [
                ("query", f"{q}\u00b0", f"\u2261 {qmod:.0f}\u00b0 on the circle", pale, False),
                ("PeriodicIndex", f"{resolved:.0f}\u00b0", f"{wdist:.0f}\u00b0 \u2014 true nearest (wraps)", accent, True),
                ("no-wrap index", f"{naive_a:.0f}\u00b0", f"{naive_d:.0f}\u00b0 \u2014 ignores the seam", pale, False),
            ]
            lead = (
                f"Asking for <b style='color:{accent};'>{q}\u00b0</b> resolves to "
                f"<b style='color:{ink};'>{resolved:.0f}\u00b0</b> by wrapping \u2014 "
                f"a plain index would pick <b style='color:{pale};'>{naive_a:.0f}\u00b0</b> ({naive_d:.0f}\u00b0 off)."
            )
        else:
            items = [
                ("query", f"{q}\u00b0", f"\u2261 {qmod:.0f}\u00b0 on the circle", pale, False),
                ("PeriodicIndex", f"{resolved:.0f}\u00b0", f"{wdist:.0f}\u00b0 nearest measured", accent, True),
                ("no-wrap index", f"{naive_a:.0f}\u00b0", "agrees here (not near the seam)", pale, False),
            ]
            lead = (
                f"Asking for <b style='color:{accent};'>{q}\u00b0</b> resolves to "
                f"<b style='color:{ink};'>{resolved:.0f}\u00b0</b>. Drag near the 0\u00b0/345\u00b0 seam "
                f"or past 360\u00b0 to see wrapping beat a plain index."
            )
        ch = []
        for nm, val, phrase, color, active in items:
            bg = "#2a1016" if active else "#10171f"
            border = color if active else "#2a2226"
            glow = f"box-shadow:0 0 0 1px {color}55;" if active else ""
            ch.append(
                f'<div style="flex:1;min-width:150px;background:{bg};border:1.5px solid {border};'
                f'border-radius:10px;padding:12px 14px;{glow}">'
                f'<div style="color:{color};font-size:9.5px;text-transform:uppercase;letter-spacing:1.1px;font-weight:700;">{nm}</div>'
                f'<div style="color:{ink};font-size:22px;font-weight:700;margin:3px 0 2px;font-family:ui-monospace,monospace;">{val}</div>'
                f'<div style="color:{pale};font-size:10.5px;">{phrase}</div></div>'
            )
        return (
            f'<div style="font-family:-apple-system,system-ui,sans-serif;">'
            f'<div style="color:{ink};font-size:13px;margin:2px 0 11px;">{lead}</div>'
            f'<div style="display:flex;gap:10px;margin-bottom:8px;flex-wrap:wrap;">{"".join(ch)}</div>'
            f'</div>'
        )


    mo.vstack([
        _pfig,
        mo.Html(_cards(_q, _qmod, _res_angle, _wrap_dist, _naive_angle, _naive_dist, _disagree)),
    ])

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
    # Synthetic microscopy: 200 z-slices (4 nm each), 2 channels.
    # A single cell sits near the middle of the stack (z~125, depth ~500 nm):
    #   nuclei   = a bright filled disk,
    #   membrane = a surrounding ring.
    # Away from that z-band the slices are pure shot noise, so dragging the depth
    # slider flies you through the cell -- noise on one side, a circle at the cell.
    n_slices = 200
    slice_thickness = 4.0  # nm per slice
    _zs_yy, _zs_xx = np.mgrid[0:128, 0:128]
    _zs_r2 = (_zs_yy - 64.0) ** 2 + (_zs_xx - 64.0) ** 2  # radial sq in the y-x plane
    _zs_zprof = np.exp(-((np.arange(n_slices) - 125.0) / 12.0) ** 2)  # cell fades in/out around z=125

    _zs_nuc = np.random.poisson(50, (n_slices, 128, 128)).astype(float)
    _zs_mem = np.random.poisson(50, (n_slices, 128, 128)).astype(float)
    # nuclei: filled disk (radius 22), modulated by the z-profile
    _zs_nuc += 240.0 * (_zs_r2[None, :, :] < 22.0 ** 2) * _zs_zprof[:, None, None]
    # membrane: ring (annulus 18..26), modulated by the z-profile
    _zs_ring = (_zs_r2[None, :, :] > 18.0 ** 2) & (_zs_r2[None, :, :] < 26.0 ** 2)
    _zs_mem += 260.0 * _zs_ring * _zs_zprof[:, None, None]

    image_data = np.stack([_zs_nuc, _zs_mem], axis=-1)

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
    print("One synthetic cell centered at z=125 (depth ~500 nm): nuclei disk + membrane ring.")
    print(f"depth_nm coordinate is LAZY (never materialized): {zstack_da.depth_nm[:3].values} ...")

    return slice_thickness, zstack_da


@app.cell
def zstack_verify(mo, np, xr, zstack_da):
    # sel by physical depth must return exactly the slice the transform maps to.
    # (z is the transform's input dim and is dropped on selection, so verify by
    #  data-equivalence against isel rather than reading a .z coordinate.)
    result = zstack_da.sel(depth_nm=500, method="nearest")
    assert np.array_equal(result.values, zstack_da.isel(z=125).values), "depth_nm=500 should be slice 125"

    result_0 = zstack_da.sel(depth_nm=0, method="nearest")
    assert np.array_equal(result_0.values, zstack_da.isel(z=0).values), "depth_nm=0 should be slice 0"

    # Vectorized: three depths -> three slices
    probe_depths = xr.DataArray([100, 200, 300], dims="probe")
    probed = zstack_da.sel(depth_nm=probe_depths, method="nearest")
    expected = zstack_da.isel(z=xr.DataArray([25, 50, 75], dims="probe"))
    assert np.array_equal(probed.values, expected.values), "[100,200,300] nm -> slices [25,50,75]"

    # Channel selection works alongside the transform (chain sels: exact channel,
    # then nearest on the numeric depth coordinate)
    nuclei = zstack_da.sel(channel="nuclei").sel(depth_nm=400, method="nearest")
    assert nuclei.channel.values == "nuclei"

    mo.callout(
        mo.md("""
        **ZStackTransform verified** (by data-equivalence to `isel`):
        - `sel(depth_nm=500)` returns slice 125's data
        - `sel(depth_nm=0)` returns slice 0's data
        - Vectorized: [100, 200, 300] nm -> slices [25, 50, 75]
        - Channel selection works alongside the transform
        """),
        kind="success",
    )

    return


@app.cell(hide_code=True)
def zstack_query(mo):
    depth_query = mo.ui.slider(
        0, 796, value=500, step=4,
        label="depth (nm) \u2014 200 slices \u00d7 4 nm, lazy coordinate",
    )
    mo.vstack([
        mo.md("**Drag the physical depth.** `ZStackTransform` lazily maps `depth_nm` \u2192 z-slice; the depth coordinate is never stored, only computed on demand at selection time."),
        depth_query,
    ])

    return (depth_query,)


@app.cell(hide_code=True)
def zstack_plot(
    depth_query,
    go,
    make_subplots,
    mo,
    slice_thickness,
    zstack_da,
):
    _d = depth_query.value
    _sel = zstack_da.sel(depth_nm=_d, method="nearest")
    # z is dropped by the transform; recover the slice index from the reverse mapping
    _slice_idx = int(round(_d / slice_thickness))
    _img = _sel.sel(channel="nuclei").values

    _depths = zstack_da.depth_nm.values
    _prof_n = zstack_da.sel(channel="nuclei").mean(("x", "y")).values
    _prof_m = zstack_da.sel(channel="membrane").mean(("x", "y")).values

    _zfig = make_subplots(
        rows=1, cols=2, column_widths=[0.42, 0.58],
        horizontal_spacing=0.14,
        subplot_titles=(f"slice {_slice_idx}  \u2014  depth {_d:.0f} nm", "mean fluorescence vs depth"),
    )
    _zfig.add_trace(go.Heatmap(
        z=_img,
        colorscale=[[0, "#0d1117"], [0.45, "#5a1a26"], [1, "#e94560"]],
        showscale=False,
        hovertemplate="y=%{y}<br>x=%{x}<br>counts=%{z}<extra></extra>",
    ), row=1, col=1)
    _zfig.add_trace(go.Scatter(
        x=_depths, y=_prof_n, mode="lines", name="nuclei",
        line=dict(color="#e94560", width=2),
    ), row=1, col=2)
    _zfig.add_trace(go.Scatter(
        x=_depths, y=_prof_m, mode="lines", name="membrane",
        line=dict(color="#7c8cf8", width=2, dash="dot"),
    ), row=1, col=2)
    _zfig.add_vline(x=float(_d), line=dict(color="#f0f9ff", width=2, dash="dash"), row=1, col=2)
    _zfig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f0f9ff", size=12),
        margin=dict(l=50, r=20, t=55, b=45),
        height=400,
        legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center"),
    )
    _zfig.update_yaxes(autorange="reversed", row=1, col=1, title_text="y")
    _zfig.update_xaxes(title_text="x", row=1, col=1)
    _zfig.update_xaxes(title_text="depth (nm)", row=1, col=2)
    _zfig.update_yaxes(title_text="mean counts", row=1, col=2)


    def _dcards(d, sidx):
        accent, pale, ink = "#e94560", "#d98a96", "#f0f9ff"
        items = [
            ("depth_nm", f"{d:.0f} nm", "the coordinate you asked for", accent, True),
            ("z-slice", str(sidx), f"{d:.0f} / 4 nm", pale, False),
            ("stored on disk?", "never", "computed by forward()", pale, False),
        ]
        ch = []
        for nm, val, phrase, color, active in items:
            bg = "#2a1016" if active else "#10171f"
            border = color if active else "#2a2226"
            glow = f"box-shadow:0 0 0 1px {color}55;" if active else ""
            ch.append(
                f'<div style="flex:1;min-width:140px;background:{bg};border:1.5px solid {border};'
                f'border-radius:10px;padding:12px 14px;{glow}">'
                f'<div style="color:{color};font-size:9.5px;text-transform:uppercase;letter-spacing:1.1px;font-weight:700;">{nm}</div>'
                f'<div style="color:{ink};font-size:22px;font-weight:700;margin:3px 0 2px;font-family:ui-monospace,monospace;">{val}</div>'
                f'<div style="color:{pale};font-size:10.5px;">{phrase}</div></div>'
            )
        lead = (
            f"Selecting <b style='color:{accent};'>{d:.0f} nm</b> materialises z-slice "
            f"<b style='color:{ink};'>{sidx}</b> \u2014 the depth axis is a pure transform, "
            f"not an array in memory."
        )
        return (
            f'<div style="font-family:-apple-system,system-ui,sans-serif;">'
            f'<div style="color:{ink};font-size:13px;margin:2px 0 11px;">{lead}</div>'
            f'<div style="display:flex;gap:10px;margin-bottom:8px;flex-wrap:wrap;">{"".join(ch)}</div>'
            f'</div>'
        )


    mo.vstack([
        _zfig,
        mo.Html(_dcards(_d, _slice_idx)),
    ])

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
    return calib_a, calib_b, ms_da


@app.cell
def massspec_verify(mo, ms_da, np, xr):
    # CoordinateTransformIndex needs point-wise (DataArray) indexers + method="nearest".
    # tof_bin is dropped on selection, so verify by data-equivalence against isel.
    result_1010 = ms_da.sel(mz=xr.DataArray([1010], dims="q"), method="nearest")
    assert np.array_equal(np.ravel(result_1010.values), np.ravel(ms_da.isel(tof_bin=100).values)), "mz=1010 -> tof_bin=100"

    result_2010 = ms_da.sel(mz=xr.DataArray([2010], dims="q"), method="nearest")
    assert np.array_equal(np.ravel(result_2010.values), np.ravel(ms_da.isel(tof_bin=400).values)), "mz=2010 -> tof_bin=400"

    # Peaks land at the expected m/z values
    peak_mz = xr.DataArray([1010, 2010, 3010], dims="peak")
    peaks = ms_da.sel(mz=peak_mz, method="nearest")
    assert all(np.asarray(peaks.values).ravel() > 100), "Expected high intensity at peak positions"

    mo.callout(
        mo.md("""
        **MassSpecTransform verified** (by data-equivalence to `isel`):
        - `sel(mz=1010)` -> tof_bin 100 (nonlinear calibration: `((1010-10)/100)\u00b2`)
        - `sel(mz=2010)` -> tof_bin 400
        - Peaks detected at the expected m/z values

        Note: `CoordinateTransformIndex` requires a `DataArray` indexer (point-wise)
        plus `method="nearest"` \u2014 a bare scalar raises `TypeError`.
        """),
        kind="success",
    )

    return


@app.cell(hide_code=True)
def massspec_query(mo):
    mz_query = mo.ui.slider(
        500, 3500, value=1010, step=10,
        label="query m/z \u2014 the three synthetic peaks sit at 1010, 2010, 3010",
    )
    mo.vstack([
        mo.md("**Drag the query m/z.** Data is stored as time-of-flight bins, but you query by mass-to-charge; `MassSpecTransform` inverts the nonlinear calibration `mz = 100\u00b7\u221atof + 10` on demand."),
        mz_query,
    ])

    return (mz_query,)


@app.cell(hide_code=True)
def massspec_plot(calib_a, calib_b, go, mo, ms_da, mz_query):
    _mzq = mz_query.value
    _mz = ms_da.mz.values
    _int = ms_da.values
    _tofq = ((_mzq - calib_b) / calib_a) ** 2

    _mfig = go.Figure()
    _mfig.add_trace(go.Scatter(
        x=_mz, y=_int, mode="lines", name="spectrum",
        line=dict(color="#39465a", width=1),
        hovertemplate="m/z=%{x:.1f}<br>intensity=%{y:.1f}<extra></extra>",
    ))
    for _pk, _tb in [(1010, 100), (2010, 400), (3010, 900)]:
        _pv = float(ms_da.isel(tof_bin=_tb).values)
        _mfig.add_trace(go.Scatter(
            x=[_pk], y=[_pv], mode="markers+text",
            marker=dict(size=12, color="#e94560", line=dict(width=1, color="#0d1117")),
            text=[f"m/z {_pk}\nTOF {_tb}"],
            textposition="top center",
            textfont=dict(color="#e94560", size=10),
            showlegend=False, hoverinfo="skip",
        ))
    _mfig.add_vline(x=float(_mzq), line=dict(color="#f0f9ff", width=2, dash="dash"))
    _mfig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)",
        font=dict(color="#f0f9ff", size=12),
        margin=dict(l=55, r=20, t=20, b=45),
        height=400,
        xaxis=dict(title="m/z (lazy coordinate)", range=[500, 3500]),
        yaxis=dict(title="intensity"),
        showlegend=False,
    )


    def _mcards(mzq, tofq):
        accent, pale, ink = "#e94560", "#d98a96", "#f0f9ff"
        items = [
            ("m/z", f"{mzq:.0f}", "the coordinate you asked for", accent, True),
            ("tof_bin", f"{tofq:.0f}", "((m/z \u2212 10) / 100)\u00b2", pale, False),
            ("mapping", "100\u00b7\u221atof+10", "nonlinear calibration", pale, False),
        ]
        ch = []
        for nm, val, phrase, color, active in items:
            bg = "#2a1016" if active else "#10171f"
            border = color if active else "#2a2226"
            glow = f"box-shadow:0 0 0 1px {color}55;" if active else ""
            ch.append(
                f'<div style="flex:1;min-width:140px;background:{bg};border:1.5px solid {border};'
                f'border-radius:10px;padding:12px 14px;{glow}">'
                f'<div style="color:{color};font-size:9.5px;text-transform:uppercase;letter-spacing:1.1px;font-weight:700;">{nm}</div>'
                f'<div style="color:{ink};font-size:20px;font-weight:700;margin:3px 0 2px;font-family:ui-monospace,monospace;">{val}</div>'
                f'<div style="color:{pale};font-size:10.5px;">{phrase}</div></div>'
            )
        lead = (
            f"Selecting <b style='color:{accent};'>m/z {mzq:.0f}</b> resolves to TOF bin "
            f"<b style='color:{ink};'>{tofq:.0f}</b> via the nonlinear calibration \u2014 "
            f"the data is stored as TOF, queried as mass."
        )
        return (
            f'<div style="font-family:-apple-system,system-ui,sans-serif;">'
            f'<div style="color:{ink};font-size:13px;margin:2px 0 11px;">{lead}</div>'
            f'<div style="display:flex;gap:10px;margin-bottom:8px;flex-wrap:wrap;">{"".join(ch)}</div>'
            f'</div>'
        )


    mo.vstack([
        _mfig,
        mo.Html(_mcards(_mzq, _tofq)),
    ])

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
