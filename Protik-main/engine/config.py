import os
from pathlib import Path


def load_dotenv(dotenv_path: Path | None = None):
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parents[1] / ".env"
    if not dotenv_path.exists():
        return

    with dotenv_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            if key not in os.environ:
                os.environ[key] = value


load_dotenv()

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", os.getenv("AssistantName", "jarvis"))
LLM_KEY = os.getenv("LLM_KEY", "AIzaSyD_U56TaM3KENVO-r1-Ex_0-hNOCCBkTNA")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", os.getenv("CohereAPIKey"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", os.getenv("GroqAPIKey"))
USERNAME = os.getenv("Username")
SYSTEM_PROMPT = """Hello, I am Protik, You are a very accurate and advanced AI chatbot named Jarvis which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, answer only the main point, and keep your response short.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""