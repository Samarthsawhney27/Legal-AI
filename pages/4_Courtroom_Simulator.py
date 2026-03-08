# pages/4_Courtroom_Simulator.py

import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import time


def nav_to(page_path: str):
    """Navigate to a page using JS redirect (works on all Streamlit versions)."""
    name = os.path.splitext(os.path.basename(page_path))[0]
    js = f'<script>window.parent.location.href = "/{name}"</script>'
    components.html(js, height=0)

from courtroom.case_parser import (
    extract_case_details,
    build_case_string,
    extract_text_from_upload,
    ALL_CASE_TYPES,
    CASE_TYPE_DESCRIPTIONS,
    CASE_BOOKS_HINT,
)
from courtroom.voice_input import (
    check_voice_dependencies,
    record_and_transcribe,
    get_voice_dependency_status,
)
from courtroom.retriever import retrieve_legal_context
from courtroom.agents import (
    build_prosecutor_message,
    build_defense_message,
    build_judge_message,
    stream_agent,
)
from courtroom.case_templates import (
    PRESET_CASES,
    SUPPORTED_CASE_TYPES,
    UNSUPPORTED_CASE_TYPES,
)
from courtroom.transcript import generate_transcript_pdf

# Ensure project root is on the path so `courtroom` package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Courtroom Simulator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown(
    """
<style>
    /* Header styling */
    .court-header {
        text-align: center;
        padding: 2rem 1.5rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 12px;
        border: 1px solid #e94560;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(233, 69, 96, 0.15);
    }

    /* Agent boxes */
    .prosecution-box {
        background: linear-gradient(145deg, #2d0000, #1a0000);
        border: 1px solid #c0392b;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }

    .defense-box {
        background: linear-gradient(145deg, #002d00, #001a00);
        border: 1px solid #27ae60;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }

    .verdict-box {
        background: linear-gradient(145deg, #1a1a00, #2d2d00);
        border: 2px solid #f39c12;
        border-radius: 10px;
        padding: 24px;
        margin: 16px 0;
    }

    /* Source chips */
    .source-chip {
        display: inline-block;
        background: #1e3a5f;
        color: #7ec8e3;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        margin: 3px;
        border: 1px solid #7ec8e3;
    }

    /* Status badges */
    .badge-prosecution { color: #e74c3c; font-weight: bold; font-size: 18px; }
    .badge-defense { color: #2ecc71; font-weight: bold; font-size: 18px; }
    .badge-judge { color: #f39c12; font-weight: bold; font-size: 18px; }

    .back-button {
        background: #546e7a;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        text-decoration: none;
        display: inline-block;
        margin-bottom: 1rem;
    }

    .back-button:hover {
        background: #455a64;
        text-decoration: none;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
col_back, col_header, col_empty = st.columns([1, 8, 1])
with col_back:
    if st.button("← Back to Main", use_container_width=True):
        nav_to("Legal_AI_RAG.py")
with col_header:
    st.markdown(
        """
    <div class="court-header">
        <h1 style="color:#e94560; margin:0; font-size:2.2rem;">AI Courtroom Simulator</h1>
        <p style="color:#aaaaaa; margin:8px 0 0 0; font-size:1rem;">
            Powered by Indian Legal RAG System — Constitution + Contract + IPC + Consumer Protection
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
with col_empty:
    st.empty()

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "trial_complete" not in st.session_state:
    st.session_state.trial_complete = False
if "prosecution_text" not in st.session_state:
    st.session_state.prosecution_text = ""
if "defense_text" not in st.session_state:
    st.session_state.defense_text = ""
if "verdict_text" not in st.session_state:
    st.session_state.verdict_text = ""
if "legal_context" not in st.session_state:
    st.session_state.legal_context = {}
if "case_details" not in st.session_state:
    st.session_state.case_details = {}
if "selected_preset_key" not in st.session_state:
    st.session_state.selected_preset_key = None
if "judgment_data" not in st.session_state:
    st.session_state.judgment_data = None
if "use_precedents" not in st.session_state:
    st.session_state.use_precedents = True
# Dynamic input session state — new keys only
if "dyn_raw_input" not in st.session_state:
    st.session_state.dyn_raw_input = ""
if "dyn_extracted" not in st.session_state:
    st.session_state.dyn_extracted = None
if "dyn_confirmed_type" not in st.session_state:
    st.session_state.dyn_confirmed_type = None
if "dyn_step" not in st.session_state:
    st.session_state.dyn_step = 1
# dyn_step: 1=input, 2=review+confirm type, 3=ready to trial

static_tab, dynamic_tab = st.tabs(
    ["📋 Static Input", "🧠 Dynamic Input — Any Case"]
)

with static_tab:
    # ─────────────────────────────────────────────
    # PRESET CASE BUTTONS
    # ─────────────────────────────────────────────
    st.markdown("### Quick Load Example Cases")
    st.caption(
        "These cases are optimized for your Constitution + Contract + IPC + Consumer Protection books"
    )

    preset_labels = list(PRESET_CASES.keys())
    # Use up to 3 columns per row to avoid cramming
    num_cols = min(3, len(preset_labels))
    rows = [
        preset_labels[i : i + num_cols]
        for i in range(0, len(preset_labels), num_cols)
    ]

    for row_labels in rows:
        cols = st.columns(len(row_labels))
        for col, label in zip(cols, row_labels):
            if col.button(
                label, use_container_width=True, key=f"preset_{label}"
            ):
                st.session_state.selected_preset_key = label

    # Resolve selected preset
    selected_preset = None
    if (
        st.session_state.selected_preset_key
        and st.session_state.selected_preset_key in PRESET_CASES
    ):
        selected_preset = PRESET_CASES[st.session_state.selected_preset_key]

    st.divider()

    # ─────────────────────────────────────────────
    # CASE INPUT FORM
    # ─────────────────────────────────────────────
    st.markdown("### Case Details")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        case_type = st.selectbox("Case Type", SUPPORTED_CASE_TYPES, index=0)
        accused = st.text_input(
            "Accused Party",
            value=selected_preset["accused"] if selected_preset else "",
            placeholder="Name, role (e.g. Ramesh Gupta — Landlord)",
        )
        victim = st.text_input(
            "Complainant / Victim",
            value=selected_preset["victim"] if selected_preset else "",
            placeholder="Name, role (e.g. Anil Kumar — Tenant)",
        )

    with col_right:
        location = st.text_input(
            "Location",
            value=selected_preset["location"] if selected_preset else "",
            placeholder="City, State",
        )
        incident = st.text_area(
            "Describe the Incident (be specific for best results)",
            value=selected_preset["incident"] if selected_preset else "",
            height=150,
            placeholder=(
                "Describe what happened, when, what was violated, "
                "what is being claimed..."
            ),
        )

    # Unsupported case type warning
    if case_type in UNSUPPORTED_CASE_TYPES:
        st.error(
            f"'{case_type}' requires legal books not yet in our database. "
            "Results will be inaccurate. Please choose a supported case type."
        )

    # Build case string for AI
    case_string = f"""
Case Type: {case_type}
Accused: {accused}
Complainant: {victim}
Location: {location}

Facts of the Case:
{incident}
""".strip()

with dynamic_tab:
    # ── Dynamic step indicator ────────────────────────────────────────
    dyn_step = st.session_state.dyn_step
    step_info = {
        1: ("📥 Input", "#e94560"),
        2: ("🧠 Review", "#ffaa00"),
        3: ("✅ Ready", "#00ff88"),
    }
    scols = st.columns(3)
    for i, (s, (label, color)) in enumerate(step_info.items()):
        active_color = (
            color
            if s == dyn_step
            else "#00ff88"
            if s < dyn_step
            else "#333"
        )
        scols[i].markdown(
            f'<div style="text-align:center; border-bottom:3px solid '
            f'{active_color}; padding-bottom:6px;">'
            f'<span style="color:{active_color}; font-weight:bold; '
            f'font-size:13px;">{label}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════
    # DYN STEP 1 — THREE INPUT SUB-TABS
    # ════════════════════════════════════════════════════════════════
    if dyn_step == 1:
        st.markdown("#### Describe your case in any format")
        st.caption(
            "Formal, casual, Hindi-English mix — all accepted. "
            "AI will structure it automatically."
        )

        sub_text, sub_voice, sub_doc = st.tabs(
            ["✍️  Type", "🎙️  Speak", "📄  Upload"]
        )

        dyn_collected = ""

        # ── SUB TAB 1: FREE TEXT ──────────────────────────────────
        with sub_text:
            typed = st.text_area(
                "What happened? Describe freely:",
                value=st.session_state.dyn_raw_input,
                height=200,
                key="dyn_typed",
                placeholder=(
                    "Examples:\n"
                    "• 'My landlord locked me out without notice after "
                    "3 years of paying rent on time'\n"
                    "• 'Ordered iPhone on Amazon, received fake product, "
                    "they are refusing refund of ₹1.2 lakh'\n"
                    "• 'Boss terminated me same day without notice period "
                    "violating my contract'\n"
                    "• 'Someone attacked me with a rod during boundary "
                    "dispute, I have medical report and 3 witnesses'\n"
                    "• 'Insurance company rejected my father's surgery "
                    "claim of ₹8 lakhs saying pre-existing condition'"
                ),
            )
            if typed.strip():
                dyn_collected = typed
                st.session_state.dyn_raw_input = typed

        # ── SUB TAB 2: VOICE ──────────────────────────────────────
        with sub_voice:
            st.caption(
                "Speak your case. Whisper AI transcribes it locally — "
                "no internet or API key needed."
            )

            if not check_voice_dependencies():
                st.warning("⚠️ Voice input needs additional packages:")
                st.caption("Streamlit is currently running with this Python:")
                st.code(sys.executable)
                st.caption("Dependency import status (what's failing):")
                st.json(get_voice_dependency_status())
                st.code(
                    f"{sys.executable} -m pip install sounddevice faster-whisper scipy numpy",
                    language="bash",
                )
                st.caption("On macOS, if `sounddevice` fails, install PortAudio first:")
                st.code("brew install portaudio", language="bash")
                st.info(
                    "After installing, restart Streamlit. "
                    "Everything runs on your machine privately."
                )
            else:
                v_dur = st.slider(
                    "Recording duration (seconds)",
                    5,
                    30,
                    15,
                    key="dyn_voice_dur",
                )
                v1, v2 = st.columns([1, 1])

                if v1.button(
                    "🎙️ Record",
                    type="primary",
                    use_container_width=True,
                    key="dyn_record",
                ):
                    with st.spinner(
                        f"Recording {v_dur}s — speak your case now..."
                    ):
                        result = record_and_transcribe(v_dur)

                    if result.startswith("Error:"):
                        st.error(result)
                    else:
                        st.session_state.dyn_raw_input = result
                        st.success("✅ Transcribed!")
                        st.rerun()

                if v2.button(
                    "🗑️ Clear",
                    use_container_width=True,
                    key="dyn_vclear",
                ):
                    st.session_state.dyn_raw_input = ""
                    st.rerun()

                if st.session_state.dyn_raw_input:
                    ve = st.text_area(
                        "Transcribed (edit if needed):",
                        value=st.session_state.dyn_raw_input,
                        height=140,
                        key="dyn_vedit",
                    )
                    dyn_collected = ve
                    st.session_state.dyn_raw_input = ve

        # ── SUB TAB 3: DOCUMENT UPLOAD ────────────────────────────
        with sub_doc:
            st.caption(
                "Upload FIR, complaint letter, contract, legal notice. "
                "Supported: PDF, DOCX, TXT"
            )
            ufile = st.file_uploader(
                "Choose file",
                type=["pdf", "docx", "txt"],
                key="dyn_uploader",
            )
            if ufile:
                with st.spinner(f"Extracting text from {ufile.name}..."):
                    doc_text = extract_text_from_upload(ufile)

                if doc_text.startswith("Error") or doc_text.startswith(
                    "Unsupported"
                ):
                    st.error(doc_text)
                else:
                    st.success(
                        f"✅ Extracted {len(doc_text)} chars "
                        f"from {ufile.name}"
                    )
                    de = st.text_area(
                        "Extracted text (edit if needed):",
                        value=doc_text,
                        height=180,
                        key="dyn_docedit",
                    )
                    dyn_collected = de
                    st.session_state.dyn_raw_input = de

        # ── ANALYZE BUTTON ────────────────────────────────────────
        st.markdown("---")
        final_dyn = (
            dyn_collected.strip() or st.session_state.dyn_raw_input.strip()
        )

        if final_dyn:
            st.info(f"📝 {len(final_dyn)} characters ready to analyze")

            if st.button(
                "🧠 Analyze & Structure My Case  →",
                type="primary",
                key="dyn_analyze",
            ):
                with st.spinner(
                    "AI is reading and structuring your case "
                    "(10–20 seconds)..."
                ):
                    details = extract_case_details(final_dyn)
                    st.session_state.dyn_extracted = details
                    st.session_state.dyn_raw_input = final_dyn
                    st.session_state.dyn_step = 2
                st.rerun()
        else:
            st.warning(
                "⬆️ Describe your case using one of the three methods above."
            )

    # ════════════════════════════════════════════════════════════════
    # DYN STEP 2 — REVIEW AI ANALYSIS + MANUAL CASE TYPE SELECTION
    # ════════════════════════════════════════════════════════════════
    elif dyn_step == 2:
        details = st.session_state.dyn_extracted
        if not details:
            st.session_state.dyn_step = 1
            st.rerun()

        st.markdown("#### 🧠 AI Analysis — Review & Confirm Case Type")

        # Confidence badge
        conf = details.get("confidence", "LOW").upper()
        conf_map = {
            "HIGH": ("#00ff88", "🟢"),
            "MEDIUM": ("#ffaa00", "🟡"),
            "LOW": ("#ff4444", "🔴"),
        }
        c_color, c_icon = conf_map.get(conf, ("#888", "⚪"))
        st.markdown(
            f'<span style="color:{c_color}; font-weight:bold;">'
            f"{c_icon} AI Confidence: {conf}</span>",
            unsafe_allow_html=True,
        )

        if conf == "LOW" or details.get("missing_info"):
            st.warning(
                "⚠️ AI was uncertain about some details. "
                "Please review and edit below."
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Two columns: details (editable) | case type selector
        left, right = st.columns([3, 2])

        with left:
            st.markdown("**📋 Extracted Details — Edit if wrong:**")

            e_accused = st.text_input(
                "🔴 Accused Party",
                value=details.get("accused", ""),
                key="dyn_e_accused",
            )
            e_victim = st.text_input(
                "🟢 Complainant / Victim",
                value=details.get("victim", ""),
                key="dyn_e_victim",
            )
            e_location = st.text_input(
                "📍 Location",
                value=details.get("location", "India"),
                key="dyn_e_location",
            )
            e_incident = st.text_area(
                "📄 Formal Incident Description",
                value=details.get("incident", ""),
                height=180,
                key="dyn_e_incident",
                help=(
                    "AI rewrote your description in formal legal language. "
                    "Edit freely."
                ),
            )

            if details.get("missing_info"):
                with st.expander(
                    f"⚠️ {len(details['missing_info'])} unclear field(s)"
                ):
                    for item in details["missing_info"]:
                        st.caption(f"• {item}")

        with right:
            st.markdown("**⚖️ Select Case Type (required):**")
            st.caption(
                "AI suggests a type but **you must confirm it manually**. "
                "This determines which law books are searched."
            )

            # AI suggestion box
            suggested = details.get(
                "ai_suggested_case_type", "General Legal Dispute"
            )
            reason = details.get("suggestion_reason", "")

            st.markdown(
                f"""
            <div style="background:#1a2332; border:1px solid #3d6b9e;
            border-radius:8px; padding:12px 14px; margin-bottom:14px;">
                <p style="color:#79c0ff; font-size:11px; margin:0 0 4px 0;">
                    🤖 AI SUGGESTS:
                </p>
                <p style="color:#e6edf3; font-size:14px;
                          font-weight:bold; margin:0 0 4px 0;">
                    {suggested}
                </p>
                <p style="color:#8b949e; font-size:11px; margin:0;">
                    {reason}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            try:
                def_idx = ALL_CASE_TYPES.index(suggested)
            except ValueError:
                def_idx = 0

            # THE MANDATORY MANUAL SELECTOR
            selected_type = st.selectbox(
                "Your Selection (you must choose):",
                options=ALL_CASE_TYPES,
                index=def_idx,
                key="dyn_manual_type",
                help=(
                    "AI suggestion shown above. "
                    "You MUST confirm or change before proceeding."
                ),
            )

            # Show books that will be searched
            books_hint = CASE_BOOKS_HINT.get(selected_type, "All books")
            st.markdown(
                f'<div style="background:#0d2818; border:1px solid #238636;'
                f'border-radius:6px; padding:8px 12px; margin-top:8px;">'
                f'<p style="color:#3fb950; font-size:11px; margin:0 0 2px 0;">'
                f"📚 BOOKS TO BE SEARCHED:</p>"
                f'<p style="color:#adbac7; font-size:12px; margin:0;">'
                f"{books_hint}</p></div>",
                unsafe_allow_html=True,
            )

            # Show case type description
            desc = CASE_TYPE_DESCRIPTIONS.get(selected_type, "")
            if desc:
                st.caption(f"ℹ️ {desc}")

        st.markdown("---")

        b1, b2, b3 = st.columns([2, 2, 1])

        if b1.button(
            "✅ Confirm & Proceed to Trial  →",
            type="primary",
            use_container_width=True,
            key="dyn_confirm",
        ):
            st.session_state.dyn_confirmed_type = selected_type
            st.session_state.dyn_extracted.update(
                {
                    "accused": e_accused,
                    "victim": e_victim,
                    "location": e_location,
                    "incident": e_incident,
                }
            )
            st.session_state.dyn_step = 3
            st.rerun()

        if b2.button(
            "✏️ Go Back & Edit Input",
            use_container_width=True,
            key="dyn_back",
        ):
            st.session_state.dyn_step = 1
            st.session_state.dyn_extracted = None
            st.rerun()

        if b3.button(
            "🔄 Reset", use_container_width=True, key="dyn_reset2"
        ):
            st.session_state.dyn_raw_input = ""
            st.session_state.dyn_extracted = None
            st.session_state.dyn_confirmed_type = None
            st.session_state.dyn_step = 1
            st.rerun()

    # ════════════════════════════════════════════════════════════════
    # DYN STEP 3 — TRIAL READY
    # ════════════════════════════════════════════════════════════════
    elif dyn_step == 3:
        details = st.session_state.dyn_extracted
        case_type_dyn = st.session_state.dyn_confirmed_type

        if not details or not case_type_dyn:
            st.session_state.dyn_step = 1
            st.rerun()

        dyn_case_string = build_case_string(case_type_dyn, details)

        # Case summary card
        st.markdown("#### ✅ Case Ready for Trial")
        st.markdown(
            f"""
        <div style="background:#0d2818; border:1px solid #238636;
        border-radius:10px; padding:16px 20px; margin-bottom:20px;">
            <table style="width:100%;">
                <tr>
                    <td style="color:#8b949e; width:130px; padding:4px 0;
                               font-size:12px;">⚖️ Case Type</td>
                    <td style="color:#3fb950; font-weight:bold;
                               font-size:13px;">{case_type_dyn}</td>
                </tr>
                <tr>
                    <td style="color:#8b949e; padding:4px 0;
                               font-size:12px;">🔴 Accused</td>
                    <td style="color:#ffa657;
                               font-size:12px;">{details.get('accused','?')}</td>
                </tr>
                <tr>
                    <td style="color:#8b949e; padding:4px 0;
                               font-size:12px;">🟢 Complainant</td>
                    <td style="color:#79c0ff;
                               font-size:12px;">{details.get('victim','?')}</td>
                </tr>
                <tr>
                    <td style="color:#8b949e; padding:4px 0;
                               font-size:12px;">📍 Location</td>
                    <td style="color:#cdd9e5;
                               font-size:12px;">{details.get('location','India')}</td>
                </tr>
            </table>
            <div style="background:#162c1c; border-radius:6px;
            padding:10px 12px; margin-top:10px;">
                <p style="color:#8b949e; font-size:11px;
                          margin:0 0 4px 0;">📄 INCIDENT</p>
                <p style="color:#cdd9e5; font-size:12px; margin:0;
                          line-height:1.6;">
                    {details.get('incident','').replace(chr(10), '<br>')}
                </p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Buttons
        tc, ec, rc = st.columns([2, 2, 1])

        dyn_start_trial = tc.button(
            "🔨 COMMENCE TRIAL",
            type="primary",
            use_container_width=True,
            key="dyn_start_trial",
        )

        if ec.button(
            "✏️ Edit Details",
            use_container_width=True,
            key="dyn_edit_back",
        ):
            st.session_state.dyn_step = 2
            st.rerun()

        if rc.button(
            "🔄 Reset", use_container_width=True, key="dyn_reset3"
        ):
            st.session_state.dyn_raw_input = ""
            st.session_state.dyn_extracted = None
            st.session_state.dyn_confirmed_type = None
            st.session_state.dyn_step = 1
            st.rerun()

        # ── TRIAL EXECUTION — reuses existing trial logic ────────
        if dyn_start_trial:
            # Override case details for trial execution
            st.session_state.case_details = {
                "type": case_type_dyn,
                "accused": details.get("accused", "Unknown"),
                "victim": details.get("victim", "Unknown"),
                "location": details.get("location", "India"),
                "incident": details.get("incident", ""),
            }

            st.markdown("---")
            st.markdown("## 🏛️ TRIAL IN PROGRESS")

            with st.status(
                "📚 Retrieving relevant laws...", expanded=True
            ) as sts:
                context_data_dyn = retrieve_legal_context(
                    dyn_case_string,
                    case_type=case_type_dyn,
                    k=8,
                )
                st.write(
                    f"✅ {context_data_dyn['total_chunks']} excerpts — "
                    + ", ".join(context_data_dyn["books_searched"])
                )
                sts.update(label="✅ Laws retrieved!", state="complete")

            st.session_state.legal_context = context_data_dyn

            # Prosecution
            st.markdown(
                '<p class="badge-prosecution">'
                "⚔️ PROSECUTION IS ARGUING...</p>",
                unsafe_allow_html=True,
            )
            p_msgs = build_prosecutor_message(
                dyn_case_string, context_data_dyn["formatted"]
            )
            prosecution_full_dyn = ""
            pp = st.empty()
            for token in stream_agent(p_msgs):
                prosecution_full_dyn += token
                pp.markdown(prosecution_full_dyn + "▌")
            pp.markdown(prosecution_full_dyn)
            st.session_state.prosecution_text = prosecution_full_dyn

            time.sleep(1)

            # Defense
            st.markdown(
                '<p class="badge-defense">'
                "🛡️ DEFENSE IS RESPONDING...</p>",
                unsafe_allow_html=True,
            )
            d_msgs = build_defense_message(
                dyn_case_string,
                context_data_dyn["formatted"],
                prosecution_full_dyn,
            )
            defense_full_dyn = ""
            dp = st.empty()
            for token in stream_agent(d_msgs):
                defense_full_dyn += token
                dp.markdown(defense_full_dyn + "▌")
            dp.markdown(defense_full_dyn)
            st.session_state.defense_text = defense_full_dyn

            time.sleep(2)

            # Judge
            st.markdown(
                '<p class="badge-judge">'
                "👨‍⚖️ COURT DELIVERS VERDICT...</p>",
                unsafe_allow_html=True,
            )
            j_msgs = build_judge_message(
                dyn_case_string, prosecution_full_dyn, defense_full_dyn
            )
            verdict_full_dyn = ""
            jp = st.empty()
            for token in stream_agent(j_msgs):
                verdict_full_dyn += token
                jp.markdown(verdict_full_dyn + "▌")
            jp.markdown(verdict_full_dyn)
            st.session_state.verdict_text = verdict_full_dyn
            st.session_state.trial_complete = True
            st.balloons()

        # PDF Export
        if st.session_state.trial_complete:
            st.markdown("---")
            with st.spinner("Preparing transcript..."):
                pdf_bytes_dyn = generate_transcript_pdf(
                    case_details=st.session_state.case_details,
                    prosecution_text=st.session_state.prosecution_text,
                    defense_text=st.session_state.defense_text,
                    verdict_text=st.session_state.verdict_text,
                    sources=st.session_state.legal_context.get(
                        "sources", []
                    ),
                )
            st.download_button(
                "📄 Download Trial Transcript (PDF)",
                data=pdf_bytes_dyn,
                file_name=f"trial_{int(time.time())}.pdf",
                mime="application/pdf",
            )

# ─────────────────────────────────────────────
# TRIAL START BUTTON
# ─────────────────────────────────────────────
st.markdown("")
start_col, _, reset_col = st.columns([2, 3, 1])

start_trial = start_col.button(
    "COMMENCE TRIAL",
    type="primary",
    use_container_width=True,
    disabled=not incident.strip(),
)

if reset_col.button("Reset", use_container_width=True):
    st.session_state.trial_complete = False
    st.session_state.prosecution_text = ""
    st.session_state.defense_text = ""
    st.session_state.verdict_text = ""
    st.session_state.selected_preset_key = None
    st.rerun()

# ─────────────────────────────────────────────
# TRIAL EXECUTION
# ─────────────────────────────────────────────
if start_trial and incident.strip():
    st.session_state.trial_complete = False

    # Store case details for PDF export
    st.session_state.case_details = {
        "type": case_type,
        "accused": accused,
        "victim": victim,
        "location": location,
        "incident": incident,
    }

    st.markdown("---")
    st.markdown("## Trial In Progress")

    # STEP 1: RAG Retrieval
    with st.status("📚 Retrieving relevant laws from legal database...", expanded=True) as status:
        st.write(f"📋 Case type detected: **{case_type}**")
        st.write(f"🔍 Searching relevant books for this case type...")

        context_data = retrieve_legal_context(case_string, case_type=case_type, k=8)
        st.session_state.legal_context = context_data

        # Show which books were searched
        BOOK_ICONS = {
            "constitution": "📜 Constitution of India",
            "contract":     "📋 Contract & Specific Relief",
            "ipc":          "⚔️ Indian Penal Code",
            "consumer":     "🛒 Consumer Protection Act",
        }
        for book in context_data["books_searched"]:
            count = len(context_data["chunks_by_book"].get(book, []))
            icon_name = BOOK_ICONS.get(book, book)
            st.write(f"  {icon_name}: {count} excerpts found")

        st.write(f"✅ Total: {context_data['total_chunks']} legal excerpts retrieved")
        status.update(label="✅ Legal context retrieved!", state="complete")

    # Show source chips
    st.markdown("**Sources Retrieved:**")
    CHIP_COLORS = {
        "constitution": "#1e3a5f",
        "contract":     "#1a3a1a",
        "ipc":          "#3a1a1a",
        "consumer":     "#2d1f00",
    }
    chips_html = ""
    for src in context_data['sources']:
        color = CHIP_COLORS.get(src.get('book_key', ''), '#333')
        chips_html += (
            f'<span style="display:inline-block; background:{color}; '
            f'color:#eee; padding:4px 10px; border-radius:20px; '
            f'font-size:12px; margin:3px; border:1px solid #666;">'
            f'📄 {src["book_name"]} — Page {src["page"]}</span>'
        )
    st.markdown(chips_html, unsafe_allow_html=True)

    st.markdown("---")

    # Build precedent context string
    precedent_ctx = ""
    if (
        st.session_state.use_precedents
        and st.session_state.judgment_data
        and st.session_state.judgment_data.get("precedent_context")
    ):
        precedent_ctx = st.session_state.judgment_data["precedent_context"]

    # STEP 2: Prosecution
    st.markdown(
        '<p class="badge-prosecution">PROSECUTION IS ARGUING...</p>',
        unsafe_allow_html=True,
    )

    prosecution_messages = build_prosecutor_message(
        case=case_string,
        legal_context=context_data["formatted"],
        precedent_context=precedent_ctx,
    )

    prosecution_full = ""
    with st.container():
        prosecution_stream_placeholder = st.empty()

        for token in stream_agent(prosecution_messages):
            prosecution_full += token
            prosecution_stream_placeholder.markdown(prosecution_full + "▌")
            time.sleep(0.01)

        prosecution_stream_placeholder.markdown(prosecution_full)

    st.session_state.prosecution_text = prosecution_full

    # Brief dramatic pause
    time.sleep(1)

    # STEP 3: Defense
    st.markdown(
        '<p class="badge-defense">DEFENSE IS RESPONDING...</p>',
        unsafe_allow_html=True,
    )

    defense_messages = build_defense_message(
        case=case_string,
        legal_context=context_data["formatted"],
        prosecution_argument=prosecution_full,
        precedent_context=precedent_ctx,
    )

    defense_full = ""
    with st.container():
        defense_stream_placeholder = st.empty()

        for token in stream_agent(defense_messages):
            defense_full += token
            defense_stream_placeholder.markdown(defense_full + "▌")
            time.sleep(0.01)

        defense_stream_placeholder.markdown(defense_full)

    st.session_state.defense_text = defense_full

    time.sleep(1)

    # STEP 4: Judge Verdict
    st.markdown("---")
    st.markdown(
        '<p class="badge-judge">THE COURT WILL NOW DELIVER ITS VERDICT...</p>',
        unsafe_allow_html=True,
    )
    time.sleep(2)  # Extra dramatic pause before verdict

    judge_messages = build_judge_message(
        case_string,
        prosecution_full,
        defense_full,
    )

    verdict_full = ""
    with st.container():
        verdict_stream_placeholder = st.empty()

        for token in stream_agent(judge_messages):
            verdict_full += token
            verdict_stream_placeholder.markdown(verdict_full + "▌")
            time.sleep(0.015)

        verdict_stream_placeholder.markdown(verdict_full)

    st.session_state.verdict_text = verdict_full
    st.session_state.trial_complete = True

    st.balloons()

# ─────────────────────────────────────────────
# SHOW PREVIOUS TRIAL + EXPORT (if complete)
# ─────────────────────────────────────────────
if st.session_state.trial_complete:
    st.markdown("---")

    export_col, _ = st.columns([1, 3])

    with export_col:
        with st.spinner("Preparing transcript PDF..."):
            pdf_bytes = generate_transcript_pdf(
                case_details=st.session_state.case_details,
                prosecution_text=st.session_state.prosecution_text,
                defense_text=st.session_state.defense_text,
                verdict_text=st.session_state.verdict_text,
                sources=st.session_state.legal_context.get("sources", []),
            )

        st.download_button(
            label="Download Full Trial Transcript (PDF)",
            data=pdf_bytes,
            file_name=f"trial_transcript_{int(time.time())}.pdf",
            mime="application/pdf",
            type="secondary",
            use_container_width=True,
        )

    # Expandable legal sources
    with st.expander("View Legal Sources Used in This Trial"):
        for i, src in enumerate(
            st.session_state.legal_context.get("sources", []), 1
        ):
            st.markdown(f"**[{i}]** `{src['source']}` — Page {src['page']}")
            st.caption(src["preview"])
            st.divider()
