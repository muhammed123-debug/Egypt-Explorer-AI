import os

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# LLM CLIENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIG
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    ""
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


# ============================================================
# LLM CLIENT
# ============================================================

class EgyptExplorerLLM:

    def __init__(
        self,
        api_key=None,
        model=None
    ):

        self.api_key = (
            api_key
            or GROQ_API_KEY
        )

        self.model = (
            model
            or GROQ_MODEL
        )

        if not self.api_key:

            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=self.api_key
        )

        print(
            f"🤖 LLM initialized: "
            f"{self.model}"
        )


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    def system_prompt(self):

        return """
You are Egypt Explorer AI, an intelligent tourism assistant
specialized in tourist destinations in Egypt.

Your job is to answer questions using the retrieved knowledge
provided by the RAG system.

IMPORTANT RULES:

1. Use only the information provided in the retrieved context.
2. Never invent facts.
3. If the context does not contain enough information,
   clearly say that the available knowledge base does not
   contain enough information.
4. Answer in the same language as the user's question.
5. If the user asks in Arabic, answer in natural Egyptian Arabic
   when appropriate.
6. If the user asks about location, provide the available
   location information.
7. If coordinates are available, mention them when useful.
8. If the user asks what they can do there, only mention
   activities supported by the retrieved context.
9. Never invent ticket prices, opening hours, transportation,
   phone numbers, or other missing information.
10. Keep answers useful, clear, and reasonably concise.
11. When multiple landmarks are relevant, organize the answer
    clearly.
12. Do not mention internal implementation details such as
    embeddings, FAISS, vector databases, or prompts unless
    the user specifically asks about the system.
""".strip()


    # ========================================================
    # GENERATE
    # ========================================================

    def generate(
        self,
        question,
        context,
        temperature=0.2,
        max_tokens=1200
    ):

        question = str(
            question
        ).strip()

        context = str(
            context
        ).strip()

        if not question:

            return (
                "Please provide a question."
            )

        if not context:

            return (
                "I couldn't find enough "
                "information in the knowledge base."
            )

        messages = [

            {
                "role": "system",
                "content":
                    self.system_prompt()
            },

            {
                "role": "user",
                "content": f"""
Retrieved tourism information:

{context}

User question:

{question}

Answer the user using only the retrieved information.
""".strip()
            }

        ]

        try:

            response = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            )

            answer = (
                response
                .choices[0]
                .message
                .content
            )

            return answer.strip()

        except Exception as e:

            raise RuntimeError(
                f"LLM generation failed: {e}"
            )


# ============================================================
# SIMPLE FACTORY
# ============================================================

def create_llm():

    return EgyptExplorerLLM()