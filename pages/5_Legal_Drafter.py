import time
from datetime import datetime

import streamlit as st

from drafter.document_types import DOCUMENT_TYPES, detect_document_type
from drafter.field_extractor import extract_fields_for_document
from drafter.document_generator import (
    generate_document_text,
    generate_whatsapp_version,
)
from drafter.pdf_generator import generate_pdf
from drafter.docx_generator import generate_docx


st.set_page_config(
    page_title="📝 Legal Document Drafter",
    page_icon="📝",
    layout="wide",
)

st.markdown(
    """
<style>
    .main { background-color: #0a0a0f; }

    .drafter-header {
        text-align: center;
        padding: 28px 20px;
        background: linear-gradient(
            135deg, #0d1117 0%, #161b22 50%, #1c2128 100%
        );
        border-radius: 14px;
        border: 1px solid #30363d;
        margin-bottom: 28px;
    }

    .doc-card {
        background: linear-gradient(145deg, #0d1117, #161b22);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        cursor: pointer;
        transition: all 0.2s;
        text-align: center;
        height: 160px;
    }
    .doc-card:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }

    .field-missing {
        background: #2d1a00;
        border: 1px solid #f39c12;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 12px;
        color: #ffa657;
    }

    .field-ok {
        background: #0d2818;
        border: 1px solid #238636;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 12px;
        color: #3fb950;
    }

    .document-preview {
        background: #ffffff;
        color: #1a1a1a;
        border: 1px solid #cccccc;
        border-top: 3px solid #1a1a2e;
        border-radius: 0px;
        padding: 48px 56px;
        font-family: 'Times New Roman', Times, serif;
        font-size: 12.5px;
        line-height: 2.0;
        white-space: pre-wrap;
        max-height: 750px;
        overflow-y: auto;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
        letter-spacing: 0.01em;
    }

    .whatsapp-box {
        background: #075e54;
        color: white;
        border-radius: 10px;
        padding: 16px 20px;
        font-family: monospace;
        font-size: 12px;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
    }

    .step-indicator {
        display: flex;
        justify-content: center;
        gap: 8px;
        margin: 16px 0;
    }

    #MainMenu {visibility: hidden;}
    footer    {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="drafter-header">
    <h1 style="color:#58a6ff; margin:0; font-size:2.2rem;">
        📝 Legal Document Drafter
    </h1>
    <p style="color:#8b949e; margin:8px 0 0 0; font-size:1rem;">
        Describe your problem in plain language → Get a ready-to-submit 
        legal document with correct Indian law citations
    </p>
    <p style="color:#3fb950; font-size:0.85rem; margin:6px 0 0 0;">
        FIR • Legal Notice • RTI Application • Consumer Complaint • Bail Application
    </p>
</div>
""",
    unsafe_allow_html=True,
)

defaults = {
    "drafter_step": 1,
    "drafter_raw_input": "",
    "drafter_doc_type": None,
    "drafter_fields": None,
    "drafter_doc_text": None,
    "drafter_whatsapp": None,
    "drafter_confirmed_type": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

step = st.session_state.drafter_step
steps = {
    1: ("📥", "Describe Problem"),
    2: ("⚖️", "Select Doc Type"),
    3: ("📋", "Review Fields"),
    4: ("📄", "Generated Document"),
}
step_cols = st.columns(4)
for i, (s, (icon, label)) in enumerate(steps.items()):
    color = (
        "#3fb950"
        if s < step
        else "#58a6ff"
        if s == step
        else "#30363d"
    )
    step_cols[i].markdown(
        f'<div style="text-align:center; border-bottom:3px solid {color};'
        f'padding-bottom:8px;">'
        f'<span style="font-size:20px;">{icon}</span><br>'
        f'<span style="color:{color}; font-size:11px; '
        f'font-weight:{"bold" if s==step else "normal"};">'
        f"{label}</span></div>",
        unsafe_allow_html=True,
    )
st.markdown("<br>", unsafe_allow_html=True)

if step == 1:
    st.markdown("### 📥 Describe Your Problem")
    st.caption(
        "Write in plain language — casual, formal, or Hindi-English mix. "
        "The more detail you give, the better the document."
    )

    st.markdown("**What kind of document do you need? (for reference)**")
    card_cols = st.columns(5)
    for i, (dtype, config) in enumerate(DOCUMENT_TYPES.items()):
        with card_cols[i]:
            st.markdown(
                f"""
            <div class="doc-card" style="border-color:{config['color']}22;">
                <div style="font-size:28px; margin-bottom:8px;">
                    {config['icon']}
                </div>
                <div style="color:#e6edf3; font-size:12px; font-weight:bold;
                            margin-bottom:6px;">{dtype}</div>
                <div style="color:#8b949e; font-size:10px; line-height:1.4;">
                    {config['description']}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    QUICK_EXAMPLES = {
        "🔒 Landlord Locked Me Out": (
            "My landlord Suresh Gupta forcefully locked me out of my rented "
            "flat in Pune without any notice. I have been paying ₹18,000 rent "
            "monthly for 3 years. He changed locks while I was at work and my "
            "belongings are inside. I have rent receipts. I want to send him a "
            "legal notice demanding re-entry and return of my deposit of ₹54,000."
        ),
        "📱 Fake Product Online": (
            "I ordered an iPhone 15 Pro from Amazon India for ₹1,34,900 but "
            "received a cheap fake Chinese phone. Amazon is refusing refund "
            "saying the seller is responsible. The seller account is now deleted. "
            "I have unboxing video proof. I want to file a consumer complaint."
        ),
        "💊 Insurance Rejected": (
            "My father had heart bypass surgery costing ₹9,50,000. Our HDFC "
            "Ergo health insurance rejected the claim saying pre-existing "
            "condition. Agent had assured coverage. I need to file consumer "
            "complaint against insurance company for deficiency of service."
        ),
        "🏛️ Government Job Denied": (
            "I topped the Maharashtra state civil engineering recruitment exam "
            "but was not appointed. Lower scoring candidates were selected. "
            "I want to file RTI to get the complete selection list, marks of "
            "all candidates, and the criteria used for final selection."
        ),
        "⚡ Property Attack": (
            "My neighbour Vijay Kumar attacked me with an iron rod during a "
            "boundary dispute yesterday evening in our colony in Delhi. I have "
            "a fractured left arm and head injuries needing 12 stitches. Three "
            "neighbours witnessed this. Hospital has treated me. I want to file "
            "FIR against Vijay Kumar for grievous hurt."
        ),
    }

    st.markdown("**⚡ Quick Examples:**")
    ex_cols = st.columns(len(QUICK_EXAMPLES))
    for i, (label, text) in enumerate(QUICK_EXAMPLES.items()):
        if ex_cols[i].button(label, use_container_width=True, key=f"ex_{i}"):
            st.session_state.drafter_raw_input = text
            st.rerun()

    raw_input = st.text_area(
        "Your Problem:",
        value=st.session_state.drafter_raw_input,
        height=200,
        key="drafter_input",
        placeholder=(
            "Describe what happened in as much detail as possible:\n"
            "• Who did what to you?\n"
            "• When and where did it happen?\n"
            "• What do you want — refund, arrest, information, bail?\n"
            "• Any evidence, witnesses, amounts involved?\n\n"
            "Example: 'My employer TechCorp fired me without notice on "
            "15th March. My contract says 3 months notice. They owe me "
            "₹2,40,000 salary for 3 months. I want to send a legal notice.'"
        ),
    )

    if raw_input.strip():
        st.session_state.drafter_raw_input = raw_input

    st.markdown("---")

    if st.session_state.drafter_raw_input.strip():
        char_count = len(st.session_state.drafter_raw_input)
        quality = (
            "🟢 Good detail"
            if char_count > 300
            else "🟡 Add more detail for better results"
            if char_count > 100
            else "🔴 Very brief — add more information"
        )
        st.caption(f"{char_count} characters | {quality}")

        if st.button(
            "🧠 Detect Document Type  →",
            type="primary",
            key="detect_btn",
        ):
            detected, confidence = detect_document_type(
                st.session_state.drafter_raw_input
            )
            st.session_state.drafter_doc_type = detected
            st.session_state.drafter_step = 2
            st.rerun()
    else:
        st.warning("⬆️ Please describe your problem above first.")

elif step == 2:
    st.markdown("### ⚖️ Select Document Type")

    detected_type = st.session_state.drafter_doc_type
    detected, confidence = detect_document_type(
        st.session_state.drafter_raw_input
    )
    doc_config = DOCUMENT_TYPES[detected]

    st.markdown(
        f"""
    <div style="background:#1a2332; border:2px solid #3d6b9e;
    border-radius:12px; padding:20px 24px; margin-bottom:24px;">
        <p style="color:#79c0ff; font-size:12px; margin:0 0 6px 0;">
            🤖 AI SUGGESTS:
        </p>
        <h2 style="color:#e6edf3; margin:0 0 8px 0; font-size:1.8rem;">
            {doc_config['icon']} {detected}
        </h2>
        <p style="color:#adbac7; font-size:13px; margin:0 0 12px 0;">
            {doc_config['description']}
        </p>
        <p style="color:#8b949e; font-size:11px; margin:0;">
            Authority: {doc_config['authority']} &nbsp;|&nbsp;
            Under: {doc_config['act']}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(f"**Common uses for {detected}:**")
    use_cols = st.columns(min(len(doc_config["use_cases"]), 4))
    for i, use in enumerate(doc_config["use_cases"]):
        use_cols[i % 4].markdown(
            f'<div style="background:#21262d; border-radius:6px; '
            f'padding:6px 10px; margin:3px 0; font-size:11px; '
            f'color:#cdd9e5;">✓ {use}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Your Selection (you MUST confirm or change):**")

    selected_cols = st.columns(len(DOCUMENT_TYPES))

    for i, (dtype, config) in enumerate(DOCUMENT_TYPES.items()):
        is_selected = dtype == detected
        border_color = config["color"] if is_selected else "#30363d"

        with selected_cols[i]:
            st.markdown(
                f"""
            <div style="
                background:{'#1a2332' if is_selected else '#0d1117'};
                border:2px solid {border_color};
                border-radius:10px; padding:14px; text-align:center;
                height:130px;
            ">
                <div style="font-size:24px;">{config['icon']}</div>
                <div style="color:#e6edf3; font-size:11px;
                            font-weight:bold; margin-top:6px;">
                    {dtype}
                </div>
                {'<div style="color:#3fb950; font-size:10px; margin-top:4px;">✓ DETECTED</div>' if is_selected else ''}
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Select {config['icon']}",
                key=f"select_{dtype}",
                use_container_width=True,
            ):
                st.session_state.drafter_confirmed_type = dtype
                st.session_state.drafter_step = 3
                st.rerun()

    st.markdown("---")
    b1, _ = st.columns([1, 4])
    if b1.button("← Go Back", use_container_width=True, key="step2_back"):
        st.session_state.drafter_step = 1
        st.rerun()

elif step == 3:
    doc_type = st.session_state.drafter_confirmed_type
    doc_config = DOCUMENT_TYPES[doc_type]

    st.markdown(f"### {doc_config['icon']} Extracting Fields for {doc_type}")

    if not st.session_state.drafter_fields:
        with st.spinner(
            f"AI is extracting all required fields for {doc_type}... "
            "(15-30 seconds)"
        ):
            fields = extract_fields_for_document(
                st.session_state.drafter_raw_input,
                doc_type,
            )
            st.session_state.drafter_fields = fields
        st.rerun()

    fields = st.session_state.drafter_fields

    missing_fields = [
        k
        for k, v in fields.items()
        if "NOT PROVIDED" in str(v) and not k.startswith("_")
    ]
    complete_fields = [
        k
        for k, v in fields.items()
        if "NOT PROVIDED" not in str(v) and not k.startswith("_")
    ]

    col_stats1, col_stats2, col_stats3 = st.columns(3)
    col_stats1.metric("✅ Fields Extracted", len(complete_fields))
    col_stats2.metric("⚠️ Fields Missing", len(missing_fields))
    col_stats3.metric(
        "🎯 Completion",
        f"{int(len(complete_fields)/max(len(fields),1)*100)}%",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("**📋 Review and Edit Fields:**")
    st.caption(
        "AI extracted these from your description. "
        "Fill in missing fields for best results. All fields are editable."
    )

    required_fields = doc_config["required_fields"]
    edited_fields = dict(fields)

    field_cols = st.columns(2)
    for i, field in enumerate(required_fields):
        current_val = fields.get(field, "NOT PROVIDED — please fill manually")
        is_missing = "NOT PROVIDED" in str(current_val)
        label = field.replace("_", " ").title()
        col = field_cols[i % 2]

        with col:
            if is_missing:
                col.markdown(
                    f'<div class="field-missing">⚠️ {label} — not found</div>',
                    unsafe_allow_html=True,
                )
            else:
                col.markdown(
                    f'<div class="field-ok">✓ {label}</div>',
                    unsafe_allow_html=True,
                )

            if field in [
                "incident_description",
                "grievance_description",
                "information_sought",
                "defect_description",
                "bail_grounds",
                "case_facts",
                "communication_attempts",
                "relief_sought",
            ]:
                edited_val = col.text_area(
                    label,
                    value=current_val if not is_missing else "",
                    key=f"field_{field}",
                    height=100,
                )
            else:
                edited_val = col.text_input(
                    label,
                    value=current_val if not is_missing else "",
                    key=f"field_{field}",
                )

            if edited_val:
                edited_fields[field] = edited_val

    st.markdown("**📚 Applicable Legal Sections:**")
    applicable = fields.get("applicable_sections", [])
    applicable_str = (
        ", ".join(applicable)
        if isinstance(applicable, list)
        else str(applicable)
    )
    edited_applicable = st.text_input(
        "Legal Sections (edit if needed)",
        value=applicable_str,
        key="field_applicable",
    )
    edited_fields["applicable_sections"] = edited_applicable

    st.session_state.drafter_fields = edited_fields

    st.markdown("---")
    b1, _, b2 = st.columns([1, 3, 1])

    if b1.button("← Back", use_container_width=True, key="step3_back"):
        st.session_state.drafter_step = 2
        st.session_state.drafter_fields = None
        st.rerun()

    if b2.button(
        "✍️ Generate Document  →",
        type="primary",
        use_container_width=True,
        key="generate_btn",
    ):
        st.session_state.drafter_step = 4
        st.rerun()

elif step == 4:
    doc_type = st.session_state.drafter_confirmed_type
    fields = st.session_state.drafter_fields
    doc_config = DOCUMENT_TYPES[doc_type]

    if not st.session_state.drafter_doc_text:
        with st.spinner(
            f"Drafting your {doc_type} with correct legal citations... "
            "(20-40 seconds)"
        ):
            doc_text = generate_document_text(doc_type, fields)
            st.session_state.drafter_doc_text = doc_text

    if not st.session_state.drafter_whatsapp:
        with st.spinner("Generating WhatsApp version..."):
            wa_text = generate_whatsapp_version(
                st.session_state.drafter_doc_text,
                doc_type,
            )
            st.session_state.drafter_whatsapp = wa_text

    doc_text = st.session_state.drafter_doc_text
    wa_text = st.session_state.drafter_whatsapp

    st.markdown(f"### Your {doc_type} is Ready")
    st.success(
        "Document drafted successfully. "
        "Review the preview below before downloading."
    )

    st.markdown("#### Download Options")
    dl1, dl2, dl3, dl4 = st.columns(4)

    with dl1:
        with st.spinner("Preparing PDF..."):
            pdf_bytes = generate_pdf(doc_type, doc_text, fields)
        st.download_button(
            "Download PDF\n(Print Ready)",
            data=pdf_bytes,
            file_name=(
                f"{doc_type.replace(' ','_')}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    with dl2:
        with st.spinner("Preparing Word doc..."):
            docx_bytes = generate_docx(doc_type, doc_text, fields)
        st.download_button(
            "Download Word\n(Editable)",
            data=docx_bytes,
            file_name=(
                f"{doc_type.replace(' ','_')}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
            use_container_width=True,
        )

    with dl3:
        st.download_button(
            "Download Text\n(Plain)",
            data=doc_text,
            file_name=(
                f"{doc_type.replace(' ','_')}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            ),
            mime="text/plain",
            use_container_width=True,
        )

    with dl4:
        st.download_button(
            "WhatsApp\nVersion",
            data=wa_text,
            file_name=f"whatsapp_{doc_type.replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("---")

    preview_tab, wa_tab, sections_tab = st.tabs(
        ["Document Preview", "WhatsApp Version", "Legal Sections Used"]
    )

    with preview_tab:
        st.markdown(
            f'<div class="document-preview">{doc_text}</div>',
            unsafe_allow_html=True,
        )

    with wa_tab:
        st.caption(
            "Copy this text and send via WhatsApp as a formal notice "
            "before filing the full document."
        )
        st.markdown(
            f'<div class="whatsapp-box">{wa_text}</div>',
            unsafe_allow_html=True,
        )
        st.code(wa_text, language=None)

    with sections_tab:
        applicable = fields.get("applicable_sections", [])
        st.markdown("**Sections cited in your document:**")
        if isinstance(applicable, list):
            for sec in applicable:
                st.markdown(
                    f'<div class="field-ok">{sec}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div class="field-ok">{applicable}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**All sections for this document type:**")
        for label, section in doc_config["ipc_sections"].items():
            st.markdown(
                f'<div style="background:#21262d; border-radius:6px; '
                f'padding:8px 12px; margin:4px 0; font-size:12px; '
                f'color:#cdd9e5;"><b style="color:#79c0ff;">{label}:</b>'
                f" {section}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    st.warning(
        "**Important:** This document is AI-generated for reference "
        "and drafting assistance. It does not constitute legal advice. "
        "Please review with a qualified advocate before submission. "
        "Verify all law section numbers independently."
    )

    ac1, ac2, ac3 = st.columns(3)
    if ac1.button(
        "Edit Fields and Regenerate", use_container_width=True
    ):
        st.session_state.drafter_doc_text = None
        st.session_state.drafter_whatsapp = None
        st.session_state.drafter_step = 3
        st.rerun()

    if ac2.button(
        "Draft Another Document",
        use_container_width=True,
        type="primary",
    ):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

    if ac3.button("Start Over", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()
