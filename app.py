import streamlit as st
from streamlit.runtime.scriptrunner import RerunData, RerunException
from streamlit.runtime.scriptrunner.script_run_context import ScriptRunContext
import sys

# Define pages
PAGES = {
    "Main": {
        "title": "Legal AI Assistant",
        "icon": "⚖️",
        "script": "main.py"
    },
    "Summarizer": {
        "title": "Document Summarizer",
        "icon": "📝",
        "script": "summarizer.py"
    },
    "Chatbot": {
        "title": "Legal Chatbot",
        "icon": "💬",
        "script": "chatbot.py"
    },
    "Document_QA": {
        "title": "Document Q&A",
        "icon": "📄",
        "script": "document_qa.py"
    }
}

def main():
    # Get current page from query parameters
    query_params = st.experimental_get_query_params()
    current_page = query_params.get("page", ["Main"])[0]
    
    # If page is not recognized, default to Main
    if current_page not in PAGES:
        current_page = "Main"
    
    # Set page config based on current page
    page_config = PAGES[current_page]
    st.set_page_config(
        page_title=page_config["title"],
        page_icon=page_config["icon"],
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Import and run the appropriate page
    try:
        if current_page == "Main":
            import main
        elif current_page == "Summarizer":
            import summarizer
        elif current_page == "Chatbot":
            import chatbot
        elif current_page == "Document_QA":
            import document_qa
    except ImportError as e:
        st.error(f"Error importing page {current_page}: {str(e)}")
        st.info("Please make sure all page files are in the same directory.")

if __name__ == "__main__":
    main()
