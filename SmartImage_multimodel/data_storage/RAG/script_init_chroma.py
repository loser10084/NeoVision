"""
script_init_chroma.py
    初始化Chroma数据库脚本（单独运行）
    将assets下的某个目录下的所有文件加载到Chroma数据库中
"""



import os
from pathlib import Path
from typing import List, Any, Dict
import json
from datetime import date, datetime

import yaml
import pandas as pd
import frontmatter
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings



load_dotenv()
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_BASE_URL"]=os.getenv("OPENAI_BASE_URL")
os.environ["OPENAI_EMBEDDING_MODEL_NAME"]=os.getenv("EMBEDDING_MODEL_NAME")


# --------- 配置区 ----------
ROOT = Path(__file__).parent
BASE_DIR = ROOT / "assets/rag_demo_package/rag_demo_package"            # 解压后的目录
PERSIST_DIR = ROOT / "chroma_db"               # 本地持久化目录
COLLECTION_NAME = "zhiying_rag_demo"            # collection 名称


print(BASE_DIR)
print(PERSIST_DIR)
print(COLLECTION_NAME)
# -------------------------

def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for key, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        elif isinstance(value, (date, datetime)):
            clean[key] = value.isoformat()
        elif isinstance(value, (list, tuple, set, dict)):
            clean[key] = json.dumps(value, ensure_ascii=True)
        else:
            clean[key] = str(value)
    return clean


def load_guideline_markdown(md_path: Path) -> List[Document]:
    post = frontmatter.load(md_path)
    meta = dict(post.metadata or {})
    content = post.content or ""

    meta.setdefault("source_uri", str(md_path))
    meta.setdefault("doc_type", "guideline")
    meta.setdefault("access_level", "public")
    meta.setdefault("version", "demo_v1")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=120,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
    )
    chunks = splitter.split_text(content)

    docs: List[Document] = []
    for i, ch in enumerate(chunks):
        m = dict(meta)
        m["chunk_index"] = i
        m["file_name"] = md_path.name
        docs.append(Document(page_content=ch, metadata=sanitize_metadata(m)))
    return docs


def load_yaml_dataset(yaml_path: Path) -> List[Document]:
    obj = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    doc_type = obj.get("doc_type", "unknown")
    version = obj.get("version", "demo_v1")
    disease_site = obj.get("disease_site", obj.get("scope", "general"))
    access_level = obj.get("access_level", "public")
    source_uri = obj.get("source_uri", str(yaml_path))

    items = obj.get("items", [])
    docs: List[Document] = []

    if doc_type == "faq":
        for it in items:
            text = f"Q: {it.get('question','')}\nA: {it.get('answer','')}"
            meta = {
                "doc_type": "faq",
                "qa_id": it.get("qa_id"),
                "role": it.get("role"),
                "trigger": it.get("trigger"),
                "tags": it.get("tags"),
                "access_level": it.get("access_level", access_level),
                "last_updated": it.get("last_updated"),
                "doc_refs": it.get("doc_refs"),
                "version": version,
                "disease_site": disease_site,
                "source_uri": source_uri,
                "file_name": yaml_path.name,
            }
            docs.append(Document(page_content=text, metadata=sanitize_metadata(meta)))

    elif doc_type in ("hospital_sop", "checklist"):
        for it in items:
            text = f"检查项: {it.get('item','')}\n严重程度: {it.get('severity','')}\n参考: {it.get('refs','')}"
            meta = {
                "doc_type": "checklist",
                "checklist_id": obj.get("checklist_id"),
                "item_id": it.get("id"),
                "severity": it.get("severity"),
                "access_level": access_level,
                "version": version,
                "disease_site": disease_site,
                "source_uri": source_uri,
                "file_name": yaml_path.name,
            }
            docs.append(Document(page_content=text, metadata=sanitize_metadata(meta)))

    elif doc_type == "failure_case":
        for it in items:
            text = (
                f"场景: {it.get('scenario','')}\n"
                f"症状: {it.get('symptom','')}\n"
                f"可能原因: {it.get('likely_causes','')}\n"
                f"建议复核: {it.get('recommended_checks','')}\n"
                f"严重程度: {it.get('severity','')}\n"
                f"标签: {it.get('tags','')}\n"
                f"模型版本: {it.get('model_version','')}"
            )
            meta = {
                "doc_type": "failure_case",
                "case_id": it.get("case_id"),
                "severity": it.get("severity"),
                "tags": it.get("tags"),
                "model_version": it.get("model_version"),
                "anonymization": obj.get("anonymization", "unknown"),
                "access_level": obj.get("access_level", access_level),
                "version": version,
                "disease_site": disease_site,
                "source_uri": source_uri,
                "file_name": yaml_path.name,
            }
            docs.append(Document(page_content=text, metadata=sanitize_metadata(meta)))

    else:
        meta = {
            "doc_type": doc_type,
            "version": version,
            "disease_site": disease_site,
            "access_level": access_level,
            "source_uri": source_uri,
            "file_name": yaml_path.name,
        }
        docs.append(Document(page_content=yaml.safe_dump(obj, allow_unicode=True), metadata=sanitize_metadata(meta)))

    return docs


def load_excel_faq(xlsx_path: Path) -> List[Document]:
    df = pd.read_excel(xlsx_path, sheet_name="faq")
    docs: List[Document] = []
    for _, row in df.iterrows():
        text = f"Q: {row.get('question','')}\nA: {row.get('answer','')}"
        meta = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        meta.update({"doc_type": "faq", "source_uri": str(xlsx_path), "file_name": xlsx_path.name})
        docs.append(Document(page_content=text, metadata=sanitize_metadata(meta)))
    return docs


def build_embeddings():
        # return OpenAIEmbeddings(model="text-embedding-3-small")
        return OpenAIEmbeddings(
            model=os.environ["OPENAI_EMBEDDING_MODEL_NAME"],
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
        )


def main():
    if not BASE_DIR.exists():
        raise FileNotFoundError(f"BASE_DIR not found: {BASE_DIR.resolve()}")

    docs: List[Document] = []

    md = BASE_DIR / "docs" / "guideline_target_volume_demo.md"
    if md.exists():
        docs.extend(load_guideline_markdown(md))

    for y in (BASE_DIR / "docs").glob("*.yaml"):
        docs.extend(load_yaml_dataset(y))

    xlsx = BASE_DIR / "data" / "faq_demo.xlsx"
    if xlsx.exists():
        docs.extend(load_excel_faq(xlsx))

    print(f"Prepared documents: {len(docs)}")

    embeddings = build_embeddings()

    # ✅ 关键：persist_directory + collection_name
    vs = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(PERSIST_DIR),
    )

    # 入库
    vs.add_documents(docs)
    print(f"Done. Chroma collection='{COLLECTION_NAME}', persist_dir='{PERSIST_DIR}'")



if __name__ == "__main__":
    main()
