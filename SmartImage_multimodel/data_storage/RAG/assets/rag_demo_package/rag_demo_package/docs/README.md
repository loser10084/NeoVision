# RAG Demo 数据包（Redis Stack / LangChain 采集格式示例）

生成日期：2025-12-20

## 内容结构
- docs/
  - guideline_target_volume_demo.md：公开资料整理的“靶区体积概念 + 同行评审要点”（含YAML头）
  - checklist_head_neck_peer_review_demo.yaml：头颈部同行评审检查清单（YAML）
  - faq_demo.yaml：FAQ数据集（YAML）
  - failure_cases_demo.yaml：匿名化失败案例库（合成示例，YAML）
- data/
  - faq_demo.xlsx：FAQ同内容的Excel格式
- schema/
  - document_meta.schema.json：文档元数据最小JSON Schema
  - faq_item.schema.json：FAQ条目最小JSON Schema

## 数据来源（公开）
- RCR Guidance: *Radiotherapy target volume definition and peer review, second edition* (Oct 2022)
- SEER Glossary: *Clinical target volume (CTV)*

> 仅用于软件演示与信息检索；不可用于临床决策。

## 入库建议（给RAG工程）
1. 文档型（guideline md）：按标题切分为chunk，保留 section_path / source_uri / version 等metadata
2. 表单型（faq、checklist、failure cases）：每条作为一个chunk或“Q+Answer”拼接入库
3. 检索时建议用 metadata filter：disease_site、access_level、version/effective_date
