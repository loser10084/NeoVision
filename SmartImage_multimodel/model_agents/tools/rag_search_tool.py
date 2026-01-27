"""
model_agents.tools.rag_search_tool：
    RAG搜索工具
"""
import json
import re
from html.parser import HTMLParser
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from langchain_core.tools import tool

from data_storage import retrieve_documents
from .. import llm
from utils import logger


@tool
def rag_search(query: str) -> str:
    """Search internal RAG documents and return relevant snippets."""
    logger.info(f"[rag_search] query={query}")
    docs = retrieve_documents(query)
    # logger.debug(f"[rag_search] docs={docs}")
    return llm.format_context(docs)