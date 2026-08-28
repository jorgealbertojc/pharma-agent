"""
Indexador de documentos en Pinecone.

Este módulo proporciona la clase Indexer que encapsula la lógica de indexación
de documentos de texto en el índice Pinecone configurado.
"""

from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from app.core.config import settings as default_settings
from app.rag.embeddings import get_embeddings


class Indexer:
    """
    Indexa documentos de texto en Pinecone.

    Args:
        file_path: Ruta al archivo de texto (.txt).
        chunk_size: Tamaño de cada fragmento (en caracteres). Default 500.
        chunk_overlap: Solapamiento entre fragmentos. Default 50.
        clear_first: Si es True, elimina todos los vectores del índice antes de indexar.
                     (Nota: en Pinecone local no está implementado; se muestra advertencia.)
    """

    def __init__(
        self,
        file_path: Path,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        clear_first: bool = False,
        settings = None,
    ):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.clear_first = clear_first
        self.settings = settings or default_settings

    def index(self) -> int:
        """
        Ejecuta el proceso de indexación.

        Returns:
            int: Número de fragmentos indexados.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si la configuración de Pinecone está incompleta.
            Exception: Cualquier error durante la conexión a Pinecone o indexación.
        """
        # Validaciones
        if not self.file_path.exists():
            raise FileNotFoundError(f"El archivo {self.file_path} no existe.")

        if not self.settings.PINECONE_HOST:
            raise ValueError("PINECONE_HOST no está definido en la configuración.")

        if not self.settings.PINECONE_INDEX_NAME:
            raise ValueError("PINECONE_INDEX_NAME no está definido en la configuración.")

        # 1. Cargar documento
        with open(self.file_path, "r", encoding="utf-8") as f:
            text = f.read()
        docs = [Document(page_content=text)]

        # 2. Dividir en fragmentos
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        if not chunks:
            raise ValueError("El documento no generó ningún fragmento.")

        # 3. Obtener embeddings
        embeddings = get_embeddings()

        # 4. Conectar con Pinecone (local)
        pinecone = Pinecone(api_key=self.settings.PINECONE_API_KEY)
        index = pinecone.Index(host=self.settings.PINECONE_HOST)

        # (Opcional) Limpiar el índice si se solicita
        if self.clear_first:
            print("⚠️  clear_first=True no implementado para Pinecone local. Se añadirán vectores sin limpiar.")

        # 5. Crear vectorstore y añadir documentos
        vectorstore = PineconeVectorStore(
            index=index,
            embedding=embeddings,
        )
        vectorstore.add_documents(chunks)

        print(f"✅ Indexados {len(chunks)} fragmentos en el índice '{self.settings.PINECONE_INDEX_NAME}'.")
        return len(chunks)
