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

# Put this near the top of app.py, after inject_style() and set_page_config()
# 1) A page-flag we can target from CSS
st.markdown("<span id='lp-flag' style='display:none'></span>", unsafe_allow_html=True)

########################################################################################

# 1) Add a local flag so CSS can target only this page
st.markdown("<span id='lp-flag' style='display:none'></span>", unsafe_allow_html=True)

# 2) Hide the sidebar + nav + toggle ONLY on this page (scoped by #lp-flag)
st.markdown("""
<style>
  /* Hide the sidebar pane + the multipage nav only when #lp-flag exists */
  :root:has(#lp-flag) [data-testid="stSidebar"]    { display: none !important; }
  :root:has(#lp-flag) [data-testid="stSidebarNav"] { display: none !important; }

  /* Hide all versions of the toggle/chevron on this page */
  :root:has(#lp-flag) [data-testid="collapsedControl"] { display: none !important; }
  :root:has(#lp-flag) header [data-testid="stSidebarCollapseControl"] { display: none !important; }
  :root:has(#lp-flag) header [data-testid="stSidebarCollapseButton"]  { display: none !important; }
  :root:has(#lp-flag) header [data-testid="baseButton-header"]        { display: none !important; }
  :root:has(#lp-flag) header [data-testid="baseButton-headerNoPadding"] { display: none !important; }
  :root:has(#lp-flag) header button[title*="sidebar"]  { display: none !important; }
  :root:has(#lp-flag) header button[aria-label*="sidebar"] { display: none !important; }

  /* Optional: remove the left padding so content is truly full-width */
  :root:has(#lp-flag) section.main > div { padding-left: 0 !important; }
</style>
""", unsafe_allow_html=True)



# Hide sidebar/nav on the landing page
# st.markdown("""
# <style>
#   [data-testid="stSidebar"] { display: none; }
#   [data-testid="stSidebarNav"] { display: none; }
# </style>
# """, unsafe_allow_html=True)

st.markdown(
    """
    <h1 style='text-align: center; font-size: 2.2em; font-weight: 700;'>
        BB M0121 Production Simulator
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h1 style='text-align: center; font-size: 1.0em; font-weight: 300;'>
        Select a mode below based on your desired input and output.
    </h1>
    """,
    unsafe_allow_html=True
)




st.markdown(
    """
    <style>
      /* Style all Streamlit buttons */
      [data-testid="stButton"] > button{
        width: 100%;
        border: 1px solid #d0d4da;
        border-radius: 12px;
        padding: 14px 18px;
        background: rgba(255,255,255,.7);
        box-shadow: 0 1px 2px rgba(0,0,0,.05);
        font-weight: 600;
        display: flex; 
        align-items: center; 
        justify-content: center;
        transition: border-color .15s, box-shadow .15s, transform .05s;
      }
      [data-testid="stButton"] > button:hover{
        border-color: #8ab4f8;
        box-shadow: 0 4px 12px rgba(0,0,0,.08);
        transform: translateY(-1px);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Center column for the two stacked buttons
padL, center, padR = st.columns([1, 2, 1])

with center:
    if st.button("⏱️ Time → Units", key="btn_time_units"):
        st.switch_page("pages/01_Time_to_Units.py")

    st.write("")  # spacer

    if st.button("📦 Units → Time", key="btn_units_time"):
        st.switch_page("pages/02_Units_to_Time.py")


# st.markdown("<div class='mode-stack'>", unsafe_allow_html=True)

# if st.button("⏱️ Time → Units", key="btn_time_units"):
#     st.switch_page("pages/01_Time_to_Units.py")

# if st.button("📦 Units → Time", key="btn_units_time"):
#     st.switch_page("pages/02_Units_to_Time.py")

# st.markdown("</div>", unsafe_allow_html=True)




# # Center column for the two stacked links
# _, center, _ = st.columns([1, 2, 1])

# with center:
#     st.page_link(
#         "pages/01_Time_to_Units.py",
#         label="⏱️ Time → Units",
#         help="Run a fixed simulated duration and see output/KPIs.",
#     )
#     st.write("")  # spacer
#     st.page_link(
#         "pages/02_Units_to_Time.py",
#         label="📦 Units → Time",
#         help="Enter a finished-units target and get the required time.",
#     )

st.markdown("---")

# Stop here — nothing else should render on the landing page
st.stop()