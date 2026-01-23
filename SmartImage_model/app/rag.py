from functools import lru_cache
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from . import config


def build_embeddings():
    return OpenAIEmbeddings(model="text-embedding-3-small")


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=config.RAG_COLLECTION,
        embedding_function=build_embeddings(),
        persist_directory=str(config.RAG_PERSIST_DIR),
    )


def retrieve_documents(query: str):
    if not query:
        return []
    vs = get_vectorstore()
    retriever = vs.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": config.RAG_TOP_K, "score_threshold": config.RAG_SCORE_THRESHOLD},
    )
    return retriever.invoke(query)
