import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        text-align: center;
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
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }

    .feature-button:hover {
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
    <h1>⚖️ Legal AI Assistant</h1>
    <p class="subtitle">Your AI-powered legal document companion</p>
</div>
""", unsafe_allow_html=True)

# Introduction
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <h2 style="color: #333;">Choose Your Legal Assistant Service</h2>
    <p style="color: #666; font-size: 1.1rem;">
        Select from our specialized AI-powered legal tools designed to help you understand, analyze, and get answers from legal documents.
    </p>
</div>
""", unsafe_allow_html=True)

# Feature Cards in Grid
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝\n\nDocument Summarizer\n\n\nUpload legal documents and get concise, accurate summaries", key="summarizer_btn", use_container_width=True):
        st.switch_page("pages/1_📝_Summarizer.py")

with col2:
    if st.button("💬\n\nLegal Chatbot\n\n\nAsk general legal questions and get AI-powered responses", key="chatbot_btn", use_container_width=True):
        st.switch_page("pages/2_💬_Chatbot.py")

with col3:
    if st.button("📄\n\nDocument Q&A\n\n\nUpload specific legal documents and ask detailed questions", key="doc_qa_btn", use_container_width=True):
        st.switch_page("pages/3_📄_Document_Q&A.py")

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
