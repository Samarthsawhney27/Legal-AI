import json
import os
import io
import time

from dotenv import load_dotenv

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
import chromadb

import streamlit as st
from pypdf import PdfReader
from constants import PERSIST_DIRECTORY

# Load environment variables from .env file
load_dotenv()

# Set up environment variables
model = os.environ.get("MODEL", "llama3.2")
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
persist_directory = os.environ.get("PERSIST_DIRECTORY", "db")
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS', 8))

# Page configuration with enhanced styling
st.set_page_config(
    page_title="Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Sidebar styling */
    .sidebar-section {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }

    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        animation: fadeIn 0.5s ease-in;
    }

    .user-message {
        background: #e3f2fd;
        border-left-color: #2196f3;
    }

    .assistant-message {
        background: #f1f8e9;
        border-left-color: #4caf50;
    }

    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Status indicators */
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 0.5rem 0;
    }

    .status-error {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 0.5rem 0;
    }

    .status-info {
        background: #cce7ff;
        color: #004085;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #abd8ff;
        margin: 0.5rem 0;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize the embeddings and database
embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

# Initialize ChromaDB with error handling for schema compatibility
try:
    # New Chroma client per migration guide
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    db = Chroma(
        client=chroma_client,
        collection_name="legal_docs",
        embedding_function=embeddings,
        persist_directory=persist_directory
    )
    retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
except (ValueError, Exception) as e:
    # If database schema is incompatible, recreate it
    if "tenant" in str(e).lower() or "no such table" in str(e).lower():
        import shutil
        import os
        # Backup old database if it exists
        if os.path.exists(persist_directory):
            backup_dir = f"{persist_directory}_backup"
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.move(persist_directory, backup_dir)
        # Recreate database
        chroma_client = chromadb.PersistentClient(path=persist_directory)
        db = Chroma(
            client=chroma_client,
            collection_name="legal_docs",
            embedding_function=embeddings,
            persist_directory=persist_directory
        )
        retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
    else:
        raise

# Initialize the LLM with correct base URL/host
raw_host = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
if not raw_host.startswith("http"):
    ollama_base = f"http://{raw_host}"
else:
    ollama_base = raw_host
llm = Ollama(model=model, base_url=ollama_base)

# Prompt template (Legal Assistant)
prompt_template = """You are Lex, a clear, careful, and neutral legal assistant.

Your role:
- Help summarize legal documents and explain key points in plain language
- Answer questions strictly based on the provided context and retrieved materials
- Highlight obligations, rights, definitions, risks, deadlines, and governing law/jurisdiction when relevant
- Provide actionable, neutral guidance without offering legal advice

Instructions:
1) Use precise, legally-aware language, but explain in simple terms
2) If unsure or context is insufficient, say so and request clarification
3) Do NOT speculate beyond the provided context
4) If user asks for advice, include a short disclaimer that this is not legal advice
5) Prefer bullet points for summaries and keep responses concise

Legal Context: {context}

User Question: {question}

Answer:"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# Initialize the QA chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

# --- Helper functions for on-the-fly legal document analysis (no DB persistence) ---
def extract_text_from_uploaded_file(uploaded_file) -> str:
    """Extract text from uploaded PDF or TXT files"""
    filename = uploaded_file.name.lower()
    if filename.endswith(".txt"):
        try:
            return uploaded_file.getvalue().decode("utf-8", errors="ignore")
        except Exception:
            return uploaded_file.getvalue().decode("latin-1", errors="ignore")
    if filename.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
            pages_text = []
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")
            return "\n".join(pages_text).strip()
        except Exception:
            return ""
    # Unsupported type
    return ""


def summarize_legal_text(document_text: str) -> str:
    """Generate a summary of legal document text"""
    if not document_text.strip():
        return "I couldn't read any text from the uploaded document."
    summary_prompt = (
        "You are a legal assistant. Summarize the following document in clear bullet points. "
        "Focus on: parties, key definitions, obligations, payment terms, confidentiality/IP, "
        "termination, liability/indemnity, warranties, dispute resolution, governing law, and deadlines. "
        "Keep it concise and neutral. If content seems insufficient, say so.\n\n"
        f"Document:\n{document_text[:12000]}\n\nSummary:"
    )
    return llm(summary_prompt)


def answer_question_about_legal_text(document_text: str, question: str) -> str:
    """Answer a question about the uploaded legal document"""
    if not document_text.strip():
        return "I couldn't read any text from the uploaded document."
    qa_prompt = (
        "You are a legal assistant answering strictly from the provided document text. "
        "If the answer is not found, say you cannot find it. Provide a concise, neutral answer.\n\n"
        f"Document:\n{document_text[:12000]}\n\nQuestion: {question}\n\nAnswer:"
    )
    return llm(qa_prompt)


def legal_qa(query: str) -> str:
    """Process legal queries using the RAG system"""
    result = qa(query)
    return result['result']


# Main UI Header
st.markdown('<div class="main-header"><h1>⚖️ Legal Assistant</h1><p>Your AI-powered legal document companion</p></div>',
            unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_doc_text" not in st.session_state:
    st.session_state.uploaded_doc_text = None
if "last_processed_prompt" not in st.session_state:
    st.session_state.last_processed_prompt = None
if "processing" not in st.session_state:
    st.session_state.processing = False

# Add a welcome message if chat is empty
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 Hi! I'm Lex, your AI Legal Assistant. Upload a legal document to summarize or ask questions, or type a general legal question about contracts, agreements, or legal concepts."
    })

# --- MAIN: Document Analysis (moved from sidebar) ---
st.markdown("### 📄 Analyze a Legal Document")
uploaded_doc = st.file_uploader(
    "Upload a legal document (PDF or TXT). It won't be saved to the database.",
    type=["pdf", "txt"],
    key="uploaded_doc_main"
)

col_sum, col_q = st.columns(2)

if uploaded_doc is not None:
    with st.spinner("📄 Reading document..."):
        doc_text = extract_text_from_uploaded_file(uploaded_doc)
        st.session_state.uploaded_doc_text = doc_text

    if st.session_state.uploaded_doc_text:
        st.success("Document loaded for analysis (not stored).")

        with col_sum:
            if st.button("📝 Generate Summary", key="gen_summary_btn"):
                with st.spinner("✍️ Summarizing..."):
                    summary = summarize_legal_text(st.session_state.uploaded_doc_text)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": summary
                    })
        with col_q:
            doc_question = st.text_input("Ask a question about the uploaded document", key="uploaded_doc_question_main")
            if st.button("❓ Ask About Document", key="ask_about_doc_btn") and doc_question:
                with st.spinner("🔎 Analyzing document..."):
                    answer = answer_question_about_legal_text(st.session_state.uploaded_doc_text, doc_question)
                    st.session_state.messages.append({
                        "role": "user",
                        "content": doc_question
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
    else:
        st.warning("Unable to extract text from the uploaded file. Please try a different file.")
else:
    st.info("Upload a PDF or TXT to enable summarization and Q&A.")

# --- Display Chat Messages ---
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    else:
        with st.chat_message("assistant"):
            st.write(message["content"])

# --- SIDEBAR: System info and controls ---
with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### ℹ️ System Information")
    with st.expander("📊 View System Details"):
        st.markdown(f"""
        **🤖 Model:** `{model}`  
        **🔍 Embeddings:** `{embeddings_model_name}`  
        **📚 Target chunks:** `{target_source_chunks}`  
        **💬 Messages:** {len(st.session_state.messages)}
        """)
    if st.button("🗑️ Clear Chat History", help="Clear all messages and reset conversation", use_container_width=True, key="clear_chat_btn"):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👋 Hi! I'm Lex, your AI Legal Assistant. Upload a legal document to summarize or ask questions, or type a general legal question about contracts, agreements, or legal concepts."
        }]
        st.session_state.uploaded_doc_text = None
        st.session_state.last_processed_prompt = None
        st.session_state.processing = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN AREA: Text Input ---
if prompt := st.chat_input("💬 Type your legal question here..."):
    # Create a unique identifier for this prompt using timestamp
    prompt_id = f"{prompt}_{time.time()}"
    
    # Only process if this is a genuinely new prompt and we're not already processing
    if prompt != st.session_state.last_processed_prompt and not st.session_state.processing:
        # Mark as processing to prevent duplicate runs
        st.session_state.processing = True
        st.session_state.last_processed_prompt = prompt
        
        # Add user message to chat immediately
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": time.time()
        }
        st.session_state.messages.append(user_message)
        
        # Generate response
        with st.spinner("🤔 Analyzing your legal question..."):
            try:
                # Call legal_qa with the fresh prompt - ensure it's not cached
                full_response = legal_qa(prompt)
                
                # Add assistant response to chat
                assistant_message = {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": time.time()
                }
                st.session_state.messages.append(assistant_message)
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": time.time()
                })
            finally:
                # Reset processing flag after a small delay to ensure state is saved
                st.session_state.processing = False


if __name__ == "__main__":
    pass