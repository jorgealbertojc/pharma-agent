import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone


load_dotenv()


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

pinecone_host = os.getenv("PINECONE_HOST")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

ollama_host = os.getenv("IA_MODEL_HOST")
embedding_model = os.getenv("IA_MODEL_EMBEDDED_NAME")


# ------------------------------------------------------------
# Load document
# ------------------------------------------------------------

workdir = Path(__file__).parent
filepath = workdir / "documents" / "book.txt"

loader = TextLoader(filepath)
docs = loader.load()


# ------------------------------------------------------------
# Split document
# ------------------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.split_documents(docs)


# ------------------------------------------------------------
# Embeddings
# ------------------------------------------------------------

embeddings = OllamaEmbeddings(
    model=embedding_model,
    base_url=ollama_host
)

print("Embedding model:")
print(embedding_model)


# ------------------------------------------------------------
# Pinecone Local
# ------------------------------------------------------------

pinecone = Pinecone(
    api_key="pclocal"
)

index = pinecone.Index(
    host=pinecone_host
)

vectorstore = PineconeVectorStore(
    index=index,
    embedding=embeddings
)


# ------------------------------------------------------------
# Index documents
# ------------------------------------------------------------

vectorstore.add_documents(chunks)


print(f"Indexed {len(chunks)} chunks")
print(f"Pinecone host: {pinecone_host}")
print(f"Index: {pinecone_index_name}")
