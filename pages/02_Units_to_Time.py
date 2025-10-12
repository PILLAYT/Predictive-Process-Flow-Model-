# pages/02_Units_to_Time.py
from __future__ import annotations
import re, importlib
import pandas as pd
import streamlit as st
from app_helpers.style import HELP_TEXT

# MUST be the first Streamlit call on this page
st.set_page_config(page_title="Units → Time", layout="wide", initial_sidebar_state="collapsed")

from app_helpers.labels import MACHINE_LABELS, GROUP_LABELS, NODE_LABELS
from app_helpers.ui_helpers import (
    schema, general_core, general_transport, machine_core, machine_transport,
    prefix_to_machines, prefix_by_label, render_number_input,
)
# from app_helpers.simulation import run_with_progress
from plant_sim.run_sim import run_sim
import plant_sim.config as cfg

# --- App banner (matches app.py / Time → Units) ---
from app_helpers.style import inject_style
inject_style()

# Hide Streamlit's default thin blue decoration line
st.markdown(
    "<style>[data-testid='stDecoration']{display:none !important;}</style>",
    unsafe_allow_html=True,
)

# Thicker dark-blue banner + centered page title
st.markdown(
    """
    <style>
      .page-title{
        text-align:center;
        font-size:2.2em;
        font-weight:700;
        margin:.25rem 0 .5rem 0;
      }
    </style>
    <div class="top-accent"></div>
    <h1 class="page-title">📦 Units → Time</h1>
    """,
    unsafe_allow_html=True,
)

# ── Heading + single top input (no SIM_TIME) ────────────────────────────────
st.markdown(HELP_TEXT, unsafe_allow_html=True)
# st.markdown("<h3 class='cfg-card-title'>Plant Simulation Configuration</h3>", unsafe_allow_html=True)
target_units = st.number_input(
    "Target finished units (Dispatch / Stage 6)",
    min_value=1, value=20, step=10
)
run_clicked = False   # set later by the bottom-left button

# ── Helpers (relabel + find Nth Dispatch arrival) ───────────────────────────
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
        if col in df.columns: df[col] = df[col].apply(map_loc)
    return df

def _pick_time_col(df: pd.DataFrame) -> str:
    for c in ["time","Time","timestamp","Timestamp","ts","TS","t","now","Now"]:
        if c in df.columns: return c
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]): return c
    return None

def _is_dispatch(value: str) -> bool:
    s = str(value).lower()
    return ("dispatch" in s) or ("fg6" in s) or ("stage 6" in s) or ("stage6storage" in s) or ("finished" in s and "good" in s)

def find_time_to_target_units(df_move: pd.DataFrame, n: int):
    if df_move is None or df_move.empty:
        return False, None, pd.DataFrame()
    df = relabel_transport(df_move)
    if "To" not in df.columns:
        for a, b in (("dest","To"),("to","To")):
            if a in df.columns and "To" not in df.columns:
                df = df.rename(columns={a:"To"})
    time_col = _pick_time_col(df)
    if time_col is None:
        return False, None, pd.DataFrame()
    mask = df["To"].apply(_is_dispatch) if "To" in df.columns else pd.Series([False]*len(df), index=df.index)
    hits = df.loc[mask].copy()
    if hits.empty:
        return False, None, pd.DataFrame()
    hits = hits.sort_values(time_col, kind="mergesort")
    if len(hits) >= int(n):
        t = hits.iloc[int(n)-1][time_col]
        return True, t, hits
    return False, None, hits

# ── Session state ───────────────────────────────────────────────────────────
st.session_state.setdefault("overrides", {})

# ── Plant-level configuration (NO SIM_TIME here) ────────────────────────────
for key in ["INTERARRIVAL", "Forklift_Capacity"]:
    if key in general_core:
        render_number_input(key, general_core[key])
    else:
        st.warning(f"{key} not found in YAML schema")


# ---- Machine Parameters help (same as Time → Units) ----


MP_HELP = """
<div class="white-box">
  <div class="app-heading">Machine Parameters</div>
  <ul>
    <li><strong>Machine Group</strong>: Select the operation of interest.</li>
    <li><strong>Machine</strong>: Choose a specific machine instance.</li>
    <li><strong>Availability</strong>: The OEE of the selected machine.</li>
    <li><strong>Cycle Time</strong>: Custom cycle time if OEE > 0.</li>
  </ul>
</div>
"""

# st.markdown("<h3 class='cfg-card-title'>Machine Parameters</h3>", unsafe_allow_html=True)
st.markdown(MP_HELP, unsafe_allow_html=True)

# Optional heading line (matches your style)
# st.markdown("<div class='app-heading'>Machine Parameters</div>", unsafe_allow_html=True)


# st.markdown("<div class='app-heading'>Machine Parameters</div>", unsafe_allow_html=True)
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
        # sync overrides
        for info in core.values():
            k = info["key"]
            if k in st.session_state: st.session_state["overrides"][k] = st.session_state[k]
            else: st.session_state["overrides"].pop(k, None)
        if grp == "TT":
            k = "TT_FAIL_INTERVAL"
            if k in st.session_state: st.session_state["overrides"][k] = st.session_state[k]
            else: st.session_state["overrides"].pop(k, None)
        for info in trans.values():
            k = info["key"]
            if k in st.session_state: st.session_state["overrides"][k] = st.session_state[k]
            else: st.session_state["overrides"].pop(k, None)

# # ── Bottom-left Run button right under the form ─────────────────────────────
# st.markdown(" ")
# btn_col, _ = st.columns([1, 6])
# with btn_col:
#     run_clicked = st.button("🚀 Run Simulation", type="primary")

# ── Sidebar: transport parameters ───────────────────────────────────────────
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
                
# ... end of the form block that updates overrides ...
# (indentation returns to the left margin here)

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

# (for Units → Time) place your bottom-left Run button right after this:
btn_col, _ = st.columns([1, 6])
with btn_col:
    run_clicked = st.button("🚀 Run Simulation", type="primary")


# ── Run: send early-stop target; compute Nth-arrival time ───────────────────
if run_clicked:
    overrides = st.session_state.get("overrides", {}).copy()
    overrides["TARGET_UNITS"] = int(target_units)
    overrides["EARLY_STOP_TARGET_UNITS"] = int(target_units)  # the new early-stop hook

    for g in ["INTERARRIVAL", "Forklift_Capacity"]:
        if g in st.session_state:
            overrides[g] = st.session_state[g]

    st.session_state["overrides"] = overrides
    importlib.reload(cfg)
    for k, v in overrides.items():
        setattr(cfg, k, v)

    with st.spinner("Running simulation..."):
        # If run_sim doesn't need a callback, you can omit it:
        sim_out = run_sim(overrides, progress_callback=None)

    df_units, _, df_move, df_final_wip, df_util, *fgs = sim_out
    fg6 = fgs[-1] if fgs else []
    n_disp = len(fg6)

    hit, t_target, df_hits = find_time_to_target_units(df_move, int(target_units))
    st.metric("Units in Dispatch (produced in this run)", n_disp)
    if hit:
        st.success(f"Time required to hit {int(target_units)} units: **{float(t_target):,.2f} minutes**")
    else:
        st.warning("Target not reached in this run — ensure early-stop is active (see run_sim hook below).")

    with st.expander("Dispatch arrivals (chronological)"):
        st.dataframe(relabel_transport(df_hits) if not df_hits.empty else pd.DataFrame({"info": ["No Dispatch/FG6 arrivals recorded."]}),
                     use_container_width=True)

    with st.expander("Machine utilisation"):
        dfu = df_util.copy()
        if "machine" in dfu.columns:
            dfu["machine"] = dfu["machine"].map(MACHINE_LABELS).fillna(dfu["machine"])
        st.dataframe(dfu, use_container_width=True)

    with st.expander("Transport log"):
        st.dataframe(relabel_transport(df_move), use_container_width=True)

    with st.expander("Final WIP count"):
        dff = df_final_wip.copy()
        if "Node" in dff.columns:
            dff["Node"] = dff["Node"].map(NODE_LABELS).fillna(dff["Node"])
        st.dataframe(dff, use_container_width=True)
