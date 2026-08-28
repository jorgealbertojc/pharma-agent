"""
Gestor de prompts para el sistema RAG.

Esta clase centraliza la construcción de prompts para el agente,
permitiendo personalizar el mensaje del sistema, el formato del contexto
y la pregunta del usuario.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate


class RAGPrompt:
    """
    Construye prompts estructurados para el sistema RAG.

    Atributos:
        system_prompt: Instrucciones iniciales para el modelo.
        context_template: Plantilla para insertar el contexto recuperado.
        question_template: Plantilla para insertar la pregunta del usuario.
        format_instructions: Indicaciones adicionales sobre el formato de la respuesta.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "Eres un asistente farmacéutico profesional. "
        "Responde las preguntas basándote ÚNICAMENTE en el contexto proporcionado. "
        "Si la información no está en el contexto, indica que no dispones de ella."
    )

    DEFAULT_CONTEXT_TEMPLATE = "Contexto:\n{context}\n"
    DEFAULT_QUESTION_TEMPLATE = "Pregunta: {question}\n"
    DEFAULT_FORMAT_INSTRUCTIONS = (
        "Proporciona respuestas claras y concisas, usando Markdown para "
        "estructurar la información (negritas, listas, títulos) cuando sea apropiado."
    )

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        context_template: Optional[str] = None,
        question_template: Optional[str] = None,
        format_instructions: Optional[str] = None,
    ):
        """
        Inicializa el gestor de prompts.

        Args:
            system_prompt: Mensaje del sistema. Si no se pasa, usa el predeterminado.
            context_template: Plantilla para el contexto (debe contener {context}).
            question_template: Plantilla para la pregunta (debe contener {question}).
            format_instructions: Instrucciones de formato adicionales.
        """
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.context_template = context_template or self.DEFAULT_CONTEXT_TEMPLATE
        self.question_template = question_template or self.DEFAULT_QUESTION_TEMPLATE
        self.format_instructions = format_instructions or self.DEFAULT_FORMAT_INSTRUCTIONS

    def build_prompt(self, context: str, question: str) -> str:
        """
        Construye el prompt completo para el modelo.

        Args:
            context: Texto del contexto recuperado (puede ser una cadena vacía).
            question: Pregunta del usuario.

        Returns:
            Prompt completo listo para ser enviado al modelo.
        """
        # Formatear cada parte
        context_block = self.context_template.format(context=context) if context else ""
        question_block = self.question_template.format(question=question)

        # Unir las partes con saltos de línea
        parts = [
            self.system_prompt,
            context_block,
            question_block,
            self.format_instructions,
        ]
        # Eliminar partes vacías
        prompt = "\n\n".join(part for part in parts if part.strip())
        return prompt

    def to_langchain_template(self) -> "ChatPromptTemplate":
        """
        Convierte el prompt en un ChatPromptTemplate de LangChain.

        Esto permite integrarlo fácilmente con cadenas de LangChain.

        Returns:
            ChatPromptTemplate listo para usar con el modelo.
        """
        from langchain_core.prompts import ChatPromptTemplate

        # Construimos el prompt en formato de mensajes
        messages = [
            ("system", self.system_prompt),
            ("human", self.context_template + self.question_template),
        ]
        # Agregamos instrucciones de formato como parte del mensaje humano
        # (o podríamos ponerlas como system adicional)
        messages[1] = ("human", self.context_template + self.question_template + "\n\n" + self.format_instructions)

        return ChatPromptTemplate.from_messages(messages)
