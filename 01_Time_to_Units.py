# pages/01_Time_to_Units.py
from __future__ import annotations
import re, importlib
import pandas as pd
import streamlit as st

# First Streamlit call on this page
st.set_page_config(page_title="Time → Units", layout="wide", initial_sidebar_state="collapsed")

# Hide multipage nav but keep the sidebar (for transport-time editing only)
st.markdown("""
<style>
  [data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ---- Mode switch header (tiles stay visible on top) ----
st.markdown("### Mode")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.page_link("pages/01_Time_to_Units.py", label="✅ ⏱️  Time → Units (current)", icon="⏱️")
with c2:
    st.page_link("pages/02_Units_to_Time.py", label="📦  Units → Time", icon="📦")
st.divider()
# --------------------------------------------------------

# ---- Bring in your original app pieces ----
from app_helpers.style import inject_style, HELP_TEXT
from app_helpers.labels import MACHINE_LABELS, GROUP_LABELS, NODE_LABELS
from app_helpers.ui_helpers import (
    schema, general_core, general_transport, machine_core, machine_transport,
    prefix_to_machines, prefix_by_label, render_number_input,
)
from app_helpers.simulation import run_with_progress
from plant_sim.run_sim import run_sim
import plant_sim.config as cfg

# Optional styles/help from your original app
inject_style()
st.markdown(HELP_TEXT, unsafe_allow_html=True)

# Helpers copied from your app.py (unchanged)
def labelize_move(df: pd.DataFrame) -> pd.DataFrame:
    if "src" in df.columns:  df["src"]  = df["src"].map(NODE_LABELS).fillna(df["src"])
    if "dest" in df.columns: df["dest"] = df["dest"].map(NODE_LABELS).fillna(df["dest"])
    if "from" in df.columns: df["from"] = df["from"].map(NODE_LABELS).fillna(df["from"])
    if "to" in df.columns:   df["to"]   = df["to"].map(NODE_LABELS).fillna(df["to"])
    for mcol in ("machine", "mc"):
        if mcol in df.columns:
            df[mcol] = df[mcol].map(MACHINE_LABELS).fillna(df[mcol])
    return df

def relabel_transport(df_move: pd.DataFrame) -> pd.DataFrame:
    if df_move is None or df_move.empty:
        return df_move
    df = df_move.copy()
    rename_map = {}
    for c in df.columns:
        c2 = c.strip()
        if c2.lower() == "from": rename_map[c] = "From"
        if c2.lower() == "to":   rename_map[c] = "To"
        if c2 == "src":          rename_map[c] = "From"
        if c2 == "dest":         rename_map[c] = "To"
    if rename_map: df = df.rename(columns=rename_map)
    def map_loc(v):
        if pd.isna(v): return v
        s = str(v).strip()
        return NODE_LABELS.get(s, MACHINE_LABELS.get(s, s))
    for col in ("From", "To"):
        if col in df.columns:
            df[col] = df[col].apply(map_loc)
    return df

# Session scaffolding
st.session_state.setdefault("sim_results", None)
st.session_state.setdefault("overrides", {})

# ---- 1) Plant-Simulation Configuration (same as before) ----
with st.container():
    st.markdown("<h3 class='cfg-card-title'>Plant Simulation Configuration</h3>", unsafe_allow_html=True)
    for key in ["SIM_TIME", "INTERARRIVAL", "Forklift_Capacity"]:
        if key in general_core:
            render_number_input(key, general_core[key])

# ---- 2) Machine Parameters (same as before) ----
MP_HELP = """
<div class="white-box">
  <div class="app-heading">Machine Parameters</div>
  <ul>
    <li><strong>Machine Group</strong>: Select the operation of interest.</li>
    <li><strong>Machine</strong>: Choose a specific machine instance.</li>
    <li><strong>Availability</strong>: The OEE of the selected machine.</li>
    <li><strong>Cycle Time</strong>: Custom cycle time if OEE > 0.</li>
    <li><strong>Weigh and Classify Reject Interval</strong>: For overweight shells identified at Weighing and Classification.</li>
    <li><strong>Tensile Test Fail Interval</strong>: For batches that fail the Tensile Test.</li>
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
    mach = st.selectbox("Machine", machines, format_func=lambda c: MACHINE_LABELS.get(c, c))

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
            if fname == "OEE": continue
            render_number_input(info["key"], info["meta"])
        if grp == "TT" and "TT_FAIL_INTERVAL" in general_core:
            render_number_input("TT_FAIL_INTERVAL", general_core["TT_FAIL_INTERVAL"])
    submitted = st.form_submit_button("Apply changes")
    if submitted:
        for info in core.values():
            k = info["key"]
            if k in st.session_state: st.session_state["overrides"][k] = st.session_state[k]
            else:                     st.session_state["overrides"].pop(k, None)
        if grp == "TT":
            k = "TT_FAIL_INTERVAL"
            if k in st.session_state: st.session_state["overrides"][k] = st.session_state[k]
            else:                     st.session_state["overrides"].pop(k, None)
        for info in trans.values():
            k = info["key"]
            if k in st.session_state: st.session_state["overrides"][k] = st.session_state[k]
            else:                     st.session_state["overrides"].pop(k, None)

# ---- 3) Sidebar – transport-time parameters ONLY ----
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

# ---- 4) Run (Time → Units) ----
run_clicked = st.button("🚀  Run (Time → Units)", type="primary")
if run_clicked:
    overrides = st.session_state.get("overrides", {}).copy()
    for g in ["SIM_TIME", "INTERARRIVAL", "Forklift_Capacity"]:
        if g in st.session_state:
            overrides[g] = st.session_state[g]
    st.session_state["overrides"] = overrides

    importlib.reload(cfg)
    for k, v in overrides.items():
        setattr(cfg, k, v)

    result = run_with_progress(lambda progress_callback=None: run_sim(overrides, progress_callback=progress_callback))
    df_units, _, df_move, df_final_wip, df_util, *fgs = result

    # Friendly names & store
    df_util["machine"] = df_util["machine"].map(MACHINE_LABELS).fillna(df_util["machine"])
    df_final_wip["Node"] = df_final_wip["Node"].map(NODE_LABELS).fillna(df_final_wip["Node"])
    df_move = relabel_transport(df_move)

    st.session_state["sim_results"] = {
        "df_units": df_units,
        "df_move": df_move,
        "df_final_wip": df_final_wip,
        "df_util": df_util,
        "fg6_count": len(fgs[-1]),
    }

# ---- 5) Results ----
results = st.session_state.get("sim_results")
if results:
    st.metric("Units in Dispatch:", results["fg6_count"])
    df_map = {
        "Machine utilisation": results["df_util"],
        "Unit-level summary": results["df_units"],
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
