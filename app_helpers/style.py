# File: app_helpers/style.py
import streamlit as st
from pathlib import Path

def inject_style():
    path = Path(__file__).parent / "style.css"
    css = path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

HELP_TEXT = """
<div class="top-banner"></div>
<div class="hero-title">BB Plant Simulator</div>

<div class="info-box">
  <div class="app-heading">Plant Simulation Configuration</div>
  <ul>
    <li><strong>Simulation Duration</strong>: Number of minutes the plant runs (empty start-up).</li>
    <li><strong>Delay Between Cut Operations</strong>: Idle time between billet cuts.</li>
    <li><strong>Available Forklifts</strong>: Number of forklifts for pallet moves.</li>
  </ul>
  <div class="app-sub">Edit Transport Times</div>
  <ul>
    <li>Check the box on the sidebar to access and edit transport times between processes.</li>
    <li>Use only if plant layout changes.</li>
    <li>Not required for standard runs.</li>
  </ul>
</div>
"""