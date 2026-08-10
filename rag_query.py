from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

from rich.markdown import Markdown
from rich.console import Console


load_dotenv()

# 1. Conectar a Pinecone
embeddings = OllamaEmbeddings(
    model = os.getenv("IA_MODEL_EMBEDDED_NAME"),
    base_url= os.getenv("IA_MODEL_HOST"))
vectorstore = PineconeVectorStore.from_existing_index(
    index_name = os.getenv("PINECONDE_INDEX_NAME"),
    embedding = embeddings)
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 4
    })

# 2. Modelo (igual que usas)
model = ChatOpenAI(
    model = os.getenv("IA_MODEL_AGENT_NAME"),
    base_url = os.getenv("IA_MODEL_HOST") + "/v1",
    api_key = os.getenv("IA_MODEL_API_KEY"),
    temperature = os.getenv("IA_MODEL_TEMPERATURE")
)

# 3. Prompt RAG
prompt = ChatPromptTemplate.from_template("""
Responde la pregunta basándote en el siguiente contexto.
**Importante:** Formatea tu respuesta en **Markdown** (usa títulos, negritas, listas, etc. cuando sea apropiado).

Contexto: {context}
Pregunta: {question}
Respuesta (en Markdown):
""")

# 4. Chain
chain = (
    {"context": retriever, "question": lambda x: x}
    | prompt
    | model
    | StrOutputParser()
)

# 5. Pregunta interactiva
print("✍️  Escribe tu pregunta (presiona Enter):")
question = input().strip()

if not question:
    print("❌ No ingresaste ninguna pregunta.")
    exit(1)

print("\n🔍 Procesando...\n")

# 6. Invocar chain
respuesta = chain.invoke(question)

print("=" * 60)
print("🤖 Respuesta:")
console = Console(
    width = 80)
console.print(Markdown(respuesta))
