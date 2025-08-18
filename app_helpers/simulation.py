# File: app_helpers/simulation.py
import streamlit as st
import hashlib
import textwrap

@st.cache_data(show_spinner=False, max_entries=3)
def run_sim_cached(hash_key: str):
    from plant_sim.run_sim import run_sim
    overrides_copy = dict(st.session_state["overrides"])
    return run_sim(overrides_copy)

def dict_hash(d: dict) -> str:
    return hashlib.sha1(str(sorted(d.items())).encode()).hexdigest()

def run_with_progress(run_fn):
    progress_text = st.empty() 
    bar_html = st.empty()
    
    base_html = """
    <div style="position:relative; height:18px; width:100%; background:#e6e6e6; border-radius:9px; margin-top:4px;">
      <div style="height:18px; width:{w}%; background:#167EE6; border-radius:9px 0 0 9px; transition:width .1s;"></div>
      <div style="position:absolute; top:-6px; left:{w}%; transform:translateX(-50%); font-size:22px; transition:left .1s;">🚀</div>
    </div>
    """

    def render(pct: int):
        bar_html.markdown(textwrap.dedent(base_html).format(w=pct), unsafe_allow_html=True)

    render(0)
    last_ui = 0.0

    def _update(p: float):
        nonlocal last_ui
        if p - last_ui < 0.005 and p < 1:
            return
        last_ui = p
        percent = int(p * 100)
        render(percent)

        # Update floating percentage text
        progress_text.markdown(
            f"""
            <div style='display: flex; justify-content: center; margin-top: 30px; margin-bottom: -20px;'>
                <span style='font-size: 22px; font-weight: bold;'>{percent}%</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Run the actual simulation
    result = run_fn(progress_callback=_update)

    # Final update at 100%
    progress_text.markdown(
        """
        <div style='display: flex; justify-content: center; margin-top: 30px; margin-bottom: -20px;'>
            <span style='font-size: 22px; font-weight: bold;'>100%</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    render(100)

    return result



# def run_with_progress(run_fn):
#     progress_text = st.empty() 
#     bar_html = st.empty()
#     base_html = """
#     <div style="position:relative; height:18px; width:100%; background:#e6e6e6; border-radius:9px; margin-top:4px;">
#       <div style="height:18px; width:{w}%; background:#167EE6; border-radius:9px 0 0 9px; transition:width .1s;"></div>
#       <div style="position:absolute; top:-6px; left:{w}%; transform:translateX(-50%); font-size:22px; transition:left .1s;">🚀</div>
#     </div>
#     """
#     def render(pct: int):
#         bar_html.markdown(textwrap.dedent(base_html).format(w=pct), unsafe_allow_html=True)
#     render(0)
#     last_ui = 0.0
    
#     def _update(p: float):
#         nonlocal last_ui
#         if p - last_ui < 0.005 and p < 1:
#             return
#         last_ui = p
#         render(int(p * 100))
        
#         # Update floating percentage text
#         progress_text.markdown(
#             f"""
#             <div style='display: flex; justify-content: center; margin-top: 30px; margin-bottom: -20px;'>
#                 <span style='font-size: 22px; font-weight: bold;'>{percent}%</span>
#             </div>
#             """,
#             unsafe_allow_html=True
#         )

    
        
#     result = run_fn(progress_callback=_update)
    
#     progress_text.markdown(
#         """
#         <div style='display: flex; justify-content: center; margin-top: 30px; margin-bottom: -20px;'>
#             <span style='font-size: 22px; font-weight: bold;'>100%</span>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )
#     render(100)

#     return result

