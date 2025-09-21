# pages/02_Units_to_Time.py
from __future__ import annotations
import re
import importlib
import pandas as pd
import streamlit as st

# Must be first Streamlit call on this page
st.set_page_config(
    page_title="Units → Time",
    layout="wide",
    initial_sidebar_state="collapsed",   # Sidebar exists, but starts collapsed
)

# ------------------ Mode switch header (tiles stay visible) ------------------
st.markdown("### Mode")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.page_link(
        "pages/01_Time_to_Units.py",
        label="⏱️  Time → Units",
        icon="⏱️",
        help="Run for a fixed simulated duration and see output/KPIs."
    )
with c2:
    st.page_link(
        "pages/02_Units_to_Time.py",
        label="✅ 📦  Units → Time (current)",
        icon="📦",
        help="Enter a finished-units target and get the time required."
    )
st.divider()
# ---------------------------------------------------------------------------

# App helpers (none of these should run st.* at import time)
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
from app_helpers.simulation import run_with_progress
from plant_sim.run_sim import run_sim
import plant_sim.config as cfg

# Base styling/help to match the original app
inject_style()
st.markdown(HELP_TEXT, unsafe_allow_html=True)

st.title("📦  Units → Time")

# Keep state like the old app
st.session_state.setdefault("overrides", {})
st.session_state.setdefault("sim_results", None)

# ── 1) Global configuration (same card as before) ───────────────────────────
with st.container():
    st.markdown("<h3 class='cfg-card-title'>Plant Simulation Configuration</h3>", unsafe_allow_html=True)
    # SIM_TIME here can act as an optional cap for this mode
    for key in ["SIM_TIME", "INTERARRIVAL", "Forklift_Capacity"]:
        if key in general_core:
            render_number_input(key, general_core[key])

# ── 2) Units target inputs (mode-specific) ─────────────────────────────────
col_tu, col_cap = st.columns(2)
with col_tu:
    target_units = st.number_input("Finished units target (Stage 6)", min_value=1, value=200, step=10, help="Run until Dispatch reaches this many units (engine change later).")
with col_cap:
    time_cap = st.number_input("Optional time cap (minutes, 0 = unlimited)", min_value=0, value=0, step=100, help="Safety stop if target not reached in time.")

st.session_state["TARGET_UNITS"] = int(target_units)
st.session_state["TIME_CAP"] = int(time_cap)

# ── 3) Machine Parameters (same as original) ───────────────────────────────
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
            if fname == "OEE":
                continue
            render_number_input(info["key"], info["meta"])
        if grp == "TT" and "TT_FAIL_INTERVAL" in general_core:
            render_number_input("TT_FAIL_INTERVAL", general_core["TT_FAIL_INTERVAL"])
    submitted = st.form_submit_button("Apply changes")
    if submitted:
        # sync overrides for core fields
        for info in core.values():
            k = info["key"]
            if k in st.session_state:
                st.session_state["overrides"][k] = st.session_state[k]
            else:
                st.session_state["overrides"].pop(k, None)
        # TT global
        if grp == "TT":
            k = "TT_FAIL_INTERVAL"
            if k in st.session_state:
                st.session_state["overrides"][k] = st.session_state[k]
            else:
                st.session_state["overrides"].pop(k, None)
        # transport fields for this machine
        for info in trans.values():
            k = info["key"]
            if k in st.session_state:
                st.session_state["overrides"][k] = st.session_state[k]
            else:
                st.session_state["overrides"].pop(k, None)

# ── 4) Sidebar — transport-time parameters only (as requested) ─────────────
with st.sidebar:
    st.subheader("Transport Times")
    if general_transport:
        st.markdown("**General**")
        for key, meta in general_transport.items():
            render_number_input(key, meta)
    if trans:
        st.markdown(f"**{mach}**")
        for info in trans.values():
            render_number_input(info["key"], info["meta"])

# ── 5) Run (Units → Time) ─────────────────────────────────────────────────
run_clicked = st.button("🚀  Run (Units → Time)", type="primary")
if run_clicked:
    overrides = st.session_state.get("overrides", {}).copy()

    # Mode-specific bits
    overrides["TARGET_UNITS"] = int(target_units)
    if time_cap > 0:
        overrides["SIM_TIME"] = int(time_cap)   # temporary cap until early-stop is implemented

    # Common top-level settings you already use
    for g in ["INTERARRIVAL", "Forklift_Capacity"]:
        if g in st.session_state:
            overrides[g] = st.session_state[g]

    st.session_state["overrides"] = overrides

    # Patch cfg and run
    import plant_sim.config as cfg
    importlib.reload(cfg)
    for k, v in overrides.items():
        setattr(cfg, k, v)

    result = run_with_progress(lambda progress_callback=None: run_sim(overrides, progress_callback=progress_callback))

    # Unpack & store minimal frames for display
    df_units, _, df_move, df_final_wip, df_util, *fgs = result
    st.session_state["sim_results"] = {
        "df_units": df_units,
        "df_move": df_move,
        "df_final_wip": df_final_wip,
        "df_util": df_util,
        "fg6_count": len(fgs[-1]),     # finished_goods6
    }

# ── 6) Results (same pattern as original) ──────────────────────────────────
results = st.session_state.get("sim_results")
if results:
    st.metric("Units in Dispatch (Stage 6)", results["fg6_count"])
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
