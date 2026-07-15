# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy==2.5.1",
#     "pandas==3.0.3",
#     "xarray==2026.7.0",
#     "scipy==1.18.0",
#     "pymc==5.26.1",
#     "arviz>=0.18,<1.0",
#     "matplotlib==3.11.0",
#     "zarr",
#     "wigglystuff==0.5.16",
#     "pytensor==2.35.1",
#     "plotly==6.9.0",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium", app_title="Linked Data Design with xarray")


@app.cell(hide_code=True)
def hero(mo):
    mo.md("""
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0c4a6e 100%);
        border-radius: 16px;
        padding: 48px 40px;
        margin: -16px -16px 24px -16px;
    ">
        <div style="font-size: 14px; color: #7dd3fc; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px;">
            xarray-linked-data &middot; Notebook 1
        </div>
        <h1 style="color: #f0f9ff; font-size: 2.4rem; margin: 0 0 16px 0; line-height: 1.2;">
            Linked Data Design for Multi-Assay Experiments
        </h1>
        <p style="color: #bae6fd; font-size: 1.1rem; margin: 0; max-width: 640px; line-height: 1.6;">
            Six assay domains. One coordinate system. Everything stays aligned.
            Build a unified xarray Dataset linking analytical chemistry, binding assays,
            cell-based assays, functional readouts, genomics, and molecular features.
        </p>
    </div>
    """)
    return


@app.cell(hide_code=True)
def cell_tour(mo):
    import wigglystuff

    tour = wigglystuff.CellTour(
        steps=[
            {"cell_name": "hero", "title": "Linked Data Design", "description": "Six assay domains unified in one xarray DataTree, linked by the molecule coordinate."},
            {"cell_name": "stage1_analytical", "title": "Analytical Chemistry", "description": "DLS, zeta potential, HPLC purity, and mass spec -- the physicochemical foundation."},
            {"cell_name": "stage2_fit", "title": "Bayesian 4PL Fitting", "description": "Hierarchical PyMC model fits all molecule/target pairs, extracting EC50 posteriors with proper uncertainty."},
            {"cell_name": "stage3_cell_assays", "title": "Cell-Based Assays", "description": "Flow cytometry uptake with Bayesian estimation of MFI and % positive per cell line."},
            {"cell_name": "stage4_functional", "title": "Functional Readouts", "description": "Potency and efficacy derived from binding EC50 x uptake efficiency -- only possible because stages share the molecule coordinate."},
            {"cell_name": "stage5_genomics", "title": "Genomics", "description": "Perturbation RNA-seq: transcriptional signatures across a 20-gene pathway panel."},
            {"cell_name": "stage6_features", "title": "Informative Feature Priors", "description": "Molecular descriptors (MW, LogP, TPSA...) derived from upstream assay posteriors -- features carry real signal, not noise."},
            {"cell_name": "unify_all", "title": "The Campaign DataTree", "description": "DataTree.from_dict() organizes each assay as a node. Posteriors live in separate nodes -- no draw dimension conflicts."},
            {"cell_name": "demo_selection", "title": "Single-Molecule Selection", "description": "campaign.sel(molecule=...) slices every node. Reports EC50 and uptake from full MCMC posteriors."},
            {"cell_name": "demo_cross_assay_query", "title": "Cross-Assay Query", "description": "Filter molecules by criteria pulled from four different tree nodes simultaneously."},
            {"cell_name": "demo_train_test_split", "title": "Train/Test Split", "description": "One .sel() call propagates the split mask across every assay node in the tree."},
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
    import pymc as pm
    import pytensor.tensor as pt
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import warnings

    warnings.filterwarnings("ignore")
    np.random.seed(42)
    return go, make_subplots, mo, np, pm, pt, xr


@app.cell(hide_code=True)
def intro(mo):
    mo.md(r"""
    ## The problem: scattered data across assays

    A molecule characterization campaign generates data from many assays.
    Each assay has its own file format, its own indexing scheme, its own
    number of replicates. Keeping track of which molecule corresponds to
    which row in which CSV is exhausting and error-prone.

    **The solution:** store everything in a single xarray `Dataset` where
    `molecule_id` is the shared coordinate. Every measurement, estimate,
    and feature knows its own coordinates. When you slice, everything
    stays aligned automatically.

    We will progressively build a unified dataset across **six assay domains**,
    verifying coordinate alignment at every stage.
    """)
    return


@app.cell(hide_code=True)
def target_diagram(mo):
    mo.md("""
    <style>
    .ldd-target { font-family: -apple-system, system-ui, sans-serif; }
    .ldd-target .ldd-label {
        font-size: 11px; font-weight: 700; letter-spacing: 2px;
        text-transform: uppercase; color: #64748b; margin-bottom: 6px;
    }
    .ldd-target .ldd-sub {
        font-size: 13px; color: #475569; line-height: 1.6; margin-bottom: 16px;
    }
    .ldd-target .ldd-sub code {
        background: #e2e8f0; padding: 1px 5px; border-radius: 4px;
        font-size: 12px; color: #0c4a6e;
    }
    .ldd-target .ldd-grid {
        display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 10px; margin: 14px 0;
    }
    .ldd-target .ldd-card {
        border-radius: 10px; padding: 12px 14px;
        background: #f8fafc; border-top: 3px solid #cbd5e1;
    }
    .ldd-target .ldd-card .num {
        font-size: 9px; font-weight: 700; letter-spacing: 0.5px;
        opacity: 0.55; text-transform: uppercase;
    }
    .ldd-target .ldd-card .name {
        font-size: 13px; font-weight: 700; margin: 2px 0 6px; color: #1e293b;
    }
    .ldd-target .ldd-card .vars {
        font-size: 11px; color: #475569; font-family: monospace; line-height: 1.55;
    }
    .ldd-target .ldd-card .note {
        font-size: 10px; color: #94a3b8; font-style: italic;
    }
    .ldd-target .ldd-card .dims {
        font-size: 10px; color: #94a3b8; margin-top: 6px;
        font-family: monospace; padding-top: 5px; border-top: 1px solid #e2e8f0;
    }
    .ldd-target .ldd-card .dims b { color: #3b82f6; }
    .ldd-target .ldd-arrow {
        text-align: center; color: #94a3b8; font-size: 22px; margin: 0;
    }
    .ldd-target .ldd-merge {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #0c4a6e 100%);
        border-radius: 12px; padding: 18px 24px; color: #e2e8f0;
    }
    .ldd-target .ldd-merge .h {
        font-size: 13px; font-weight: 700; color: #7dd3fc;
        margin-bottom: 10px; font-family: monospace;
    }
    .ldd-target .ldd-merge .row { font-size: 12px; font-family: monospace; line-height: 1.8; color: #cbd5e1; }
    .ldd-target .ldd-merge .k { color: #f0f9ff; font-weight: 600; }
    .ldd-target .ldd-merge .a { color: #7dd3fc; font-weight: 600; }
    </style>
    <div class="ldd-target">
      <div class="ldd-label">The target &mdash; what we're building towards</div>
      <div class="ldd-sub">
        Six independent assay datasets, each with their own dimensions,
        unified into a <b>single xarray Dataset</b> via the shared
        <code>molecule</code> coordinate. Every variable knows its own
        dimensions &mdash; slice one molecule and all linked data comes along.
      </div>

      <div class="ldd-grid">
        <div class="ldd-card" style="border-color: #3b82f6;">
          <div class="num">Stage 1</div>
          <div class="name">Analytical Chemistry</div>
          <div class="vars">dls_diameter_nm<br>zeta_potential_mv<br>hplc_purity_percent<br>observed_mass_da</div>
          <div class="dims"><b>molecule</b>, batch, replicate, time_min</div>
        </div>
        <div class="ldd-card" style="border-color: #8b5cf6;">
          <div class="num">Stage 2</div>
          <div class="name">Binding Assays</div>
          <div class="vars">od450 &rarr; ec50_nm<br>ec50_nm_std<br>hill_coefficient<br><span class="note">Bayesian 4PL fit</span></div>
          <div class="dims"><b>molecule</b>, target, conc_nm, replicate</div>
        </div>
        <div class="ldd-card" style="border-color: #10b981;">
          <div class="num">Stage 3</div>
          <div class="name">Cell-Based Assays</div>
          <div class="vars">uptake_median_mfi<br>uptake_pct_positive</div>
          <div class="dims"><b>molecule</b>, cell_line</div>
        </div>
        <div class="ldd-card" style="border-color: #f59e0b;">
          <div class="num">Stage 4</div>
          <div class="name">Functional Readouts</div>
          <div class="vars">functional_ec50_um<br>efficacy_percent</div>
          <div class="dims"><b>molecule</b>, cell_line</div>
        </div>
        <div class="ldd-card" style="border-color: #ec4899;">
          <div class="num">Stage 5</div>
          <div class="name">Genomics</div>
          <div class="vars">log2_fold_change<br><span class="note">20-gene pathway panel</span></div>
          <div class="dims"><b>molecule</b>, cell_line, gene</div>
        </div>
        <div class="ldd-card" style="border-color: #14b8a6;">
          <div class="num">Stage 6</div>
          <div class="name">Features &amp; Splits</div>
          <div class="vars">features (6 descriptors)<br>train_mask, test_mask</div>
          <div class="dims"><b>molecule</b>, feature, split_type</div>
        </div>
      </div>

      <div class="ldd-arrow">&#x2193;&nbsp;&nbsp;&#x2193;&nbsp;&nbsp;&#x2193;</div>

      <div class="ldd-merge">
        <div class="h">unified = xr.merge([ds_stage1, ..., ds_stage6], join="outer")</div>
        <div class="row">
          <span class="k">Dimensions:</span> <span class="a">molecule</span>(40), batch(2), replicate(3), time_min(5),
        </div>
        <div class="row">
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;target(3), concentration_nm(8), cell_line(3), gene(20), feature(6), split_type(3)
        </div>
        <br>
        <div class="row">
          <span class="k">Coordinates:</span> <span class="a">molecule</span> [LNP_001 .. LNP_040] &larr; the shared spine
        </div>
        <br>
        <div class="row">
          <span class="k">Data variables:</span> 15+ variables across 6 domains &mdash; all auto-aligned
        </div>
      </div>
    </div>
    """)
    return


@app.cell(hide_code=True)
def design_coords(np):
    # Experimental design: 40 candidate molecules across 2 batches
    n_molecules = 40
    molecule_ids = [f"LNP_{i:03d}" for i in range(1, n_molecules + 1)]
    batches = ["batch_A", "batch_B"]
    replicates = ["r1", "r2", "r3"]

    # Binding targets and cell lines
    targets = ["EGFR", "HER2", "CD20"]
    cell_lines = ["HEPG2", "HEK293", "primary_hepatocytes"]

    # Concentration series for dose-response (log-spaced, nM)
    concentrations_nm = np.logspace(0, 4, 8)  # 1 nM to 10000 nM

    # Time points for stability (minutes)
    time_min = np.array([0, 15, 30, 60, 120])

    print(f"Design: {n_molecules} molecules x {len(batches)} batches x {len(replicates)} replicates")
    print(f"Targets: {targets}")
    print(f"Cell lines: {cell_lines}")
    print(f"Concentrations (nM): {concentrations_nm}")
    return (
        batches,
        cell_lines,
        concentrations_nm,
        molecule_ids,
        n_molecules,
        replicates,
        targets,
        time_min,
    )


@app.cell(hide_code=True)
def stage1_header(mo):
    mo.md("""
    ## Stage 1: Analytical Chemistry

    Raw physicochemical characterization: DLS particle size, zeta potential,
    HPLC purity, and mass spectrometry observed mass. Each measurement aligned
    by `molecule_id` and `batch`.
    """)
    return


@app.cell(hide_code=True)
def stage1_analytical(
    batches,
    molecule_ids,
    n_molecules,
    np,
    replicates,
    time_min,
    xr,
):
    # --- Stage 1: Analytical Chemistry ---
    # Realistic priors informed by LNP characterization literature
    # (e.g., Schoenmaker et al. 2021 Int J Pharm; FDA LNP product guidance)

    # Latent formulation quality: creates realistic cross-metric correlation
    # (well-controlled formulations score well across all physicochemical metrics)
    formulation_quality = np.random.beta(4, 1.5, n_molecules)  # mean ~0.73

    # --- DLS: hydrodynamic diameter timeseries ---
    # Target 80-100 nm (standard for LNP drug delivery; FDA-approved LNPs ~60-100 nm)
    # lognormal(ln(85), 0.08) → median ~85 nm, most values 75-100 nm
    TARGET_SIZE_NM = 85.0
    dls_diameter = np.random.lognormal(
        np.log(TARGET_SIZE_NM), 0.08,
        (n_molecules, 2, 3, len(time_min)),
    )
    # Lower-quality formulations deviate more from the target size
    size_jitter = (1 - formulation_quality)[:, None, None, None] * 15
    dls_diameter += np.random.normal(0, 1, dls_diameter.shape) * size_jitter
    # Batch B: different microfluidic mixing parameters → ~5 nm larger on average
    dls_diameter[:, 1, :, :] += np.random.normal(5, 1)
    # Time stability: high-quality formulations are stable; poor ones aggregate
    # (aggregation rate inversely proportional to formulation quality)
    for drift_idx, drift_t in enumerate(time_min):
        drift = (1 - formulation_quality)[:, None, None] * 0.002 * drift_t
        dls_diameter[:, :, :, drift_idx] *= (1 + drift)

    # --- Zeta potential ---
    # Ionizable lipid LNPs at pH 7.4: surface charge typically -5 to -25 mV
    # (near-neutral by design: reduces opsonization, enables endosomal escape at low pH)
    zeta_potential = np.random.normal(-12, 4, (n_molecules, 2, 3))
    # Batch B slightly more negative (lipid composition batch variability)
    zeta_potential[:, 1, :] -= 2

    # --- HPLC purity ---
    # Pharmaceutical release spec: >=90%; typical values 93-99%
    # Beta-shaped distribution right-skewed toward high purity, modulated by quality
    hplc_purity = (
        np.random.beta(10, 2, (n_molecules, 2)) * 10  # → ~75-99%
        + 88
        + formulation_quality[:, None] * 3  # quality bonus
    ).clip(82, 100)

    # --- Mass spec: observed molecular weight ---
    # Payload assumed to be siRNA duplex (21-mer): ~13,000-14,000 Da
    # (ssRNA ~6,500 Da per strand; duplex ~2x)
    observed_mass = np.random.lognormal(
        np.log(13_500), 0.05, n_molecules
    )

    ds_stage1 = xr.Dataset(
        data_vars={
            "dls_diameter_nm": (["molecule", "batch", "replicate", "time_min"], dls_diameter),
            "zeta_potential_mv": (["molecule", "batch", "replicate"], zeta_potential),
            "hplc_purity_percent": (["molecule", "batch"], hplc_purity),
            "observed_mass_da": (["molecule"], observed_mass),
        },
        coords={
            "molecule": molecule_ids,
            "batch": batches,
            "replicate": replicates,
            "time_min": time_min,
        },
        attrs={"stage": "1_analytical_chemistry", "description": "Physicochemical characterization"},
    )
    print(ds_stage1)
    return (ds_stage1,)


@app.cell(hide_code=True)
def verify_stage1(ds_stage1, mo):
    # Self-verifying: check coordinate alignment
    assert ds_stage1.dls_diameter_nm.dims == ("molecule", "batch", "replicate", "time_min")
    assert ds_stage1.sizes["molecule"] == 40
    assert ds_stage1.sizes["time_min"] == 5
    assert "molecule" in ds_stage1.dls_diameter_nm.coords
    # Zeta potential shares molecule + batch + replicate coords
    assert ds_stage1.zeta_potential_mv.sel(molecule="LNP_001", batch="batch_A").shape == (3,)
    mo.callout(
        mo.md("**Stage 1 verified:** all analytical chemistry data aligned by `molecule` coordinate."),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def stage1_plot(batches, ds_stage1, go, make_subplots, np, time_min):
    batch_colors = {"batch_A": "#3b82f6", "batch_B": "#f59e0b"}


    def ecdf(data, ax, color, label, marker="o"):
        """Plot empirical CDF with step markers."""
        x = np.sort(data)
        y = np.arange(1, len(x) + 1) / len(x)
        ax.plot(x, y, marker=marker, color=color, label=label, linewidth=1.5, markersize=3, alpha=0.8)


    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "A. DLS Size Stability (median + IQR)",
            "B. Zeta Potential by Batch",
            "C. HPLC Purity by Batch",
            "D. Mass Spec: Observed Mass",
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    # --- A: DLS diameter vs time (median + IQR ribbon per batch) ---
    for batch in batches:
        vals = ds_stage1.dls_diameter_nm.sel(batch=batch).values
        median = np.median(vals, axis=(0, 1))
        q25 = np.percentile(vals, 25, axis=(0, 1))
        q75 = np.percentile(vals, 75, axis=(0, 1))
        fig.add_trace(go.Scatter(
            x=list(time_min) + list(time_min[::-1]),
            y=list(q75) + list(q25[::-1]),
            fill="toself",
            fillcolor=batch_colors[batch],
            opacity=0.15,
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=time_min,
            y=median,
            mode="lines+markers",
            line=dict(color=batch_colors[batch], width=2),
            marker=dict(size=7),
            name=batch,
        ), row=1, col=1)

    # --- B: Zeta potential ECDFs by batch ---
    for batch in batches:
        zeta = np.sort(ds_stage1.zeta_potential_mv.sel(batch=batch).values.ravel())
        ecdf_y = np.arange(1, len(zeta) + 1) / len(zeta)
        fig.add_trace(go.Scatter(
            x=zeta, y=ecdf_y,
            mode="lines+markers",
            line=dict(color=batch_colors[batch], width=2),
            marker=dict(size=3),
            name=batch,
            showlegend=False,
        ), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=[-30, -30], y=[0, 1],
        mode="lines", line=dict(color="red", dash="dash", width=1.5),
        showlegend=False,
    ), row=1, col=2)

    # --- C: HPLC purity ECDFs by batch ---
    for batch in batches:
        purity = np.sort(ds_stage1.hplc_purity_percent.sel(batch=batch).values.ravel())
        ecdf_y = np.arange(1, len(purity) + 1) / len(purity)
        fig.add_trace(go.Scatter(
            x=purity, y=ecdf_y,
            mode="lines+markers",
            line=dict(color=batch_colors[batch], width=2),
            marker=dict(size=3),
            name=batch,
            showlegend=False,
        ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=[90, 90], y=[0, 1],
        mode="lines", line=dict(color="red", dash="dash", width=1.5),
        showlegend=False,
    ), row=2, col=1)

    # --- D: Observed mass ECDF ---
    mass = np.sort(ds_stage1.observed_mass_da.values)
    ecdf_y = np.arange(1, len(mass) + 1) / len(mass)
    fig.add_trace(go.Scatter(
        x=mass, y=ecdf_y,
        mode="lines+markers",
        line=dict(color="#10b981", width=2),
        marker=dict(size=4),
        name="All molecules",
        showlegend=False,
    ), row=2, col=2)
    median_mass = np.median(mass)
    fig.add_trace(go.Scatter(
        x=[median_mass, median_mass], y=[0, 1],
        mode="lines", line=dict(color="navy", width=2),
        showlegend=False,
    ), row=2, col=2)

    fig.update_xaxes(title_text="Time (min)", row=1, col=1)
    fig.update_xaxes(title_text="Zeta Potential (mV)", row=1, col=2)
    fig.update_xaxes(title_text="HPLC Purity (%)", row=2, col=1)
    fig.update_xaxes(title_text="Observed Mass (Da)", row=2, col=2)
    fig.update_yaxes(title_text="Diameter (nm)", row=1, col=1)
    fig.update_yaxes(title_text="ECDF", row=1, col=2)
    fig.update_yaxes(title_text="ECDF", row=2, col=1)
    fig.update_yaxes(title_text="ECDF", row=2, col=2)

    fig.update_layout(
        title=dict(text="Stage 1: Analytical Chemistry Characterization", font=dict(size=16)),
        height=750,
        width=1000,
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, title="Batch"),
    )

    fig
    return


@app.cell(hide_code=True)
def stage2_header(mo):
    mo.md("""
    ## Stage 2: Binding Assays (ELISA Dose-Response)

    ELISA OD450 readings across a concentration series. We fit **Bayesian
    4-parameter logistic (4PL) curves** using PyMC to extract EC50 and Hill
    coefficient estimates with proper uncertainty quantification.

    The hierarchical model fits all molecule/target pairs simultaneously,
    sharing information across the population while allowing individual
    variation.
    """)
    return


@app.function(hide_code=True)
def four_pl(conc, bottom, top, ec50, hill):
    """4-parameter logistic dose-response curve."""
    return bottom + (top - bottom) / (1 + (ec50 / conc) ** hill)


@app.cell(hide_code=True)
def stage2_binding(
    concentrations_nm,
    molecule_ids,
    n_molecules,
    np,
    replicates,
    targets,
    xr,
):
    # Generate synthetic ELISA dose-response data
    # True EC50 per molecule/target, generated via a Gaussian copula to encode
    # biologically realistic cross-target correlations.
    from scipy import stats

    # --- Gaussian copula for correlated EC50 across targets ---
    # EGFR and HER2 are both ERBB-family receptor tyrosine kinases
    #   -> molecules that potently inhibit one often cross-react with the other
    #   -> strong positive correlation
    # CD20 is an unrelated B-cell surface marker (MS4A1)
    #   -> no shared binding pocket -> near-zero / slightly negative correlation
    copula_corr = np.array([
        #       EGFR   HER2   CD20
        [1.00,  0.65, -0.15],   # EGFR
        [0.65,  1.00,  0.10],   # HER2
        [-0.15, 0.10,  1.00],   # CD20
    ])

    # Draw correlated standard normals, push through copula to lognormal marginals
    copula_z = stats.multivariate_normal.rvs(
        mean=np.zeros(len(targets)),
        cov=copula_corr,
        size=n_molecules,
    )  # (n_molecules, n_targets)
    copula_u = stats.norm.cdf(copula_z)  # uniform marginals in [0, 1]
    true_ec50 = stats.lognorm.ppf(
        copula_u, s=1, scale=np.exp(2)
    )  # lognormal(mu=2, sigma=1) -> median ~7.4 nM

    true_hill = np.random.normal(1.5, 0.4, (n_molecules, len(targets)))
    true_bottom = 0.05
    true_top = 2.5

    # OD450 readings: (molecule, target, concentration, replicate)
    od450 = np.zeros((n_molecules, len(targets), len(concentrations_nm), 3))
    for bind_m in range(n_molecules):
        for bind_t in range(len(targets)):
            signal = four_pl(
                concentrations_nm,
                true_bottom,
                true_top,
                true_ec50[bind_m, bind_t],
                true_hill[bind_m, bind_t],
            )
            noise = np.random.normal(0, 0.05, (len(concentrations_nm), 3))
            od450[bind_m, bind_t] = signal[:, None] + noise

    ds_stage2 = xr.Dataset(
        data_vars={
            "od450": (
                ["molecule", "target", "concentration_nm", "replicate"],
                od450,
            ),
        },
        coords={
            "molecule": molecule_ids,
            "target": targets,
            "concentration_nm": concentrations_nm,
            "replicate": replicates,
        },
        attrs={"stage": "2_binding_assays", "assay": "ELISA dose-response"},
    )
    empirical_corr = np.corrcoef(np.log(true_ec50), rowvar=False)
    print(f"ELISA data shape: {od450.shape}")
    print(f"Concentration range: {concentrations_nm[0]:.1f} - {concentrations_nm[-1]:.0f} nM")
    print(f"Copula target correlation matrix:\n{copula_corr}")
    print(f"Empirical log-EC50 correlation:\n{np.round(empirical_corr, 2)}")
    return (ds_stage2,)


@app.cell(hide_code=True)
def stage2_fit(concentrations_nm, ds_stage2, mo, np, pm, pt):
    # Bayesian 4PL estimation with PyMC -- hierarchical model
    # Hyperpriors enable partial pooling across molecule/target pairs
    n_mol = ds_stage2.sizes["molecule"]
    n_tgt = ds_stage2.sizes["target"]
    n_rep = ds_stage2.sizes["replicate"]
    n_conc = ds_stage2.sizes["concentration_nm"]

    od450_all = ds_stage2.od450.values  # (n_mol, n_tgt, n_conc, n_rep)

    with pm.Model() as fourpl_model:
        bottom = pm.Normal("bottom", mu=0.05, sigma=0.1)
        top = pm.Normal("top", mu=2.5, sigma=0.5)

        mu_log_ec50 = pm.Normal("mu_log_ec50", mu=np.log(50), sigma=2)
        sigma_log_ec50 = pm.HalfNormal("sigma_log_ec50", sigma=1)
        log_ec50 = pm.Normal(
            "log_ec50",
            mu=mu_log_ec50,
            sigma=sigma_log_ec50,
            shape=(n_mol, n_tgt),
        )

        mu_hill = pm.HalfNormal("mu_hill", sigma=2)
        sigma_hill = pm.HalfNormal("sigma_hill", sigma=0.5)
        hill = pm.TruncatedNormal(
            "hill", mu=mu_hill, sigma=sigma_hill, lower=0.1,
            shape=(n_mol, n_tgt),
        )

        sigma = pm.HalfNormal("sigma", sigma=0.1)

        ec50 = pt.exp(log_ec50)[:, :, None, None]
        conc_tensor = concentrations_nm[None, None, :, None]
        mu_curves = bottom + (top - bottom) / (
            1 + (ec50 / conc_tensor) ** hill[:, :, None, None]
        )
        pm.Normal("obs", mu=mu_curves, sigma=sigma, observed=od450_all)

        trace = pm.sample(1000, chains=4, progressbar=True, target_accept=0.9)

    # Posterior summaries
    ec50_posterior = np.exp(trace.posterior["log_ec50"]).values  # (chain, draw, n_mol, n_tgt)
    ec50_estimates = ec50_posterior.mean(axis=(0, 1))
    ec50_stds = ec50_posterior.std(axis=(0, 1))
    hill_estimates = trace.posterior["hill"].mean(axis=(0, 1)).values

    # Store full posterior draws aligned by molecule/target coordinates
    n_total_draws_s2 = trace.posterior.sizes["chain"] * trace.posterior.sizes["draw"]
    ec50_full_post = ec50_posterior.reshape(-1, n_mol, n_tgt).transpose(1, 2, 0)

    ds_stage2_fitted = ds_stage2.assign(
        {
            "ec50_nm": (["molecule", "target"], ec50_estimates),
            "ec50_nm_std": (["molecule", "target"], ec50_stds),
            "hill_coefficient": (["molecule", "target"], hill_estimates),
            "ec50_nm_posterior": (["molecule", "target", "draw"], ec50_full_post),
        }
    )
    ds_stage2_fitted = ds_stage2_fitted.assign_coords(draw=np.arange(n_total_draws_s2))

    mo.callout(
        mo.md(
            f"**Bayesian 4PL fit complete:** Hierarchical posterior EC50 for {n_mol} molecules x {n_tgt} targets. "
            f"Median EC50 = {np.nanmedian(ec50_estimates):.1f} nM "
            f"(population mu = {np.exp(trace.posterior['mu_log_ec50'].mean()):.1f} nM). "
            f"Full posterior ({n_total_draws_s2} draws) stored as `ec50_nm_posterior`."
        ),
        kind="info",
    )
    return ds_stage2_fitted, n_mol, n_tgt, trace


@app.cell(hide_code=True)
def stage2_forest(
    go,
    make_subplots,
    molecule_ids,
    n_mol,
    n_tgt,
    np,
    targets,
    trace,
):
    # Flatten posterior samples: (chain, draw, n_mol, n_tgt) -> (n_samples, n_mol, n_tgt)
    ec50_post = np.exp(trace.posterior["log_ec50"].values).reshape(-1, n_mol, n_tgt)

    forest_medians = np.median(ec50_post, axis=0)
    forest_ci_low = np.percentile(ec50_post, 3, axis=0)
    forest_ci_high = np.percentile(ec50_post, 97, axis=0)

    target_colors = ["#3b82f6", "#8b5cf6", "#10b981"]
    mol_y = np.arange(n_mol)

    forest_fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[f"EC50 vs {t}" for t in targets],
        shared_yaxes=True,
        horizontal_spacing=0.07,
    )

    for t_idx, t_name in enumerate(targets):
        col = t_idx + 1
        color = target_colors[t_idx]

        # Credible interval lines (single trace, None-separated)
        ci_x, ci_y = [], []
        for m in range(n_mol):
            ci_x.extend([forest_ci_low[m, t_idx], forest_ci_high[m, t_idx], None])
            ci_y.extend([m, m, None])
        forest_fig.add_trace(go.Scatter(
            x=ci_x, y=ci_y,
            mode="lines",
            line=dict(color=color, width=2),
            showlegend=False,
            hoverinfo="skip",
        ), row=1, col=col)

        # Median markers with hover
        forest_fig.add_trace(go.Scatter(
            x=forest_medians[:, t_idx],
            y=mol_y,
            mode="markers",
            marker=dict(color=color, size=7),
            name=t_name,
            showlegend=False,
            customdata=np.stack(
                [forest_ci_low[:, t_idx], forest_ci_high[:, t_idx]], axis=-1
            ),
            text=molecule_ids,
            hovertemplate=(
                "<b>%{text}</b> vs " + t_name + "<br>"
                "Median EC50: %{x:.1f} nM<br>"
                "94% CI: [%{customdata[0]:.1f}, %{customdata[1]:.1f}]<extra></extra>"
            ),
        ), row=1, col=col)

    # Log-scale x-axes
    for t_idx in range(len(targets)):
        forest_fig.update_xaxes(title_text="EC50 (nM)", type="log", row=1, col=t_idx + 1)

    # Molecule labels on y-axis (reverse so LNP_001 is at top)
    forest_fig.update_yaxes(
        tickvals=mol_y[::2],
        ticktext=[molecule_ids[i] for i in mol_y[::2]],
        row=1, col=1,
        autorange="reversed",
    )

    forest_fig.update_layout(
        title=dict(
            text="Posterior EC50 Forest Plots by Target (94% Credible Intervals)",
            font=dict(size=15),
        ),
        height=800,
        width=1100,
    )

    forest_fig
    return


@app.cell(hide_code=True)
def verify_stage2(ds_stage2_fitted, mo):
    assert "ec50_nm" in ds_stage2_fitted
    assert ds_stage2_fitted.ec50_nm.dims == ("molecule", "target")
    assert ds_stage2_fitted.ec50_nm.sel(target="EGFR").shape == (40,)
    # Verify OD450 and EC50 share the molecule coordinate
    assert (
        ds_stage2_fitted.od450.molecule.values
        == ds_stage2_fitted.ec50_nm.molecule.values
    ).all()
    mo.callout(
        mo.md(
            "**Stage 2 verified:** dose-response data and 4PL estimates aligned by `molecule` and `target`."
        ),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def stage3_header(mo):
    mo.md("""
    ## Stage 3: Cell-Based Assays (Flow Cytometry)

    Cell uptake measured by flow cytometry. Per-event fluorescence intensity
    for each molecule/cell_line combination. We compute summary statistics
    (median fluorescence, % positive cells) and add them to the unified dataset.
    """)
    return


@app.cell(hide_code=True)
def stage3_cell_assays(
    cell_lines,
    molecule_ids,
    n_molecules,
    np,
    replicates,
    xr,
):
    # Flow cytometry uptake: cell-line-specific baselines + biological replicates
    # Realistic priors from LNP transfection literature:
    # - HEPG2 (hepatocarcinoma): high LDL-R / scavenger receptor expression -> strong uptake
    # - HEK293 (embryonic kidney): moderate uptake, standard transfectable line
    # - primary_hepatocytes: lower uptake (primary cells harder to transfect than immortalized)
    n_events = 500  # events per replicate (simulation context)

    # Cell-line baseline log-median-MFI: exp(5.3)=200, exp(4.7)=110, exp(4.3)=74
    cl_baseline_logmfi = np.array([5.3, 4.7, 4.3])
    cl_baseline_pctpos = np.array([45.0, 30.0, 20.0])

    # Per-molecule uptake propensity (some formulations enter cells more efficiently)
    uptake_potency = np.random.normal(0, 1, n_molecules)

    # True latent parameters per molecule x cell_line
    true_logmfi = (
        cl_baseline_logmfi[None, :]
        + uptake_potency[:, None] * 0.5
        + np.random.normal(0, 0.15, (n_molecules, len(cell_lines)))
    )
    true_pctpos = (
        cl_baseline_pctpos[None, :]
        + uptake_potency[:, None] * 10
        + np.random.normal(0, 5, (n_molecules, len(cell_lines)))
    ).clip(2, 95)

    # Generate biological replicates (independent flow cytometry runs)
    median_mfi_rep = np.zeros((n_molecules, len(cell_lines), len(replicates)))
    pct_pos_rep = np.zeros((n_molecules, len(cell_lines), len(replicates)))
    for cl_idx in range(len(cell_lines)):
        for rep_idx in range(len(replicates)):
            median_mfi_rep[:, cl_idx, rep_idx] = np.random.lognormal(
                true_logmfi[:, cl_idx], 0.15
            )
            pct_pos_rep[:, cl_idx, rep_idx] = np.random.normal(
                true_pctpos[:, cl_idx], 5
            ).clip(1, 99)

    ds_stage3 = xr.Dataset(
        data_vars={
            "median_mfi_replicate": (["molecule", "cell_line", "replicate"], median_mfi_rep),
            "pct_positive_replicate": (["molecule", "cell_line", "replicate"], pct_pos_rep),
        },
        coords={
            "molecule": molecule_ids,
            "cell_line": cell_lines,
            "replicate": replicates,
        },
        attrs={"stage": "3_cell_based_assays", "assay": "Flow cytometry uptake (3 replicates)"},
    )
    print(f"Replicate data: {n_molecules} molecules x {len(cell_lines)} cell lines x {len(replicates)} replicates")
    print(f"Median MFI range: [{median_mfi_rep.min():.0f}, {median_mfi_rep.max():.0f}]")
    print(f"% Positive range: [{pct_pos_rep.min():.1f}, {pct_pos_rep.max():.1f}]")
    return ds_stage3, median_mfi_rep, pct_pos_rep


@app.cell(hide_code=True)
def stage3_fit(
    cell_lines,
    ds_stage3,
    median_mfi_rep,
    mo,
    n_molecules,
    np,
    pct_pos_rep,
    pm,
):
    # Hierarchical Bayesian estimation of uptake parameters
    # Models both median MFI (log scale) and % positive (logit scale)
    # Partial pooling: cell-line baselines + molecule-level deviations

    log_mfi_rep = np.log(median_mfi_rep)  # (n_mol, n_cl, n_rep)
    logit_pct_rep = np.log(pct_pos_rep / (100 - pct_pos_rep))

    with pm.Model() as uptake_model:
        mu_cl_mfi = pm.Normal("mu_cl_mfi", mu=5.0, sigma=0.5, shape=len(cell_lines))
        sigma_mol_mfi = pm.HalfNormal("sigma_mol_mfi", sigma=0.5)
        mol_dev_mfi = pm.Normal(
            "mol_dev_mfi", mu=0, sigma=sigma_mol_mfi,
            shape=(n_molecules, len(cell_lines)),
        )
        sigma_obs_mfi = pm.HalfNormal("sigma_obs_mfi", sigma=0.3)
        mu_mfi_true = mu_cl_mfi[None, :] + mol_dev_mfi
        pm.Normal("mfi_obs", mu=mu_mfi_true[:, :, None], sigma=sigma_obs_mfi, observed=log_mfi_rep)

        mu_cl_pct = pm.Normal("mu_cl_pct", mu=0.0, sigma=1.0, shape=len(cell_lines))
        sigma_mol_pct = pm.HalfNormal("sigma_mol_pct", sigma=0.5)
        mol_dev_pct = pm.Normal(
            "mol_dev_pct", mu=0, sigma=sigma_mol_pct,
            shape=(n_molecules, len(cell_lines)),
        )
        sigma_obs_pct = pm.HalfNormal("sigma_obs_pct", sigma=0.3)
        mu_pct_true = mu_cl_pct[None, :] + mol_dev_pct
        pm.Normal("pct_obs", mu=mu_pct_true[:, :, None], sigma=sigma_obs_pct, observed=logit_pct_rep)

        pm.Deterministic("median_mfi_est", pm.math.exp(mu_mfi_true))
        pm.Deterministic("pct_positive_est", 100 / (1 + pm.math.exp(-mu_pct_true)))

        trace_stage3 = pm.sample(1000, tune=1500, chains=4, progressbar=True, target_accept=0.95)

    # Posterior summaries
    mfi_estimates = trace_stage3.posterior["median_mfi_est"].mean(dim=("chain", "draw")).values
    mfi_stds = trace_stage3.posterior["median_mfi_est"].std(dim=("chain", "draw")).values
    pct_estimates = trace_stage3.posterior["pct_positive_est"].mean(dim=("chain", "draw")).values
    pct_stds = trace_stage3.posterior["pct_positive_est"].std(dim=("chain", "draw")).values

    # Store full posterior draws aligned by molecule/cell_line coordinates
    n_total_draws_s3 = trace_stage3.posterior.sizes["chain"] * trace_stage3.posterior.sizes["draw"]
    mfi_full_post = trace_stage3.posterior["median_mfi_est"].values.reshape(
        -1, n_molecules, len(cell_lines)
    ).transpose(1, 2, 0)
    pct_full_post = trace_stage3.posterior["pct_positive_est"].values.reshape(
        -1, n_molecules, len(cell_lines)
    ).transpose(1, 2, 0)

    ds_stage3_fitted = ds_stage3.assign(
        {
            "uptake_median_mfi": (["molecule", "cell_line"], mfi_estimates),
            "uptake_median_mfi_std": (["molecule", "cell_line"], mfi_stds),
            "uptake_pct_positive": (["molecule", "cell_line"], pct_estimates),
            "uptake_pct_positive_std": (["molecule", "cell_line"], pct_stds),
            "uptake_median_mfi_posterior": (["molecule", "cell_line", "draw"], mfi_full_post),
            "uptake_pct_positive_posterior": (["molecule", "cell_line", "draw"], pct_full_post),
        }
    )
    ds_stage3_fitted = ds_stage3_fitted.assign_coords(draw=np.arange(n_total_draws_s3))

    mo.callout(
        mo.md(
            f"**Bayesian uptake estimation complete:** Posterior estimates for {n_molecules} molecules x {len(cell_lines)} cell lines. "
            f"Cell-line baseline log-MFI: {np.round(trace_stage3.posterior['mu_cl_mfi'].mean(dim=('chain', 'draw')).values, 2)}. "
            f"Full posteriors ({n_total_draws_s3} draws) stored inline."
        ),
        kind="info",
    )
    return (ds_stage3_fitted,)


@app.cell(hide_code=True)
def stage3_plot(
    cell_lines,
    ds_stage3_fitted,
    go,
    make_subplots,
    molecule_ids,
    np,
):
    cell_line_colors = {
        "HEPG2": "#ef4444",
        "HEK293": "#3b82f6",
        "primary_hepatocytes": "#10b981",
    }

    stage3_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "A. Posterior Median MFI by Cell Line",
            "B. Posterior % Positive by Cell Line",
            "C. Uptake Intensity vs Frequency (&plusmn;1&sigma;)",
            "D. % Positive Heatmap (posterior mean)",
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.12,
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "heatmap"}],
        ],
    )

    # --- A: ECDF of posterior-mean median MFI by cell line ---
    for cline in cell_lines:
        s3_sorted_mfi = np.sort(ds_stage3_fitted.uptake_median_mfi.sel(cell_line=cline).values)
        s3_cumprob_mfi = np.arange(1, len(s3_sorted_mfi) + 1) / len(s3_sorted_mfi)
        stage3_fig.add_trace(go.Scatter(
            x=s3_sorted_mfi, y=s3_cumprob_mfi,
            mode="lines+markers",
            line=dict(color=cell_line_colors[cline], width=2),
            marker=dict(size=3),
            name=cline,
        ), row=1, col=1)
    stage3_fig.add_trace(go.Scatter(
        x=[200, 200], y=[0, 1],
        mode="lines", line=dict(color="red", dash="dash", width=1.5),
        showlegend=False,
    ), row=1, col=1)

    # --- B: ECDF of posterior-mean % positive by cell line ---
    for cline in cell_lines:
        s3_sorted_pct = np.sort(ds_stage3_fitted.uptake_pct_positive.sel(cell_line=cline).values)
        s3_cumprob_pct = np.arange(1, len(s3_sorted_pct) + 1) / len(s3_sorted_pct)
        stage3_fig.add_trace(go.Scatter(
            x=s3_sorted_pct, y=s3_cumprob_pct,
            mode="lines+markers",
            line=dict(color=cell_line_colors[cline], width=2),
            marker=dict(size=3),
            name=cline,
            showlegend=False,
        ), row=1, col=2)

    # --- C: Scatter posterior mean MFI vs % positive with +/-1 sigma error bars ---
    for cline in cell_lines:
        s3_mfi_mean = ds_stage3_fitted.uptake_median_mfi.sel(cell_line=cline).values
        s3_mfi_sd = ds_stage3_fitted.uptake_median_mfi_std.sel(cell_line=cline).values
        s3_pct_mean = ds_stage3_fitted.uptake_pct_positive.sel(cell_line=cline).values
        s3_pct_sd = ds_stage3_fitted.uptake_pct_positive_std.sel(cell_line=cline).values
        stage3_fig.add_trace(go.Scatter(
            x=s3_mfi_mean, y=s3_pct_mean,
            mode="markers",
            marker=dict(color=cell_line_colors[cline], size=6, opacity=0.7),
            error_x=dict(type="data", array=s3_mfi_sd, visible=True, thickness=1, width=3),
            error_y=dict(type="data", array=s3_pct_sd, visible=True, thickness=1, width=3),
            name=cline,
            showlegend=False,
            text=molecule_ids,
            hovertemplate="<b>%{text}</b><br>MFI: %{x:.0f}<br>% Positive: %{y:.1f}%<extra></extra>",
        ), row=2, col=1)

    # --- D: Heatmap of posterior mean % positive (molecule x cell_line) ---
    s3_pct_heatmap = ds_stage3_fitted.uptake_pct_positive.values
    stage3_fig.add_trace(go.Heatmap(
        z=s3_pct_heatmap,
        x=cell_lines,
        y=molecule_ids,
        colorscale="Viridis",
        colorbar=dict(title="% Pos", x=1.0),
        hovertemplate="Molecule: %{y}<br>Cell Line: %{x}<br>% Positive: %{z:.1f}%<extra></extra>",
    ), row=2, col=2)

    # Axis labels
    stage3_fig.update_xaxes(title_text="Median MFI", row=1, col=1)
    stage3_fig.update_xaxes(title_text="% Positive", row=1, col=2)
    stage3_fig.update_xaxes(title_text="Median MFI (posterior mean)", row=2, col=1)
    stage3_fig.update_yaxes(title_text="ECDF", row=1, col=1)
    stage3_fig.update_yaxes(title_text="ECDF", row=1, col=2)
    stage3_fig.update_yaxes(title_text="% Positive (posterior mean)", row=2, col=1)

    stage3_fig.update_layout(
        title=dict(text="Stage 3: Cell-Based Assays (Bayesian Uptake Estimates)", font=dict(size=16)),
        height=800,
        width=1100,
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, title="Cell Line"),
    )

    stage3_fig
    return (cell_line_colors,)


@app.cell(hide_code=True)
def stage4_header(mo):
    mo.md("""
    ## Stage 4: Functional Readouts (Derived)

    Functional potency and efficacy are **derived from linked upstream data**:
    binding EC50 (Stage 2) sets the potency ceiling, while cell uptake
    (Stage 3) determines how much of that potency translates to functional
    effect. This cross-assay derivation is only possible because all stages
    share the `molecule` coordinate.
    """)
    return


@app.cell(hide_code=True)
def stage4_functional(
    cell_lines,
    ds_stage2_fitted,
    ds_stage3_fitted,
    molecule_ids,
    np,
    xr,
):
    # Functional potency is DERIVED from linked upstream data:
    # - Binding EC50 (Stage 2): sets the potency ceiling per molecule
    # - Cell uptake (Stage 3): determines delivery efficiency per cell line
    # Poor uptake shifts functional EC50 far above binding EC50 (delivery-limited potency)

    # Best binding EC50 per molecule (most potent target, from posterior mean)
    best_binding_ec50 = ds_stage2_fitted.ec50_nm.min(dim="target")  # (molecule,)

    # Uptake efficiency per molecule x cell_line (from Stage 3 Bayesian estimates)
    uptake_frac = ds_stage3_fitted.uptake_pct_positive / 100  # (molecule, cell_line)

    # Delivery penalty: poor uptake -> large shift from binding to functional EC50
    # At 100% uptake: penalty ~1x (functional ~ binding)
    # At 5% uptake: penalty ~20x
    delivery_penalty = 1.0 / uptake_frac.clip(min=0.05)

    # Functional EC50 (nM -> uM), with in vitro assay noise
    func_ec50_base = (best_binding_ec50 * delivery_penalty / 1000).values
    func_ec50_um = func_ec50_base * np.random.lognormal(0, 0.3, func_ec50_base.shape)

    # Efficacy: uptake-limited maximum response
    # Well-delivered molecules -> higher ceiling on efficacy
    efficacy_base = (20 + 75 * uptake_frac.values).clip(0, 100)
    efficacy_percent = (efficacy_base * np.random.normal(1, 0.1, efficacy_base.shape)).clip(0, 100)

    ds_stage4 = xr.Dataset(
        data_vars={
            "functional_ec50_um": (["molecule", "cell_line"], func_ec50_um),
            "efficacy_percent": (["molecule", "cell_line"], efficacy_percent),
        },
        coords={
            "molecule": molecule_ids,
            "cell_line": cell_lines,
        },
        attrs={
            "stage": "4_functional_readouts",
            "description": "Derived from binding EC50 (Stage 2) x uptake efficiency (Stage 3)",
        },
    )
    corr_binding_func = np.corrcoef(
        np.log(best_binding_ec50.values),
        np.log(func_ec50_um.mean(axis=1)),
    )[0, 1]
    print(f"Functional EC50 range: {func_ec50_um.min():.2f} - {func_ec50_um.max():.2f} uM")
    print(f"Efficacy range: {efficacy_percent.min():.1f} - {efficacy_percent.max():.1f}%")
    print(f"Binding-func EC50 correlation: {corr_binding_func:.2f}")
    return (ds_stage4,)


@app.cell(hide_code=True)
def stage4_plot(
    cell_line_colors,
    cell_lines,
    ds_stage2_fitted,
    ds_stage3_fitted,
    ds_stage4,
    go,
    make_subplots,
    molecule_ids,
    np,
):
    s4_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "A. Functional EC50 by Cell Line",
            "B. Efficacy by Cell Line",
            "C. Binding vs Functional EC50 (delivery penalty)",
            "D. Uptake vs Efficacy",
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.12,
    )

    # --- A: ECDF of functional EC50 by cell line ---
    for s4_cl in cell_lines:
        s4_func_sorted = np.sort(ds_stage4.functional_ec50_um.sel(cell_line=s4_cl).values)
        s4_cumprob = np.arange(1, len(s4_func_sorted) + 1) / len(s4_func_sorted)
        s4_fig.add_trace(go.Scatter(
            x=s4_func_sorted, y=s4_cumprob,
            mode="lines+markers",
            line=dict(color=cell_line_colors[s4_cl], width=2),
            marker=dict(size=3),
            name=s4_cl,
        ), row=1, col=1)

    # --- B: ECDF of efficacy by cell line ---
    for s4_cl in cell_lines:
        s4_eff_sorted = np.sort(ds_stage4.efficacy_percent.sel(cell_line=s4_cl).values)
        s4_cumprob_eff = np.arange(1, len(s4_eff_sorted) + 1) / len(s4_eff_sorted)
        s4_fig.add_trace(go.Scatter(
            x=s4_eff_sorted, y=s4_cumprob_eff,
            mode="lines+markers",
            line=dict(color=cell_line_colors[s4_cl], width=2),
            marker=dict(size=3),
            name=s4_cl,
            showlegend=False,
        ), row=1, col=2)

    # --- C: Scatter binding EC50 vs functional EC50 (log-log) ---
    s4_binding = ds_stage2_fitted.ec50_nm.min(dim="target").values
    for s4_cl in cell_lines:
        s4_func_cl = ds_stage4.functional_ec50_um.sel(cell_line=s4_cl).values
        s4_fig.add_trace(go.Scatter(
            x=s4_binding, y=s4_func_cl,
            mode="markers",
            marker=dict(color=cell_line_colors[s4_cl], size=6, opacity=0.7),
            name=s4_cl,
            showlegend=False,
            text=molecule_ids,
            hovertemplate="<b>%{text}</b> ("
            + s4_cl
            + ")<br>Binding: %{x:.1f} nM<br>Functional: %{y:.4f} uM<extra></extra>",
        ), row=2, col=1)

    # --- D: Scatter uptake % vs efficacy ---
    for s4_cl in cell_lines:
        s4_uptake_cl = ds_stage3_fitted.uptake_pct_positive.sel(cell_line=s4_cl).values
        s4_eff_cl = ds_stage4.efficacy_percent.sel(cell_line=s4_cl).values
        s4_fig.add_trace(go.Scatter(
            x=s4_uptake_cl, y=s4_eff_cl,
            mode="markers",
            marker=dict(color=cell_line_colors[s4_cl], size=6, opacity=0.7),
            name=s4_cl,
            showlegend=False,
            text=molecule_ids,
            hovertemplate="<b>%{text}</b> ("
            + s4_cl
            + ")<br>Uptake: %{x:.1f}%<br>Efficacy: %{y:.1f}%<extra></extra>",
        ), row=2, col=2)

    s4_fig.update_xaxes(title_text="Functional EC50 (uM)", row=1, col=1)
    s4_fig.update_xaxes(title_text="Efficacy (%)", row=1, col=2)
    s4_fig.update_xaxes(title_text="Binding EC50 (nM)", type="log", row=2, col=1)
    s4_fig.update_xaxes(title_text="Uptake % Positive", row=2, col=2)
    s4_fig.update_yaxes(title_text="ECDF", row=1, col=1)
    s4_fig.update_yaxes(title_text="ECDF", row=1, col=2)
    s4_fig.update_yaxes(title_text="Functional EC50 (uM)", type="log", row=2, col=1)
    s4_fig.update_yaxes(title_text="Efficacy (%)", row=2, col=2)

    s4_fig.update_layout(
        title=dict(
            text="Stage 4: Functional Readouts (Derived from Binding x Uptake)",
            font=dict(size=16),
        ),
        height=800,
        width=1100,
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, title="Cell Line"),
    )

    s4_fig
    return


@app.cell(hide_code=True)
def stage5_header(mo):
    mo.md("""
    ## Stage 5: Genomics (Perturbation Transcriptomics)

    RNA-seq after treatment: how does each molecule reshape gene expression?
    Each molecule produces a transcriptional signature across a focused panel
    of pathway genes --- drug targets, interferon-stimulated genes, and stress
    markers. This links molecular structure directly to transcriptional
    response.
    """)
    return


@app.cell(hide_code=True)
def stage5_genomics(cell_lines, molecule_ids, n_molecules, np, xr):
    # Perturbation transcriptomics: log2 fold change vs DMSO control
    # Per molecule x cell_line x gene panel (20 pathway genes)
    gene_panel = [
        "EGFR", "ERBB2", "MS4A1",         # drug targets
        "IFIT1", "OAS1", "ISG15", "MX1",  # interferon-stimulated genes
        "BAX", "BCL2", "CASP3",           # apoptosis
        "ATF4", "XBP1", "HSPA5",          # ER stress
        "CLTC", "CAV1", "LDLR",           # endocytosis / trafficking
        "IL6", "TNF",                     # inflammatory
        "GAPDH", "ACTB",                  # housekeeping (~0 log2FC)
    ]

    # Each molecule produces a distinct transcriptional signature
    log2fc = np.random.normal(0, 0.5, (n_molecules, len(cell_lines), len(gene_panel)))

    # Drug-target knockdown: map binding targets to gene symbols
    target_gene = {"EGFR": "EGFR", "HER2": "ERBB2", "CD20": "MS4A1"}
    for tgt, gene in target_gene.items():
        if gene in gene_panel:
            gidx = gene_panel.index(gene)
            potency = np.random.exponential(0.8, n_molecules)
            log2fc[:, :, gidx] -= potency[:, None]  # downregulation

    # Off-target innate immune activation (subset of molecules)
    isg_indices = [gene_panel.index(g) for g in ["IFIT1", "OAS1", "ISG15", "MX1"]]
    isg_trigger = np.random.beta(2, 5, n_molecules)  # most low, a few high
    for gidx in isg_indices:
        log2fc[:, :, gidx] += 2 * isg_trigger[:, None]

    # Housekeeping genes stay near zero
    for gene in ["GAPDH", "ACTB"]:
        gidx = gene_panel.index(gene)
        log2fc[:, :, gidx] = np.random.normal(0, 0.1, (n_molecules, len(cell_lines)))

    ds_stage5 = xr.Dataset(
        data_vars={
            "log2_fold_change": (["molecule", "cell_line", "gene"], log2fc),
        },
        coords={
            "molecule": molecule_ids,
            "cell_line": cell_lines,
            "gene": gene_panel,
        },
        attrs={
            "stage": "5_genomics",
            "assay": "Perturbation RNA-seq (log2FC vs DMSO control)",
        },
    )
    print(f"Perturbation panel: {len(gene_panel)} genes x {n_molecules} molecules x {len(cell_lines)} cell lines")
    print(f"log2FC range: [{log2fc.min():.2f}, {log2fc.max():.2f}]")
    return ds_stage5, gene_panel


@app.cell(hide_code=True)
def stage5_plot(
    cell_lines,
    ds_stage2_fitted,
    ds_stage3_fitted,
    ds_stage5,
    gene_panel,
    go,
    make_subplots,
    molecule_ids,
    np,
):
    s5_gene_cats = {
        "Drug targets": ["EGFR", "ERBB2", "MS4A1"],
        "Interferon-stimulated": ["IFIT1", "OAS1", "ISG15", "MX1"],
        "Apoptosis": ["BAX", "BCL2", "CASP3"],
        "ER stress": ["ATF4", "XBP1", "HSPA5"],
        "Trafficking": ["CLTC", "CAV1", "LDLR"],
        "Inflammatory": ["IL6", "TNF"],
        "Housekeeping": ["GAPDH", "ACTB"],
    }

    s5_cat_colors = {
        "Drug targets": "#ef4444",
        "Interferon-stimulated": "#f59e0b",
        "Apoptosis": "#8b5cf6",
        "ER stress": "#ec4899",
        "Trafficking": "#14b8a6",
        "Inflammatory": "#6366f1",
        "Housekeeping": "#6b7280",
    }

    s5_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "A. Mean log2FC Heatmap (gene x cell line)",
            "B. log2FC Distribution by Gene Category",
            "C. Binding Potency vs Target Knockdown",
            "D. Uptake vs Innate Immune Activation",
        ],
        vertical_spacing=0.14,
        horizontal_spacing=0.14,
        specs=[
            [{"type": "heatmap"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}],
        ],
    )

    # --- A: Heatmap of mean log2FC (gene x cell_line, averaged across molecules) ---
    s5_heatmap_vals = ds_stage5.log2_fold_change.mean(dim="molecule").values.T  # (gene, cell_line)
    s5_fig.add_trace(go.Heatmap(
        z=s5_heatmap_vals,
        x=cell_lines,
        y=gene_panel,
        colorscale="RdBu_r",
        zmid=0,
        colorbar=dict(title="log2FC", x=1.02, len=0.42, y=0.79),
        hovertemplate="Gene: %{y}<br>Cell Line: %{x}<br>log2FC: %{z:.2f}<extra></extra>",
    ), row=1, col=1)

    # --- B: ECDF of log2FC by gene category ---
    for s5_cat_name, s5_cat_genes in s5_gene_cats.items():
        s5_cat_vals = np.sort(
            ds_stage5.log2_fold_change.sel(gene=s5_cat_genes).values.ravel()
        )
        s5_cat_cumprob = np.arange(1, len(s5_cat_vals) + 1) / len(s5_cat_vals)
        s5_fig.add_trace(go.Scatter(
            x=s5_cat_vals, y=s5_cat_cumprob,
            mode="lines+markers",
            line=dict(color=s5_cat_colors[s5_cat_name], width=2),
            marker=dict(size=3),
            name=s5_cat_name,
        ), row=1, col=2)

    # --- C: Scatter binding EC50 vs target gene knockdown (cross-assay: Stage 2 -> 5) ---
    s5_target_map = {"EGFR": "EGFR", "HER2": "ERBB2", "CD20": "MS4A1"}
    s5_tgt_colors = {"EGFR": "#3b82f6", "HER2": "#8b5cf6", "CD20": "#10b981"}
    for s5_target, s5_gene_sym in s5_target_map.items():
        s5_binding_vals = ds_stage2_fitted.ec50_nm.sel(target=s5_target).values
        s5_knockdown_vals = ds_stage5.log2_fold_change.sel(
            gene=s5_gene_sym
        ).mean(dim="cell_line").values
        s5_fig.add_trace(go.Scatter(
            x=s5_binding_vals, y=s5_knockdown_vals,
            mode="markers",
            marker=dict(color=s5_tgt_colors[s5_target], size=6, opacity=0.7),
            name=s5_target,
            showlegend=True,
            text=molecule_ids,
            hovertemplate=(
                "<b>%{text}</b><br>"
                + s5_target
                + " EC50: %{x:.1f} nM<br>"
                + s5_gene_sym
                + " log2FC: %{y:.2f}<extra></extra>"
            ),
        ), row=2, col=1)

    # --- D: Scatter uptake vs ISG activation (cross-assay: Stage 3 -> 5) ---
    s5_isg_gene_list = ["IFIT1", "OAS1", "ISG15", "MX1"]
    s5_isg_mean = ds_stage5.log2_fold_change.sel(
        gene=s5_isg_gene_list
    ).mean(dim=["gene", "cell_line"]).values
    s5_uptake_mean = ds_stage3_fitted.uptake_pct_positive.mean(dim="cell_line").values
    s5_fig.add_trace(go.Scatter(
        x=s5_uptake_mean, y=s5_isg_mean,
        mode="markers",
        marker=dict(color="#f59e0b", size=7, opacity=0.7),
        name="ISG activation",
        showlegend=False,
        text=molecule_ids,
        hovertemplate="<b>%{text}</b><br>Uptake: %{x:.1f}%<br>ISG log2FC: %{y:.2f}<extra></extra>",
    ), row=2, col=2)

    # Axis labels
    s5_fig.update_yaxes(title_text="Gene", row=1, col=1, autorange="reversed")
    s5_fig.update_xaxes(title_text="log2FC", row=1, col=2)
    s5_fig.update_yaxes(title_text="ECDF", row=1, col=2)
    s5_fig.update_xaxes(title_text="Binding EC50 (nM)", type="log", row=2, col=1)
    s5_fig.update_yaxes(title_text="Target gene log2FC", row=2, col=1)
    s5_fig.update_xaxes(title_text="Mean Uptake % Positive", row=2, col=2)
    s5_fig.update_yaxes(title_text="Mean ISG log2FC", row=2, col=2)

    s5_fig.update_layout(
        title=dict(text="Stage 5: Perturbation Transcriptomics", font=dict(size=16)),
        height=800,
        width=1150,
        legend=dict(yanchor="bottom", y=0.02, xanchor="right", x=0.98, title=""),
    )

    s5_fig
    return


@app.cell(hide_code=True)
def stage6_header(mo):
    mo.md("""
    ## Stage 6: Molecular Features + Train/Test Splits

    Computed molecular descriptors (MW, LogP, HBD, HBA, TPSA, charge) as
    a feature matrix aligned by `molecule`. Plus boolean train/test masks
    for ML-ready splitting.
    """)
    return


@app.cell
def stage6_features(
    ds_stage1,
    ds_stage2_fitted,
    ds_stage3_fitted,
    ds_stage4,
    molecule_ids,
    n_molecules,
    np,
    xr,
):
    # Molecular descriptors derived from upstream assay data as informative priors.
    # Each feature is grounded in measured physicochemical or biological properties
    # from Stages 1-4, ensuring they carry real signal for downstream ML.

    # --- Pull upstream signals (posterior means where available) ---
    upstream_mass = ds_stage1.observed_mass_da.values
    zeta_mean = ds_stage1.zeta_potential_mv.mean(dim=["batch", "replicate"]).values
    purity_mean = ds_stage1.hplc_purity_percent.mean(dim="batch").values

    # Binding potency (posterior mean EC50, most potent target per molecule)
    best_ec50 = ds_stage2_fitted.ec50_nm.min(dim="target").values

    # Uptake efficiency (posterior mean, averaged across cell lines)
    uptake_mean = ds_stage3_fitted.uptake_pct_positive.mean(dim="cell_line").values

    # Functional efficacy (Stage 4, mean across cell lines)
    efficacy_mean = ds_stage4.efficacy_percent.mean(dim="cell_line").values

    # --- Derive informative molecular descriptors ---

    # MW: anchored to observed mass spec (payload + lipid envelope contribution)
    mw_da = upstream_mass * 1.15 + np.random.normal(2000, 400, n_molecules)

    # Charge: correlated with zeta potential (more negative zeta -> more negative charge)
    charge = np.clip(
        np.round(zeta_mean / 4 + np.random.normal(0, 0.5, n_molecules)),
        -2, 2,
    ).astype(int)

    # LogP: key predictor of uptake. Map uptake efficiency to lipophilicity score.
    uptake_norm = (uptake_mean - uptake_mean.min()) / (uptake_mean.max() - uptake_mean.min() + 1e-10)
    logp = 0.5 + 3.5 * uptake_norm + np.random.normal(0, 0.4, n_molecules)

    # HBD (H-bond donors): anti-correlated with LogP (more donors -> more hydrophilic)
    hbd = np.clip(np.round(4 - logp + np.random.normal(0, 1, n_molecules)), 0, 7).astype(int)

    # HBA (H-bond acceptors): scales with formulation complexity (proxy: MW)
    hba = np.clip(
        np.round((mw_da - 12000) / 900 + np.random.normal(0, 1, n_molecules)),
        2, 14,
    ).astype(int)

    # TPSA: derived from HBD and HBA (HBD ~20 Angstrom^2, HBA ~12 Angstrom^2 each)
    tpsa = hbd * 20.0 + hba * 12.0 + np.random.normal(0, 15, n_molecules)

    feature_names = ["mw_da", "logp", "hbd", "hba", "tpsa", "charge"]
    feature_matrix = np.column_stack([mw_da, logp, hbd, hba, tpsa, charge])

    # Verify features carry signal
    print(f"Feature correlations with upstream data:")
    print(f"  LogP   <-> uptake:  {np.corrcoef(logp, uptake_mean)[0, 1]:+.2f}")
    print(f"  charge <-> zeta:    {np.corrcoef(charge, zeta_mean)[0, 1]:+.2f}")
    print(f"  MW     <-> mass:    {np.corrcoef(mw_da, upstream_mass)[0, 1]:+.2f}")

    # Train/test split masks
    split_types = ["random_80_20", "scaffold_split", "temporal_split"]
    train_masks = np.zeros((n_molecules, len(split_types)), dtype=bool)
    test_masks = np.zeros((n_molecules, len(split_types)), dtype=bool)
    for s in range(len(split_types)):
        indices = np.random.permutation(n_molecules)
        n_train = int(0.8 * n_molecules)
        train_masks[indices[:n_train], s] = True
        test_masks[indices[n_train:], s] = True

    ds_stage6 = xr.Dataset(
        data_vars={
            "features": (["molecule", "feature"], feature_matrix),
            "train_mask": (["molecule", "split_type"], train_masks),
            "test_mask": (["molecule", "split_type"], test_masks),
        },
        coords={
            "molecule": molecule_ids,
            "feature": feature_names,
            "split_type": split_types,
        },
        attrs={"stage": "6_features_splits"},
    )
    print(f"\nFeature matrix: {feature_matrix.shape}")
    print(f"Splits: {split_types}")
    return (ds_stage6,)


@app.cell(hide_code=True)
def stage6_split_boxplot(ds_stage6, go, make_subplots):
    # Boxplots: verify train/test splits produce balanced feature distributions
    feat_names = list(ds_stage6.feature.values)
    split_names = list(ds_stage6.split_type.values)

    split_box = make_subplots(
        rows=2, cols=3,
        subplot_titles=[f.upper() for f in feat_names],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    for f_idx, feat in enumerate(feat_names):
        subplot_row = f_idx // 3 + 1
        subplot_col = f_idx % 3 + 1
        feat_vals = ds_stage6.features.sel(feature=feat).values

        for s_idx, sname in enumerate(split_names):
            train_m = ds_stage6.train_mask.sel(split_type=sname).values
            test_m = ds_stage6.test_mask.sel(split_type=sname).values
            box_n_train = int(train_m.sum())
            box_n_test = int(test_m.sum())

            split_box.add_trace(go.Box(
                y=feat_vals[train_m],
                x=[s_idx - 0.2] * box_n_train,
                name="Train",
                marker_color="#3b82f6",
                width=0.3,
                legendgroup="Train",
                showlegend=(f_idx == 0 and s_idx == 0),
            ), row=subplot_row, col=subplot_col)
            split_box.add_trace(go.Box(
                y=feat_vals[test_m],
                x=[s_idx + 0.2] * box_n_test,
                name="Test",
                marker_color="#ef4444",
                width=0.3,
                legendgroup="Test",
                showlegend=(f_idx == 0 and s_idx == 0),
            ), row=subplot_row, col=subplot_col)

        split_box.update_xaxes(
            tickvals=list(range(len(split_names))),
            ticktext=[s.replace("_", " ") for s in split_names],
            title_text="Split type",
            tickangle=0,
            row=subplot_row, col=subplot_col,
        )
        split_box.update_yaxes(title_text="Value", row=subplot_row, col=subplot_col)

    split_box.update_layout(
        title=dict(text="Train (blue) vs Test (red) Feature Distributions by Split Type", font=dict(size=15)),
        height=700, width=1100,
        boxmode="group",
    )

    split_box
    return


@app.cell(hide_code=True)
def unify_header(mo):
    mo.md("""
    ## The Campaign DataTree

    Instead of flattening six assays into one Dataset, we use xarray's
    `DataTree` to organize each assay domain as a node in a hierarchy.
    Every node shares the `molecule` coordinate; non-overlapping dimensions
    (`time_min`, `draw`, `gene`) live independently in their own nodes.
    """)
    return


@app.cell
def unify_all(
    ds_stage1,
    ds_stage2_fitted,
    ds_stage3_fitted,
    ds_stage4,
    ds_stage5,
    ds_stage6,
    mo,
    xr,
):
    campaign = xr.DataTree.from_dict({
        "/analytical": ds_stage1,
        "/binding": ds_stage2_fitted,
        "/cell_assays": ds_stage3_fitted,
        "/functional": ds_stage4,
        "/genomics": ds_stage5,
        "/features": ds_stage6,
    })
    campaign.attrs = {
        "title": "Multi-Assay Molecule Characterization Campaign",
        "description": "Six assay domains as a DataTree, linked by the molecule coordinate",
    }
    mo.md(f"""
    **Campaign DataTree** - 6 assay nodes, all aligned by `molecule`.

    ```
    {campaign}
    ```
    """)
    return (campaign,)


@app.cell(hide_code=True)
def verify_unified(campaign, mo):
    # Verify each node has the expected variables
    tree_check = {
        "/analytical": {"dls_diameter_nm", "zeta_potential_mv", "hplc_purity_percent", "observed_mass_da"},
        "/binding": {"od450", "ec50_nm", "ec50_nm_std", "hill_coefficient", "ec50_nm_posterior"},
        "/cell_assays": {"uptake_median_mfi", "uptake_pct_positive", "uptake_pct_positive_posterior"},
        "/functional": {"functional_ec50_um", "efficacy_percent"},
        "/genomics": {"log2_fold_change"},
        "/features": {"features", "train_mask", "test_mask"},
    }
    for tree_path, tree_vars in tree_check.items():
        tree_found = set(campaign[tree_path].ds.data_vars)
        assert tree_vars.issubset(tree_found), f"Missing in {tree_path}: {tree_vars - tree_found}"

    assert campaign["/analytical"].ds.sizes["molecule"] == 40
    assert "gene" in campaign["/genomics"].ds.dims

    n_binding_draws = campaign["/binding"].ds.sizes["draw"]
    n_cell_draws = campaign["/cell_assays"].ds.sizes["draw"]

    mo.callout(
        mo.md(f"**DataTree verified:** {len(tree_check)} nodes, all variables present. "
              f"Binding posteriors (draw={n_binding_draws}) and cell assay posteriors (draw={n_cell_draws}) "
              f"live in separate nodes -- no dimension conflicts."),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def selection_header(mo):
    mo.md("""
    ## Linked Selection: everything stays aligned

    The power of a coordinate-aligned DataTree: selecting on one dimension
    propagates to ALL nodes. No manual index-matching across assays.
    """)
    return


@app.cell
def demo_selection(campaign, mo, np):
    # Select a single molecule across all nodes in the tree
    single = campaign.sel(molecule="LNP_007")

    dls_vals = single["/analytical"].ds.dls_diameter_nm.values.ravel()

    ec50_egfr_post = single["/binding"].ds.ec50_nm_posterior.sel(target="EGFR").values
    ec50_median = np.median(ec50_egfr_post)
    ec50_ci = np.percentile(ec50_egfr_post, [3, 97])

    uptake_hepg2_post = single["/cell_assays"].ds.uptake_pct_positive_posterior.sel(cell_line="HEPG2").values
    uptake_median = np.median(uptake_hepg2_post)
    uptake_ci = np.percentile(uptake_hepg2_post, [3, 97])

    func_ec50 = single["/functional"].ds.functional_ec50_um.sel(cell_line="HEPG2").values
    purity_vals = single["/analytical"].ds.hplc_purity_percent.values

    mo.md(
        f"""
        **`campaign.sel(molecule="LNP_007")`** slices every node in the tree:

        - DLS diameter (all batches/replicates/time): **{np.median(dls_vals):.1f} nm** [IQR: {np.percentile(dls_vals, 25):.1f}-{np.percentile(dls_vals, 75):.1f}]
        - EC50 vs EGFR (posterior, {len(ec50_egfr_post)} draws from `/binding`): **{ec50_median:.1f} nM** [94% CI: {ec50_ci[0]:.1f}-{ec50_ci[1]:.1f}]
        - Uptake in HEPG2 (posterior, {len(uptake_hepg2_post)} draws from `/cell_assays`): **{uptake_median:.1f}%** [94% CI: {uptake_ci[0]:.1f}-{uptake_ci[1]:.1f}%]
        - Functional EC50 in HEPG2 (`/functional`): **{func_ec50:.2f} uM**
        - HPLC purity (all batches, `/analytical`): **{np.mean(purity_vals):.1f}%**
        """
    )
    return


@app.cell
def demo_cross_assay_query(campaign, mo):
    # Cross-assay query: pull criteria from different tree nodes
    query_dls = campaign["/analytical"].ds.dls_diameter_nm.mean(dim=["batch", "replicate", "time_min"])
    query_ec50 = campaign["/binding"].ds.ec50_nm.sel(target="EGFR").drop_vars("target")
    query_uptake = campaign["/cell_assays"].ds.uptake_pct_positive.sel(cell_line="HEPG2").drop_vars("cell_line")
    query_eff = campaign["/functional"].ds.efficacy_percent.sel(cell_line="HEPG2").drop_vars("cell_line")

    query_criteria = (query_dls < 91) & (query_ec50 < 8) & (query_uptake > 40) & (query_eff > 50)
    query_hit_ids = list(query_dls.molecule.values[query_criteria.values])
    query_n_hits = len(query_hit_ids)

    mo.callout(
        mo.md(f"""
        **Cross-assay query result:** {query_n_hits} molecules meet ALL criteria:
        - DLS diameter < 91 nm (`/analytical`)
        - EGFR EC50 < 8 nM (`/binding`)
        - HEPG2 uptake > 40% (`/cell_assays`)
        - HEPG2 efficacy > 50% (`/functional`)

        Molecules: {", ".join(query_hit_ids[:5])}{"..." if query_n_hits > 5 else ""}
        """),
        kind="info",
    )
    return


@app.cell
def demo_train_test_split(campaign, mo):
    # Train/test split: extract molecule IDs from masks, then select on the tree
    dt_train_mask = campaign["/features"].ds.train_mask.sel(split_type="random_80_20")
    dt_test_mask = campaign["/features"].ds.test_mask.sel(split_type="random_80_20")

    dt_train_mols = list(dt_train_mask.molecule.values[dt_train_mask.values])
    dt_test_mols = list(dt_test_mask.molecule.values[dt_test_mask.values])

    campaign_train = campaign.sel(molecule=dt_train_mols)
    campaign_test = campaign.sel(molecule=dt_test_mols)

    mo.md(
        f"""
        **Train/test split via DataTree coordinate selection:**

        - Train: **{len(dt_train_mols)}** molecules -- all assay nodes sliced in one `.sel()` call
        - Test: **{len(dt_test_mols)}** molecules -- same propagation across the entire tree

        No manual index tracking. `campaign.sel(molecule=...)` propagates to every node.
        """
    )
    return


@app.cell(hide_code=True)
def display_tree(campaign):
    campaign
    return


@app.cell(hide_code=True)
def save_header(mo):
    mo.md("""
    ## Cloud-native storage: Zarr
    """)
    return


@app.cell(hide_code=True)
def save_zarr(campaign):
    import tempfile
    from pathlib import Path
    import os

    dt_zarr_path = Path(tempfile.mkdtemp()) / "campaign.zarr"
    campaign.to_zarr(str(dt_zarr_path), mode="w")

    dt_size_mb = sum(f.stat().st_size / 1e6 for f in dt_zarr_path.rglob("*") if f.is_file())
    print(f"Saved to: {dt_zarr_path}")
    print(f"Size: {dt_size_mb:.2f} MB")
    top_groups = [d.name for d in dt_zarr_path.iterdir() if d.is_dir()]
    print(f"Top-level groups: {top_groups}")
    return


@app.cell(hide_code=True)
def close(mo):
    mo.md("""
    ---

    ## Key takeaways

    1. **Coordinates are the linkage.** Every variable shares the `molecule` coordinate.
       Selection propagates to all linked data automatically.

    2. **Progressive accumulation.** Start with raw data (Stage 1), add derived
       estimates (Stage 2), features (Stage 6), and splits -- all reusing the same
       coordinate system.

    3. **Cross-assay queries are one-liners.** Multi-criteria filtering across DLS,
       ELISA, flow cytometry, and HPLC is a single `.where()` call.

    4. **Cloud-ready.** One `.to_zarr()` call preserves all coordinates, metadata,
       and linkage for cloud storage.

    ### Next steps
    - [Notebook 2](02_periodic_and_transform_indexes.py): Custom indexes for angular/physical coordinates
    - [Notebook 3](03_ndindex_time_locking.py): N-D derived coordinates and time-locking
    - [Notebook 4](04_linked_intervals_cross_slicing.py): Linked interval cross-slicing
    - [Notebook 5](05_cross_experiment_datatree.py): DataTree for heterogeneous assays

    *Built with xarray, marimo, and synthetic data. AI tools were used in creation.*
    """)
    return


if __name__ == "__main__":
    app.run()
