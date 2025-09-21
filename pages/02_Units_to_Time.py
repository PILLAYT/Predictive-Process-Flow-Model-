# pages/02_Units_to_Time.py
import importlib
import pandas as pd
import streamlit as st
from app_helpers.simulation import run_with_progress
from plant_sim.run_sim import run_sim
import plant_sim.config as cfg

st.set_page_config(page_title="Units → Time", layout="wide")
st.title("📦  Units → Time")

# Inputs
target_units = st.number_input("Finished units target (Stage 6)", min_value=1, value=200, step=10)
time_cap     = st.number_input("Optional time cap (minutes, 0 = unlimited)", min_value=0, value=0, step=100)

st.session_state.setdefault("overrides", {})
st.session_state["TARGET_UNITS"] = int(target_units)
st.session_state["TIME_CAP"]     = int(time_cap)

if st.button("🚀 Run (Units → Time)"):
    overrides = st.session_state["overrides"].copy()

    # Pass the target (we’ll wire true early-stop later if you want)
    overrides["TARGET_UNITS"] = int(target_units)
    if time_cap > 0:
        overrides["SIM_TIME"] = int(time_cap)  # cap the run

    # include other top-level settings if you want them applied
    for g in ["INTERARRIVAL", "Forklift_Capacity"]:
        if g in st.session_state:
            overrides[g] = st.session_state[g]

    # persist + patch cfg
    st.session_state["overrides"] = overrides
    importlib.reload(cfg)
    for k, v in overrides.items():
        setattr(cfg, k, v)

    # run
    result = run_with_progress(lambda progress_callback=None: run_sim(overrides, progress_callback=progress_callback))

    # unpack minimal outputs
    df_units, _, df_move, df_final_wip, df_util, *fgs = result
    fg6 = fgs[-1]

    # For now, we show what was produced within the cap.
    # When you’re ready, we’ll end the run the moment Stage 6 hits the target.
    st.metric("Units in Dispatch (Stage 6)", len(fg6))
    if time_cap > 0:
        st.caption(f"Cap applied: {time_cap} minutes")

    # optional frames
    with st.expander("Machine utilisation"):
        st.dataframe(df_util, use_container_width=True)
    with st.expander("Transport log"):
        st.dataframe(df_move, use_container_width=True)
    with st.expander("Final WIP count"):
        st.dataframe(df_final_wip, use_container_width=True)
