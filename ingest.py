#!/usr/bin/env python3
import os
import glob
import shutil
import requests
import streamlit as st
import pandas as pd
from typing import List
from multiprocessing import Pool
from tqdm import tqdm
from datetime import datetime
import tempfile
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time
import math

# LangChain imports
from langchain.document_loaders import (
    CSVLoader,
    EverNoteLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredEmailLoader,
    UnstructuredEPubLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredODTLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

import chromadb


# Constants / helpers for Chroma client
def get_chroma_client(persist_directory):
    return chromadb.PersistentClient(path=persist_directory)


# Configuration
class Config:
    def __init__(self):
        self.persist_directory = 'db'
        self.source_directory = 'source_documents'
        self.embeddings_model_name = 'all-MiniLM-L6-v2'
        self.chunk_size = 500
        self.chunk_overlap = 50
        self.scraped_directory = 'scraped_documents'
        self.batch_size = 1000  # Maximum batch size for ChromaDB

    def update_directories(self, source_dir, persist_dir):
        self.source_directory = source_dir
        self.persist_directory = persist_dir
        # Create directories if they don't exist
        os.makedirs(self.source_directory, exist_ok=True)
        os.makedirs(self.persist_directory, exist_ok=True)
        os.makedirs(self.scraped_directory, exist_ok=True)


config = Config()


# Custom document loaders
class MyElmLoader(UnstructuredEmailLoader):
    """Wrapper to fallback to text/plain when default does not work"""

    def load(self) -> List[Document]:
        """Wrapper adding fallback for elm without html"""
        try:
            try:
                doc = UnstructuredEmailLoader.load(self)
            except ValueError as e:
                if 'text/html content not found in email' in str(e):
                    # Try plain text
                    self.unstructured_kwargs["content_source"] = "text/plain"
                    doc = UnstructuredEmailLoader.load(self)
                else:
                    raise
        except Exception as e:
            # Add file_path to exception message
            raise type(e)(f"{self.file_path}: {e}") from e

        return doc


# Map file extensions to document loaders and their arguments
LOADER_MAPPING = {
    ".csv": (CSVLoader, {}),
    ".doc": (UnstructuredWordDocumentLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".enex": (EverNoteLoader, {}),
    ".eml": (MyElmLoader, {}),
    ".epub": (UnstructuredEPubLoader, {}),
    ".html": (UnstructuredHTMLLoader, {}),
    ".md": (UnstructuredMarkdownLoader, {}),
    ".odt": (UnstructuredODTLoader, {}),
    ".pdf": (PyMuPDFLoader, {}),
    ".ppt": (UnstructuredPowerPointLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}),
}


class WebScraper:
    def __init__(self, max_pages=10, delay=1):
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def get_page_content(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            st.error(f"Error fetching {url}: {str(e)}")
            return None

    def extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text
        text = soup.get_text()

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def scrape_website(self, url, save_directory):
        if not self.is_valid_url(url):
            st.error("Invalid URL provided")
            return False

        try:
            # Create filename from URL
            parsed_url = urlparse(url)
            filename = f"{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filename = filename.replace('__', '_').strip('_')

            # Get page content
            html_content = self.get_page_content(url)
            if not html_content:
                return False

            # Extract text
            text_content = self.extract_text_from_html(html_content)

            # Save to file
            file_path = os.path.join(save_directory, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(text_content)

            st.success(f"Successfully scraped and saved: {filename}")
            return True

        except Exception as e:
            st.error(f"Error scraping website: {str(e)}")
            return False


def load_single_document(file_path: str) -> List[Document]:
    ext = "." + file_path.rsplit(".", 1)[-1].lower()
    if ext in LOADER_MAPPING:
        loader_class, loader_args = LOADER_MAPPING[ext]
        loader = loader_class(file_path, **loader_args)
        return loader.load()

    raise ValueError(f"Unsupported file extension '{ext}'")


def load_documents(source_dir: str, ignored_files: List[str] = []) -> List[Document]:
    """
    Loads all documents from the source documents directory, ignoring specified files
    """
    all_files = []
    for ext in LOADER_MAPPING:
        all_files.extend(
            glob.glob(os.path.join(source_dir, f"**/*{ext}"), recursive=True)
        )
    filtered_files = [file_path for file_path in all_files if file_path not in ignored_files]

    if not filtered_files:
        return []

    # For Streamlit, we'll use single processing to avoid issues
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, file_path in enumerate(filtered_files):
        try:
            status_text.text(f'Loading document {i + 1}/{len(filtered_files)}: {os.path.basename(file_path)}')
            docs = load_single_document(file_path)
            results.extend(docs)
            progress_bar.progress((i + 1) / len(filtered_files))
        except Exception as e:
            st.error(f"Error loading {file_path}: {str(e)}")

    status_text.text(f'Successfully loaded {len(results)} documents!')
    return results


def process_documents(ignored_files: List[str] = []) -> List[Document]:
    """
    Load documents and split in chunks
    """
    st.info(f"Loading documents from {config.source_directory}")
    documents = load_documents(config.source_directory, ignored_files)
    if not documents:
        st.warning("No new documents to load")
        return []

    st.success(f"Loaded {len(documents)} new documents from {config.source_directory}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap
    )
    texts = text_splitter.split_documents(documents)
    st.info(f"Split into {len(texts)} chunks of text (max. {config.chunk_size} tokens each)")
    return texts


def add_documents_in_batches(db, texts, batch_size=1000):
    """
    Add documents to ChromaDB in batches to avoid batch size limits
    """
    total_batches = math.ceil(len(texts) / batch_size)

    # Create progress bar for batching
    batch_progress = st.progress(0)
    batch_status = st.empty()

    for i in range(0, len(texts), batch_size):
        batch_num = (i // batch_size) + 1
        batch_texts = texts[i:i + batch_size]

        batch_status.text(f'Processing batch {batch_num}/{total_batches} ({len(batch_texts)} documents)')

        try:
            db.add_documents(batch_texts)
            batch_progress.progress(batch_num / total_batches)
        except Exception as e:
            st.error(f"Error processing batch {batch_num}: {str(e)}")
            # Try with smaller batch size if this batch fails
            if len(batch_texts) > 100:
                st.info(f"Retrying batch {batch_num} with smaller batch size...")
                smaller_batch_size = len(batch_texts) // 2
                for j in range(0, len(batch_texts), smaller_batch_size):
                    smaller_batch = batch_texts[j:j + smaller_batch_size]
                    try:
                        db.add_documents(smaller_batch)
                    except Exception as e2:
                        st.error(f"Error with smaller batch: {str(e2)}")
                        continue
            else:
                st.error(f"Skipping batch {batch_num} due to persistent errors")
                continue

    batch_status.text(f'Successfully processed all {total_batches} batches!')


def does_vectorstore_exist(persist_directory: str) -> bool:
    """
    Checks if vectorstore exists
    """
    # Check for ChromaDB files
    if os.path.exists(persist_directory):
        # Look for ChromaDB specific files
        chroma_files = [
            'chroma.sqlite3',  # ChromaDB database file
            'index',  # Index directory
        ]

        # Check if any ChromaDB files exist
        for file in chroma_files:
            if os.path.exists(os.path.join(persist_directory, file)):
                return True

        # Also check for any .parquet files which indicate ChromaDB collections
        parquet_files = glob.glob(os.path.join(persist_directory, '*.parquet'))
        if parquet_files:
            return True

        # Check for any subdirectories with ChromaDB data
        for item in os.listdir(persist_directory):
            item_path = os.path.join(persist_directory, item)
            if os.path.isdir(item_path):
                # Check if this directory contains ChromaDB files
                if any(os.path.exists(os.path.join(item_path, f)) for f in ['data.db', 'index']):
                    return True

    return False


def get_document_stats(source_directory):
    """Get statistics about documents in the directory"""
    stats = {}
    all_files = []

    for ext in LOADER_MAPPING:
        files = glob.glob(os.path.join(source_directory, f"**/*{ext}"), recursive=True)
        all_files.extend(files)
        stats[ext] = len(files)

    return stats, all_files


def ingest_documents():
    """Main ingestion function with batch processing"""
    try:
        # Create embeddings
        embeddings = HuggingFaceEmbeddings(model_name=config.embeddings_model_name)
        # Create new-style Chroma client
        chroma_client = get_chroma_client(config.persist_directory)

        if does_vectorstore_exist(config.persist_directory):
            # Update and store locally vectorstore
            st.info(f"Appending to existing vectorstore at {config.persist_directory}")
            db = Chroma(
                client=chroma_client,
                collection_name="legal_docs",
                embedding_function=embeddings,
                persist_directory=config.persist_directory
            )
            collection = db.get()
            texts = process_documents([metadata['source'] for metadata in collection['metadatas']])

            if texts:
                st.info(f"Creating embeddings for {len(texts)} documents in batches...")
                add_documents_in_batches(db, texts, config.batch_size)
                st.success("Documents added to existing vectorstore!")
            else:
                st.info("No new documents to add.")
        else:
            # Create and store locally vectorstore
            st.info("Creating new vectorstore")
            texts = process_documents()

            if texts:
                st.info(f"Creating embeddings for {len(texts)} documents in batches...")

                # Create initial vectorstore with first batch
                first_batch = texts[:config.batch_size]
                remaining_texts = texts[config.batch_size:]

                db = Chroma.from_documents(
                    first_batch,
                    embeddings,
                    client=chroma_client,
                    collection_name="legal_docs",
                    persist_directory=config.persist_directory
                )

                # Add remaining documents in batches if any
                if remaining_texts:
                    add_documents_in_batches(db, remaining_texts, config.batch_size)

                st.success("New vectorstore created successfully!")
            else:
                st.error("No documents found to create vectorstore.")
                return

        # Persist the database
        db.persist()
        db = None

        st.success("Ingestion complete! You can now query your documents.")

    except Exception as e:
        st.error(f"Error during ingestion: {str(e)}")
        st.error("Make sure ChromaDB is properly installed: pip install chromadb")


def main():
    st.set_page_config(
        page_title="RAG Document Ingestion System",
        page_icon="📚",
        layout="wide"
    )

    st.title("📚 RAG Document Ingestion System")
    st.markdown("---")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Directory settings
        st.subheader("Directory Settings")
        source_dir = st.text_input("Source Directory", value=config.source_directory)
        persist_dir = st.text_input("Persist Directory", value=config.persist_directory)

        if st.button("Update Directories"):
            config.update_directories(source_dir, persist_dir)
            st.success("Directories updated!")

        # Model settings
        st.subheader("Model Settings")
        config.embeddings_model_name = st.selectbox(
            "Embeddings Model",
            ["all-MiniLM-L6-v2", "all-mpnet-base-v2", "sentence-transformers/all-MiniLM-L12-v2"],
            index=0
        )

        config.chunk_size = st.slider("Chunk Size", 100, 2000, config.chunk_size)
        config.chunk_overlap = st.slider("Chunk Overlap", 0, 200, config.chunk_overlap)

        # Batch processing settings
        st.subheader("Batch Processing")
        config.batch_size = st.slider("Batch Size", 100, 2000, config.batch_size,
                                      help="Number of documents to process at once. Reduce if you encounter batch size errors.")

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📁 Document Overview", "📤 Upload Files", "🌐 Scrape Website", "⚡ Ingest Documents"])

    with tab1:
        st.header("Document Overview")

        # Check if directories exist
        if not os.path.exists(config.source_directory):
            st.warning(f"Source directory '{config.source_directory}' does not exist. It will be created when needed.")
        else:
            # Get document statistics
            stats, all_files = get_document_stats(config.source_directory)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Document Statistics")
                total_docs = sum(stats.values())
                st.metric("Total Documents", total_docs)

                # Show breakdown by file type
                if total_docs > 0:
                    df_stats = pd.DataFrame(list(stats.items()), columns=['File Type', 'Count'])
                    df_stats = df_stats[df_stats['Count'] > 0]
                    st.dataframe(df_stats, use_container_width=True)

            with col2:
                st.subheader("Vectorstore Status")
                if does_vectorstore_exist(config.persist_directory):
                    st.success("✅ Vectorstore exists")

                    # Try to get vectorstore info
                    try:
                        embeddings = HuggingFaceEmbeddings(model_name=config.embeddings_model_name)
                        chroma_client = get_chroma_client(config.persist_directory)
                        db = Chroma(client=chroma_client,
                                    collection_name="legal_docs",
                                    embedding_function=embeddings,
                                    persist_directory=config.persist_directory)
                        collection = db.get()
                        st.metric("Embedded Documents", len(collection['metadatas']))
                        db = None
                    except Exception as e:
                        st.error(f"Error reading vectorstore: {str(e)}")
                else:
                    st.warning("⚠️ No vectorstore found")

            # Show recent files
            if all_files:
                st.subheader("Recent Documents")
                recent_files = sorted(all_files, key=lambda x: os.path.getctime(x), reverse=True)[:10]

                for file_path in recent_files:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.text(os.path.basename(file_path))
                    with col2:
                        st.text(f"{os.path.getsize(file_path) / 1024:.1f} KB")
                    with col3:
                        st.text(datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d"))

    with tab2:
        st.header("Upload Files")

        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            type=['txt', 'pdf', 'docx', 'doc', 'csv', 'md', 'html', 'ppt', 'pptx', 'epub', 'eml', 'enex', 'odt']
        )

        if uploaded_files:
            st.subheader("Files to Upload")
            for file in uploaded_files:
                st.write(f"📄 {file.name} ({file.size} bytes)")

            if st.button("Upload Files", type="primary"):
                # Create source directory if it doesn't exist
                os.makedirs(config.source_directory, exist_ok=True)

                success_count = 0
                for file in uploaded_files:
                    try:
                        file_path = os.path.join(config.source_directory, file.name)
                        with open(file_path, "wb") as f:
                            f.write(file.getbuffer())
                        success_count += 1
                    except Exception as e:
                        st.error(f"Error uploading {file.name}: {str(e)}")

                st.success(f"Successfully uploaded {success_count} files!")

    with tab3:
        st.header("Scrape Website")

        col1, col2 = st.columns(2)

        with col1:
            url = st.text_input("Website URL", placeholder="https://example.com")
            max_pages = st.slider("Max Pages to Scrape", 1, 50, 1)
            delay = st.slider("Delay between requests (seconds)", 0.5, 5.0, 1.0)

        with col2:
            st.info("💡 Tips for Web Scraping:")
            st.markdown("""
            - Start with 1 page to test
            - Respect robots.txt
            - Use appropriate delays
            - Some sites may block automated requests
            """)

        if st.button("Scrape Website", type="primary"):
            if url:
                # Create source directory if it doesn't exist
                os.makedirs(config.source_directory, exist_ok=True)

                scraper = WebScraper(max_pages=max_pages, delay=delay)
                success = scraper.scrape_website(url, config.source_directory)

                if success:
                    st.balloons()
            else:
                st.error("Please enter a valid URL")

    with tab4:
        st.header("Ingest Documents")

        # Check if there are documents to ingest
        if os.path.exists(config.source_directory):
            stats, all_files = get_document_stats(config.source_directory)
            total_docs = sum(stats.values())

            if total_docs > 0:
                st.info(f"Found {total_docs} documents ready for ingestion")

                # Show batch processing info
                estimated_chunks = total_docs * 2  # rough estimate
                estimated_batches = math.ceil(estimated_chunks / config.batch_size)
                st.info(f"Estimated processing: ~{estimated_batches} batches of {config.batch_size} documents each")

                # Show what will be ingested
                with st.expander("Documents to be ingested"):
                    for file_path in all_files:
                        st.write(f"📄 {os.path.relpath(file_path, config.source_directory)}")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🚀 Start Ingestion", type="primary", use_container_width=True):
                        with st.spinner("Processing documents..."):
                            ingest_documents()

                with col2:
                    if st.button("🗑️ Clear All Documents", use_container_width=True):
                        if st.checkbox("I understand this will delete all documents"):
                            try:
                                shutil.rmtree(config.source_directory)
                                os.makedirs(config.source_directory, exist_ok=True)
                                st.success("All documents cleared!")
                            except Exception as e:
                                st.error(f"Error clearing documents: {str(e)}")
            else:
                st.warning("No documents found. Please upload files or scrape websites first.")
        else:
            st.warning("Source directory does not exist. Please upload files or scrape websites first.")

    # Footer
    st.markdown("---")
    st.markdown("### 🔧 Supported File Types")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Documents:**")
        st.markdown("• PDF, DOCX, DOC, ODT")
        st.markdown("• TXT, MD, HTML")

    with col2:
        st.markdown("**Presentations:**")
        st.markdown("• PPT, PPTX")
        st.markdown("• EPUB, EML")

    with col3:
        st.markdown("**Data:**")
        st.markdown("• CSV")
        st.markdown("• ENEX (Evernote)")


if __name__ == "__main__":
    main()