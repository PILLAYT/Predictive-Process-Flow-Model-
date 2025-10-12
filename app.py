# File: app.py
from __future__ import annotations
import streamlit as st

# MUST be the first Streamlit call on this page (and only once)
st.set_page_config(
    page_title="BB M0121 Sim",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from app_helpers.style import inject_style

inject_style()

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
      /* Ensure landing-page button containers and buttons stretch full width */
      :root:has(#lp-flag) [data-testid="stButton"] { width: 100% !important; }
      :root:has(#lp-flag) [data-testid="stButton"] > * { width: 100% !important; max-width: 100% !important; min-width: 0 !important; }
      :root:has(#lp-flag) [data-testid="stButton"] [class^="st-emotion-cache-"] { width: 100% !important; max-width: 100% !important; min-width: 0 !important; }

      /* Also force the top-level element container of each specific button to stretch */
      :root:has(#lp-flag) [data-testid="stElementContainer"].st-key-btn_time_units,
      :root:has(#lp-flag) [data-testid="stElementContainer"].st-key-btn_units_time {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        display: block !important;
        align-self: stretch !important;
      }
      :root:has(#lp-flag) [data-testid="stElementContainer"].st-key-btn_time_units > *,
      :root:has(#lp-flag) [data-testid="stElementContainer"].st-key-btn_units_time > * {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
      }
      :root:has(#lp-flag) [data-testid="stElementContainer"][width="fit-content"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
      }
      :root:has(#lp-flag) [data-testid="stElementContainer"].st-key-btn_time_units [class^="st-emotion-cache-"],
      :root:has(#lp-flag) [data-testid="stElementContainer"].st-key-btn_units_time [class^="st-emotion-cache-"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
      }

      /* Style all Streamlit buttons */
      :root:has(#lp-flag) [data-testid="stButton"] > button{
        width: 100% !important;
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
      :root:has(#lp-flag) [data-testid="stButton"] > button:hover{
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


st.markdown("---")

# Stop here — nothing else should render on the landing page
st.stop()
