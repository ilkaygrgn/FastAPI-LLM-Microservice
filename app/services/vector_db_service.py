from google import genai
from langchain_community.vectorstores import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

# Configure the database URL to include PGVector connection details
# This will use the DATABASE_URL from settings which should point to PostgreSQL
CONNECTION_STRING = settings.DATABASE_URL.replace("sqlite:///", "postgresql://").replace("postgresql://", "postgresql+psycopg2://")

# Initialize the embedding model
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=settings.GOOGLE_API_KEY
)

COLLECTION_NAME = "rag_documents"

def get_vector_store():
    """Initializes and returns the PGVector store instance."""
    return PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        embedding_function=embeddings
    )

def save_chunk_to_vector_db(chunks: list):
    """Saves the document chunks to the PGVector database."""
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    print(f"[INFO] Saved {len(chunks)} document chunks to PGVector.")