import os
import sys
import time

import streamlit as st
import streamlit.components.v1 as components

# Ensure project root is on the path so `courtroom` package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from courtroom.judgment_finder import find_past_judgments
from courtroom.judgment_ui import display_all_judgments


def nav_to(page_path: str) -> None:
    """Navigate to a page using JS redirect (works on all Streamlit versions)."""
    name = os.path.splitext(os.path.basename(page_path))[0]
    js = f'<script>window.parent.location.href = "/{name}"</script>'
    components.html(js, height=0)


st.set_page_config(
    page_title="Past Judgment Finder",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state
if "judgment_data" not in st.session_state:
    st.session_state.judgment_data = None
if "use_precedents" not in st.session_state:
    st.session_state.use_precedents = True

# Header
col_back, col_header, col_empty = st.columns([1, 8, 1])
with col_back:
    if st.button("← Back to Courtroom", use_container_width=True):
        nav_to("4_Courtroom_Simulator.py")
with col_header:
    st.markdown("### 📚 Past Judgment Finder")
    st.caption(
        "Search Indian Kanoon for real past court judgments matching your case. "
        "These precedents will be available to the AI lawyers in the courtroom simulator."
    )
with col_empty:
    st.empty()

st.markdown("---")

# Case input (simplified, but consistent with simulator)
st.markdown("### Case Description for Precedent Search")

col_left, col_right = st.columns([1, 1])

with col_left:
    case_type = st.text_input(
        "Case Type (optional, e.g. Contract, IPC, Consumer, etc.)",
        value="General",
    )
    accused = st.text_input(
        "Accused Party (optional)",
        placeholder="Name, role (e.g. Ramesh Gupta — Landlord)",
    )
    victim = st.text_input(
        "Complainant / Victim (optional)",
        placeholder="Name, role (e.g. Anil Kumar — Tenant)",
    )

with col_right:
    location = st.text_input(
        "Location (optional)",
        placeholder="City, State",
    )
    incident = st.text_area(
        "Describe the Incident (this powers the search)",
        height=180,
        placeholder=(
            "Describe what happened, when, which rights or laws may have been "
            "violated, and what remedy is being sought..."
        ),
    )

# Build case string for the finder
case_string = f"""
Case Type: {case_type}
Accused: {accused}
Complainant: {victim}
Location: {location}

Facts of the Case:
{incident}
""".strip()

st.markdown("---")

col_toggle, col_button = st.columns([1, 2])

with col_toggle:
    use_precedents = st.toggle(
        "Use these precedents in simulator",
        value=st.session_state.use_precedents,
        help=(
            "When ON, any judgments found here can be used as precedents by "
            "AI lawyers in the Courtroom Simulator page."
        ),
    )
    st.session_state.use_precedents = use_precedents

with col_button:
    search_clicked = st.button(
        "🔍 Find Past Judgments",
        type="primary",
        use_container_width=True,
        disabled=not incident.strip(),
    )

if search_clicked and incident.strip():
    progress_messages = st.empty()
    judgment_status_messages = []

    def update_progress(msg: str) -> None:
        judgment_status_messages.append(msg)
        progress_messages.markdown("\n\n".join(judgment_status_messages[-3:]))

    with st.spinner("Searching Indian legal database..."):
        judgment_data = find_past_judgments(
            case_description=case_string,
            case_type=case_type,
            progress_callback=update_progress,
        )
        st.session_state.judgment_data = judgment_data

    progress_messages.empty()

    if judgment_data.get("error"):
        st.error(f"⚠️ {judgment_data['error']}")
    else:
        st.success(
            f"✅ Found {judgment_data['total_found']} past judgments! "
            "These will now be available as precedents in the Courtroom Simulator."
        )
        display_all_judgments(judgment_data)

elif st.session_state.judgment_data:
    st.info(
        "Using previously loaded past judgments. "
        "Click the button above to refresh the search."
    )
    with st.expander(
        f"📚 {st.session_state.judgment_data.get('total_found', 0)} "
        "Past Judgments Loaded (click to view)",
        expanded=False,
    ):
        display_all_judgments(st.session_state.judgment_data)

