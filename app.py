# File: app.py
from __future__ import annotations
import re
import streamlit as st
import importlib
from app_helpers.style import inject_style, HELP_TEXT
from app_helpers.labels import MACHINE_LABELS, GROUP_LABELS, NODE_LABELS
from app_helpers.ui_helpers import (
    schema,
    general_core,
    general_transport,
    machine_core,
    machine_transport,
    prefix_to_machines,
    prefix_by_label,
    render_number_input,
)
from app_helpers.simulation import run_with_progress, run_sim_cached, dict_hash
from plant_sim.run_sim import run_sim
import plant_sim.config as cfg
import pandas as pd

def labelize_move(df):
    """
    Replace technical codes in movement log with friendly labels.
    Works whether your columns are named src/dest or from/to, 
    and whether the machine column is 'machine' or 'mc'.
    """
    if "src" in df.columns:
        df["src"] = df["src"].map(NODE_LABELS).fillna(df["src"])
    if "dest" in df.columns:
        df["dest"] = df["dest"].map(NODE_LABELS).fillna(df["dest"])

    if "from" in df.columns:      # just in case your columns are named this way
        df["from"] = df["from"].map(NODE_LABELS).fillna(df["from"])
    if "to" in df.columns:
        df["to"] = df["to"].map(NODE_LABELS).fillna(df["to"])

    # machine column (name may vary)
    for mcol in ("machine", "mc"):
        if mcol in df.columns:
            df[mcol] = df[mcol].map(MACHINE_LABELS).fillna(df[mcol])

    return df

def relabel_transport(df_move: pd.DataFrame) -> pd.DataFrame:
    if df_move is None or df_move.empty:
        return df_move
    df = df_move.copy()

    # normalize column names
    rename_map = {}
    for c in df.columns:
        c2 = c.strip()
        if c2.lower() == "from": rename_map[c] = "From"
        if c2.lower() == "to":   rename_map[c] = "To"
        if c2 == "src":          rename_map[c] = "From"
        if c2 == "dest":         rename_map[c] = "To"
    if rename_map:
        df = df.rename(columns=rename_map)

    def map_loc(v):
        if pd.isna(v):
            return v
        s = str(v).strip()
        # Try node labels first, then machine labels, else leave as is
        return NODE_LABELS.get(s, MACHINE_LABELS.get(s, s))

    for col in ("From", "To"):
        if col in df.columns:
            df[col] = df[col].apply(map_loc)

    return df

# ── 0) Keep simulation outputs across reruns ───────────
st.session_state.setdefault("sim_results", None)
st.session_state.setdefault("overrides", {})

# ── Inject styling and help text ─────────────────────
inject_style()
st.markdown(HELP_TEXT, unsafe_allow_html=True)

# ── 1️⃣ Plant-Simulation Configuration card ───────────
with st.container():
    st.markdown("<h3 class='cfg-card-title'>Plant Simulation Configuration</h3>", unsafe_allow_html=True)
    for key in ["SIM_TIME", "INTERARRIVAL", "Forklift_Capacity"]:
        if key in general_core:
            render_number_input(key, general_core[key])
        else:
            st.warning(f"{key} not found in YAML schema")

# ── 2️⃣ Machine Parameters panel ──────────────────────
MP_HELP = """
<div class="white-box">
  <div class="app-heading">Machine Parameters</div>
  <ul>
    <li><strong>Machine Group</strong>: Select the operation of interest.</li>
    <li><strong>Machine</strong>: Choose a specific machine instance.</li>
    <li><strong>Availability</strong>: The OEE of the selected machine.</li>
    <li><strong>Cycle Time</strong>: Custom cycle time if OEE > 0.</li>
    <li><strong>Weigh and Classify Reject Interval</strong>: For overweight shells identified at Weighing and Classification.</li>
    <li><strong>Tensile Test Fail Interval</strong>: For batches that fail the Tensile Test. Note these failed batches go into a scrap buffer.</li>
  </ul>
</div>
"""
st.markdown(MP_HELP, unsafe_allow_html=True)

st.markdown("<div class='app-heading'>Machine Parameters</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    disp = st.selectbox("Machine Group", list(prefix_by_label.keys()))
    grp = prefix_by_label[disp]
with col2:
    machines = prefix_to_machines[grp]
    if grp == "TT":
        machines = [m for m in machines if re.search(r"\d+$", m)]
    mach = st.selectbox(
        "Machine",
        machines,
        format_func=lambda c: MACHINE_LABELS.get(c, c)
    )

core = machine_core.get(mach, {})
trans = machine_transport.get(mach, {})

with st.form(key=f"form_{mach}"):
    if "OEE" not in core:
        st.error(f"No OEE field in schema for {mach}")
        oee = None
    else:
        oee = render_number_input(core["OEE"]["key"], core["OEE"]["meta"])
    if oee and oee > 0:
        for fname, info in core.items():
            if fname == "OEE":
                continue
            render_number_input(info["key"], info["meta"])
        if grp == "TT" and "TT_FAIL_INTERVAL" in general_core:
            render_number_input("TT_FAIL_INTERVAL", general_core["TT_FAIL_INTERVAL"])
    submitted = st.form_submit_button("Apply changes")
    if submitted:
        # sync overrides for core
        for info in core.values():
            k = info["key"]
            if k in st.session_state:
                st.session_state["overrides"][k] = st.session_state[k]
            else:
                st.session_state["overrides"].pop(k, None)
        # sync global TT interval
        if grp == "TT":
            k = "TT_FAIL_INTERVAL"
            if k in st.session_state:
                st.session_state["overrides"][k] = st.session_state[k]
            else:
                st.session_state["overrides"].pop(k, None)
        # sync transport fields
        for info in trans.values():
            k = info["key"]
            if k in st.session_state:
                st.session_state["overrides"][k] = st.session_state[k]
            else:
                st.session_state["overrides"].pop(k, None)

# ── 3️⃣ Sidebar – transport times ─────────────────────
with st.sidebar:
    if st.checkbox("Edit transport-time parameters", value=False):
        st.subheader("Transport Times")
        if general_transport:
            st.markdown("**General**")
            for key, meta in general_transport.items():
                render_number_input(key, meta)
        if trans:
            st.markdown(f"**{mach}**")
            for info in trans.values():
                render_number_input(info["key"], info["meta"])
                


# # ── Run button & result display ─────────────────────
# run_clicked = st.button("🚀  Run simulation", type="primary")
# if run_clicked:
#     # 1) Grab overrides
#     overrides = st.session_state.get("overrides", {})

#     # 2) (Optional) persist to user schema
#     # save_overrides_to_user_schema(overrides)

#     # 3) Patch config
#     importlib.reload(cfg)
#     for k, v in overrides.items():
#         setattr(cfg, k, v)

#     # 4) Define a small runner that accepts our progress callback
#     def _run_live(progress_callback=None):
#         return run_sim(overrides, progress_callback=progress_callback)

#     # 5) Run with spinner and custom progress bar
#     with st.spinner("Running simulation..."):
#         sim_out = run_with_progress(_run_live)

#     # 6) Unpack and save results
#     df_units, df_wip, df_move, df_final_wip, df_util, *fgs = sim_out
#     st.session_state["sim_results"] = {
#         "df_units": df_units,
#         "df_wip": df_wip,
#         "df_move": df_move,
#         "df_final_wip": df_final_wip,
#         "df_util": df_util,
#         "fg6_count": len(fgs[-1]),
#     }

# ── Machine Status Overview ─────────────────────────────
with st.expander("🔍 Machine Status Overview", expanded=False):
    status_rows = []
    for mc, fields in machine_core.items():
        if "OEE" not in fields:
            continue
        key = fields["OEE"]["key"]
        oee_val = st.session_state.get("overrides", {}).get(
            key,
            schema[key]["default"]
        )
        status = "🟢 Running" if oee_val and oee_val > 0 else "🔴 Offline"
        status_rows.append({
            "Code": mc,
            "Name": MACHINE_LABELS.get(mc, mc),
            "OEE": f"{oee_val:.2f}",
            "Status": status
        })

    df_status = pd.DataFrame(status_rows)

    # Build a master order list by flattening your prefix_to_machines
    all_order = []
    for prefix in GROUP_LABELS.keys():
        all_order += prefix_to_machines.get(prefix, [])

    # Map each code to its position in that sequence
    order_map = {mc: i for i, mc in enumerate(all_order)}
    df_status["order"] = df_status["Code"].map(order_map)

    # Sort by that sequence index
    df_status = df_status.sort_values("order").drop(columns="order")
    
    st.table(df_status.drop(columns="Code"))

#     st.table(df_status)


run_clicked = st.button("🚀  Run simulation", type="primary")
if run_clicked:
    # 1) Pull in the machine overrides you’ve accumulated:
    overrides = st.session_state.get("overrides", {}).copy()

    # 2) ALSO include your top‐level settings so they actually get passed in:
    for g in ["SIM_TIME", "INTERARRIVAL", "Forklift_Capacity"]:
        if g in st.session_state:
            overrides[g] = st.session_state[g]

    # 3) Persist back in case you need them later
    st.session_state["overrides"] = overrides

    # 4) Patch the config module
    importlib.reload(cfg)
    for k, v in overrides.items():
        setattr(cfg, k, v)

    # 5) If you’re using the cached SimPy runner:
    def _run_live(progress_callback=None):
        return run_sim(overrides, progress_callback=progress_callback)
    
    sim_out = run_with_progress(_run_live)

#     # 6) Fire off the sim with your progress bar
#     with st.spinner("Running simulation..."):
#         sim_out = run_with_progress(_run_live)


    # 7) Unpack & store results as before
    df_units, _, df_move, df_final_wip, df_util, *fgs = sim_out
    
    df_util["machine"] = df_util["machine"].map(MACHINE_LABELS).fillna(df_util["machine"])
    
    # Friendly node names in Final WIP
    df_final_wip["Node"] = df_final_wip["Node"].map(NODE_LABELS).fillna(df_final_wip["Node"])

    df_move = relabel_transport(df_move)
    
    st.session_state["sim_results"] = {
        "df_units": df_units,
#         "df_wip": df_wip,
        "df_move": df_move,
        "df_final_wip": df_final_wip,
        "df_util": df_util,
        "fg6_count": len(fgs[-1]),
    }

# Show any captured logs in-app
if st.session_state.get("sim_logs"):
    st.subheader("Simulation Log")
    st.text_area("", st.session_state["sim_logs"], height=200)
    
    

    

# ── Show results ─────────────────────────────────────
results = st.session_state.get("sim_results")
if results:
    st.metric("Units in Dispatch:", results["fg6_count"])
    df_map = {
        "Machine utilisation": results["df_util"],
        "Unit-level summary": results["df_units"],
#         "Complete WIP history": results["df_wip"],
        "Transport log": results["df_move"],
        "Final WIP count": results["df_final_wip"],
    }
    sel = st.multiselect("Data Frames:", list(df_map.keys()))
    for name in sel:
        df = df_map[name]
        st.markdown(f"### {name}")
        st.dataframe(df, use_container_width=True)
        st.download_button(
            f"Download {name} CSV",
            df.to_csv(index=False).encode(),
            file_name=f"{name.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"dl_{name}"
        )
else:
    st.info("Run the simulation to see results.")


