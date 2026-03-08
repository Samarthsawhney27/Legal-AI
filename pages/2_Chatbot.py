import streamlit as st
import streamlit.components.v1 as components
import time
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
import chromadb


def nav_to(page_path: str):
    """Navigate to a page using JS redirect (works on all Streamlit versions)."""
    name = os.path.splitext(os.path.basename(page_path))[0]
    js = f'<script>window.parent.location.href = "/{name}"</script>'
    components.html(js, height=0)

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Legal Chatbot",
    page_icon="💬",
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

    .info-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1565c0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize environment variables
model = os.environ.get("MODEL", "llama3.2")
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
persist_directory = os.environ.get("PERSIST_DIRECTORY", "db")
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS', 4))

# Initialize embeddings and database
try:
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    db = Chroma(
        client=chroma_client,
        collection_name="legal_docs",
        embedding_function=embeddings,
        persist_directory=persist_directory
    )
    retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
    
    # Initialize LLM
    raw_host = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
    if not raw_host.startswith("http"):
        ollama_base = f"http://{raw_host}"
    else:
        ollama_base = raw_host
    llm = OllamaLLM(model=model, base_url=ollama_base)
    
    system_ready = True
except Exception as e:
    system_ready = False
    error_message = str(e)

# Header with back button
col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    if st.button("← Back to Main", use_container_width=True):
        nav_to("Legal_AI_RAG.py")
with col2:
    st.markdown('<div class="main-header"><h1>Legal Chatbot</h1><p>Ask general legal questions</p></div>', unsafe_allow_html=True)
with col3:
    st.empty()

# System status
if system_ready:
    st.success("System ready - Knowledge base loaded")
else:
    st.error(f"System error: {error_message}")
    st.markdown('<div class="info-box">Please make sure you have ingested documents first using the ingest.py script.</div>', unsafe_allow_html=True)

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# Sidebar
with st.sidebar:
    st.markdown("### System Information")
    if system_ready:
        st.markdown(f"""
        **Model:** `{model}`  
        **Embeddings:** `{embeddings_model_name}`  
        **Target chunks:** `{target_source_chunks}`  
        **Messages:** {len(st.session_state.chat_messages)}
        """)
        
        # Clear chat button
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    else:
        st.warning("System not ready. Check configuration.")

# Welcome message
if not st.session_state.chat_messages and system_ready:
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": "Hello. I am your Legal Assistant. I can help you understand legal concepts, terminology, and general legal principles based on the knowledge base. What would you like to know?"
    })

# Display chat messages
for message in st.session_state.chat_messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message assistant-message"><strong>Legal Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)

# Chat input
if system_ready:
    if prompt := st.chat_input("Ask your legal question here..."):
        if not st.session_state.processing:
            st.session_state.processing = True
            
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Generate response
            with st.spinner("Processing..."):
                try:
                    # Retrieve relevant documents
                    docs = retriever.invoke(prompt)
                    
                    # Combine retrieved context
                    context = "\n\n".join([doc.page_content for doc in docs])
                    
                    # Create prompt for LLM
                    qa_prompt = f"""You are a professional legal assistant specializing in Indian law and governance.
    
    Your role:
    - Help users understand Indian legal concepts, terminology, and constitutional provisions
    - Answer questions specifically about Indian law, Indian Constitution, and Indian legal system
    - Provide explanations of Indian legal principles, statutes, and procedures
    - Offer guidance on legal research approaches within Indian jurisdiction
    
    IMPORTANT RESTRICTIONS:
    - Focus ONLY on Indian law, the Indian Constitution, and Indian governance
    - Do NOT provide information about USA, UK, or any other country's legal systems
    - If a question is about non-Indian legal systems, politely redirect to Indian law
    - Only use the provided context which contains Indian legal documents
    
    Instructions:
    1) Use precise, professional language.
    2) If unsure or context is insufficient, state this clearly.
    3) Do NOT provide specific legal advice.
    4) Include a disclaimer that this is not legal advice for specific situations.
    5) Provide structured, clear explanations.
    6) If asked about non-Indian legal matters, politely state: "I specialize in Indian law only. Please ask questions related to the Indian Constitution, Indian statutes, or Indian legal system."
    
    Legal Context (Indian Law):
    {context}
    
    User Question: {prompt}
    
    Answer:"""
                    
                    response = llm.invoke(qa_prompt)
                    
                    # Add assistant response
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                except Exception as e:
                    error_response = f"I encountered an error: {str(e)}"
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": error_response
                    })
                finally:
                    st.session_state.processing = False
                    st.rerun()
else:
    st.info("Chatbot is not available. Please check system configuration and ensure documents have been ingested.")

# Help section
st.markdown("---")
st.markdown("### Example Questions")
st.markdown("""
Here are some example questions you can ask:

- What is a contract and what are its essential elements?
- Explain the difference between a tort and a crime
- What is consideration in contract law?
- How does intellectual property protection work?
- What are the basic principles of negligence law?
- Explain the concept of due diligence
- What is the statute of limitations?
- How are legal precedents used in common law?

**Note**: This chatbot provides general legal information based on the ingested knowledge base, not specific legal advice. Always consult with qualified legal professionals for your specific situation.
""", unsafe_allow_html=True)
