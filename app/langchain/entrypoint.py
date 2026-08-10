from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOpenAI(
    model = "claude-3-5-sonnet-20241022:latest",
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    temperature=0.7,
)

messages = [
    SystemMessage(
        content = "Eres un experto en informatica con un excelente conocimiento de Inteligencias Artificiales"
    ),
    HumanMessage(
        content = "¿Qué es la inteligencia artificial? Explícalo como si fuera para alguien que no sabe nada de tecnología."
    ),
]

response = model.invoke(messages)
print(response.content)
