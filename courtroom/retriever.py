# courtroom/retriever.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
import os

# ── Must match your existing project exactly ──────────────────────────────
VECTORSTORE_PATH   = "db"
COLLECTION_NAME    = "legal_docs"
EMBEDDINGS_MODEL   = "all-MiniLM-L6-v2"

# ── Book filename keywords → used for metadata filtering ──────────────────
BOOK_KEYWORDS = {
    "constitution": ["constitution"],
    "contract":     ["contract", "avtar", "specific_relief", "specific relief"],
    "ipc":          ["ipc", "penal", "indian_penal"],
    "consumer":     ["consumer", "consumer_protection"],
}

# ── Which books to search for each case type ──────────────────────────────
CASE_TYPE_BOOK_MAP = {
    # Contract / Civil cases
    "Contract Breach":                          ["contract", "constitution"],
    "Landlord-Tenant Dispute":                  ["contract", "constitution"],
    "Employment Contract Dispute":              ["contract", "constitution"],
    "Property Sale Agreement Dispute":          ["contract", "constitution"],
    "Specific Performance of Contract":         ["contract", "constitution"],
    "Coercion / Misrepresentation in Contract": ["contract", "constitution"],

    # Constitutional cases
    "Fundamental Rights Violation (Government Action)": ["constitution", "ipc"],
    "Arbitrary State Action (Article 14)":              ["constitution", "contract"],

    # Criminal cases — NOW SUPPORTED
    "Criminal / IPC":                           ["ipc", "constitution"],
    "Assault / Hurt":                           ["ipc"],
    "Theft / Robbery":                          ["ipc"],
    "Cheating / Fraud (Criminal)":              ["ipc", "consumer"],
    "Murder / Culpable Homicide":               ["ipc"],

    # Consumer cases — NOW SUPPORTED
    "Consumer Rights / Defective Product":      ["consumer", "constitution"],
    "E-commerce Fraud / Online Shopping":       ["consumer", "ipc"],
    "Service Deficiency":                       ["consumer", "constitution"],
    "Misleading Advertisement":                 ["consumer", "ipc"],
    "Medical Negligence (Consumer)":            ["consumer", "constitution"],
}

# Default: search all books if case type not found in map
DEFAULT_BOOKS = ["constitution", "contract", "ipc", "consumer"]


def _get_vectorstore():
    """Initialize and return the ChromaDB vectorstore."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
    client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=VECTORSTORE_PATH
    )


def _identify_book(source_path: str) -> str:
    """
    Given a source file path from metadata, identify which book it belongs to.
    Returns book key: 'constitution', 'contract', 'ipc', or 'consumer'
    """
    source_lower = source_path.lower()
    for book_key, keywords in BOOK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in source_lower:
                return book_key
    return "unknown"


def retrieve_legal_context(
    case_description: str,
    case_type: str = None,
    k: int = 8
) -> dict:
    """
    Retrieve relevant legal chunks from the correct books based on case type.

    Args:
        case_description: The full case text
        case_type: Selected case type from dropdown (used for book filtering)
        k: Number of chunks to retrieve per book

    Returns dict with:
        - formatted: str ready for LLM prompt
        - sources: list of source metadata for display
        - chunks_by_book: dict of book -> list of chunks
        - total_chunks: int
        - books_searched: list of book names searched
    """
    db = _get_vectorstore()

    # Determine which books to search
    if case_type and case_type in CASE_TYPE_BOOK_MAP:
        books_to_search = CASE_TYPE_BOOK_MAP[case_type]
    else:
        books_to_search = DEFAULT_BOOKS

    # Retrieve all docs without filter first (ChromaDB community version
    # has limited where-clause support for LIKE queries)
    # We filter by book AFTER retrieval using source metadata
    chunks_per_book = max(3, k // len(books_to_search))
    all_retrieved = db.similarity_search(case_description, k=k * 2)

    # Separate chunks by book using metadata
    chunks_by_book = {book: [] for book in books_to_search}
    unmatched = []

    for doc in all_retrieved:
        source = doc.metadata.get("source", "")
        book_key = _identify_book(source)
        if book_key in chunks_by_book:
            if len(chunks_by_book[book_key]) < chunks_per_book:
                chunks_by_book[book_key].append(doc)
        else:
            unmatched.append(doc)

    # If any target book got 0 chunks, do a targeted search for it
    for book_key in books_to_search:
        if len(chunks_by_book[book_key]) == 0:
            # Search with more results and hope to find this book's chunks
            extra_docs = db.similarity_search(case_description, k=k * 3)
            for doc in extra_docs:
                source = doc.metadata.get("source", "")
                if _identify_book(source) == book_key:
                    chunks_by_book[book_key].append(doc)
                    if len(chunks_by_book[book_key]) >= 2:
                        break

    # ── Format context string for LLM ─────────────────────────────────────
    BOOK_DISPLAY_NAMES = {
        "constitution": "CONSTITUTION OF INDIA",
        "contract":     "LAW OF CONTRACT & SPECIFIC RELIEF (AVTAR SINGH, 12th Ed.)",
        "ipc":          "INDIAN PENAL CODE, 1860",
        "consumer":     "CONSUMER PROTECTION ACT, 2019",
    }

    formatted_parts = []
    all_docs_flat = []

    for book_key in books_to_search:
        chunks = chunks_by_book.get(book_key, [])
        if not chunks:
            continue

        display_name = BOOK_DISPLAY_NAMES.get(book_key, book_key.upper())
        formatted_parts.append(f"\n{'='*60}")
        formatted_parts.append(f"SOURCE BOOK: {display_name}")
        formatted_parts.append(f"{'='*60}")

        for i, doc in enumerate(chunks, 1):
            page = doc.metadata.get("page", "N/A")
            formatted_parts.append(f"\n[EXCERPT {i} | Page {page}]")
            formatted_parts.append(doc.page_content.strip())

        all_docs_flat.extend(chunks)

    formatted_context = "\n".join(formatted_parts)

    # ── Build sources list for UI display ─────────────────────────────────
    sources = []
    for doc in all_docs_flat:
        source_path = doc.metadata.get("source", "Unknown")
        book_key = _identify_book(source_path)
        sources.append({
            "source":    source_path,
            "book_key":  book_key,
            "book_name": BOOK_DISPLAY_NAMES.get(book_key, "Unknown"),
            "page":      doc.metadata.get("page", "N/A"),
            "preview":   doc.page_content[:180].strip() + "..."
        })

    return {
        "formatted":      formatted_context,
        "sources":        sources,
        "chunks_by_book": {k: v for k, v in chunks_by_book.items() if v},
        "total_chunks":   len(all_docs_flat),
        "books_searched": books_to_search,
    }
