# app/rag/query.py
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

# ------------------------------------------------------------
# Configuración por defecto (variables de entorno)
# ------------------------------------------------------------

OLLAMA_HOST = os.getenv("IA_MODEL_HOST")
EMBEDDING_MODEL = os.getenv("IA_MODEL_EMBEDDED_NAME")
AGENT_MODEL = os.getenv("IA_MODEL_AGENT_NAME")
API_KEY = os.getenv("IA_MODEL_API_KEY")
TEMPERATURE = float(os.getenv("IA_MODEL_TEMPERATURE", "0"))
PINECONE_HOST = os.getenv("PINECONE_HOST")


def get_embeddings(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> OllamaEmbeddings:
    """Retorna el modelo de embeddings configurado."""
    model = model or EMBEDDING_MODEL
    base_url = base_url or OLLAMA_HOST
    if not model:
        raise ValueError("Falta IA_MODEL_EMBEDDED_NAME (variable de entorno o parámetro).")
    return OllamaEmbeddings(model=model, base_url=base_url)


def get_vectorstore(
    pinecone_host: Optional[str] = None,
    embeddings: Optional[OllamaEmbeddings] = None,
) -> PineconeVectorStore:
    """Retorna el vectorstore de Pinecone."""
    pinecone_host = pinecone_host or PINECONE_HOST
    if not pinecone_host:
        raise ValueError("Falta PINECONE_HOST (variable de entorno o parámetro).")
    if embeddings is None:
        embeddings = get_embeddings()
    pinecone = Pinecone(api_key="pclocal")
    index = pinecone.Index(host=pinecone_host)
    return PineconeVectorStore(index=index, embedding=embeddings)


def get_retriever(
    k: int = 4,
    pinecone_host: Optional[str] = None,
    embeddings: Optional[OllamaEmbeddings] = None,
):
    """Retorna un retriever configurado con el número k de fragmentos."""
    vectorstore = get_vectorstore(pinecone_host, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": k})


def get_llm(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: Optional[float] = None,
) -> ChatOpenAI:
    """Retorna el modelo de lenguaje (ChatOpenAI apuntando a Ollama)."""
    model = model or AGENT_MODEL
    base_url = base_url or OLLAMA_HOST
    api_key = api_key or API_KEY
    temperature = temperature if temperature is not None else TEMPERATURE
    if not model:
        raise ValueError("Falta IA_MODEL_AGENT_NAME (variable de entorno o parámetro).")
    return ChatOpenAI(
        model=model,
        base_url=f"{base_url}/v1",
        api_key=api_key,
        temperature=temperature,
    )


def create_rag_chain(
    retriever,
    llm,
    prompt_template: Optional[str] = None,
):
    """
    Crea la cadena RAG completa.

    Args:
        retriever: Retriever configurado.
        llm: Modelo de lenguaje.
        prompt_template: Template para el prompt (debe tener {context} y {question}).

    Returns:
        Cadena invocable.
    """
    if prompt_template is None:
        prompt_template = """
Responde la pregunta basándote en el contexto dado. Es obligatorio que la
respuesta esté formateada en Markdown (usar títulos, negritas, listas, etc.
cuando sea apropiado).

Contexto: {context}

Pregunta: {question}

Respuesta en Markdown:
"""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = (
        {"context": retriever, "question": lambda x: x}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def query(
    question: str,
    retriever: Optional = None,
    llm: Optional = None,
    k: int = 4,
    prompt_template: Optional[str] = None,
) -> str:
    """
    Ejecuta una consulta RAG y retorna la respuesta.

    Args:
        question: Pregunta del usuario.
        retriever: Si no se pasa, se crea uno con k=4.
        llm: Si no se pasa, se crea uno con configuración por defecto.
        k: Número de fragmentos a recuperar (solo si retriever es None).
        prompt_template: Plantilla personalizada.

    Returns:
        Respuesta generada.
    """
    if retriever is None:
        retriever = get_retriever(k=k)
    if llm is None:
        llm = get_llm()
    chain = create_rag_chain(retriever, llm, prompt_template)
    return chain.invoke(question)


# ------------------------------------------------------------
# Punto de entrada para ejecución directa
# ------------------------------------------------------------
if __name__ == "__main__":
    from rich.console import Console
    from rich.markdown import Markdown

    print("Dime cuál es tu pregunta (al finalizar presiona ENTER):")
    question = input().strip()

    if not question:
        print("ERROR: no hay pregunta que responder, inténtalo nuevamente.")
        exit(1)

    print("Procesando...")
    answer = query(question)

    print("=" * 80)
    print("Respuesta:")
    console = Console(width=80)
    console.print(Markdown(answer))
