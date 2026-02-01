from utils import logger
"""
全局配置环境
"""

### 基础路径与环境加载
import os
from pathlib import Path
from dotenv import load_dotenv

# 定位项目根目录
BASE_DIR = Path(__file__).resolve().parents[0]
print(f"Current Base Directory: {BASE_DIR}")

# 从 .env 文件加载环境变量
load_dotenv(BASE_DIR / ".env")





### AI 模型接口配置 (LLM Settings)
# API 访问凭据
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

# 模型名称定义
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")           # 默认文本模型
IMAGE_MODEL_NAME = os.getenv("IMAGE_MODEL_NAME", "gpt-5-mini") # 图像处理模型
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small") # 向量模型

# 模型运行参数
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.2")) # 生成温度 (控制随机性)
MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "60"))           # 接口超时时间




### 系统提示词配置 (Prompt Management)
# 提示词文件路径
SYSTEM_PROMPT_PATH = Path(os.getenv("SYSTEM_PROMPT_PATH", BASE_DIR / "system_prompt.md"))
IMAGE_SYSTEM_PROMPT_PATH = Path(os.getenv("IMAGE_SYSTEM_PROMPT_PATH", ""))

def load_system_prompt() -> str:
    """加载通用文本系统提示词"""
    prompt_path = SYSTEM_PROMPT_PATH
    prompt_text = ""
    if prompt_path.is_file():
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
    if prompt_text:
        return prompt_text
    return os.getenv("SYSTEM_PROMPT", "")

def load_image_system_prompt() -> str:
    """加载图像处理专用系统提示词"""
    prompt_path = IMAGE_SYSTEM_PROMPT_PATH
    prompt_text = ""
    if prompt_path and prompt_path.is_file():
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
    if prompt_text:
        return prompt_text
    return os.getenv("IMAGE_SYSTEM_PROMPT", "")

# 预加载提示词内容
SYSTEM_PROMPT = load_system_prompt()
IMAGE_SYSTEM_PROMPT = load_image_system_prompt()

# 聊天配置
SHOW_TOOL_CALLS = os.getenv("SHOW_TOOL_CALLS", "false").lower() == "true"











### 缓存与会话管理 (Redis Settings)
# Redis 连接基础配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

# Redis Key 前缀与策略
TOKEN_KEY_PREFIX = "auth:token:"              # 鉴权 Token 前缀
CHAT_HISTORY_KEY_PREFIX = "chat:history:"     # 聊天历史记录前缀
CHAT_SUMMARY_KEY_PREFIX = "chat:summary:"     # 会话摘要前缀

# 历史记录限制
CHAT_HISTORY_TTL_SECONDS = int(os.getenv("CHAT_HISTORY_TTL_SECONDS", "3600")) # 过期时间 (1小时)
CHAT_HISTORY_MAX_TOKENS = int(os.getenv("CHAT_HISTORY_MAX_TOKENS", "1200"))   # 最大保存 Token 数






### 检索增强生成配置 (RAG Settings)
# 向量数据库存储路径
RAG_PERSIST_DIR = Path(os.getenv("RAG_PERSIST_DIR", BASE_DIR/ "data_storage" / "RAG" / "chroma_db"))
logger.info(f"RAG_PERSIST_DIR: {RAG_PERSIST_DIR}")

# RAG 检索参数
RAG_COLLECTION = os.getenv("RAG_COLLECTION", "zhiying_rag_demo") # 集合(表)名称
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))                   # 检索最相似的文档数量
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.3")) # 相似度分数阈值














