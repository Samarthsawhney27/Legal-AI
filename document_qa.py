import streamlit as st
import io
import time
from pypdf import PdfReader
from langchain_community.llms import Ollama
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Document Q&A - Legal AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        animation: fadeIn 0.5s ease-in;
    }

    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }

    .assistant-message {
        background: #f1f8e9;
        border-left: 4px solid #4caf50;
    }

    .document-info {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .back-button {
        background: #6c757d;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        text-decoration: none;
        display: inline-block;
        margin-bottom: 1rem;
    }

    .back-button:hover {
        background: #5a6268;
        text-decoration: none;
        color: white;
    }

    .qa-history {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
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
llm = Ollama(model=model, base_url=ollama_base)

# Header with back button
col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    st.markdown('<a href="http://localhost:8501" class="back-button">← Back</a>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="main-header"><h1>📄 Document Q&A</h1><p>Ask questions about your uploaded documents</p></div>', unsafe_allow_html=True)
with col3:
    st.empty()

# Initialize session state
if "doc_qa_history" not in st.session_state:
    st.session_state.doc_qa_history = []
if "current_document" not in st.session_state:
    st.session_state.current_document = None
if "current_doc_text" not in st.session_state:
    st.session_state.current_doc_text = None
if "doc_qa_messages" not in st.session_state:
    st.session_state.doc_qa_messages = []

# Sidebar for document info and history
with st.sidebar:
    st.markdown("### 📄 Document Information")
    
    if st.session_state.current_document:
        st.markdown(f"""
        <div class="document-info">
            <strong>Current Document:</strong><br>
            {st.session_state.current_document}<br><br>
            <strong>Length:</strong> {len(st.session_state.current_doc_text) if st.session_state.current_doc_text else 0} characters<br>
            <strong>Q&A Sessions:</strong> {len([h for h in st.session_state.doc_qa_history if h['filename'] == st.session_state.current_document])}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No document uploaded yet")
    
    st.markdown("### 📜 Q&A History")
    if st.session_state.doc_qa_history:
        for i, item in enumerate(st.session_state.doc_qa_history[-5:]):  # Show last 5 sessions
            with st.expander(f"{item['filename']} - {item['timestamp']}"):
                st.write(f"**Questions:** {len(item['qa_pairs'])}")
                for j, qa in enumerate(item['qa_pairs'][:3]):  # Show first 3 Q&A
                    st.write(f"Q{j+1}: {qa['question'][:50]}...")
                if len(item['qa_pairs']) > 3:
                    st.write(f"... and {len(item['qa_pairs']) - 3} more")
    else:
        st.info("No Q&A sessions yet")
    
    if st.button("🗑️ Clear All History", use_container_width=True):
        st.session_state.doc_qa_history = []
        st.session_state.doc_qa_messages = []
        st.rerun()

# Main content area
st.markdown("### 📄 Upload Document for Q&A")

uploaded_file = st.file_uploader(
    "Choose a legal document (PDF or TXT)",
    type=["pdf", "txt"],
    key="doc_qa_upload"
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

    with st.spinner("📄 Reading document..."):
        doc_text = extract_text_from_file(uploaded_file)
        
    if doc_text:
        # Update session state
        st.session_state.current_document = uploaded_file.name
        st.session_state.current_doc_text = doc_text
        st.session_state.doc_qa_messages = [{
            "role": "assistant",
            "content": f"📄 Document '{uploaded_file.name}' loaded successfully! You can now ask questions about this document. The document contains {len(doc_text)} characters."
        }]
        
        st.success(f"Document loaded: {uploaded_file.name}")
        st.info(f"Document length: {len(doc_text)} characters")
        
        # Show document preview
        with st.expander("📖 Document Preview"):
            st.text_area("Document Content", doc_text[:2000] + "..." if len(doc_text) > 2000 else doc_text, height=200, disabled=True)
    else:
        st.error("Unable to extract text from the uploaded file. Please try a different file.")

# Q&A Section
if st.session_state.current_doc_text:
    st.markdown("---")
    st.markdown("### 💬 Ask Questions About This Document")
    
    # Display chat messages
    for message in st.session_state.doc_qa_messages:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    
    # Chat input
    if question := st.chat_input("💬 Ask a question about the document..."):
        # Add user question
        st.session_state.doc_qa_messages.append({
            "role": "user",
            "content": question
        })
        
        # Generate answer
        with st.spinner("🔎 Analyzing document..."):
            try:
                qa_prompt = (
                    "You are a legal assistant answering strictly from the provided document text. "
                    "If the answer is not found in the document, say so clearly. "
                    "Provide a concise, neutral answer based only on the document content. "
                    "Include relevant quotes or references from the document when possible.\n\n"
                    f"Document:\n{st.session_state.current_doc_text[:12000]}\n\n"
                    f"Question: {question}\n\nAnswer:"
                )
                
                answer = llm(qa_prompt)
                
                # Add assistant answer
                st.session_state.doc_qa_messages.append({
                    "role": "assistant",
                    "content": answer
                })
                
                # Update history
                current_session = None
                for session in st.session_state.doc_qa_history:
                    if session['filename'] == st.session_state.current_document:
                        current_session = session
                        break
                
                if current_session is None:
                    current_session = {
                        'filename': st.session_state.current_document,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'qa_pairs': []
                    }
                    st.session_state.doc_qa_history.append(current_session)
                
                current_session['qa_pairs'].append({
                    'question': question,
                    'answer': answer,
                    'timestamp': time.strftime("%H:%M:%S")
                })
                
                st.rerun()
                
            except Exception as e:
                error_response = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.doc_qa_messages.append({
                    "role": "assistant",
                    "content": error_response
                })
                st.rerun()
else:
    st.info("Please upload a document to start asking questions.")

# Instructions
st.markdown("---")
st.markdown("### 💡 How to Use Document Q&A")
st.markdown("""
1. **Upload Document**: Choose a PDF or TXT file containing legal content
2. **Wait for Processing**: The system will extract and analyze the text
3. **Ask Questions**: Type specific questions about the document content
4. **Get Answers**: Receive responses based only on the uploaded document
5. **Review History**: Access previous Q&A sessions in the sidebar

**Example Questions:**
- "What are the key obligations in this contract?"
- "Who are the parties mentioned in this document?"
- "What is the termination clause?"
- "What jurisdiction governs this agreement?"
- "What are the payment terms?"

**Note**: Answers are based solely on the document content. This tool is for educational purposes only and does not constitute legal advice.
""", unsafe_allow_html=True)
