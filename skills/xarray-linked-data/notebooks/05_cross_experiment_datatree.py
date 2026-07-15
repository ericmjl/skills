# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy==2.5.1",
#     "xarray==2026.7.0",
#     "wigglystuff==0.5.16",
#     "plotly==6.9.0",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium", app_title="Cross-Experiment DataTree")


@app.cell(hide_code=True)
def hero(mo):
    mo.md("""
    <div style="
        background: linear-gradient(135deg, #0c0c1d 0%, #1c1c3a 50%, #2d2d5e 100%);
        border-radius: 16px;
        padding: 48px 40px;
        margin: -16px -16px 24px -16px;
    ">
        <div style="font-size: 14px; color: #7c8cf8; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px;">
            xarray-linked-data &middot; Notebook 5
        </div>
        <h1 style="color: #f0f9ff; font-size: 2.4rem; margin: 0 0 16px 0; line-height: 1.2;">
            Deep DataTree: Inheritance &amp; Incompatible Grids
        </h1>
        <p style="color: #a0a8e8; font-size: 1.1rem; margin: 0; max-width: 640px; line-height: 1.6;">
            When assay grids are mostly compatible, a flat DataTree of sibling
            nodes is the right tool (Notebook&nbsp;1). But when assays share nothing
            except the molecule ID &mdash; and even <b>replicate labels are
            semantically independent</b> across assays &mdash; you need a deep
            DataTree with root inheritance.
        </p>
    </div>
    """)
    return


@app.cell(hide_code=True)
def cell_tour(mo):
    import wigglystuff

    tour = wigglystuff.CellTour(
        steps=[
            {"cell_name": "hero", "title": "Deep DataTree", "description": "Going beyond Notebook 1's flat tree: root inheritance, multi-level nesting, incompatible grids."},
            {"cell_name": "why_not_dataset", "title": "Why Not a Dataset?", "description": "Forcing incompatible grids into one Dataset creates a multi-terabyte sparse array — and falsely aligns independent replicates."},
            {"cell_name": "generate_data", "title": "Campaign Data", "description": "30 molecules across five incompatible grids — DLS, HPLC, ELISA, flow cytometry, and derived estimates."},
            {"cell_name": "build_tree", "title": "Multi-Level Hierarchy", "description": "Nodes nest two levels deep: /characterization/dls, /bioassays/binding — mirroring the lab workflow."},
            {"cell_name": "verify_tree", "title": "Inheritance Verified", "description": "The molecule coordinate is inherited, not duplicated. Each node retains its own incompatible dims."},
            {"cell_name": "assay_overview_plot", "title": "Assay Overview", "description": "Visualize four incompatible grids side by side — same molecules, completely different shapes."},
            {"cell_name": "query_controls", "title": "Interactive Query", "description": "Adjust target, EC50 threshold, cell line, and uptake to filter molecules in real time."},
            {"cell_name": "cross_assay_query", "title": "Cross-Assay Query", "description": "Find promising molecules from derived estimates, then pull data from every incompatible grid."},
            {"cell_name": "molecule_explorer", "title": "Molecule Explorer", "description": "Pick any molecule and see its data across all incompatible grids in one interactive view."},
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
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return go, make_subplots, mo, np, xr


@app.cell(hide_code=True)
def intro(mo):
    mo.md(r"""
    ## From compatible to incompatible grids

    Notebook 1's six assay stages shared enough secondary dimensions
    (`batch`, `replicate`, `cell_line`) that a flat DataTree of sibling
    nodes worked well. Each node independently carried the `molecule`
    coordinate, and that was enough.

    But consider a campaign where the assays share almost nothing except
    the molecule ID:

    - DLS: 3 replicates × 150 timepoints per molecule
    - HPLC: 3 replicates × 500 chromatogram bins per molecule
    - ELISA: 3 targets × 8 concentrations × 3 replicates per molecule
    - Flow cytometry: 2 cell lines × 2000 events per molecule

    Even the `replicate` dimension is a trap — technical replicate "r1"
    in a DLS run is a completely independent measurement from replicate
    "r1" in an ELISA plate. They share a label, not a sample. A single
    Dataset would **falsely align** them, implying correspondence where
    none exists.

    These grids have no truly shared secondary dimension. Forcing them
    into one Dataset makes any cross-variable operation broadcast to
    ~650 billion cells of NaN. And a flat DataTree, while functional,
    treats every assay as an unrelated sibling — missing the natural
    experimental hierarchy (analytical chemistry vs bioassays vs derived
    estimates).

    Here we build a **deep** DataTree:

    - A **root registry node** (`/`) defines shared identifiers once
    - Every child **inherits** the root's coordinates — no duplication
    - Multi-level grouping (`/characterization/dls`, `/bioassays/binding`)
      mirrors the lab workflow
    - Cross-assay queries span incompatible grids in one `.sel()` call
    """)
    return


@app.cell
def why_not_dataset(mo):
    # What happens if we force incompatible grids into ONE Dataset?
    # Each assay lives on a completely different grid:
    grid_shapes = {
        "DLS timeseries":      "(molecule, replicate, time_s)        = (30, 3, 150)",
        "HPLC chromatogram":   "(molecule, replicate, retention_min) = (30, 3, 500)",
        "ELISA dose-response": "(molecule, target, conc, replicate)  = (30, 3, 8, 3)",
        "Flow cytometry":      "(molecule, cell_line, event)         = (30, 2, 2000)",
    }

    # Any cross-variable operation (.to_array(), arithmetic, .values)
    # broadcasts to the UNION of all dimensions:
    # (molecule x replicate x time_s x retention_min x target x concentration x cell_line x event)
    broadcast_size = 30 * 3 * 150 * 500 * 3 * 8 * 2 * 2000
    dense_gb = broadcast_size * 8 / 1e9  # float64

    mo.callout(
        mo.md(f"""
        **Forcing these into one Dataset** works at first -- each variable
        keeps its own dimensions. But any cross-variable operation
        (`.to_array()`, arithmetic, reductions) broadcasts to the union:

        ```
        {'\\n'.join(f'  {k}: {v}' for k, v in grid_shapes.items())}
        ```

        Union grid: **30 x 3 x 150 x 500 x 3 x 8 x 2 x 2000**
        = **{broadcast_size:,}** cells (~{dense_gb:,.0f} GB as float64)

        Worse: `replicate` appears in DLS, HPLC, and ELISA with matching
        labels (`r1`, `r2`, `r3`) — but they are **independent
        measurements**. A single Dataset would align them as if replicate
        "r1" in DLS corresponds to "r1" in ELISA. It does not.

        Almost every cell is `NaN`. A flat Dataset is the wrong tool.
        """),
        kind="danger",
    )
    return


@app.cell(hide_code=True)
def generate_data(mo, np, xr):
    # Generate synthetic campaign data: 30 molecules across four incompatible grids
    np.random.seed(42)
    n_molecules = 30
    molecule_ids = [f"LNP_{m_id:03d}" for m_id in range(1, n_molecules + 1)]
    replicates = ["r1", "r2", "r3"]

    # Root: molecule registry with shared identifiers
    root_ds = xr.Dataset(
        data_vars={
            "smiles": (["molecule"], [f"C({'C' * m_id})O{'N' * (m_id % 3)}" for m_id in range(n_molecules)]),
            "molecular_weight_da": (["molecule"], np.random.normal(15000, 3000, n_molecules)),
        },
        coords={"molecule": molecule_ids},
        attrs={"description": "Root: molecule registry shared across all assay nodes"},
    )

    # Analytical chemistry: DLS timeseries + HPLC chromatograms
    # Each assay has its OWN replicates -- r1 in DLS is not r1 in HPLC
    dls_time_s = np.linspace(0, 300, 150)
    dls_base = np.random.normal(85, 18, n_molecules).clip(50, 160)
    dls_jitter = np.random.normal(0, 2.5, (n_molecules, len(replicates), len(dls_time_s)))
    dls_diameter = (dls_base[:, None, None] + dls_jitter).clip(30, 250)

    analytical_ds = xr.Dataset(
        data_vars={
            "dls_diameter_nm": (["molecule", "replicate", "time_s"], dls_diameter),
            "purity_percent": (["molecule"], np.random.normal(95, 3, n_molecules).clip(80, 100)),
        },
        coords={"molecule": molecule_ids, "replicate": replicates, "time_s": dls_time_s},
        attrs={"assay_type": "analytical_chemistry"},
    )

    retention_min = np.linspace(0, 30, 500)
    hplc_signal = np.full((n_molecules, len(replicates), len(retention_min)), 0.005)
    for hplc_mol in range(n_molecules):
        for pk in range(np.random.randint(2, 5)):
            peak_rt = np.random.uniform(4, 26)
            peak_w = np.random.uniform(0.3, 0.8)
            for hplc_rep in range(len(replicates)):
                peak_amp = np.random.uniform(0.3, 1.2)
                hplc_signal[hplc_mol, hplc_rep] += peak_amp * np.exp(
                    -0.5 * ((retention_min - peak_rt) / peak_w) ** 2
                )
    hplc_signal += np.random.normal(0, 0.008, hplc_signal.shape)
    hplc_signal = hplc_signal.clip(0, None)

    hplc_ds = xr.Dataset(
        data_vars={"hplc_signal_au": (["molecule", "replicate", "retention_min"], hplc_signal)},
        coords={"molecule": molecule_ids, "replicate": replicates, "retention_min": retention_min},
        attrs={"assay_type": "HPLC chromatography"},
    )

    # Bioassays: ELISA dose-response + flow cytometry
    targets = ["EGFR", "HER2", "CD20"]
    concentrations = np.logspace(0, 4, 8)

    ec50_grid = np.random.lognormal(2.5, 0.9, (n_molecules, len(targets)))
    hill_grid = np.random.uniform(0.8, 1.6, (n_molecules, len(targets)))
    bottom_od = np.random.uniform(0.05, 0.15, (n_molecules, len(targets)))
    top_od = np.random.uniform(2.5, 3.5, (n_molecules, len(targets)))

    binding_data = np.empty((n_molecules, len(targets), len(concentrations), len(replicates)))
    for assay_mol in range(n_molecules):
        for tgt_idx in range(len(targets)):
            dose_curve = bottom_od[assay_mol, tgt_idx] + (
                (top_od[assay_mol, tgt_idx] - bottom_od[assay_mol, tgt_idx])
                / (1 + (ec50_grid[assay_mol, tgt_idx] / concentrations) ** hill_grid[assay_mol, tgt_idx])
            )
            for rep_idx in range(len(replicates)):
                binding_data[assay_mol, tgt_idx, :, rep_idx] = dose_curve + np.random.normal(0, 0.06, len(concentrations))
    binding_data = binding_data.clip(0, None)

    binding_ds = xr.Dataset(
        data_vars={"od450": (["molecule", "target", "concentration_nm", "replicate"], binding_data)},
        coords={
            "molecule": molecule_ids,
            "target": targets,
            "concentration_nm": concentrations,
            "replicate": replicates,
        },
        attrs={"assay_type": "ELISA dose-response"},
    )

    n_events = 2000
    cell_lines = ["HEPG2", "HEK293"]
    flow_data = np.empty((n_molecules, len(cell_lines), n_events))
    for flow_mol in range(n_molecules):
        for cl_idx in range(len(cell_lines)):
            frac_positive = np.random.uniform(0.15, 0.75)
            n_pos = int(frac_positive * n_events)
            n_neg = n_events - n_pos
            neg_signal = np.random.lognormal(4.5, 0.5, n_neg)
            pos_signal = np.random.lognormal(9.5, 0.4, n_pos)
            flow_data[flow_mol, cl_idx] = np.concatenate([neg_signal, pos_signal])
            np.random.shuffle(flow_data[flow_mol, cl_idx])

    flow_ds = xr.Dataset(
        data_vars={
            "fluorescence_mfi": (["molecule", "cell_line", "event"], flow_data),
            "median_mfi": (["molecule", "cell_line"], np.median(flow_data, axis=2)),
        },
        coords={"molecule": molecule_ids, "cell_line": cell_lines, "event": np.arange(n_events)},
        attrs={"assay_type": "flow cytometry"},
    )

    # Derived estimates: Bayesian posterior summaries
    derived_targets = ["EGFR", "HER2", "CD20"]
    derived_cell_lines = ["HEPG2", "HEK293"]

    ec50_mean = np.random.lognormal(2, 1, (n_molecules, len(derived_targets)))
    ec50_cv = 0.5
    ec50_hdi3 = ec50_mean * np.exp(-1.88 * ec50_cv)
    ec50_hdi97 = ec50_mean * np.exp(1.88 * ec50_cv)

    derived_ds = xr.Dataset(
        data_vars={
            "ec50_nm_mean": (["molecule", "target"], ec50_mean),
            "ec50_nm_hdi3": (["molecule", "target"], ec50_hdi3),
            "ec50_nm_hdi97": (["molecule", "target"], ec50_hdi97),
            "uptake_pct": (
                ["molecule", "cell_line"],
                np.random.normal(50, 20, (n_molecules, len(derived_cell_lines))).clip(0, 100),
            ),
        },
        coords={
            "molecule": molecule_ids,
            "target": derived_targets,
            "cell_line": derived_cell_lines,
        },
        attrs={"assay_type": "derived_estimates", "estimation": "Bayesian posterior summaries"},
    )

    mo.md(f"""
    **Synthetic campaign data** — {n_molecules} molecules across six nodes (root + five assays):

    | Node | Grid | Shape |
    |------|------|-------|
    | Root registry | molecule | ({n_molecules},) |
    | DLS | molecule × replicate × time_s | ({n_molecules}, 3, 150) |
    | HPLC | molecule × replicate × retention_min | ({n_molecules}, 3, 500) |
    | Binding | molecule × target × conc × replicate | ({n_molecules}, 3, 8, 3) |
    | Flow cytometry | molecule × cell_line × event | ({n_molecules}, 2, 2000) |
    | Derived | molecule × target × cell_line | ({n_molecules}, 3, 2) |

    Each assay defines its **own** `replicate` dimension — the labels match
    (`r1`, `r2`, `r3`) but the measurements are independent across assays.
    """)
    return analytical_ds, binding_ds, derived_ds, flow_ds, hplc_ds, root_ds


@app.cell
def build_tree(
    analytical_ds,
    binding_ds,
    derived_ds,
    flow_ds,
    hplc_ds,
    root_ds,
    xr,
):
    # Build the DataTree: each assay is a node, molecule_id inherited from root
    campaign_tree = xr.DataTree.from_dict({
        "/": root_ds,
        "/characterization/dls": analytical_ds,
        "/characterization/hplc": hplc_ds,
        "/bioassays/binding": binding_ds,
        "/bioassays/flow_cytometry": flow_ds,
        "/derived": derived_ds,
    })

    campaign_tree
    return (campaign_tree,)


@app.cell(hide_code=True)
def verify_tree(campaign_tree, mo):
    # Verify: molecule coordinate is INHERITED from root, not independently set
    verify_root = campaign_tree.ds
    verify_dls = campaign_tree["/characterization/dls"].ds
    verify_binding = campaign_tree["/bioassays/binding"].ds
    verify_derived = campaign_tree["/derived"].ds

    # The molecule coordinate lives on the root; children inherit it
    assert "molecule" in verify_root.coords, "root must define molecule"
    assert (verify_dls.molecule.values == verify_root.molecule.values).all()
    assert (verify_binding.molecule.values == verify_root.molecule.values).all()
    assert (verify_derived.molecule.values == verify_root.molecule.values).all()

    # Each node retains its OWN incompatible dimensions
    assert "replicate" in verify_dls.dims
    assert "time_s" in verify_dls.dims
    assert "concentration_nm" in verify_binding.dims
    assert "event" in campaign_tree["/bioassays/flow_cytometry"].ds.dims

    # Contrast with Notebook 1: there, every sibling independently carried the
    # molecule coordinate. Here, the root is the SINGLE source of truth.
    tree_depth = max(len(p.path.split("/")) - 1 for p in campaign_tree.subtree)

    mo.callout(
        mo.md(f"""
        **Inheritance verified** (tree depth: {tree_depth} levels):

        - `molecule` defined **once** at root (`/`), inherited by all descendants
        - Notebook&nbsp;1's flat tree: siblings each independently carrying `molecule`
        - This notebook: **1 root** → children inherit, no duplication
        - Each node keeps its own incompatible dims (`replicate`, `time_s`, `concentration_nm`, `event`)
        - Replicate labels match across nodes but represent **independent measurements**
        """),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def assay_overview(mo):
    mo.md("""
    ## Four incompatible grids, one tree

    Every assay measures the same 30 molecules — but on completely different
    grids. Here is what those grids look like side by side.
    """)
    return


@app.cell
def assay_overview_plot(campaign_tree, go, make_subplots, mo):
    # Visualize the four incompatible grids in one figure
    overview_dls = campaign_tree["/characterization/dls"].ds
    overview_bind = campaign_tree["/bioassays/binding"].ds
    overview_hplc = campaign_tree["/characterization/hplc"].ds
    overview_flow = campaign_tree["/bioassays/flow_cytometry"].ds

    overview_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "DLS diameter distribution",
            "ELISA dose-response (all targets)",
            "HPLC chromatogram (first 5 molecules)",
            "Flow cytometry MFI (HEPG2)",
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.1,
    )

    # (1) DLS: histogram of mean diameters across molecules and replicates
    dls_diameters = overview_dls.dls_diameter_nm.mean(dim=["replicate", "time_s"]).values
    overview_fig.add_trace(go.Histogram(x=dls_diameters, nbinsx=12, name="DLS"), row=1, col=1)
    overview_fig.update_xaxes(title_text="diameter (nm)", row=1, col=1)

    # (2) Binding: dose-response curves (median across molecules, per target)
    for overview_target in overview_bind.target.values:
        dose_median = overview_bind.od450.sel(target=overview_target).median(dim=["molecule", "replicate"]).values
        overview_fig.add_trace(go.Scatter(
            x=overview_bind.concentration_nm.values, y=dose_median,
            mode="lines+markers", name=str(overview_target), showlegend=True,
        ), row=1, col=2)
    overview_fig.update_xaxes(title_text="concentration (nM)", type="log", row=1, col=2)
    overview_fig.update_yaxes(title_text="OD450", row=1, col=2)

    # (3) HPLC: chromatograms for first 5 molecules (median across replicates)
    for show_idx in range(5):
        mol_label = overview_hplc.molecule.values[show_idx]
        overview_fig.add_trace(go.Scatter(
            x=overview_hplc.retention_min.values,
            y=overview_hplc.hplc_signal_au.sel(molecule=mol_label).median(dim="replicate").values,
            mode="lines", name=mol_label, line=dict(width=1), showlegend=show_idx == 0,
        ), row=2, col=1)
    overview_fig.update_xaxes(title_text="retention (min)", row=2, col=1)
    overview_fig.update_yaxes(title_text="signal (AU)", row=2, col=1)

    # (4) Flow: histogram of fluorescence for HEPG2
    hepg2_values = overview_flow.fluorescence_mfi.sel(cell_line="HEPG2").values.ravel()
    overview_fig.add_trace(go.Histogram(x=hepg2_values, nbinsx=50, name="Flow"), row=2, col=2)
    overview_fig.update_xaxes(title_text="fluorescence (MFI)", row=2, col=2)

    overview_fig.update_layout(
        height=560, width=860,
        showlegend=True, legend=dict(x=0.72, y=0.98, font=dict(size=9)),
        margin=dict(l=50, r=20, t=40, b=40),
    )

    mo.vstack([
        overview_fig,
        mo.md("*Four incompatible grids, side by side — each panel measures the same 30 molecules on a completely different grid.*"),
    ])
    return


@app.cell(hide_code=True)
def query_header(mo):
    mo.md("""
    ## Cross-assay queries

    The derived estimates node has the decision-making metrics. Query it
    to find promising molecules, then pull characterization and bioassay
    data from other nodes for the same molecules.
    """)
    return


@app.cell(hide_code=True)
def query_controls(campaign_tree, mo):
    query_target = mo.ui.dropdown(
        options=list(campaign_tree["/derived"].ds.target.values),
        value="EGFR",
        label="Target",
    )
    max_ec50 = mo.ui.slider(start=1, stop=1000, step=5, value=100, label="Max EC50 (nM)")
    query_cell_line = mo.ui.dropdown(
        options=list(campaign_tree["/derived"].ds.cell_line.values),
        value="HEPG2",
        label="Cell line",
    )
    min_uptake = mo.ui.slider(start=0, stop=100, step=5, value=40, label="Min uptake (%)")

    mo.hstack([query_target, max_ec50, query_cell_line, min_uptake], justify="start")
    return max_ec50, min_uptake, query_cell_line, query_target


@app.cell
def cross_assay_query(
    campaign_tree,
    max_ec50,
    min_uptake,
    mo,
    query_cell_line,
    query_target,
):
    derived = campaign_tree["/derived"].ds
    criteria = (
        derived.ec50_nm_mean.sel(target=query_target.value).drop_vars("target") < max_ec50.value
    ) & (derived.uptake_pct.sel(cell_line=query_cell_line.value).drop_vars("cell_line") > min_uptake.value)
    hits = derived.where(criteria, drop=True)
    hit_molecules = list(hits.molecule.values)

    dls_node = campaign_tree["/characterization/dls"].ds
    dls_hits = dls_node.sel(molecule=hit_molecules) if hit_molecules else dls_node.isel(molecule=slice(0))
    binding_node = campaign_tree["/bioassays/binding"].ds
    binding_hits = binding_node.sel(molecule=hit_molecules) if hit_molecules else binding_node.isel(molecule=slice(0))

    hit_list = ", ".join(hit_molecules[:10]) + ("..." if len(hit_molecules) > 10 else "") if hit_molecules else "—"

    mo.callout(
        mo.md(f"""
        **Query:** {query_target.value} EC50 < {max_ec50.value} nM AND {query_cell_line.value} uptake > {min_uptake.value}%

        - **Hits:** {len(hit_molecules)} / {len(derived.molecule)} molecules ({hit_list})
        - DLS pulled: {dls_hits.sizes["molecule"]} molecules × {dls_hits.sizes["time_s"]} timepoints
        - Binding pulled: {binding_hits.sizes["molecule"]} molecules × {binding_hits.sizes["concentration_nm"]} concentrations

        One `.sel(molecule=hit_molecules)` per node pulls linked data from incompatible grids.
        """),
        kind="info" if hit_molecules else "warning",
    )
    return


@app.cell(hide_code=True)
def explorer_header(mo):
    mo.md("""
    ## Molecule explorer

    Pick any molecule and see its footprint across all four incompatible grids
    simultaneously — DLS timeseries, dose-response, HPLC chromatogram, and flow
    histogram. One `.sel()` per node; no manual alignment.
    """)
    return


@app.cell
def molecule_selector(campaign_tree, mo):
    mol_choices = list(campaign_tree.ds.molecule.values)
    molecule_selector = mo.ui.dropdown(
        options=mol_choices,
        value=mol_choices[0],
        label="Select molecule",
    )
    molecule_selector
    return (molecule_selector,)


@app.cell
def molecule_explorer(campaign_tree, go, make_subplots, mo, molecule_selector):
    chosen_mol = molecule_selector.value
    sel_dls = campaign_tree["/characterization/dls"].ds.sel(molecule=chosen_mol)
    sel_bind = campaign_tree["/bioassays/binding"].ds.sel(molecule=chosen_mol)
    sel_hplc = campaign_tree["/characterization/hplc"].ds.sel(molecule=chosen_mol)
    sel_flow = campaign_tree["/bioassays/flow_cytometry"].ds.sel(molecule=chosen_mol)

    explorer_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            f"DLS timeseries — {chosen_mol}",
            f"Dose-response — {chosen_mol}",
            f"HPLC chromatogram — {chosen_mol}",
            f"Flow histogram — {chosen_mol}",
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.1,
    )

    # (1) DLS timeseries (median across replicates)
    explorer_fig.add_trace(go.Scatter(
        x=sel_dls.time_s.values,
        y=sel_dls.dls_diameter_nm.median(dim="replicate").values,
        mode="lines", name="DLS", line=dict(width=1.5),
        showlegend=False,
    ), row=1, col=1)
    explorer_fig.update_xaxes(title_text="time (s)", row=1, col=1)
    explorer_fig.update_yaxes(title_text="diameter (nm)", row=1, col=1)

    # (2) Dose-response per target (median across replicates)
    for bind_target in sel_bind.target.values:
        sel_curve = sel_bind.od450.sel(target=bind_target).median(dim="replicate").values
        explorer_fig.add_trace(go.Scatter(
            x=sel_bind.concentration_nm.values, y=sel_curve,
            mode="lines+markers", name=str(bind_target),
        ), row=1, col=2)
    explorer_fig.update_xaxes(title_text="concentration (nM)", type="log", row=1, col=2)
    explorer_fig.update_yaxes(title_text="OD450", row=1, col=2)

    # (3) HPLC chromatogram (median across replicates)
    explorer_fig.add_trace(go.Scatter(
        x=sel_hplc.retention_min.values,
        y=sel_hplc.hplc_signal_au.median(dim="replicate").values,
        mode="lines", name="HPLC", line=dict(width=1.5),
        showlegend=False,
    ), row=2, col=1)
    explorer_fig.update_xaxes(title_text="retention (min)", row=2, col=1)
    explorer_fig.update_yaxes(title_text="signal (AU)", row=2, col=1)

    # (4) Flow histogram per cell line
    for flow_line in sel_flow.cell_line.values:
        flow_values = sel_flow.fluorescence_mfi.sel(cell_line=flow_line).values
        explorer_fig.add_trace(go.Histogram(
            x=flow_values, nbinsx=40, name=str(flow_line), opacity=0.7,
        ), row=2, col=2)
    explorer_fig.update_xaxes(title_text="fluorescence (MFI)", row=2, col=2)
    explorer_fig.update_yaxes(title_text="count", row=2, col=2)

    explorer_fig.update_layout(
        height=560, width=860,
        showlegend=True, legend=dict(x=0.72, y=0.98, font=dict(size=9)),
        margin=dict(l=50, r=20, t=40, b=40),
        barmode="overlay",
    )

    explorer_caption = (
        f'One `.sel(molecule="{chosen_mol}")` per node pulls all four views '
        f"— DLS, dose-response, HPLC, and flow — without manual alignment."
    )

    mo.vstack([
        explorer_fig,
        mo.md(f"*{explorer_caption}*"),
    ])
    return


@app.cell
def hierarchical_access(campaign_tree, mo):
    # Demonstrate hierarchical access patterns
    dls_via_path = campaign_tree["/characterization/dls"].ds
    dls_via_dot = campaign_tree.characterization.dls.ds

    # Both access methods return the same data
    assert dls_via_path.equals(dls_via_dot)

    # Can navigate the tree structure programmatically
    top_level_nodes = list(campaign_tree.children)
    char_children = list(campaign_tree["characterization"].children)

    mo.md(
        f"""
        **Hierarchical access:**

        - Path syntax: `tree["/characterization/dls"].ds`
        - Dot syntax: `tree.characterization.dls.ds`
        - Top-level groups: `{top_level_nodes}`
        - Characterization children: `{char_children}`

        DataTree mirrors a filesystem-like hierarchy for heterogeneous data.
        """
    )
    return


@app.cell(hide_code=True)
def close(mo):
    mo.md("""
    ---

    ## Summary

    | DataTree shape | When to use | Key property |
    |----------------|-------------|--------------|
    | **Flat** (Notebook 1) | Assays with mostly compatible dimensions | Sibling nodes share coordinates independently |
    | **Deep** (this notebook) | Assays on incompatible grids | Root defines shared coords; children **inherit** them |

    A deep DataTree does what a single `Dataset` cannot do well: organizing
    assays whose only common ground is the molecule ID. A 150-point DLS
    timeseries, a 500-bin HPLC chromatogram, an 8-point dose-response, and a
    2000-event flow run coexist in one object, linked by a root registry node
    whose coordinates cascade to every child.

    ### The full xarray-linked-data toolkit

    1. **[Notebook 1](01_linked_data_design.py):** Progressive accumulation in a flat DataTree
    2. **[Notebook 2](02_periodic_and_transform_indexes.py):** PeriodicIndex + CoordinateTransform
    3. **[Notebook 3](03_ndindex_time_locking.py):** NDIndex for N-D derived coordinates
    4. **[Notebook 4](04_linked_intervals_cross_slicing.py):** DimensionInterval for cross-slicing
    5. **This notebook:** Deep DataTree — root inheritance & incompatible grids

    *Built with xarray, marimo, and synthetic data. AI tools were used in creation.*
    """)
    return


if __name__ == "__main__":
    app.run()
