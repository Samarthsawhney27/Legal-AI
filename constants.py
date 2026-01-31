import os

# Define the folder for storing database
PERSIST_DIRECTORY = os.environ.get('PERSIST_DIRECTORY', 'db')

COLLECTION_NAME = os.environ.get('CHROMA_COLLECTION', 'legal_docs')
