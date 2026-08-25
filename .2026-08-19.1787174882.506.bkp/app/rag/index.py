# app/rag/index.py
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

load_dotenv()

# ------------------------------------------------------------
# Configuración por defecto (cargada de variables de entorno)
# ------------------------------------------------------------

PINECONE_HOST = os.getenv("PINECONE_HOST")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
OLLAMA_HOST = os.getenv("IA_MODEL_HOST")
EMBEDDING_MODEL = os.getenv("IA_MODEL_EMBEDDED_NAME")


def index_document(
    file_path: Path,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    pinecone_host: Optional[str] = None,
    pinecone_index_name: Optional[str] = None,
    ollama_host: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> int:
    """
    Indexa un documento de texto en Pinecone (local).

    Args:
        file_path: Ruta al archivo de texto.
        chunk_size: Tamaño de cada fragmento (en caracteres).
        chunk_overlap: Solapamiento entre fragmentos.
        pinecone_host: Host de Pinecone (si no se pasa, usa variable de entorno).
        pinecone_index_name: Nombre del índice (si no se pasa, usa variable de entorno).
        ollama_host: Host de Ollama (si no se pasa, usa variable de entorno).
        embedding_model: Modelo de embeddings (si no se pasa, usa variable de entorno).

    Returns:
        Número de fragmentos indexados.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si falta alguna configuración necesaria.
    """
    # Usar valores por defecto desde entorno si no se pasan
    pinecone_host = pinecone_host or PINECONE_HOST
    pinecone_index_name = pinecone_index_name or PINECONE_INDEX_NAME
    ollama_host = ollama_host or OLLAMA_HOST
    embedding_model = embedding_model or EMBEDDING_MODEL

    # Validaciones
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo {file_path} no existe.")
    if not pinecone_host:
        raise ValueError("Falta PINECONE_HOST (variable de entorno o parámetro).")
    if not embedding_model:
        raise ValueError("Falta IA_MODEL_EMBEDDED_NAME (variable de entorno o parámetro).")

    # 1. Cargar documento
    loader = TextLoader(file_path)
    docs = loader.load()

    # 2. Dividir en fragmentos
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    # 3. Configurar embeddings
    embeddings = OllamaEmbeddings(
        model=embedding_model,
        base_url=ollama_host,
    )

    # 4. Conectar con Pinecone
    pinecone = Pinecone(api_key="pclocal")
    index = pinecone.Index(host=pinecone_host)

    # 5. Crear vectorstore y añadir documentos
    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embeddings,
    )
    vectorstore.add_documents(chunks)

    print(f"✅ Indexados {len(chunks)} fragmentos en el índice '{pinecone_index_name}'")
    return len(chunks)


# ------------------------------------------------------------
# Punto de entrada para ejecución directa (modo script)
# ------------------------------------------------------------
if __name__ == "__main__":
    workdir = Path(__file__).parent
    default_file = workdir / "documents" / "book.txt"

    try:
        cantidad = index_document(default_file)
        print(f"Proceso completado. {cantidad} fragmentos indexados.")
    except Exception as e:
        print(f"❌ Error: {e}")
