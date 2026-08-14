from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
import os

from rich.console import Console
from rich.markdown import Markdown


load_dotenv()

ai_model_engines_host: str = os.getenv("AI_MODEL_ENGINES_HOST")
ai_model_embedded_model_name: str = os.getenv("AI_MODEL_EMBEDDED_MODEL_NAME")
ai_model_agent_model_name: str = os.getenv("AI_MODEL_AGENT_MODEL_NAME")
ai_model_api_key: str = os.getenv("AI_MODEL_API_KEY")
ai_model_temperature: float = os.getenv("AI_MODEL_TEMPERATURE")

pinecone_api_key: str = os.getenv("PINECONE_API_KEY")
pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT")
pineconde_index_name: str = os.getenv("PINECONDE_INDEX_NAME")
pineconde_index_dimentions: str = os.getenv("PINECONDE_INDEX_DIMENTIONS")
pinecone_index_metric: str = os.getenv("PINECONE_INDEX_METRIC")

embeddings: OllamaEmbeddings = OllamaEmbeddings(
    model = ai_model_embedded_model_name,
    base_url= ai_model_engines_host)

vectorstore: PineconeVectorStore = PineconeVectorStore(
    index_name = pineconde_index_name,
    embedding = embeddings)

retriever = vectorstore.as_retriever(
    search_kwargs = {
        "k": 4
    })

model = ChatOpenAI(
    model = ai_model_agent_model_name,
    base_url = ai_model_engines_host + "/v1",
    api_key = ai_model_api_key,
    temperature = ai_model_temperature)

prompt = ChatPromptTemplate.from_template("""
Responde la pregunta basandote en el contexto dado. Es obligatorio que la
respuesta estÉ formateada en Markdown (usar tÍtulos, negritas, listas, etc.
cuando sea apropiado).

Contexto: {context}
Pregunta: {question}
Respuesta en Markdown:
""")

chain = (
    { "context": retriever, "question": lambda x: x }
    | prompt
    | model
    | StrOutputParser()
)

print("Dime cual es tu pregunta (al finalizar presiona ENTER):")
question = input().strip()

if not question:
    print("ERROR: no hay pregunta que responder, intentalo nuevamente.")

print("procesando ... ... ...")

answer = chain.invoke(question)

print("=" * 60)
print("Respuesta:")
console = Console( width = 80 )
console.print(
    Markdown(answer))
