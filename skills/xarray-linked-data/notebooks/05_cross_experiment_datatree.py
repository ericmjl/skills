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
            Cross-Experiment Linking with DataTree
        </h1>
        <p style="color: #a0a8e8; font-size: 1.1rem; margin: 0; max-width: 640px; line-height: 1.6;">
            Heterogeneous assays with incompatible grids organized in one
            DataTree. Shared coordinates inherited across nodes. Cross-assay
            queries that span the entire experimental hierarchy.
        </p>
    </div>
    """)
    return


@app.cell(hide_code=True)
def cell_tour(mo):
    import wigglystuff

    tour = wigglystuff.CellTour(
        steps=[
            {"cell_name": "hero", "title": "Cross-Experiment Linking", "description": "DataTree for heterogeneous assays with incompatible grids."},
            {"cell_name": "build_root", "title": "Root Node", "description": "Molecule registry with shared identifiers inherited by all children."},
            {"cell_name": "build_analytical", "title": "Analytical Chemistry", "description": "DLS timeseries and HPLC chromatograms on different grids."},
            {"cell_name": "build_bioassays", "title": "Bioassays", "description": "ELISA dose-response and flow cytometry with yet another set of dimensions."},
            {"cell_name": "build_tree", "title": "DataTree Assembly", "description": "One DataTree.from_dict call links all nodes with inherited coordinates."},
            {"cell_name": "verify_tree", "title": "Inheritance Verified", "description": "molecule coordinate shared across all nodes without duplication."},
            {"cell_name": "cross_assay_query", "title": "Cross-Assay Query", "description": "Find promising molecules then pull data from every assay node."},
        ],
        auto_start=False,
        show_progress=True,
    )
    mo.ui.anywidget(tour)


@app.cell(hide_code=True)
def imports():
    import marimo as mo
    import numpy as np
    import xarray as xr

    return mo, np, xr


@app.cell(hide_code=True)
def intro(mo):
    mo.md(r"""
    ## When a single Dataset is not enough

    Notebook 1 merged six assay domains into one Dataset. But some assays
    produce data on **incompatible grids** -- different resolutions,
    different dimensions, different coordinate systems.

    `xr.DataTree` solves this: each assay is a tree node with its own
    dimensions, while shared coordinates (like `molecule_id`) are inherited
    from the root. One object, heterogeneous data, unified access.
    """)
    return


@app.cell
def build_root(np, xr):
    # Root node: molecule registry with shared identifiers
    n_molecules = 30
    molecule_ids = [f"LNP_{m_id:03d}" for m_id in range(1, n_molecules + 1)]

    root_ds = xr.Dataset(
        data_vars={
            "smiles": (["molecule"], [f"C({'C' * m_id})O{'N' * (m_id % 3)}" for m_id in range(n_molecules)]),
            "molecular_weight_da": (["molecule"], np.random.normal(15000, 3000, n_molecules)),
        },
        coords={"molecule": molecule_ids},
        attrs={"description": "Root: molecule registry shared across all assay nodes"},
    )
    print(f"Root: {n_molecules} molecules registered")
    return molecule_ids, n_molecules, root_ds


@app.cell
def build_analytical(molecule_ids, n_molecules, np, xr):
    # Analytical chemistry node: DLS timeseries (high-res, incompatible with scalar assays)
    dls_time_s = np.linspace(0, 300, 150)  # 150 timepoints over 5 minutes
    dls_diameter = np.random.lognormal(4, 0.2, (n_molecules, len(dls_time_s)))

    analytical_ds = xr.Dataset(
        data_vars={
            "dls_diameter_nm": (["molecule", "time_s"], dls_diameter),
            "purity_percent": (["molecule"], np.random.normal(95, 3, n_molecules).clip(80, 100)),
        },
        coords={"molecule": molecule_ids, "time_s": dls_time_s},
        attrs={"assay_type": "analytical_chemistry"},
    )

    # HPLC chromatograms: different grid entirely (retention time, not real time)
    retention_min = np.linspace(0, 30, 500)
    hplc_signal = np.random.exponential(0.1, (n_molecules, len(retention_min)))

    hplc_ds = xr.Dataset(
        data_vars={"hplc_signal_au": (["molecule", "retention_min"], hplc_signal)},
        coords={"molecule": molecule_ids, "retention_min": retention_min},
        attrs={"assay_type": "HPLC chromatography"},
    )
    print(f"Analytical node: DLS ({dls_diameter.shape}), HPLC ({hplc_signal.shape})")
    return analytical_ds, hplc_ds


@app.cell
def build_bioassays(molecule_ids, n_molecules, np, xr):
    # Binding assay: dose-response grid (concentration x target x replicate)
    targets = ["EGFR", "HER2", "CD20"]
    concentrations = np.logspace(0, 4, 8)
    replicates = ["r1", "r2", "r3"]
    binding_data = np.random.lognormal(0, 0.3, (n_molecules, len(targets), len(concentrations), len(replicates)))

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

    # Flow cytometry: per-event data (very different grid)
    n_events = 2000
    cell_lines = ["HEPG2", "HEK293"]
    flow_data = np.random.lognormal(5, 0.8, (n_molecules, len(cell_lines), n_events))

    flow_ds = xr.Dataset(
        data_vars={
            "fluorescence_mfi": (["molecule", "cell_line", "event"], flow_data),
            "median_mfi": (["molecule", "cell_line"], np.median(flow_data, axis=2)),
        },
        coords={"molecule": molecule_ids, "cell_line": cell_lines, "event": np.arange(n_events)},
        attrs={"assay_type": "flow cytometry"},
    )
    print(f"Bioassay nodes: binding ({binding_data.shape}), flow ({flow_data.shape})")
    return binding_ds, flow_ds


@app.cell
def build_derived(molecule_ids, n_molecules, np, xr):
    # Derived estimates: scalar per molecule/target (Bayesian posterior summaries)
    # HDI bounds derived FROM the mean to guarantee hdi3 < hdi97 ordering
    derived_targets = ["EGFR", "HER2", "CD20"]
    derived_cell_lines = ["HEPG2", "HEK293"]

    ec50_mean = np.random.lognormal(2, 1, (n_molecules, len(derived_targets)))
    ec50_cv = 0.5  # coefficient of variation for HDI spread
    ec50_hdi3 = ec50_mean * np.exp(-1.88 * ec50_cv)   # ~3% lower bound
    ec50_hdi97 = ec50_mean * np.exp(1.88 * ec50_cv)   # ~97% upper bound

    derived_ds = xr.Dataset(
        data_vars={
            "ec50_nm_mean": (
                ["molecule", "target"],
                ec50_mean,
            ),
            "ec50_nm_hdi3": (
                ["molecule", "target"],
                ec50_hdi3,
            ),
            "ec50_nm_hdi97": (
                ["molecule", "target"],
                ec50_hdi97,
            ),
            "uptake_pct": (
                ["molecule", "cell_line"],
                np.random.normal(
                    50, 20, (n_molecules, len(derived_cell_lines))
                ).clip(0, 100),
            ),
        },
        coords={
            "molecule": molecule_ids,
            "target": derived_targets,
            "cell_line": derived_cell_lines,
        },
        attrs={
            "assay_type": "derived_estimates",
            "estimation": "Bayesian posterior summaries",
        },
    )
    print(f"Derived node: {len(derived_ds.data_vars)} estimate variables")
    return (derived_ds,)


@app.cell
def build_tree(
    analytical_ds,
    binding_ds,
    derived_ds,
    flow_ds,
    hplc_ds,
    mo,
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

    # List all nodes
    node_list = list(campaign_tree.groups)
    mo.md(
        f"""
        **DataTree built:** {len(node_list)} nodes

        ```
        {chr(10).join(node_list)}
        ```

        The `molecule` coordinate is defined at the root and **inherited**
        by every child node -- no duplication.
        """
    )
    return (campaign_tree,)


@app.cell
def verify_tree(campaign_tree, mo):
    # Verify: molecule coordinate is accessible in every child
    dls_node = campaign_tree["/characterization/dls"].ds
    binding_node = campaign_tree["/bioassays/binding"].ds
    derived_node = campaign_tree["/derived"].ds

    assert "molecule" in dls_node.coords
    assert "molecule" in binding_node.coords
    assert "molecule" in derived_node.coords

    # Verify: all nodes share the same molecule IDs (inherited)
    assert (dls_node.molecule.values == binding_node.molecule.values).all()
    assert (dls_node.molecule.values == derived_node.molecule.values).all()

    # Verify: each node has its OWN dimensions that don't conflict
    assert "time_s" in dls_node.dims
    assert "concentration_nm" in binding_node.dims
    assert "event" in campaign_tree["/bioassays/flow_cytometry"].ds.dims

    mo.callout(
        mo.md("""
        **DataTree verified:**
        - `molecule` coordinate inherited across all nodes
        - Each node has its own incompatible dimensions (time_s, concentration_nm, event)
        - All molecule IDs consistent across the tree
        """),
        kind="success",
    )
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


@app.cell
def cross_assay_query(campaign_tree, mo):
    # Query: find molecules with high EGFR potency AND good uptake
    derived = campaign_tree["/derived"].ds
    criteria = (
        derived.ec50_nm_mean.sel(target="EGFR").drop_vars("target") < 500
    ) & (derived.uptake_pct.sel(cell_line="HEPG2").drop_vars("cell_line") > 40)
    hits = derived.where(criteria, drop=True)
    hit_molecules = list(hits.molecule.values)

    # Pull analytical data for the same molecules
    dls_node = campaign_tree["/characterization/dls"].ds
    dls_hits = dls_node.sel(molecule=hit_molecules)

    # Pull binding data for the same molecules
    binding_node = campaign_tree["/bioassays/binding"].ds
    binding_hits = binding_node.sel(molecule=hit_molecules)

    mo.callout(
        mo.md(f"""
        **Cross-assay query result:**

        - Molecules meeting criteria: **{len(hit_molecules)}**
        - DLS data pulled for those molecules: **{dls_hits.sizes["molecule"]}** molecules x **{dls_hits.sizes["time_s"]}** timepoints
        - Binding data pulled: **{binding_hits.sizes["molecule"]}** molecules x **{binding_hits.sizes["concentration_nm"]}** concentrations

        One `.sel(molecule=hit_molecules)` call per node pulls linked data
        from incompatible grids without manual alignment.
        """),
        kind="info",
    )
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

    | Container | When to use | Key feature |
    |-----------|-------------|-------------|
    | `Dataset` | All variables share compatible dims | One flat coordinate registry |
    | `DataTree` | Variables on incompatible grids | Coordinate inheritance across nodes |

    DataTree enables **cross-experiment queries** across assays with
    fundamentally different shapes -- a 150-point DLS timeseries, a
    500-bin HPLC chromatogram, an 8-point dose-response curve, and a
    2000-event flow cytometry run, all in one object linked by `molecule_id`.

    ### The full xarray-linked-data toolkit

    1. **[Notebook 1](01_linked_data_design.py):** Progressive accumulation in one Dataset
    2. **[Notebook 2](02_periodic_and_transform_indexes.py):** PeriodicIndex + CoordinateTransform
    3. **[Notebook 3](03_ndindex_time_locking.py):** NDIndex for N-D derived coordinates
    4. **[Notebook 4](04_linked_intervals_cross_slicing.py):** DimensionInterval for cross-slicing
    5. **This notebook:** DataTree for heterogeneous multi-assay data

    *Built with xarray, marimo, and synthetic data. AI tools were used in creation.*
    """)
    return


if __name__ == "__main__":
    app.run()
