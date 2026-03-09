from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from utils import logger

BASE_DIR = Path(__file__).resolve().parents[0]
print(f"Current Base Directory: {BASE_DIR}")

load_dotenv(BASE_DIR / ".env")

# API / LLM settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")

# Segmentation model settings
SEG_MODEL_DIR = os.getenv("SEG_MODEL_DIR", "")
SEG_WEIGHTS_PATH = os.getenv("SEG_WEIGHTS_PATH", "")
SEG_DEVICE = os.getenv("SEG_DEVICE", "cpu")
SEG_LABEL_CLASS = int(os.getenv("SEG_LABEL_CLASS", "1"))
SEG_MODALITY_DIR = os.getenv("SEG_MODALITY_DIR", "")

# CTV refine/expand model settings
CTV_MODEL_DIR = os.getenv("CTV_MODEL_DIR", "")
CTV_PYTHON = os.getenv("CTV_PYTHON", "")
CTV_REFINE_SCRIPT = os.getenv("CTV_REFINE_SCRIPT", "")
CTV_EXPAND_SCRIPT = os.getenv("CTV_EXPAND_SCRIPT", "")
CTV_UNET_CKPT = os.getenv("CTV_UNET_CKPT", "")
CTV_REFINE_CKPT = os.getenv("CTV_REFINE_CKPT", "")
CTV_DEVICE = os.getenv("CTV_DEVICE", "")
CTV_EXPANSION_MM = float(os.getenv("CTV_EXPANSION_MM", "1"))
CTV_SPACING_MM = os.getenv("CTV_SPACING_MM", "")
CTV_CONF_SCRIPT = os.getenv("CTV_CONF_SCRIPT", "")
CTV_CONF_SLICE_INDEX = int(os.getenv("CTV_CONF_SLICE_INDEX", "80"))
CTV_CONF_NORMALIZE = os.getenv("CTV_CONF_NORMALIZE", "true").lower() == "true"

# CPDM CT->PET settings
CPDM_ROOT_DIR = os.getenv("CPDM_ROOT_DIR", "")
CPDM_PYTHON = os.getenv("CPDM_PYTHON", "")
CPDM_TEMPLATE_CONFIG = os.getenv("CPDM_TEMPLATE_CONFIG", "")
CPDM_MODEL_CKPT = os.getenv("CPDM_MODEL_CKPT", "")
CPDM_VQGAN_CKPT = os.getenv("CPDM_VQGAN_CKPT", "")
CPDM_UNET_CKPT = os.getenv("CPDM_UNET_CKPT", "")
CPDM_GPU_IDS = os.getenv("CPDM_GPU_IDS", "-1")
CPDM_SAMPLE_STEP = int(os.getenv("CPDM_SAMPLE_STEP", "200"))
CPDM_TIMEOUT_SECONDS = int(os.getenv("CPDM_TIMEOUT_SECONDS", "1800"))
CPDM_MPLCONFIGDIR = os.getenv("CPDM_MPLCONFIGDIR", "")
CPDM_KEEP_JOB_DIR = os.getenv("CPDM_KEEP_JOB_DIR", "false").lower() == "true"

# Model names and runtime options
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
IMAGE_MODEL_NAME = os.getenv("IMAGE_MODEL_NAME", "gpt-5-mini")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "60"))

# Prompt settings
SYSTEM_PROMPT_PATH = Path(os.getenv("SYSTEM_PROMPT_PATH", str(BASE_DIR / "system_prompt.md")))
IMAGE_SYSTEM_PROMPT_PATH = Path(os.getenv("IMAGE_SYSTEM_PROMPT_PATH", ""))


def load_system_prompt() -> str:
    """Load text system prompt from file or environment."""
    prompt_text = ""
    if SYSTEM_PROMPT_PATH.is_file():
        prompt_text = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    if prompt_text:
        return prompt_text
    return os.getenv("SYSTEM_PROMPT", "")


def load_image_system_prompt() -> str:
    """Load image system prompt from file or environment."""
    prompt_text = ""
    if IMAGE_SYSTEM_PROMPT_PATH and IMAGE_SYSTEM_PROMPT_PATH.is_file():
        prompt_text = IMAGE_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    if prompt_text:
        return prompt_text
    return os.getenv("IMAGE_SYSTEM_PROMPT", "")


SYSTEM_PROMPT = load_system_prompt()
IMAGE_SYSTEM_PROMPT = load_image_system_prompt()
SHOW_TOOL_CALLS = os.getenv("SHOW_TOOL_CALLS", "false").lower() == "true"

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

TOKEN_KEY_PREFIX = "auth:token:"
CHAT_HISTORY_KEY_PREFIX = "chat:history:"
CHAT_SUMMARY_KEY_PREFIX = "chat:summary:"

CHAT_HISTORY_TTL_SECONDS = int(os.getenv("CHAT_HISTORY_TTL_SECONDS", "3600"))
CHAT_HISTORY_MAX_TOKENS = int(os.getenv("CHAT_HISTORY_MAX_TOKENS", "1200"))

# RAG settings
RAG_PERSIST_DIR = Path(os.getenv("RAG_PERSIST_DIR", str(BASE_DIR / "data_storage" / "RAG" / "chroma_db")))
logger.info(f"RAG_PERSIST_DIR: {RAG_PERSIST_DIR}")
RAG_COLLECTION = os.getenv("RAG_COLLECTION", "zhiying_rag_demo")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.3"))
