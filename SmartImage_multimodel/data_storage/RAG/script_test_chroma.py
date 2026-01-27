
"""
script_init_chroma.py
    测试Chroma数据库的脚本（可单独运行）
"""



import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from data_storage.RAG.engine import retrieve_documents

load_dotenv()
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_BASE_URL"]=os.getenv("OPENAI_BASE_URL")
os.environ["EMBEDDING_MODEL_NAME"]=os.getenv("EMBEDDING_MODEL_NAME")

ROOT = Path(__file__).parent
PERSIST_DIR = str(ROOT / "chroma_db")
COLLECTION_NAME = "zhiying_rag_demo"
RAG_TOP_K = os.getenv("RAG_TOP_K")

def build_embeddings():
        return OpenAIEmbeddings(
            model=os.environ["EMBEDDING_MODEL_NAME"],
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
        )


def main():
    embeddings = build_embeddings()
    vs = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )


    # query = "GTV、CTV、PTV有什么区别？"
    query = "靶区勾画 基本概念 GTV CTV PTV OAR PRV"

    # 1) 普通相似度检索
    docs = vs.similarity_search(query, k=5)
    # 打印原docs
    print("\n=== Top-5 ===")
    for i, d in enumerate(docs, 1):
        print(f"[{i}] doc_type={d.metadata.get('doc_type')} access={d.metadata.get('access_level')} file={d.metadata.get('file_name')}")
        print(d.page_content[:200])
        print()

    # 2) 带过滤（示例：只看 doc_type=faq）
    docs2 = vs.similarity_search(
        query,
        k=5,
        filter={"doc_type": "faq"}   # Chroma 的 metadata filter
    )
    print("\n=== Top-5 (filter: doc_type=faq) ===")
    for i, d in enumerate(docs2, 1):
        print(f"[{i}] qa_id={d.metadata.get('qa_id')} file={d.metadata.get('file_name')}")
        print(d.page_content[:200])
        print()


if __name__ == "__main__":
    
    main()
