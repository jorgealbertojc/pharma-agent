import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from pathlib import Path

load_dotenv()


workdir = Path( __file__ ).parent
filepath = workdir / "mi_texto.txt"
loader = TextLoader( filepath )
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(
    chunk_size = 500,
    chunk_overlap = 50)
chunks = splitter.split_documents(docs)

embeddings = OllamaEmbeddings(
    model = os.getenv("IA_MODEL_EMBEDDED_NAME"),
    base_url = os.getenv("IA_MODEL_HOST"))
print("embeddings: ")
print(embeddings)

vectorstore = PineconeVectorStore.from_documents(
    documents = chunks,
    embedding = embeddings,
    index_name = os.getenv("PINECONDE_INDEX_NAME")
)

print(f"✅ Indexed {len(chunks)} chunks")
