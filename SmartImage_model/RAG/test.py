import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_BASE_URL"]=os.getenv("OPENAI_BASE_URL")

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "zhiying_rag_demo"


def build_embeddings():
        return OpenAIEmbeddings(model="text-embedding-3-small")

def main():
    embeddings = build_embeddings()
    vs = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )

    query = "GTV、CTV、PTV有什么区别？"

    # 1) 普通相似度检索
    docs = vs.similarity_search(query, k=5)
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
