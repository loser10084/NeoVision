import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
SYSTEM_PROMPT_PATH = Path(os.getenv("SYSTEM_PROMPT_PATH", BASE_DIR / "system_prompt.md"))
IMAGE_SYSTEM_PROMPT_PATH = Path(os.getenv("IMAGE_SYSTEM_PROMPT_PATH", ""))

def load_system_prompt() -> str:
    prompt_path = SYSTEM_PROMPT_PATH
    prompt_text = ""
    if prompt_path.is_file():
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
    if prompt_text:
        return prompt_text
    return os.getenv("SYSTEM_PROMPT", "")

SYSTEM_PROMPT = load_system_prompt()

def load_image_system_prompt() -> str:
    prompt_path = IMAGE_SYSTEM_PROMPT_PATH
    prompt_text = ""
    if prompt_path and prompt_path.is_file():
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
    if prompt_text:
        return prompt_text
    return os.getenv("IMAGE_SYSTEM_PROMPT", "")

IMAGE_SYSTEM_PROMPT = load_image_system_prompt()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
TOKEN_KEY_PREFIX = "auth:token:"
CHAT_HISTORY_KEY_PREFIX = "chat:history:"
CHAT_HISTORY_TTL_SECONDS = int(os.getenv("CHAT_HISTORY_TTL_SECONDS", "3600"))
CHAT_SUMMARY_KEY_PREFIX = "chat:summary:"
CHAT_HISTORY_MAX_TOKENS = int(os.getenv("CHAT_HISTORY_MAX_TOKENS", "1200"))


RAG_PERSIST_DIR = Path(os.getenv("RAG_PERSIST_DIR", BASE_DIR / "RAG" / "chroma_db"))
RAG_COLLECTION = os.getenv("RAG_COLLECTION", "zhiying_rag_demo")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.3"))

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
IMAGE_MODEL_NAME = os.getenv("IMAGE_MODEL_NAME", "gpt-5-mini")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "60"))
