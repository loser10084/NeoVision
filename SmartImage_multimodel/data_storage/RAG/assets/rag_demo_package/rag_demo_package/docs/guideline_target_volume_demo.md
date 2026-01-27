---
doc_id: PUBLIC_GUIDE_TARGETVOLUME_2022_RCR_DEMO
title: 放疗靶区体积（GTV/CTV/ITV/PTV）与同行评审要点（公开资料整理·Demo）
doc_type: guideline
disease_site: general
version: demo_v1
effective_date: 2022-10-01
publisher: Demo (compiled)
owner: demo_user
reviewer: demo_user
source_uri:
  - https://www.rcr.ac.uk/media/bpvngu2n/rcr-publications_radiotherapy-target-volume-definition-and-peer-review-second-edition-rcr-guidance_october-2022.pdf
  - https://seer.cancer.gov/seertools/glossary/view/5532f75ae4b0e16303c8fb8e/
copyright: public_summary_only
access_level: public
language: zh
tags: ["GTV","CTV","ITV","PTV","OAR","peer review","QA"]
summary: |
  基于公开来源（RCR 2022 指南与 SEER 术语表）整理放疗靶区体积概念与同行评审关键点。
  仅用于RAG Demo，不可用于临床决策。
compiled_date: 2025-12-20
---

# 1. 目的与适用范围
本文为 **RAG Demo** 用的公开资料整理：介绍 GTV/CTV/ITV/PTV 与 OAR 的基本概念，以及为什么需要对靶区勾画进行质量保证（QA）与同行评审（peer review）。

> 免责声明：以下内容为公开资料的**摘要与转述**，用于软件演示与信息检索，不构成医疗建议或临床处方。

# 2. 关键体积概念（概念卡片）
## 2.1 GTV（Gross Target Volume / 大体肿瘤体积）
- 定义要点：GTV 指“肉眼/影像可见或可证实的恶性病灶范围”，是后续 CTV、PTV 推导的起点。
- 实务提示：GTV 若遗漏，后续 CTV/PTV 可能“放大错误”，导致地理性漏照风险增加。

**来源**：RCR 2022 在“Defining target volumes / GTV”处给出定义与强调其作为链路起点的重要性。

## 2.2 CTV（Clinical Target Volume / 临床靶体积）
- 定义要点：CTV 包含“可见病灶（GTV）以及需要被消灭的亚临床/微小病灶风险区域”，目的是实现治愈或缓解。
- 实务提示：CTV 设计高度依赖肿瘤生物学与解剖屏障，常存在个体差异；应尽量使用共识协议/图谱来减少不必要变异。

**来源**：RCR 2022 与 SEER Glossary 对 CTV 的表述一致，均强调“GTV + 亚临床微小病灶风险”。

## 2.3 ITV（Internal Target Volume / 内靶体积）
- 定义要点：ITV = CTV + internal margin，用于覆盖器官运动、充盈等引起的 CTV 相对参考框架（常以骨性结构）的位置变化。
- 适用场景：呼吸运动明显的部位（如肺/食管）常用 4D-CT 等估计运动范围。

**来源**：RCR 2022 “ITV – internal target volume”。

## 2.4 PTV（Planning Target Volume / 计划靶体积）
- 定义要点（实务化描述）：PTV 是在 CTV 或 ITV 的基础上加入与摆位误差、系统/随机误差相关的安全边界，用于保证“处方剂量实际覆盖到 CTV”。
- 实务提示：
  - 部门应定期审计系统/随机误差，用以计算 CTV–PTV margin；
  - PTV 通常从 CTV/ITV 扩展得到，扩展后一般不再随意编辑；如为满足 OAR 约束发生妥协，应在计划中体现而不是“把 PTV 改小”。

**来源**：RCR 2022 “PTV – planning target volume” 章节强调 margin 审计与 PTV 处理原则。

## 2.5 OAR（Organs At Risk / 危及器官）与 PRV
- OAR：放疗计划中需要特别保护、尽量避免超过耐受剂量的正常组织结构。
- PRV：对某些关键 OAR（如脊髓/视神经等）可添加 margin，形成 PRV，用于考虑不确定性并降低严重并发症风险。

**来源**：RCR 2022 “OAR – organs at risk” 与 PRV 描述。

# 3. 为什么需要同行评审（Peer Review）
- 靶区勾画是放疗链路中的关键环节：勾画过小可能漏照影响控制率，勾画过大增加正常组织照射与毒性风险。
- 定义靶区需要综合临床信息、影像、微小浸润路径与位置误差等因素，天然存在变异与偏差。
- 建议建立**可审计、标准化**的同行评审流程，并记录结果以便年度审计与持续改进（含复发模式回顾）。

**来源**：RCR 2022 引言与建议条目（含标准化 peer review outcome record 模板的建议）。

# 4. Head & Neck（头颈部）示例：靶区命名（示例）
> 下列仅展示“命名与分层思路”的示例（非剂量处方建议）：例如按风险层次建立多个 CTV/PTV（如高/中/低剂量区）。

RCR 2022 附录提供了头颈治疗的示例 contour labels（如 GTV、CTV_65、PTV_65、CTV_60、PTV_60 等）。

**来源**：RCR 2022 Appendix “Sample contouring labels”。

# 5. 建议的 RAG 入库切分（给工程用）
- 按章节切分：GTV/CTV/ITV/PTV/OAR/peer review recommendations/appendix
- chunk_size（中文）：建议 800–1200 字；overlap 100–150
- 元数据：doc_type, version, effective_date, section_title, section_path, access_level, source_uri

