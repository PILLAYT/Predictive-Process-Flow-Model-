# File: app.py
from __future__ import annotations
import re
import streamlit as st

# MUST be the first Streamlit call on this page (and only once)
st.set_page_config(
    page_title="BB M0121 Sim",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

inject_style()

########################################################################################

# Hide sidebar/nav on the landing page
st.markdown("""
<style>
  [data-testid="stSidebar"] { display: none; }
  [data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("Choose how to run the simulation")

col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/01_Time_to_Units.py", label="⏱️  Time → Units", icon="⏱️",
                 help="Run a fixed simulated duration and see output/KPIs.")
with col2:
    st.page_link("pages/02_Units_to_Time.py", label="📦  Units → Time", icon="📦",
                 help="Enter a finished-units target and get the required time.")

st.markdown("---")
st.caption("Open one of the modes above to configure and run the simulation.")

# Stop here — nothing else should render on the landing page
st.stop()

