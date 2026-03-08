import streamlit as st
import streamlit.components.v1 as components


def nav_to(page_path: str):
    """Navigate to a page using JS redirect (works on all Streamlit versions)."""
    # In Streamlit multipage apps, pages are at /PageName
    # e.g. pages/1_Summarizer.py -> /1_Summarizer
    import os
    name = os.path.splitext(os.path.basename(page_path))[0]
    js = f'<script>window.parent.location.href = "/{name}"</script>'
    components.html(js, height=0)

# Set page configuration
# Set page configuration
st.set_page_config(
    page_title="Legal Assistant Platform",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
        padding: 3rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }

    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        height: 100%;
        text-align: center;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        text-align: center;
        color: #1a237e;
    }

    .feature-title {
        color: #333;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }

    .feature-description {
        color: #666;
        line-height: 1.6;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .feature-button {
        background: #1a237e;
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        height: 3rem;
        font-size: 1rem;
    }

    .feature-button:hover {
        background: #0d47a1;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    .subtitle {
        color: #f0f0f0;
        font-size: 1.2rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <h1>Legal Assistant Platform</h1>
    <p class="subtitle">Your professional legal document companion</p>
</div>
""", unsafe_allow_html=True)

# Introduction
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <h2 style="color: #333;">Choose Your Service</h2>
    <p style="color: #666; font-size: 1.1rem;">
        Select from our specialized tools designed to help you analyze and understand legal documents.
    </p>
</div>
""", unsafe_allow_html=True)

# Feature Cards in Grid
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">Document Summarizer</div>
        <div class="feature-description">
            Upload legal documents and get concise, accurate summaries. Extract key points, obligations, rights, and important clauses in plain language.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Summarizer", key="summarizer_btn", use_container_width=True):
        nav_to("pages/1_Summarizer.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">Legal Chatbot</div>
        <div class="feature-description">
            Ask general legal questions and get responses based on your knowledge base. Get help with legal concepts, terminology, and guidance.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Chatbot", key="chatbot_btn", use_container_width=True):
        nav_to("pages/2_Chatbot.py")

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">Document Q&A</div>
        <div class="feature-description">
            Upload specific legal documents and ask detailed questions about them. Get precise answers based on the content of your uploaded documents.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Document Q&A", key="doc_qa_btn", use_container_width=True):
        nav_to("pages/3_Document_QA.py")

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">Courtroom Simulator</div>
        <div class="feature-description">
            Simulate an AI-powered courtroom trial. Prosecution, Defense, and Judge AI agents argue your case using real Indian law retrieved from the knowledge base.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Courtroom Simulator", key="courtroom_btn", use_container_width=True):
        nav_to("pages/4_Courtroom_Simulator.py")

# Add Legal Document Drafter card
col5, col6 = st.columns(2)

with col5:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">Legal Document Drafter</div>
        <div class="feature-description">
            FIR · Legal Notice · RTI · Consumer Complaint · Bail Application —
            drafted with correct law sections, ready to print and file.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Legal Drafter", key="drafter_btn", use_container_width=True):
        nav_to("pages/5_Legal_Drafter.py")

# Additional Information
st.markdown("---")

col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h4 style="color: #667eea;">🔐 Privacy First</h4>
        <p style="color: #666;">All processing happens locally on your machine. Your documents never leave your system.</p>
    </div>
    """, unsafe_allow_html=True)

with col_info2:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h4 style="color: #667eea;">⚡ Fast & Efficient</h4>
        <p style="color: #666;">Get instant responses with our optimized AI models and vector database.</p>
    </div>
    """, unsafe_allow_html=True)

with col_info3:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h4 style="color: #667eea;">🎯 Legal Focused</h4>
        <p style="color: #666;">Specialized prompts and models trained for legal document analysis.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>⚠️ This tool is for educational purposes only and does not constitute legal advice.</p>
    <p>Always consult with qualified legal professionals for legal matters.</p>
</div>
""", unsafe_allow_html=True)