import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from rich.console import Console
from rich.markdown import Markdown


load_dotenv()


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

ollama_host = os.getenv("IA_MODEL_HOST")
embedding_model = os.getenv("IA_MODEL_EMBEDDED_NAME")
agent_model = os.getenv("IA_MODEL_AGENT_NAME")
api_key = os.getenv("IA_MODEL_API_KEY")
temperature = float(os.getenv("IA_MODEL_TEMPERATURE", "0"))

pinecone_host = os.getenv("PINECONE_HOST")


# ------------------------------------------------------------
# Embeddings
# ------------------------------------------------------------

embeddings = OllamaEmbeddings(
    model=embedding_model,
    base_url=ollama_host
)


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

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 4
    }
)


# ------------------------------------------------------------
# Language model
# ------------------------------------------------------------

model = ChatOpenAI(
    model=agent_model,
    base_url=ollama_host + "/v1",
    api_key=api_key,
    temperature=temperature
)


# ------------------------------------------------------------
# RAG prompt
# ------------------------------------------------------------

prompt = ChatPromptTemplate.from_template("""
Responde la pregunta basándote en el contexto dado. Es obligatorio que la
respuesta esté formateada en Markdown (usar títulos, negritas, listas, etc.
cuando sea apropiado).

Contexto: {context}

Pregunta: {question}

Respuesta en Markdown:
""")


# ------------------------------------------------------------
# RAG chain
# ------------------------------------------------------------

chain = (
    {"context": retriever, "question": lambda x: x}
    | prompt
    | model
    | StrOutputParser()
)


# ------------------------------------------------------------
# Query
# ------------------------------------------------------------

print("Dime cuál es tu pregunta (al finalizar presiona ENTER):")
question = input().strip()

if not question:
    print("ERROR: no hay pregunta que responder, inténtalo nuevamente.")
    exit(1)

print("Procesando...")


answer = chain.invoke(question)


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

print("=" * 80)
print("Respuesta:")

console = Console(width=80)
console.print(Markdown(answer))
