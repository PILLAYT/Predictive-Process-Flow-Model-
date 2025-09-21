# pages/01_Time_to_Units.py
import importlib
import pandas as pd
import streamlit as st
from app_helpers.simulation import run_with_progress
from plant_sim.run_sim import run_sim
import plant_sim.config as cfg

st.set_page_config(page_title="Time → Units", layout="wide")
st.title("⏱️  Time → Units")

# Inputs (keep simple; expand later if you want)
sim_time = st.number_input("Simulate for (minutes)", min_value=1, value=int(getattr(cfg, "SIM_TIME", 10_000)), step=100)
st.session_state.setdefault("overrides", {})
st.session_state["SIM_TIME"] = int(sim_time)
st.session_state["TARGET_UNITS"] = 0  # ensure unit-target mode is off here

if st.button("🚀 Run (Time → Units)"):
    overrides = st.session_state["overrides"].copy()
    # include top-level settings you already use
    for g in ["SIM_TIME", "INTERARRIVAL", "Forklift_Capacity"]:
        if g in st.session_state:
            overrides[g] = st.session_state[g]

    # persist + patch cfg
    st.session_state["overrides"] = overrides
    importlib.reload(cfg)
    for k, v in overrides.items():
        setattr(cfg, k, v)

    # run
    result = run_with_progress(lambda progress_callback=None: run_sim(overrides, progress_callback=progress_callback))

    # unpack minimal outputs you already use
    df_units, _, df_move, df_final_wip, df_util, *fgs = result
    fg6 = fgs[-1]

    # quick summary
    st.metric("Units in Dispatch (Stage 6)", len(fg6))
    if sim_time > 0:
        st.metric("Throughput (units/min)", round(len(fg6) / sim_time, 4))

    # show a couple of frames (optional)
    with st.expander("Machine utilisation"):
        st.dataframe(df_util, use_container_width=True)
    with st.expander("Transport log"):
        st.dataframe(df_move, use_container_width=True)
    with st.expander("Final WIP count"):
        st.dataframe(df_final_wip, use_container_width=True)
