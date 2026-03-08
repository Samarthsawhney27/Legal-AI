import streamlit as st
import streamlit.components.v1 as components
import io
import time
from pypdf import PdfReader
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv
import os


def nav_to(page_path: str):
    """Navigate to a page using JS redirect (works on all Streamlit versions)."""
    name = os.path.splitext(os.path.basename(page_path))[0]
    js = f'<script>window.parent.location.href = "/{name}"</script>'
    components.html(js, height=0)

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Document Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .summary-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1a237e;
        margin: 1rem 0;
    }

    .feature-button {
        background: #1a237e;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }

    .feature-button:hover {
        background: #0d47a1;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

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
""", unsafe_allow_html=True)

# Initialize LLM
model = os.environ.get("MODEL", "llama3.2")
raw_host = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
if not raw_host.startswith("http"):
    ollama_base = f"http://{raw_host}"
else:
    ollama_base = raw_host
llm = OllamaLLM(model=model, base_url=ollama_base)

# Header with back button
col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    if st.button("← Back to Main", use_container_width=True):
        nav_to("Legal_AI_RAG.py")
with col2:
    st.markdown('<div class="main-header"><h1>Document Summarizer</h1><p>Get concise summaries of legal documents</p></div>', unsafe_allow_html=True)
with col3:
    st.empty()

# Initialize session state
if "summary_history" not in st.session_state:
    st.session_state.summary_history = []
if "current_doc_text" not in st.session_state:
    st.session_state.current_doc_text = None

# Sidebar for history
with st.sidebar:
    st.markdown("### Summary History")
    if st.session_state.summary_history:
        for i, item in enumerate(st.session_state.summary_history):
            with st.expander(f"Summary {i+1} - {item['filename']}"):
                st.write(f"**Generated:** {item['timestamp']}")
                st.write(f"**Length:** {len(item['summary'])} characters")
                if st.button(f"View Summary {i+1}", key=f"view_{i}"):
                    st.session_state.current_summary = item['summary']
                    st.session_state.current_filename = item['filename']
    else:
        st.info("No summaries yet. Upload a document to get started!")

    if st.button("Clear History", use_container_width=True):
        st.session_state.summary_history = []
        st.rerun()

# Main content
st.markdown("### Upload Legal Document")

uploaded_file = st.file_uploader(
    "Choose a legal document (PDF or TXT)",
    type=["pdf", "txt"],
    key="summarizer_upload"
)

if uploaded_file is not None:
    # Extract text from uploaded file
    def extract_text_from_file(file):
        filename = file.name.lower()
        if filename.endswith(".txt"):
            try:
                return file.getvalue().decode("utf-8", errors="ignore")
            except Exception:
                return file.getvalue().decode("latin-1", errors="ignore")
        elif filename.endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(file.getvalue()))
                pages_text = []
                for page in reader.pages:
                    pages_text.append(page.extract_text() or "")
                return "\n".join(pages_text).strip()
            except Exception as e:
                st.error(f"Error reading PDF: {str(e)}")
                return ""
        return ""

    with st.spinner("Reading document..."):
        doc_text = extract_text_from_file(uploaded_file)
        st.session_state.current_doc_text = doc_text

    if st.session_state.current_doc_text:
        st.success(f"Document loaded: {uploaded_file.name}")
        st.info(f"Document length: {len(st.session_state.current_doc_text)} characters")

        # Show document preview
        with st.expander("Document Preview"):
            st.text_area("Document Content", st.session_state.current_doc_text[:2000] + "..." if len(st.session_state.current_doc_text) > 2000 else st.session_state.current_doc_text, height=200, disabled=True)

        # Summarize button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Generate Summary", type="primary", use_container_width=True, key="generate_summary"):
                with st.spinner("Analyzing document..."):
                    try:
                        summary_prompt = (
                            "You are a legal assistant. Summarize the following document in clear bullet points. "
                            "Focus on: parties, key definitions, obligations, payment terms, confidentiality/IP, "
                            "termination, liability/indemnity, warranties, dispute resolution, governing law, and deadlines. "
                            "Keep it concise and neutral. If content seems insufficient, say so.\n\n"
                            f"Document:\n{st.session_state.current_doc_text[:12000]}\n\nSummary:"
                        )
                        
                        summary = llm.invoke(summary_prompt)
                        
                        # Store in history
                        st.session_state.summary_history.append({
                            'filename': uploaded_file.name,
                            'summary': summary,
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'doc_length': len(st.session_state.current_doc_text)
                        })
                        
                        # Display summary
                        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
                        st.markdown("### Document Summary")
                        st.write(summary)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Error generating summary: {str(e)}")
    else:
        st.error("Unable to extract text from the uploaded file. Please try a different file.")

# Display current summary if selected from history
if "current_summary" in st.session_state:
    st.markdown("---")
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown(f"### Summary of: {st.session_state.current_filename}")
    st.write(st.session_state.current_summary)
    st.markdown('</div>', unsafe_allow_html=True)

