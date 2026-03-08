import streamlit as st
import streamlit.components.v1 as components
import io
import time
from pypdf import PdfReader
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
import tempfile
import uuid


def nav_to(page_path: str):
    """Navigate to a page using JS redirect (works on all Streamlit versions)."""
    name = os.path.splitext(os.path.basename(page_path))[0]
    js = f'<script>window.parent.location.href = "/{name}"</script>'
    components.html(js, height=0)

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Document Q&A",
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

    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        animation: fadeIn 0.5s ease-in;
    }

    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #1565c0;
    }

    .assistant-message {
        background: #f5f5f5;
        border-left: 4px solid #2e7d32;
    }

    .document-info {
        background: #e8eaf6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1a237e;
        margin: 1rem 0;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
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

# Initialize embeddings
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

# Header with back button
col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    if st.button("← Back to Main", use_container_width=True):
        nav_to("Legal_AI_RAG.py")
with col2:
    st.markdown('<div class="main-header"><h1>Document Q&A</h1><p>Ask questions about your uploaded documents</p></div>', unsafe_allow_html=True)
with col3:
    st.empty()

# Initialize session state
if "doc_text" not in st.session_state:
    st.session_state.doc_text = None
if "doc_name" not in st.session_state:
    st.session_state.doc_name = None
if "doc_vectorstore" not in st.session_state:
    st.session_state.doc_vectorstore = None
if "doc_chunks_count" not in st.session_state:
    st.session_state.doc_chunks_count = 0
if "doc_messages" not in st.session_state:
    st.session_state.doc_messages = []

# Sidebar for document info
with st.sidebar:
    st.markdown("### Document Information")
    
    if st.session_state.doc_name:
        st.markdown(f"""
        <div class="document-info">
            <strong>Current Document:</strong><br>
            {st.session_state.doc_name}<br><br>
            <strong>Statistics:</strong><br>
            • Characters: {len(st.session_state.doc_text) if st.session_state.doc_text else 0:,}<br>
            • Chunks: {st.session_state.doc_chunks_count}<br>
            • Messages: {len(st.session_state.doc_messages)}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Clear Document & Chat", use_container_width=True):
            st.session_state.doc_text = None
            st.session_state.doc_name = None
            st.session_state.doc_vectorstore = None
            st.session_state.doc_chunks_count = 0
            st.session_state.doc_messages = []
            st.rerun()
    else:
        st.info("No document uploaded yet")

# Main content area
st.markdown("### Upload Document")

uploaded_file = st.file_uploader(
    "Choose a legal document (PDF or TXT)",
    type=["pdf", "txt"],
    help="Upload a document to ask questions about it using AI"
)

if uploaded_file is not None:
    # Check if this is a new document
    if st.session_state.doc_name != uploaded_file.name:
        
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


        with st.spinner("Processing document..."):
            # Extract text
            doc_text = extract_text_from_file(uploaded_file)
            
            if doc_text:
                # Split into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                )
                chunks = text_splitter.split_text(doc_text)
                
                # Create temporary directory for this document's vector store
                temp_dir = os.path.join(tempfile.gettempdir(), f"doc_qa_{uuid.uuid4().hex}")
                
                # Create vector store using Chroma
                vectorstore = Chroma.from_texts(
                    texts=chunks,
                    embedding=embeddings,
                    persist_directory=temp_dir
                )
                
                # Update session state
                st.session_state.doc_text = doc_text
                st.session_state.doc_name = uploaded_file.name
                st.session_state.doc_vectorstore = vectorstore
                st.session_state.doc_chunks_count = len(chunks)
                st.session_state.doc_messages = [{
                    "role": "assistant",
                    "content": f"Document '{uploaded_file.name}' processed successfully.\n\nStatistics:\n• {len(doc_text):,} characters\n• {len(chunks)} chunks created\n\nYou can now ask questions about this document."
                }]
                
                st.success(f"Document processed: {uploaded_file.name}")
                st.rerun()
            else:
                st.error("Unable to extract text from the uploaded file. Please try a different file.")

# Q&A Section
if st.session_state.doc_vectorstore is not None:
    st.markdown("---")
    st.markdown("### Ask Questions")
    
    # Display chat messages BEFORE the input widget
    for message in st.session_state.doc_messages:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    
    # Chat input comes AFTER message display
    if question := st.chat_input("Ask a question about the document..."):
        # Add user question
        st.session_state.doc_messages.append({
            "role": "user",
            "content": question
        })
        
        # Generate answer using RAG
        with st.spinner("Searching document..."):
            try:
                # Retrieve relevant chunks
                relevant_docs = st.session_state.doc_vectorstore.similarity_search(question, k=4)
                
                # Combine retrieved context
                context = "\n\n".join([doc.page_content for doc in relevant_docs])
                
                # Create prompt for LLM
                qa_prompt = f"""You are a professional assistant analyzing a document. Answer the question based ONLY on the provided context from the document.

If the answer is not in the context, say "I cannot find this information in the document."

Be concise and accurate. Use quotes from the document when relevant.

Context from document:
{context}

Question: {question}

Answer:"""
                
                # Get answer from LLM
                answer = llm.invoke(qa_prompt)
                
                # Add assistant answer
                st.session_state.doc_messages.append({
                    "role": "assistant",
                    "content": answer
                })
                
                # Force rerun to show the new messages
                st.rerun()
                
            except Exception as e:
                error_response = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.doc_messages.append({
                    "role": "assistant",
                    "content": error_response
                })
                st.rerun()
else:
    st.info("Please upload a document above to start asking questions.")
    
    # Example questions
    st.markdown("---")
    st.markdown("### Example Questions")
    st.markdown("""
    Once you upload a document, you can ask questions like:
    
    - What is the main topic of this document?
    - Summarize the key points
    - What does it say about [specific topic]?
    - Are there any deadlines mentioned?
    - Who are the parties involved?
    - What are the main obligations?
    
    The AI will search through your document and provide accurate answers based on the content.
    """)
