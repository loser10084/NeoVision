"""
data_storage.RAG.engine
    原rag.py
"""

from functools import lru_cache
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

import config


def build_embeddings():
    return OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL_NAME,
        base_url=config.OPENAI_BASE_URL,
        api_key=config.OPENAI_API_KEY,
        )


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=config.RAG_COLLECTION,
        embedding_function=build_embeddings(),
        persist_directory=str(config.RAG_PERSIST_DIR),
    )


def retrieve_documents(query: str, top_k: int = config.RAG_TOP_K, score_threshold: float = config.RAG_SCORE_THRESHOLD):
    """
    从RAG中检索与查询相关的文档
    新增参数：top_k：返回的文档数量
    新增参数：score_threshold：文档相似度阈值
    """
    if not query:
        return []
    vs = get_vectorstore()
    retriever = vs.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": top_k, "score_threshold": score_threshold},
    )
    return retriever.invoke(query)
