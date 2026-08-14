import os

from pinecone import Pinecone
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore


pinecone_host = "http://localhost:5081"

embeddings = OllamaEmbeddings(
    model=os.getenv("IA_MODEL_EMBEDDED_NAME", "nomic-embed-text:latest"),
    base_url=os.getenv("IA_MODEL_HOST", "http://localhost:11434"),
)

pc = Pinecone(
    api_key="pclocal",
)

index = pc.Index(
    host=pinecone_host,
)

print("Pinecone index:")
print(index)

vectorstore = PineconeVectorStore(
    index=index,
    embedding=embeddings,
)

print("VectorStore creado correctamente")

print(
    index.describe_index_stats()
)
