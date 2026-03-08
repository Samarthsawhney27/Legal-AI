#!/usr/bin/env python3
"""
Test script to check if the multi-page Legal AI app works correctly
"""

import sys
import subprocess
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'langchain_community',
        'chromadb',
        'sentence_transformers',
        'pypdf',
        'python_dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - OK")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def test_imports():
    """Test the specific imports used in the app"""
    print("\n🧪 Testing imports...")
    
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print("✅ HuggingFaceEmbeddings import - OK")
    except ImportError as e:
        print(f"❌ HuggingFaceEmbeddings import failed: {e}")
    
    try:
        from langchain_community.vectorstores import Chroma
        print("✅ Chroma import - OK")
    except ImportError as e:
        print(f"❌ Chroma import failed: {e}")
    
    try:
        from langchain.chains import RetrievalQA
        print("✅ RetrievalQA import - OK")
    except ImportError as e:
        print(f"❌ RetrievalQA import failed: {e}")
    
    try:
        from langchain_community.llms import Ollama
        print("✅ Ollama import - OK")
    except ImportError as e:
        print(f"❌ Ollama import failed: {e}")

def main():
    print("🔍 Legal AI App - Dependency Checker")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Test imports
    test_imports()
    
    print("\n" + "=" * 50)
    print("🚀 You can now run the app with:")
    print("streamlit run Legal_AI_RAG.py")
    print("\n📁 Available pages:")
    print("  • Main: Legal_AI_RAG.py")
    print("  • Summarizer: pages/1_📝_Summarizer.py")
    print("  • Chatbot: pages/2_💬_Chatbot.py")
    print("  • Document Q&A: pages/3_📄_Document_Q&A.py")

if __name__ == "__main__":
    main()
